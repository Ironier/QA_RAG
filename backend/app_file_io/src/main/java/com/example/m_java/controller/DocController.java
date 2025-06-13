package com.example.m_java.controller;

import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;



@RestController
public class DocController {

    private final MongoTemplate mongoTemplate;

    public DocController(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }

    @GetMapping("/api/dynamic-collection")
    public List<Map<String, Object>> getCollectionData(
            @RequestParam("collectionName") String collectionName) {
        collectionName=collectionName.replace(".","_");
        // 使用MongoTemplate查询指定集合的所有文档
        List<Map<String, Object>> result = new ArrayList<>();
        List<Map> documents = mongoTemplate.find(new Query(), Map.class, collectionName);

        for (Map document : documents) {
            // 转换每个文档的键值对类型
            Map<String, Object> typedDocument = new HashMap<>();
            document.forEach((key, value) -> typedDocument.put((String) key, value));
            result.add(typedDocument);
        }

        return result;
    }
}
