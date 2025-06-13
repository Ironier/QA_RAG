package com.example.m_java.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        // 1. 创建CORS配置对象
        CorsConfiguration config = new CorsConfiguration();
        // 允许前端域名（如 http://localhost:9528），生产环境建议替换为具体域名，不要用*
        config.addAllowedOrigin("http://localhost:9528");
        // 允许的请求方法（GET、POST等）
        config.addAllowedMethod("*");
        // 允许的请求头（如Content-Type、Authorization等）
        config.addAllowedHeader("*");
        // 允许前端获取的响应头（可选，根据业务需求）
        config.addExposedHeader("*");
        // 是否允许携带Cookie（前端withCredentials为true时需要）
        config.setAllowCredentials(true);

        // 2. 配置作用于所有接口路径（如/api/**）
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config); // 匹配所有路径

        // 3. 返回CORS过滤器
        return new CorsFilter(source);
    }
}

