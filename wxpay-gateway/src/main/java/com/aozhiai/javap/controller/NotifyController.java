package com.aozhiai.javap.controller;

import com.aozhiai.javap.config.WxPayProperties;
import com.wechat.pay.java.core.Config;
import com.wechat.pay.java.core.RSAAutoCertificateConfig;
import com.wechat.pay.java.core.exception.ValidationException;
import com.wechat.pay.java.core.notification.NotificationConfig;
import com.wechat.pay.java.core.notification.NotificationParser;
import com.wechat.pay.java.core.notification.RequestParam;
import com.wechat.pay.java.service.payments.model.Transaction;
import com.wechat.pay.java.service.refund.model.RefundNotification;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 微信支付通知接口
 */
@RestController
@RequestMapping("/wechatpay/notify")
@Tag(name = "微信支付通知接口", description = "处理微信支付平台推送的支付结果和退款结果通知")
public class NotifyController {
    
    private static final Logger log = LoggerFactory.getLogger(NotifyController.class);
    
    private final RestTemplate restTemplate = new RestTemplate();
    
    @Autowired
    private Config wxPayConfig;
    
    @Autowired
    private WxPayProperties wxPayProperties;
    
    @Value("${business.api.base-url}")
    private String businessApiBaseUrl;
    
    @Value("${business.api.payment-update-url}")
    private String paymentUpdateUrl;
    
    
    @Value("${business.api.payment-token}")
    private String paymentToken;
    
    /**
     * 支付结果通知
     */
    @PostMapping("/payment")
    @Operation(summary = "支付结果通知", description = "接收微信支付平台推送的支付结果通知")
    public Map<String, String> paymentNotify(
            @Parameter(description = "微信支付平台证书序列号") @RequestHeader("Wechatpay-Serial") String serial,
            @Parameter(description = "微信支付签名") @RequestHeader("Wechatpay-Signature") String signature,
            @Parameter(description = "微信支付请求时间戳") @RequestHeader("Wechatpay-Timestamp") String timestamp,
            @Parameter(description = "微信支付请求随机串") @RequestHeader("Wechatpay-Nonce") String nonce,
            @Parameter(description = "通知数据") @RequestBody String body) {
        
        log.info("接收到支付结果通知");
        
        try {
            // 构建请求参数
            RequestParam requestParam = new RequestParam.Builder()
                    .serialNumber(serial)
                    .signature(signature)
                    .nonce(nonce)
                    .timestamp(timestamp)
                    .body(body)
                    .build();
            
            // 创建通知配置
            NotificationConfig notificationConfig = new RSAAutoCertificateConfig.Builder()
                    .merchantId(wxPayProperties.getMchId())
                    .privateKeyFromPath(wxPayProperties.getPrivateKeyPath())
                    .merchantSerialNumber(wxPayProperties.getMchSerialNo())
                    .apiV3Key(wxPayProperties.getApiV3Key())
                    .build();
                    
            // 初始化通知解析器
            NotificationParser parser = new NotificationParser(notificationConfig);
            
            // 解析并验证通知数据
            Transaction transaction = parser.parse(requestParam, Transaction.class);
            log.info("支付结果通知解析成功，商户订单号: {}, 微信支付订单号: {}, 交易状态: {}", 
                    transaction.getOutTradeNo(), transaction.getTransactionId(), transaction.getTradeState());
            
            // 将支付结果转发给业务后端
            forwardPaymentResultToBusiness(transaction);
            
            // 返回成功
            Map<String, String> result = new HashMap<>();
            result.put("code", "SUCCESS");
            result.put("message", "成功");
            return result;
            
        } catch (ValidationException e) {
            log.error("支付结果通知验证失败", e);
            Map<String, String> result = new HashMap<>();
            result.put("code", "FAIL");
            result.put("message", "验证失败");
            return result;
        } catch (Exception e) {
            log.error("处理支付结果通知异常", e);
            Map<String, String> result = new HashMap<>();
            result.put("code", "FAIL");
            result.put("message", "处理失败: " + e.getMessage());
            return result;
        }
    }
    
    /**
     * 退款结果通知
     */
    @PostMapping("/refund")
    @Operation(summary = "退款结果通知", description = "接收微信支付平台推送的退款结果通知")
    public Map<String, String> refundNotify(
            @Parameter(description = "微信支付平台证书序列号") @RequestHeader("Wechatpay-Serial") String serial,
            @Parameter(description = "微信支付签名") @RequestHeader("Wechatpay-Signature") String signature,
            @Parameter(description = "微信支付请求时间戳") @RequestHeader("Wechatpay-Timestamp") String timestamp,
            @Parameter(description = "微信支付请求随机串") @RequestHeader("Wechatpay-Nonce") String nonce,
            @Parameter(description = "通知数据") @RequestBody String body) {
        
        log.info("接收到退款结果通知");
        
        try {
            // 构建请求参数
            RequestParam requestParam = new RequestParam.Builder()
                    .serialNumber(serial)
                    .signature(signature)
                    .nonce(nonce)
                    .timestamp(timestamp)
                    .body(body)
                    .build();
            
            // 创建通知配置
            NotificationConfig notificationConfig = new RSAAutoCertificateConfig.Builder()
                    .merchantId(wxPayProperties.getMchId())
                    .privateKeyFromPath(wxPayProperties.getPrivateKeyPath())
                    .merchantSerialNumber(wxPayProperties.getMchSerialNo())
                    .apiV3Key(wxPayProperties.getApiV3Key())
                    .build();
                    
            // 初始化通知解析器
            NotificationParser parser = new NotificationParser(notificationConfig);
            
            // 解析并验证通知数据
            RefundNotification refundNotification = parser.parse(requestParam, RefundNotification.class);
            log.info("退款结果通知解析成功，商户退款单号: {}, 微信支付退款单号: {}, 退款状态: {}", 
                    refundNotification.getOutRefundNo(), refundNotification.getRefundId(), refundNotification.getRefundStatus());
            
            // 将退款结果转发给业务后端
            forwardRefundResultToBusiness(refundNotification);
            
            // 返回成功
            Map<String, String> result = new HashMap<>();
            result.put("code", "SUCCESS");
            result.put("message", "成功");
            return result;
            
        } catch (ValidationException e) {
            log.error("退款结果通知验证失败", e);
            Map<String, String> result = new HashMap<>();
            result.put("code", "FAIL");
            result.put("message", "验证失败");
            return result;
        } catch (Exception e) {
            log.error("处理退款结果通知异常", e);
            Map<String, String> result = new HashMap<>();
            result.put("code", "FAIL");
            result.put("message", "处理失败: " + e.getMessage());
            return result;
        }
    }
    
    /**
     * 转发支付结果给业务后端
     */
    private void forwardPaymentResultToBusiness(Transaction transaction) {
        try {
            String url = businessApiBaseUrl + paymentUpdateUrl;
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-Payment-Token", paymentToken);
            
            Map<String, Object> body = new HashMap<>();
            // 转换成业务后端所需格式
            body.put("order_no", transaction.getOutTradeNo());
            body.put("payment_id", transaction.getTransactionId());
            body.put("status", transaction.getTradeState().name());
            body.put("amount", transaction.getAmount().getTotal());
            // 保留原始数据以备需要
            body.put("raw_data", transaction);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);
            
            log.info("转发支付结果给业务后端成功，响应状态: {}", response.getStatusCode());
        } catch (Exception e) {
            log.error("转发支付结果给业务后端失败", e);
            // 通知失败不影响向微信返回结果，记录日志即可
        }
    }
    
    /**
     * 将微信支付状态映射为业务状态
     */
    private String mapTradeStateToStatus(String tradeState) {
        switch (tradeState) {
            case "SUCCESS":
                return "success";
            case "REFUND":
                return "refunded";
            case "NOTPAY":
                return "pending";
            case "CLOSED":
                return "cancelled";
            case "REVOKED":
                return "cancelled";
            case "USERPAYING":
                return "processing";
            case "PAYERROR":
                return "failed";
            default:
                return "unknown";
        }
    }
    
    /**
     * 转发退款结果给业务后端
     */
    private void forwardRefundResultToBusiness(RefundNotification refundNotification) {
        try {
            String url = businessApiBaseUrl + paymentUpdateUrl;
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-Payment-Token", paymentToken);
            
            Map<String, Object> body = new HashMap<>();
            body.put("type", "refund");
            body.put("data", refundNotification);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);
            
            log.info("转发退款结果给业务后端成功，响应状态: {}", response.getStatusCode());
        } catch (Exception e) {
            log.error("转发退款结果给业务后端失败", e);
            // 通知失败不影响向微信返回结果，记录日志即可
        }
    }
} 