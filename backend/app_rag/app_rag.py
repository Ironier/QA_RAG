from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_service import initialize_rag_sync, run_async_in_thread, insert_chunks_into_rag, global_rag, rag_lock
import os
import configparser

app = Flask(__name__)
CORS(app)

g_config = configparser.ConfigParser()
g_config.read("config.ini")  # 这里建议使用相对或绝对路径

# # 设置环境变量以供 Neo4JStorage 使用
# os.environ["NEO4J_URI"] = g_config["neo4j"]["uri"]
# os.environ["NEO4J_USERNAME"] = g_config["neo4j"]["username"]
# os.environ["NEO4J_PASSWORD"] = g_config["neo4j"]["password"]
# os.environ["NEO4J_DATABASE"] = 'neo4j' #Community Edition ONLY contains one database called 'neo4j'

# os.environ["MILVUS_URI"] = g_config["milvus"]["uri"]


# 初始化 RAG（同步阻塞，启动时执行一次）
initialize_rag_sync()

@app.route("/api/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    question = data.get("question")
    mode = data.get("mode", "hybrid")
    if not question:
        return jsonify({"error": "Missing question"}), 400

    try:
        with rag_lock:
            rag = global_rag
            answer = run_async_in_thread(rag.query, question, mode=mode)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/insert", methods=["POST"])
def handle_insert():
    data = request.get_json()
    chunks = data.get("chunks", [])
    if not chunks:
        return jsonify({"error": "Missing chunks"}), 400

    try:
        with rag_lock:
            rag = global_rag
            run_async_in_thread(insert_chunks_into_rag, rag, chunks)
        return jsonify({"message": f"Inserted {len(chunks)} chunks successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
