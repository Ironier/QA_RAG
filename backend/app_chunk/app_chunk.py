from flask import Flask, request, jsonify
import os
from minio import Minio
from io import BytesIO
from docx import Document
import json
import docx
import markdownify
from docx import Document

import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from pymongo import MongoClient
from flask_cors import CORS
import datetime
import threading
import numpy as np

from lightrag.utils import setup_logger, EmbeddingFunc

import nest_asyncio
nest_asyncio.apply()
# 初始化日志
setup_logger("lightrag", level="INFO")

from app_rag.rag_service import initialize_rag_sync, insert_chunks_into_rag, run_async_in_thread, get_rag_instance


# 配置RAG
# os.environ["HF_DATASETS_CACHE"] = "/path/to/cache"  # 修改为你的缓存路径
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

mongo_client = MongoClient('mongodb://172.27.177.119:27017/')

import configparser
g_config = configparser.ConfigParser()
g_config.read("config.ini")

minio_client = Minio(
    g_config.get("minio", "uri"),
    access_key=g_config.get("minio", "access_key"),
    secret_key=g_config.get("minio", "secret_key"),
    secure=False
)

app = Flask(__name__)
CORS(app)


def get_minio_doc(filename):
    try:
        response = minio_client.get_object('doc', filename)
        docx_bytes = response.read()
        response.close()
        return Document(BytesIO(docx_bytes))
    except Exception as e:
        app.logger.error(f"MinIO获取文件失败: {str(e)}")
        return None

def parse_docx_to_markdown(doc):
    # 0.定义返回对象
    chunk_doc_list = []  # 用于存储叶子标题的完整内容和路径
    last_chunk = None  # 存储上一段内容，以便在前后非标题少文字时与当前段落合并
    temp_chunk = None  # 用于临时保存以冒号结尾的段落
    title_stack = []  # **用于构建标题路径树 list中 每个元素的位置 和自己的level级别对应


    # 2.解析文档内容，包括段落、表格 和 图片
    for element in doc.element.body:
        if isinstance(element.tag, str) and element.tag.endswith("p"):  # 段落
            paragraph = docx.text.paragraph.Paragraph(element, doc)


            # 2.2 处理标题
            if paragraph.style.name.startswith("Heading"):
                # 获取当前目录级别
                level = int(paragraph.style.name.replace("Heading ", "").strip())
                # 获取当前的目录内容
                content = paragraph.text
                # 根据当前的level 把目录放在title_stack正确的位置
                #  2.2.1如果该位置上有值 就替换 例如：level=2 ,content=’标题2‘，title_stack =["XXX1","XXX2"] ,时  需要最终title_stack = ["XXX1","标题2"]
                #  2.2.2 如果该位置上没有值  就新增上去例如：level=2 ,content=’标题2‘，title_stack =["XXX1"] ,时  需要最终title_stack = ["XXX1","标题2"]
                #  特别注意：如果 小于level 在title_stack前没有值 对应位置补充空字符串 例如：level=2 ,content=’标题2‘，title_stack =[] ,时  需要最终title_stack = ["","标题2"]
                # 处理 title_stack，根据标题层级调整
                while len(title_stack) < level:  # 如果层级不足，填充空字符串
                    title_stack.append("")
                if len(title_stack) >= level:  # 确保 title_stack 至少包含当前层级
                    title_stack[level - 1] = content  # 更新当前层级的标题内容
                    # 当前层级后面的标题都清空  避免例如 2级标题 刚解析到  上个阶段的3级标题还在
                    for i in range(level, len(title_stack)):
                        title_stack[i] = ""

                last_chunk = None  # 重置上一段内容，因为是新标题
                temp_chunk = None  # 带有冒号的缓存段落也清理掉

            # 2.3 处理段落文本
            elif paragraph.text.strip():
                # 2.3.0 拿取当前段落内容
                content = markdownify.markdownify(paragraph.text, heading_style="ATX")
                current_chunk = {
                    "title_path": " > ".join(title_stack),
                    "content": content
                }
                # 2.3 判断是否需要合并段落 ：
                if len(paragraph.text.strip()) < 100:
                    # 2.3.1 当前内容少 且以冒号结尾 进入temp_chunk 缓存起来
                    if paragraph.text.strip().endswith(":") or paragraph.text.strip().endswith("："):
                        # 只有此时 生成临时段落
                        # 如果temp_chunk 本身就有内容则累加， 例如 连续冒号，   1： 产品如下：
                        if temp_chunk:
                            temp_chunk["content"] += " \n " + current_chunk["content"]
                        else:
                            temp_chunk = current_chunk
                    # 2.3.2 当前内容少 且不以冒号结尾 =》  在title_path和上一段一致的时候和上一段合并，在title_path和上一段不一致的时候 自成一段
                    else:
                        # 在title_path和上一段一致的时候和上一段合并
                        if last_chunk and last_chunk["title_path"] == current_chunk["title_path"]:
                            # 这里要考虑 消耗temp_chunk的情况
                            if temp_chunk:
                                last_chunk["content"] += " \n " + temp_chunk["content"]
                                temp_chunk = None  # 重置临时段落
                            last_chunk["content"] += " \n " + current_chunk["content"]

                        else:
                            # 在title_path和上一段不一致的时候 自成一段
                            if temp_chunk:
                                temp_chunk["content"] += " \n " + current_chunk["content"]
                                chunk_doc_list.append(temp_chunk)
                                last_chunk = temp_chunk
                                temp_chunk = None  # 重置临时段落
                            else:
                                chunk_doc_list.append(current_chunk)
                                last_chunk = current_chunk  # 更新上一段内容
                else:
                    # 2.3.3 当前内容多 =》 有temp_chunk存在则进行合并  ， 没有则创建新的段落
                    if temp_chunk:
                        temp_chunk["content"] += " \n " + current_chunk["content"]
                        last_chunk = temp_chunk
                        temp_chunk = None  # 重置临时段落
                    else:
                        # 当前段落与上一段不同路径，添加为新的段落
                        chunk_doc_list.append(current_chunk)
                        last_chunk = current_chunk  # 更新上一段内容

        # 3. 处理表格
        elif isinstance(element.tag, str) and element.tag.endswith("tbl"):  # 表格
            table = docx.table.Table(element, doc)
            markdown_table = []
            max_columns = 0  # 用于跟踪最大列数
            # 计算每一行的列数，确保列数一致
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                max_columns = max(max_columns, len(row_cells))  # 更新最大列数
                markdown_table.append(row_cells)

            # 处理每一行，确保列数一致
            for row in markdown_table:
                # 如果当前行列数少于最大列数，填充空单元格
                while len(row) < max_columns:
                    row.append('')  # 填充空列

            # 清理表格内容：移除换行符或将其替换为空格
            for i in range(len(markdown_table)):
                markdown_table[i] = [cell.replace("\n", " ") for cell in markdown_table[i]]

            # 构建 Markdown 表格
            markdown_table = [
                "| " + " | ".join(row) + " |" for row in markdown_table
            ]

            if markdown_table:
                separator = "| " + " | ".join(["---"] * max_columns) + " |"
                markdown_table.insert(1, separator)

                # 将生成的 Markdown 表格内容添加到 chunk_doc_list
                tab_chunk = {
                    "title_path": " > ".join(title_stack),
                    "content": "\n".join(markdown_table)
                }

                # 如果存在temp_chunk，需要合并
                if temp_chunk:
                    temp_chunk["content"] += " \n " + tab_chunk["content"]
                    chunk_doc_list.append(temp_chunk)
                    last_chunk = temp_chunk  # 刷新last_chunk
                    temp_chunk = None  # 重置临时段落
                else:
                    chunk_doc_list.append(tab_chunk)
                    last_chunk = tab_chunk  # 刷新last_chunk

    return chunk_doc_list
def split_sentence(chunk_doc_list):
    nlp = spacy.load("zh_core_web_sm")
    index = 0
    result = []
    for item in chunk_doc_list:
        if ('【' in item['content']):
            continue
        if ('|' in item['content']):
            temp = item['content'].split('\n')
            for line in temp:
                if '|' not in line:
                    continue
                if '-' in line:
                    continue
                if line[0] == ' ':
                    continue
                line = line.replace('|', ':')
                result.append({
                    "id": index,
                    "content": line[1:-1]
                })
                index += 1
            continue
        doc = nlp(item['content'])
        for i, sent in enumerate(doc.sents):
            if (sent.text == "" or sent.text == '\n ' or sent.text == ' \n '):
                continue
            result.append({
                "id": index,
                "content": sent.text
            })
            index += 1
    return result
def group(load_dict):
    sentence = load_dict[0]['content']
    result = []
    index = 1
    for i in range(1, len(load_dict)):
        text1 = load_dict[i - 1]['content']
        text2 = load_dict[i]['content']
        # 计算文本的 TF-IDF 特征向量
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        #print(cosine_sim)
        if (cosine_sim[0][0] > 0):
            sentence += text2
        else:
            result.append({
                "id": index,
                "content": sentence,
                "updateTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            index += 1
            sentence = text2
    return result
def mongo_insert(filename,grouped_result):
    filename=filename.replace(".","_")
    db=mongo_client['blocks']
    if filename in db.list_collection_names():
        db[filename].drop()
    product_collection = db[filename]
    product_collection.insert_many(grouped_result)


@app.route('/api/block', methods=['GET'])
def run_script():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"code": 400, "msg": "缺少必要参数: filename"}), 400

    try:
        doc = get_minio_doc(filename)
        if not doc:
            return jsonify({"code": 500, "msg": "文件获取失败"}), 500

        chunks = parse_docx_to_markdown(doc)
        sentences = split_sentence(chunks)
        grouped_result = group(sentences)

        # 保存到MongoDB
        mongo_insert(filename, grouped_result)

        # 将分块加入RAG
        try:
            run_async_in_thread(insert_chunks_into_rag, get_rag_instance(), grouped_result)

        except Exception as e:
            app.logger.error(f"插入RAG失败: {str(e)}")
            # 可以选择记录错误但继续处理
            return jsonify({
                "code": 200,
                "msg": "处理成功但RAG插入失败",
                "rag_error": str(e)
            })

        return jsonify({
            "code": 200,
            "msg": "处理成功",
        })
    except Exception as e:
        app.logger.error(f"处理异常: {str(e)}")
        return jsonify({"code": 500, "msg": f"处理失败: {str(e)}"}), 500

# ... [保留原有的get_minio_doc, parse_docx_to_markdown, split_sentence, group, mongo_insert函数] ...

if __name__ == '__main__':
    # 在应用启动时初始化RAG
    initialize_rag_sync()
    app.run(host='0.0.0.0', port=5000)