<template>
  <div>
    <el-container>
      <el-header>
        <el-select
          v-model="value"
          placeholder="请选择"
          @change="handleSelectChange"
        >
          <el-option
            v-for="item in tableData"
            :key="item.name"
            :label="item.name"
            :value="item.name"
          >
          </el-option>
        </el-select>
      </el-header>
      <el-main>
        <div class="policy-list">
          <!-- 政策卡片列表 -->
          <el-card
            v-for="(item, index) in currentList"
            :key="item.id"
            class="policy-card"
          >
            <div class="policy-content">
              <!-- 编辑状态显示输入框，非编辑状态显示文本 -->
              <div v-if="editingItemId === item.id">
                <el-input
                  v-model="item.content"
                  placeholder="请输入更新内容"
                  class="edit-input"
                />
              </div>
              <p v-else class="policy-title">
                {{ index + 1 }}. {{ item.content }}
              </p>
              <p class="update-time">
                更新于 {{ item.updateTime || "未记录" }}
              </p>
              <!-- 建议数据包含更新时间字段 -->
            </div>
            <div class="action-buttons">
              <!-- 编辑状态显示保存/取消按钮 -->
              <div v-if="editingItemId === item.id">
                <el-button
                  type="success"
                  size="small"
                  @click="handleSave(item)"
                >
                  保存
                </el-button>
                <el-button
                  type="default"
                  size="small"
                  @click="handleCancelEdit(item)"
                >
                  取消
                </el-button>
              </div>
              <!-- 非编辑状态显示编辑/删除按钮 -->
              <div v-else>
                <el-button
                  type="primary"
                  size="small"
                  @click="handleEdit(item)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(item)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </el-card>

          <!-- 分页组件 -->
          <div class="fixed-pagination">
            <el-pagination
              :hide-on-single-page="hide"
              background
              :current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="handleCurrentChange"
            ></el-pagination>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import axios from "axios";
export default {
  data() {
    return {
      tableData: [],
      hide: true,
      value: "",
      blockList: [],
      currentPage: 1, // 当前页码
      pageSize: 3, // 每页显示数量
      editingItemId: null, // 记录当前正在编辑的条目id（关键状态）
      originalContent: null, // 保存编辑前的原始内容（用于取消）
    };
  },
  computed: {
    currentList() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.blockList.slice(start, end);
    },
    total() {
      return this.blockList.length;
    },
  },
  created() {
    window.addEventListener("storage", this.handleStorageChange);
    this.readStoredData();
  },
  beforeDestroy() {
    window.removeEventListener("storage", this.handleStorageChange);
  },
  methods: {
    handleStorageChange(e) {
      if (e.key === "documentList") {
        this.readStoredData();
      }
    },
    readStoredData() {
      const data = localStorage.getItem("documentList");
      this.tableData = data ? JSON.parse(data) : null;
      const unprocessedItems = this.tableData.filter(
        (item) => item.state === "已分块"
      );
      this.tableData = unprocessedItems;
    },
    handleCurrentChange(val) {
      this.currentPage = val;
    },
    handleCurrentChange(val) {
      this.currentPage = val;
    },

    // 进入编辑状态
    handleEdit(policy) {
      this.editingItemId = policy.id; // 标记当前编辑的条目id
      this.originalContent = policy.content; // 保存原始内容用于取消
    },

    // 保存编辑内容
    handleSave(policy) {
      // 简单校验：内容不能为空
      if (!policy.content.trim()) {
        this.$message.warning("政策内容不能为空");
        return;
      }

      // 更新数据（假设需要同步到localStorage，根据实际存储方式调整）
      const targetIndex = this.blockList.findIndex(
        (item) => item.id === policy.id
      );
      if (targetIndex !== -1) {
        // 更新内容和时间戳（假设数据包含updateTime字段）
        this.blockList[targetIndex] = {
          ...this.blockList[targetIndex],
          content: policy.content,
          updateTime: new Date().toLocaleString(), // 记录最新更新时间
        };
      }

      // 退出编辑状态
      this.editingItemId = null;
      this.$message.success("保存成功");
    },

    // 取消编辑
    handleCancelEdit(policy) {
      // 恢复原始内容
      const targetIndex = this.blockList.findIndex(
        (item) => item.id === policy.id
      );
      if (targetIndex !== -1) {
        this.blockList[targetIndex].content = this.originalContent;
      }
      // 退出编辑状态
      this.editingItemId = null;
    },

    // 删除操作（带分页适配）
    handleDelete(policy) {
      this.$confirm("确定删除该分块吗？", "提示", { type: "warning" })
        .then(() => {
          this.blockList = this.blockList.filter(
            (item) => item.id !== policy.id
          );
          // 处理删除后当前页无数据的情况
          const totalPages = Math.ceil(this.total / this.pageSize);
          if (this.currentPage > totalPages && totalPages > 0) {
            this.currentPage = totalPages;
          }
          this.$message.success("删除成功");
        })
        .catch(() => {
          this.$message.info("已取消删除");
        });
    },
    async handleSelectChange(value) {
      try {
        const response = await axios.get(
          `${this.$API.MINIO}/api/dynamic-collection`,
          {
            params: {
              collectionName: value,
            },
          }
        );
        this.blockList = response.data;
      } catch (error) {
        console.error(
          "查询失败:",
          error.response ? error.response.data : error.message
        );
      }
    },
  },
};
</script>

<style scoped>
.policy-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.policy-content {
  flex: 1;
  padding: 20px;
  min-width: 0; /* 防止内容溢出 */
}

.policy-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 15px 20px;
}

.policy-title {
  font-weight: 500;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.update-time {
  color: #666;
  font-size: 12px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-left: 20px;
  flex-shrink: 0; /* 防止按钮被压缩 */
}

.fixed-pagination {
  padding: 15px 20px;
  background-color: #fff;
  border-top: 1px solid #ebeef5;
  text-align: center;
}

/* 编辑输入框样式 */
.edit-input {
  width: 900px; /* 根据实际需求调整输入框宽度 */
  min-width: 200px; /* 设置最小宽度防止过小 */
}
</style>