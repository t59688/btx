package com.aozhiai.javap;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.autoconfigure.jdbc.DataSourceTransactionManagerAutoConfiguration;
import org.mybatis.spring.boot.autoconfigure.MybatisAutoConfiguration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

/**
 * 微信支付服务应用程序
 */
@SpringBootApplication(exclude = {
		DataSourceAutoConfiguration.class,
		DataSourceTransactionManagerAutoConfiguration.class,
		MybatisAutoConfiguration.class
})
@EnableConfigurationProperties
@OpenAPIDefinition(
		info = @Info(
				title = "微信支付服务 API",
				description = "微信支付服务接口文档，提供小程序支付相关功能",
				version = "1.0.0"
		)
)
public class JavapApplication {

	public static void main(String[] args) {
		SpringApplication.run(JavapApplication.class, args);
	}

}
