package com.example.m_java.utils;

import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import io.minio.GetPresignedObjectUrlArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.RemoveObjectArgs;
import io.minio.http.Method;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.util.concurrent.TimeUnit;

@Component
public class MinioUtils {

    @Autowired
    private MinioClient minioClient;

    @Autowired
    @Qualifier("bucketName")
    private String bucketName;

    /**
     * 上传文件到MinIO
     */
    public String uploadFile(MultipartFile file) throws Exception {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("上传文件不能为空");
        }

        // 生成唯一文件名（避免覆盖）
        String originalFileName = file.getOriginalFilename();
//        String ext = StrUtil.subAfter(originalFileName, ".", true);  // 获取文件后缀
//        String newFileName = IdUtil.fastSimpleUUID() + "." + ext;   // UUID+后缀

        // 执行上传
        minioClient.putObject(PutObjectArgs.builder()
                .bucket(bucketName)
                .object(originalFileName)
                .contentType(file.getContentType())
                .stream(file.getInputStream(), file.getSize(), -1)
                .build());

        // 返回文件访问路径（可根据MinIO配置是否开启匿名访问）
        return getFileUrl(originalFileName);
    }

    /**
     * 获取文件临时访问URL（带过期时间）
     */
    public String getFileUrl(String objectName) throws Exception {
        return minioClient.getPresignedObjectUrl(GetPresignedObjectUrlArgs.builder()
                .bucket(bucketName)
                .object(objectName)
                .method(Method.GET)
                .expiry(7, TimeUnit.DAYS)  // 7天后过期
                .build());
    }

    /**
     * 删除文件
     */
    public void deleteFile(String objectName) throws Exception {
        minioClient.removeObject(RemoveObjectArgs.builder()
                .bucket(bucketName)
                .object(objectName)
                .build());
    }
}
