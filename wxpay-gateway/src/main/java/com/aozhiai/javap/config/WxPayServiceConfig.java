package com.aozhiai.javap.config;

import com.wechat.pay.java.core.Config;
import com.wechat.pay.java.core.RSAAutoCertificateConfig;
import com.wechat.pay.java.service.payments.jsapi.JsapiServiceExtension;
import com.wechat.pay.java.service.refund.RefundService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.ResourceUtils;

import java.io.File;

/**
 * 微信支付服务配置类
 */
@Configuration
public class WxPayServiceConfig {

    /**
     * 微信支付核心配置
     */
    @Bean
    public Config wxPayConfig(WxPayProperties wxPayProperties) throws Exception {
        // 获取商户私钥文件
        String privateKeyPath = wxPayProperties.getPrivateKeyPath();
        File privateKeyFile = ResourceUtils.getFile(privateKeyPath);

        // 构建微信支付配置
        return new RSAAutoCertificateConfig.Builder()
                .merchantId(wxPayProperties.getMchId())
                .privateKeyFromPath(privateKeyFile.getAbsolutePath())
                .merchantSerialNumber(wxPayProperties.getMchSerialNo())
                .apiV3Key(wxPayProperties.getApiV3Key())
                .build();
    }

    /**
     * JSAPI支付服务
     */
    @Bean
    public JsapiServiceExtension jsapiService(Config config) {
        return new JsapiServiceExtension.Builder()
                .config(config)
                .signType("RSA")
                .build();
    }

    /**
     * 退款服务
     */
    @Bean
    public RefundService refundService(Config config) {
        return new RefundService.Builder()
                .config(config)
                .build();
    }
} 