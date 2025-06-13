const express = require('express');
const multer = require('multer');
const cors = require('cors');
const Minio = require('minio');

const app = express();
app.use(cors()); // 解决跨域问题

// 配置 Multer 处理文件上传
const upload = multer({ dest: 'tmp/' }); // 临时存储目录

// MinIO 配置（请替换为你的 MinIO 信息）
const minioClient = new Minio.Client({
  endPoint: '172.27.177.119', // MinIO 服务器地址
  port: 9990, // 端口
  useSSL: false, // 是否启用 HTTPS
  accessKey: 'admin', // 访问密钥
  secretKey: 'admin123456' // 秘密密钥
});

// 上传接口
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    const file = req.file;
    if (!file) {
      return res.status(400).json({ error: '请选择上传文件' });
    }

    const bucketName = 'your-bucket-name'; // 存储桶名称
    const objectName = file.originalname; // 文件名（可自定义命名规则）

    // 检查存储桶是否存在，不存在则创建
    const bucketExists = await minioClient.bucketExists(bucketName);
    if (!bucketExists) {
      await minioClient.makeBucket(bucketName, 'us-east-1');
    }

    // 上传文件到 MinIO
    const fileStream = require('fs').createReadStream(file.path);
    await minioClient.putObject(bucketName, objectName, fileStream, file.size);

    // 获取文件访问 URL（根据 MinIO 配置生成）
    const fileUrl = `http://172.27.177.119/${bucketName}/${objectName}`;

    // 清理临时文件
    require('fs').unlinkSync(file.path);

    res.status(200).json({ success: true, url: fileUrl });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: '文件上传失败' });
  }
});

// 启动服务
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
