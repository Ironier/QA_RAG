import asyncio
import threading
import numpy as np
import configparser
from lightrag import LightRAG
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger, EmbeddingFunc

setup_logger("lightrag", level="INFO")

# 读取配置
g_config = configparser.ConfigParser()
g_config.read("config.ini")

import os
# 设置环境变量以供 Neo4JStorage 使用
os.environ["NEO4J_URI"] = g_config["neo4j"]["uri"]
os.environ["NEO4J_USERNAME"] = g_config["neo4j"]["username"]
os.environ["NEO4J_PASSWORD"] = g_config["neo4j"]["password"]
os.environ["NEO4J_DATABASE"] = 'neo4j' #Community Edition ONLY contains one database called 'neo4j'

os.environ["MILVUS_URI"] = g_config["milvus"]["uri"]

# 全局实例
global_rag = None
rag_lock = threading.Lock()

# 嵌入函数
async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embed(
        texts,
        model=g_config["embedding_model"]["name"],
        api_key=g_config["embedding_model"]["api_key"],
        base_url=g_config["embedding_model"]["uri"],
    )

# LLM 生成函数
async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
    return await openai_complete_if_cache(
        g_config["chat_model"]["name"],
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=g_config["chat_model"]["api_key"],
        base_url=g_config["chat_model"]["uri"],
        **kwargs,
    )

# 初始化 RAG
async def initialize_rag_async():
    rag = LightRAG(
        working_dir="./output",
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=embedding_func,
        ),
        llm_model_func=llm_model_func,
        graph_storage="Neo4JStorage",
        vector_storage="MilvusVectorDBStorage",
        vector_db_storage_cls_kwargs={
            "cosine_better_than_threshold": 0.6,
        },
        addon_params={
            "example_number": 5,
            "language": "Simplified Chinese",
            "entity_types": ["organization", "person", "geo", "event", "legal term", "category"],
        },
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

def initialize_rag_sync():
    global global_rag

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(initialize_rag_async())

    if global_rag is None:
        with rag_lock:
            if global_rag is None:
                global_rag = run()
    return global_rag

# 插入 chunk 数据
async def insert_chunks_into_rag(rag, chunks):
    for chunk in chunks:
        rag.insert(chunk["content"])
    print(f"成功插入 {len(chunks)} 个分块到 RAG")

# 提供异步任务在线程中运行的能力
def run_async_in_thread(async_func, *args, **kwargs):
    result_container = {}

    def wrapper():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result_container["result"] = loop.run_until_complete(async_func(*args, **kwargs))

    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join()
    return result_container.get("result", None)

def get_rag_instance():
    global global_rag

    if global_rag is None:
        with rag_lock:
            if global_rag is None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                global_rag = loop.run_until_complete(initialize_rag_sync())
    return global_rag

__all__ = [
    "initialize_rag_sync",
    "insert_chunks_into_rag",
    "run_async_in_thread",
    "get_rag_instance",
]
