package com.example.m_java.controller;

import com.example.m_java.utils.MinioUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class FileController {

    @Autowired
    private MinioUtils minioUtils;

    @PostMapping("/upload")
    public Map<String, Object> uploadFile(@RequestParam("file") MultipartFile file) {
        Map<String, Object> result = new HashMap<>();
        try {
            String fileUrl = minioUtils.uploadFile(file);
            result.put("code", 200);
            result.put("msg", "上传成功");
            result.put("data", new HashMap<String, String>(){{ put("fileUrl", fileUrl); }});
        } catch (Exception e) {
            result.put("code", 500);
            result.put("msg", "上传失败：" + e.getMessage());
        }
        return result;
    }

    @GetMapping("/del")
    public Map<String, Object> del(@RequestParam String objectName) {
        Map<String, Object> result = new HashMap<>();
        try {
            minioUtils.deleteFile(objectName);
            result.put("code", 200);
            result.put("msg", "删除成功");
        } catch (Exception e) {
            result.put("code", 500);
            result.put("msg", "删除失败：" + e.getMessage());
        }
        return result;
    }
}
