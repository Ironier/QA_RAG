package com.example.m_java.config;

import io.minio.MinioClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MinioConfig {

    @Value("${minio.endpoint}")        // MinIO服务地址（如：http://127.0.0.1:9000）
    private String endpoint;

    @Value("${minio.access-key}")     // MinIO访问密钥
    private String accessKey;

    @Value("${minio.secret-key}")     // MinIO秘密密钥
    private String secretKey;

    @Value("${minio.bucket-name}")    // 默认存储桶名称
    private String bucketName;

    // 初始化MinIO客户端
    @Bean
    public MinioClient minioClient() {
        return MinioClient.builder()
                .endpoint(endpoint)
                .credentials(accessKey, secretKey)
                .build();
    }

    // 暴露桶名称供其他类使用
    @Bean
    public String bucketName() {
        return bucketName;
    }
}
