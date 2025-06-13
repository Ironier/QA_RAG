<template>
  <el-tabs v-model="activeName" @tab-click="handleClick">
    <el-tab-pane label="文档管理" name="first">
      <el-container>
        <el-header>
          <div class="search-container">
            <span class="con-state">状态</span>
            <el-select
              v-model="state"
              placeholder="请选择状态"
              style="width: 150px"
              size="small"
              @change="handleSelectChange"
            >
              <el-option
                v-for="item in options"
                :key="item"
                :label="item"
                :value="item"
              >
              </el-option>
            </el-select>
            <span class="search">文件名称</span>
            <el-input
              v-model="input"
              placeholder="请输入文件名称"
              style="width: 150px"
              size="small"
            ></el-input>
            <el-button
              type="primary"
              icon="el-icon-search"
              size="small"
              @click="handleSearch"
              >搜索</el-button
            >
            <el-button icon="el-icon-refresh" size="small" @click="handleReset"
              >重置</el-button
            >
            <span class="count">文件数量</span>
            <el-tag>1</el-tag>
            <span class="count">已构建文档</span>
            <el-tag type="success">1</el-tag>
            <span class="count">未构建文档</span>
            <el-tag type="warning">1</el-tag>
          </div>

          <div class="button-group">
            <el-button type="success" size="small" @click="dialogVisible = true"
              >导入文档
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="handleGenerateKnowledge"
              >生成知识库
            </el-button>
          </div>
        </el-header>

        <el-dialog title="添加文件" :visible.sync="dialogVisible" width="60%">
          <div class="dialog-content">
            <!-- 知识文件部分 -->
            <div class="file-section">
              <span class="required">*知识文件</span>
              <el-upload
                class="upload-demo"
                :action="uploadUrl"
                :auto-upload="true"
                :before-upload="beforeUpload"
                :on-remove="handleRemove"
                :on-success="handleSuccess"
                :on-error="handleError"
                multiple
                :limit="1"
                :file-list="fileList"
                :on-exceed="handleExceed"
              >
                <el-button size="small" type="primary">选择文件</el-button>
              </el-upload>
            </div>
            <div class="tip">请上传大小不超过50MB格式为docx的文件</div>

            <!-- 构建场景部分 -->
            <div class="scene-section">
              <span class="con-scene">构建场景</span>
              <el-select
                v-model="scene"
                placeholder="请选择构建场景"
                style="width: 500px"
                size="small"
              >
                <el-option
                  v-for="item in tableScene"
                  :key="item"
                  :label="item"
                  :value="item"
                >
                </el-option>
              </el-select>
            </div>

            <!-- 知识标签部分 -->
            <div class="tag-section">
              <span class="required">*知识标签</span>
              <el-transfer
                filterable
                :filter-method="filterMethod"
                :titles="['未选择标签', '已选择标签']"
                filter-placeholder="请输入搜索内容"
                v-model="value"
                :data="data"
                style="width: 100%"
              >
              </el-transfer>
            </div>
          </div>
          <span slot="footer" class="dialog-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="addItem">确定</el-button>
          </span>
        </el-dialog>
        <el-divider></el-divider>
        <el-main>
          <el-table
            :data="
              tableData.slice(
                (currentPage - 1) * pageSize,
                currentPage * pageSize
              )
            "
            border
            style="width: 100%"
          >
            <el-table-column
              prop="name"
              label="文件名称"
              width="280"
              align="center"
            >
            </el-table-column>
            <el-table-column
              prop="state"
              label="状态"
              width="100"
              align="center"
            >
              <template slot-scope="scope">
                <el-tag
                  :type="scope.row.state === '已分块' ? 'success' : 'info'"
                  disable-transitions
                  >{{ scope.row.state }}</el-tag
                >
              </template>
            </el-table-column>
            <el-table-column
              prop="labels"
              label="标签"
              width="280"
              align="center"
            >
              <template slot-scope="scope">
                <span
                  v-for="(tag, index) in scope.row.labels"
                  :key="index"
                  class="tag-item"
                >
                  {{ tag }}
                  <span v-if="index !== scope.row.labels.length - 1">,</span>
                </span>
              </template>
            </el-table-column>
            <el-table-column
              prop="time"
              label="修改时间"
              width="150"
              align="center"
            >
            </el-table-column>
            <el-table-column prop="operation" label="操作" align="center">
              <template slot-scope="scope">
                <!-- 查看按钮 -->
                <el-button
                  type="text"
                  icon="el-icon-view"
                  @click="handleView(scope.row)"
                  style="color: #409eff"
                >
                  查看
                </el-button>

                <!-- 下载按钮 -->
                <el-button
                  type="text"
                  icon="el-icon-download"
                  @click="handleDownload(scope.row)"
                  style="color: #67c23a"
                >
                  下载
                </el-button>

                <!-- 删除按钮 -->
                <el-button
                  type="text"
                  icon="el-icon-delete"
                  @click="handleDelete(scope.row)"
                  style="color: #f56c6c"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <!-- 分页器 -->
          <div class="block" style="margin-top: 15px">
            <el-pagination
              align="center"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="currentPage"
              :page-sizes="[1, 5, 10, 20]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="tableData.length"
            >
            </el-pagination>
          </div>
        </el-main>
      </el-container>
    </el-tab-pane>
    <el-tab-pane label="原文片段" name="second">原文片段</el-tab-pane>
    <el-tab-pane label="图谱管理" name="third">图谱管理</el-tab-pane>
  </el-tabs>
</template>
<script>
import axios from "axios";
export default {
  data() {
    const generateData = (_) => {
      const data = [];
      const scenaros = [
        "资源监测",
        "遥感应用",
        "资源开发",
        "规划审批",
        "法规政策",
      ];
      // 注意：这里保留pinyin字段不影响功能，但实际已不需要用于过滤
      scenaros.forEach((scenaro, index) => {
        data.push({
          label: scenaro, // label字段保存城市名称
          key: index,
        });
      });
      return data;
    };
    return {
      tableData: JSON.parse(localStorage.getItem("documentList") || "[]"),
      uploadUrl: `${this.$API.MINIO}/api/upload`,
      currentPage: 1, // 当前页码
      total: 20, // 总条数
      pageSize: 2, // 每页的数据条数
      dialogVisible: false,
      fileList: [],
      tempFile: null,
      scene: "", // 构建场景
      unselectedTags: [
        "窗口",
        "收费情况",
        "办理流程",
        "标签",
        "办件",
        "事物",
        "人物",
      ], // 示例未选择标签
      selectedTags: [], // 已选择标签
      data: generateData(),
      value: [],
      tableScene: ["自然资源"],
      activeName: "first",
      options: ["未处理", "已分块"],
      state: "",
      input: "",
    };
  },
  methods: {
    fillLabel(indexes) {
      const data = [];
      for (let i = 0; i < indexes.length; i++) {
        data.push(this.data[indexes[i]].label);
      }
      return data;
    },
    filterMethod(query, item) {
      return item.label.indexOf(query) > -1;
    },
    handleSuccess(res, file) {
      this.$message.success("文件上传成功！");
    },
    // 上传失败回调
    handleError(err) {
      this.$message.error("文件上传失败，请重试！");
      console.error("Upload error:", err);
    },
    addItem() {
      if (this.tempFile) {
        const newItem = {
          name: this.tempFile.name,
          state: "未处理",
          time: new Date().toLocaleString(),
          labels: this.fillLabel(this.value),
        };
        this.tableData.push(newItem);
        // 添加数据后同步更新localStorage
        this.saveToLocalStorage();

        this.dialogVisible = false;
        this.fileList = [];
        this.tempFile = null;
      } else {
        this.$message.warning("请先选择文件！");
      }
    },
    beforeUpload(file) {
      console.log("触发 beforeUpload，文件：", file);
      // 校验文件类型和大小（示例：仅允许 doc/docx）
      const isDoc = file.type === "application/msword";
      const isDocx =
        file.type ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
      const isSizeValid = file.size / 1024 / 1024 <= 50; // 50MB限制

      if (!isDoc && !isDocx) {
        this.$message.error("只能上传doc/docx文件！");
        return false; // 阻止文件加入fileList
      }
      if (!isSizeValid) {
        this.$message.error("文件大小不能超过50MB！");
        return false;
      }

      this.tempFile = file; // 暂存选中的文件
      return true; // 允许文件加入fileList
    },
    // 其他方法（handleClose、handleRemove等）保持不变
    handleSizeChange(val) {
      console.log(`每页 ${val} 条`);
      this.currentPage = 1;
      this.pageSize = val;
    },
    //当前页改变时触发 跳转其他页
    handleCurrentChange(val) {
      console.log(`当前页: ${val}`);
      this.currentPage = val;
    },
    handleRemove(file, fileList) {
      console.log(file, fileList);
    },
    handlePreview(file) {
      console.log(file);
    },
    handleExceed(files, fileList) {
      this.$message.warning(
        `当前限制选择 1 个文件，本次选择了 ${files.length} 个文件，共选择了 ${
          files.length + fileList.length
        } 个文件`
      );
    },
    handleView(row) {
      console.log("查看数据：", row);
      // 可跳转到详情页或打开弹窗
    },
    // 下载操作
    handleDownload(row) {
      console.log("下载数据：", row);
      // 调用下载接口或生成文件
    },
    // 删除操作
    handleDelete(row) {
      this.$confirm("确定删除该记录？", "提示", { type: "warning" })
        .then(() => {
          // 正确拼接 URL，并通过 params 传递参数
          axios
            .get(`${this.$API.MINIO}/api/del`, {
              params: { objectName: row.name }, // 参数名与后端 @RequestParam 一致
            })
            .then((response) => {
              if (response.data.code === 200) {
                // 根据后端返回状态判断
                this.tableData = this.tableData.filter((item) => item !== row);
                this.saveToLocalStorage();
                this.$message.success("删除成功");
              } else {
                this.$message.error("删除失败：" + response.data.msg);
              }
            })
            .catch((error) => {
              this.$message.error("删除请求失败：" + error.message);
            });
        })
        .catch(() => {});
    },
    saveToLocalStorage() {
      // 将数组转换为JSON字符串存储（localStorage只能存字符串）
      localStorage.setItem("documentList", JSON.stringify(this.tableData));
    },
    async handleGenerateKnowledge() {
      const unprocessedItems = this.tableData.filter(
        (item) => item.state === "未处理"
      );

      for (const item of unprocessedItems) {
        try {
          // 调用后端分块接口（注意参数名改为filename）
          const response = await axios.get(`${this.$API.CHUNK}/api/block`, {
            params: { filename: item.name },
          });

          if (response.data.code === 200) {
            item.state = "已分块"; // 处理成功后更新状态
            this.saveToLocalStorage();
          } else {
            this.$message.error(`处理${item.name}失败：${response.data.msg}`);
          }
        } catch (error) {
          this.$message.error(`处理${item.name}请求失败：${error.message}`);
        }
      }
    },
    moveToSelected() {
      // 将选中的未选择标签移动到已选择
      // 这里需要先获取选中的复选框，假设使用ref获取，或者在checkbox的change事件中记录选中的标签
      // 简化处理：假设直接移动第一个标签（实际需要遍历选中的）
      if (this.unselectedTags.length > 0) {
        this.selectedTags.push(this.unselectedTags[0]);
        this.unselectedTags.shift();
      }
    },
    moveToUnselected() {
      // 将选中的已选择标签移动到未选择
      if (this.selectedTags.length > 0) {
        this.unselectedTags.push(this.selectedTags[0]);
        this.selectedTags.shift();
      }
    },
    confirmDialog() {
      // 处理确定按钮逻辑
      this.dialogVisible = false;
    },
    handleSelectChange(state) {
      this.tableData = JSON.parse(localStorage.getItem("documentList") || "[]");
      const unprocessedItems = this.tableData.filter(
        (item) => item.state === state
      );
      this.tableData = unprocessedItems;
    },
    handleSearch() {
      const unprocessedItems = this.tableData.filter(
        (item) => item.name.indexOf(this.input) !== -1
      );
      console.log(unprocessedItems);
      this.tableData = unprocessedItems;
    },
    handleReset() {
      this.tableData = JSON.parse(localStorage.getItem("documentList") || "[]");
    },
  },
};
</script>

<style>
.button-group {
  display: flex; /* 启用 Flex 布局 */
  justify-content: space-between; /* 两端对齐（左按钮居左，右按钮居右） */
  width: 100%; /* 确保父容器占满宽度（根据需求调整） */
  padding: 10px; /* 可选：增加内边距避免紧凑 */
}
.file-section {
  display: flex; /* 启用Flex布局 */
  align-items: center; /* 垂直居中对齐 */
}
.required {
  color: red;
  margin-right: 10px;
}
.tip {
  color: #999;
  font-size: 10px;
}
.scene-section {
  margin-bottom: 20px;
  margin-top: 20px;
}
.tag-container {
  display: flex;
  justify-content: space-between;
}
.tag-right {
  width: 45%;
}
.tag-header {
  margin-bottom: 10px;
}
.tag-search {
  margin-bottom: 10px;
}
.tag-buttons {
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin: 0 10px;
}
.tag-buttons button {
  margin: 5px 0;
}
.tag-list {
  max-height: 200px;
  overflow-y: auto;
}
.con-scene {
  margin-right: 20px;
}
.el-tabs {
  margin-left: 10px;
}
.con-state {
  margin-right: 10px;
  font-size: 12px;
}
.search {
  margin-right: 10px;
  font-size: 12px;
}
.el-main {
  padding: 0;
}
.search-container {
  display: flex;
  align-items: center;
}

.el-select {
  margin-right: 10px;
}
.el-input {
  margin-right: 10px;
}
.count {
  margin-right: 10px;
  margin-left: 10px;
  font-size: 12px;
}
</style>

