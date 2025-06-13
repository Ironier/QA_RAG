<template>
  <div class="graph-container">
    <!-- 搜索工具栏 -->
    <div class="toolbar">
      <el-input v-model="nodeFilter" placeholder="节点关键词" style="width: 200px" />
      <el-input v-model="edgeFilter" placeholder="边关键词" style="width: 200px" />
      <el-button type="primary" icon="el-icon-search" @click="fetchGraph">搜索</el-button>
      <el-button icon="el-icon-refresh" @click="fetchGraph">刷新</el-button>
      <el-button icon="el-icon-download" @click="exportGraph">导出图谱</el-button>
    </div>

    <!-- 图谱视图 -->
    <div class="vis-embed">
      <div id="graph" class="graph-canvas"></div>
      <div v-if="loading" class="loading-overlay">
        <i class="el-icon-loading"></i>
        <span>加载知识图谱中...</span>
      </div>
    </div>

    <!-- 右侧节点信息 -->
    <div class="graph-info">
      <el-card shadow="never">
        <div slot="header" class="card-header">
          <span>当前节点信息</span>
          <el-tag :type="nodeTypeClass">{{ nodeType }}</el-tag>
        </div>

        <div v-if="currentNode.name" class="node-details">
          <h3>{{ currentNode.name }}</h3>
          <p>{{ currentNode.description }}</p>
          <div class="node-stats">
            <el-statistic title="关联节点" :value="currentNode.relatedCount" />
            <el-statistic title="重要度" :value="currentNode.importance" />
          </div>
        </div>

        <div v-else class="empty-node">
          <el-empty description="点击图谱中的节点查看详情" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { Network } from 'vis-network/standalone';
import _ from 'lodash';
import GraphStyle from '@/styles/graphStyle';

export default {
  data() {
    return {
      loading: true,
      currentNode: {},
      network: null,
      nodeFilter: '',
      edgeFilter: '',

      // 使用响应式数据管理图谱数据
      graphData: {
        nodes: [],
        edges: []
      },

      // 保存原始样式，用于重置
      originalStyles: {
        nodes: new Map(),
        edges: new Map()
      },

      // 当前高亮的元素ID
      highlightedElements: {
        nodes: new Set(),
        edges: new Set()
      }
    };
  },

  computed: {
    nodeTypeClass() {
      const map = {
        person: 'success',
        organization: 'warning',
        concept: 'primary',
        event: 'danger',
        location: ''
      };
      return map[this.currentNode.type] || 'info';
    },

    nodeType() {
      const map = {
        person: '人物',
        organization: '组织',
        concept: '概念',
        event: '事件',
        location: '地点'
      };
      return map[this.currentNode.type] || '未知类型';
    }
  },

  methods: {
    async fetchGraph() {
      this.loading = true;
      try {
        const res = await axios.get(`${this.$API.GRAPH}/api/graph`, {
          params: {
            node: this.nodeFilter,
            edge: this.edgeFilter
          }
        });

        // 初始化图谱数据并保存原始样式
        this.initializeGraphData(res.data);
        // 创建网络实例
        this.createNetwork();

        this.loading = false;
      } catch (err) {
        console.error('图谱加载失败', err);
        this.loading = false;
      }
    },

    // 初始化图谱数据和原始样式
    initializeGraphData(rawData) {
      // 清空之前的数据
      this.originalStyles.nodes.clear();
      this.originalStyles.edges.clear();
      this.highlightedElements.nodes.clear();
      this.highlightedElements.edges.clear();

      // 处理节点数据
      this.graphData.nodes = rawData.nodes.map(node => {
        const processedNode = {
          ...node,
          color: { ...GraphStyle.node.default.color },
          font: { ...GraphStyle.node.default.font },
          shape: GraphStyle.node.default.shape
        };

        // 保存原始样式
        this.originalStyles.nodes.set(node.id, {
          color: { ...GraphStyle.node.default.color },
          font: { ...GraphStyle.node.default.font }
        });

        return processedNode;
      });

      // 处理边数据
      this.graphData.edges = rawData.edges.map(edge => {
        // 确保边有唯一ID
        if (!edge.id) {
          const [a, b] = [edge.from, edge.to].map(id => id.toString()).sort();
          edge.id = `${a}-${b}`;
        }

        const processedEdge = {
          ...edge,
          color: { ...GraphStyle.edge.default.color },
          width: GraphStyle.edge.default.width
        };

        // 保存原始样式
        this.originalStyles.edges.set(edge.id, {
          color: { ...GraphStyle.edge.default.color },
          width: GraphStyle.edge.default.width
        });

        return processedEdge;
      });
    },

    // 创建网络实例
    createNetwork() {
      const container = document.getElementById('graph');

      const options = {
        nodes: GraphStyle.node.default,
        edges: GraphStyle.edge.default,
        layout: {
          improvedLayout: true,
          hierarchical: {
            enabled: false,
            nodeSpacing: 150
          }
        },
        interaction: {
          hideEdgesOnDrag: false,
          hover: true
        },
        physics: {
          enabled: true,
          stabilization: {
            enabled: true,
            iterations: 5
          },
          solver: 'repulsion',
          repulsion: {
            nodeDistance: 150,
            centralGravity: 0.5,
            springLength: 150,
            springConstant: 0.08,
            damping: 0.2
          },
          timestep: 0.1
        }
      };

      this.network = new Network(container, this.graphData, options);

      // 使用防抖的点击事件
      this.network.on('click', _.debounce((params) => {
        this.handleNodeClick(params);
      }, 50));
    },

    // 处理节点点击事件
    handleNodeClick(params) {
      // 重置之前的高亮 - 确保完全清理
      this.resetHighlight();

      // 等待重置完成后再进行新的高亮
      this.$nextTick(() => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const nodeData = this.getNodeData(nodeId);
          this.currentNode = nodeData;

          // 短暂延迟确保重置完全生效
          setTimeout(() => {
            this.highlightNode(nodeId);
          }, 50);
        } else {
          this.currentNode = {};
        }
      });
    },

    // 获取节点数据
    getNodeData(nodeId) {
      const node = this.graphData.nodes.find(n => n.id === nodeId);
      if (node && node.metadata) {
        return {
          ...node.metadata,
          name: node.metadata.label || node.label || nodeId
        };
      }
      return { name: nodeId };
    },

    // 高亮节点及其连接（重构版本 - 操作Vue响应式数据）
    highlightNode(targetNodeId) {
      if (!this.network) return;

      const connectedNodeIds = new Set([targetNodeId]);
      const connectedEdgeIds = new Set();

      this.graphData.edges.forEach(edge => {
        if (edge.from === targetNodeId || edge.to === targetNodeId) {
          connectedNodeIds.add(edge.from);
          connectedNodeIds.add(edge.to);
          connectedEdgeIds.add(edge.id);
        }
      });

      const updatedNodes = [];
      connectedNodeIds.forEach(nodeId => {
        const nodeIndex = this.graphData.nodes.findIndex(n => n.id === nodeId);
        if (nodeIndex !== -1) {
          const isMainNode = (nodeId === targetNodeId);
          const targetStyle = isMainNode ? GraphStyle.node.main : GraphStyle.node.connected;

          // 更新 Vue 数据
          this.$set(this.graphData.nodes[nodeIndex], 'color',
            this.deepClone(this.createSafeColorObject(targetStyle.color)));
          this.$set(this.graphData.nodes[nodeIndex], 'font',
            this.deepClone(targetStyle.font));
          this.$set(this.graphData.nodes[nodeIndex], 'borderWidth', isMainNode ? 3 : 2);
          this.$set(this.graphData.nodes[nodeIndex], 'chosen', false);

          updatedNodes.push(this.graphData.nodes[nodeIndex]);
          this.highlightedElements.nodes.add(nodeId);
        }
      });

      const updatedEdges = [];
      connectedEdgeIds.forEach(edgeId => {
        const edgeIndex = this.graphData.edges.findIndex(e => e.id === edgeId);
        if (edgeIndex !== -1) {
          this.$set(this.graphData.edges[edgeIndex], 'color',
            this.deepClone(this.createSafeColorObject(GraphStyle.edge.highlight.color)));
          this.$set(this.graphData.edges[edgeIndex], 'width', GraphStyle.edge.highlight.width);

          updatedEdges.push(this.graphData.edges[edgeIndex]);
          this.highlightedElements.edges.add(edgeId);
        }
      });

      // 通知 vis-network 更新节点和边
      this.network.body.data.nodes.update(updatedNodes);
      this.network.body.data.edges.update(updatedEdges);

      this.focusNode(targetNodeId);
    },

    resetHighlight() {
      if (!this.network) return;

      this.network.unselectAll();

      const updatedNodes = [];
      this.highlightedElements.nodes.forEach(nodeId => {
        const nodeIndex = this.graphData.nodes.findIndex(n => n.id === nodeId);
        const originalStyle = this.originalStyles.nodes.get(nodeId);
        if (nodeIndex !== -1 && originalStyle) {
          this.$set(this.graphData.nodes[nodeIndex], 'color', this.deepClone(originalStyle.color));
          this.$set(this.graphData.nodes[nodeIndex], 'font', this.deepClone(originalStyle.font));
          updatedNodes.push(this.graphData.nodes[nodeIndex]);
        }
      });

      const updatedEdges = [];
      this.highlightedElements.edges.forEach(edgeId => {
        const edgeIndex = this.graphData.edges.findIndex(e => e.id === edgeId);
        const originalStyle = this.originalStyles.edges.get(edgeId);
        if (edgeIndex !== -1 && originalStyle) {
          this.$set(this.graphData.edges[edgeIndex], 'color', this.deepClone(originalStyle.color));
          this.$set(this.graphData.edges[edgeIndex], 'width', originalStyle.width);
          updatedEdges.push(this.graphData.edges[edgeIndex]);
        }
      });

      this.network.body.data.nodes.update(updatedNodes);
      this.network.body.data.edges.update(updatedEdges);

      this.highlightedElements.nodes.clear();
      this.highlightedElements.edges.clear();
    },


    // 深度克隆方法
    deepClone(obj) {
      if (obj === null || typeof obj !== 'object') return obj;
      if (obj instanceof Date) return new Date(obj);
      if (Array.isArray(obj)) return obj.map(item => this.deepClone(item));

      const cloned = {};
      for (let key in obj) {
        if (obj.hasOwnProperty(key)) {
          cloned[key] = this.deepClone(obj[key]);
        }
      }
      return cloned;
    },

    // 安全创建颜色对象
    createSafeColorObject(colorInput) {
      if (typeof colorInput === 'string') {
        return { color: colorInput };
      } else if (typeof colorInput === 'object' && colorInput !== null) {
        return { ...colorInput };
      }
      return { color: '#2B7CE9' }; // 默认颜色
    },

    // 聚焦节点
    focusNode(nodeId) {
      this.network.selectNodes([nodeId]);
      this.network.focus(nodeId, {
        scale: 1.3,
        animation: {
          duration: 300,
          easingFunction: 'easeOutQuad'
        }
      });
    },
    // 导出图谱
    exportGraph() {
      if (!this.network) return;

      const canvas = this.network.canvas.frame.canvas;
      const link = document.createElement('a');
      link.href = canvas.toDataURL('image/png');
      link.download = `knowledge_graph_${new Date().getTime()}.png`;
      link.click();
    }
  },

  mounted() {
    this.fetchGraph();
  },

  // 组件销毁时清理资源
  beforeDestroy() {
    if (this.network) {
      this.network.destroy();
      this.network = null;
    }
  }
};
</script>

<style scoped>
.graph-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.toolbar {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.vis-embed {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.graph-canvas {
  width: 100%;
  height: calc(100vh - 240px);
  /* 启用GPU加速和限制重绘范围 */
  transform: translate3d(0,0,0);
  contain: strict;
  will-change: transform;
}

.graph-info {
  padding: 10px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  flex-direction: column;
}

/* 优化网络动画 */
.vis-network {
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}
</style>