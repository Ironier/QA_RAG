from flask import Flask, request, jsonify
from flask_cors import CORS
from py2neo import Graph as NeoGraph
import networkx as nx
import hashlib
import configparser

app = Flask(__name__)
CORS(app)

# 读取配置文件
config = configparser.ConfigParser()
config.read('./config.ini')

# 连接 Neo4j
neo4j_uri = config['neo4j']['uri']
neo4j_user = config['neo4j']['username']
neo4j_pass = config['neo4j']['password']
neo_graph = NeoGraph(neo4j_uri, auth=(neo4j_user, neo4j_pass))

# 从 Neo4j 中构建 NetworkX 图
def load_graph_from_neo4j():
    G = nx.Graph()
    query = """
    MATCH (n)-[r]->(m)
    RETURN n, r, m
    LIMIT 1000
    """
    results = neo_graph.run(query)

    for record in results:
        n = record['n']
        m = record['m']
        r = record['r']
        n_id = str(n.identity)  # 转字符串
        m_id = str(m.identity)

        # 将节点属性转为 dict
        n_attrs = dict(n)
        m_attrs = dict(m)

        G.add_node(n_id, **n_attrs)
        G.add_node(m_id, **m_attrs)
        G.add_edge(n_id, m_id, **dict(r))

    return G

G = load_graph_from_neo4j()

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def filter_graph(G, node_keyword='', edge_keyword='', max_nodes=100):
    subG = nx.Graph()
    for u, v, data in G.edges(data=True):
        if edge_keyword and edge_keyword not in str(data.get("keywords", "")):
            continue
        subG.add_edge(u, v, **data)

    nodes_to_keep = set(subG.nodes())
    for node_id, attrs in G.nodes(data=True):
        if node_keyword and node_keyword not in node_id and node_id not in nodes_to_keep:
            continue
        subG.add_node(node_id, **attrs)

    if subG.number_of_nodes() > max_nodes:
        nodes_sorted = sorted(subG.degree, key=lambda x: x[1], reverse=True)[:max_nodes]
        allowed_nodes = set([n for n, deg in nodes_sorted])
        filteredG = nx.Graph()
        for n in allowed_nodes:
            filteredG.add_node(n, **subG.nodes[n])
        for u, v, data in subG.edges(data=True):
            if u in allowed_nodes and v in allowed_nodes:
                filteredG.add_edge(u, v, **data)
        return filteredG

    return subG

def convert_to_vis_format(G):
    nodes = []
    edges = []

    # 这里直接用Neo4j节点ID字符串作为id，无需MD5
    for n, attrs in G.nodes(data=True):
        nodes.append({
            'id': n,
            'label': attrs.get("entity_id", n),
            'title': attrs.get('description', ''),
            'group': attrs.get('type', 'concept'),
            'metadata': attrs
        })

    for u, v, attrs in G.edges(data=True):
        from_node, to_node = sorted([u, v])
        edges.append({
        'id': f"{from_node}_{to_node}",
            'from': u,
            'to': v,
            'label': f"{attrs.get('keywords', '')} : {attrs.get('weight', '')}"
        })

    return {'nodes': nodes, 'edges': edges}

@app.route('/api/graph', methods=['GET'])
def get_graph():
    node_filter = request.args.get('node', '')
    edge_filter = request.args.get('edge', '')
    subgraph = filter_graph(G, node_filter, edge_filter)
    data = convert_to_vis_format(subgraph)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
