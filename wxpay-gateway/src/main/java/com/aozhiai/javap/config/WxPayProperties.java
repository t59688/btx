package com.aozhiai.javap.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 微信支付配置
 */
@Component
@ConfigurationProperties(prefix = "wechat.pay")
public class WxPayProperties {
    
    /** 应用ID */
    private String appId;
    
    /** 商户号 */
    private String mchId;
    
    /** 商户API证书序列号 */
    private String mchSerialNo;
    
    /** 商户私钥路径 */
    private String privateKeyPath;
    
    /** 商户APIv3密钥 */
    private String apiV3Key;
    
    /** 支付通知地址 */
    private String notifyUrl;
    
    /** 退款通知地址 */
    private String refundNotifyUrl;
    
    /** 平台证书路径（非必填，自动更新时下载的平台证书保存路径） */
    private String platformKeyPath;

    public String getAppId() {
        return appId;
    }

    public void setAppId(String appId) {
        this.appId = appId;
    }

    public String getMchId() {
        return mchId;
    }

    public void setMchId(String mchId) {
        this.mchId = mchId;
    }

    public String getMchSerialNo() {
        return mchSerialNo;
    }

    public void setMchSerialNo(String mchSerialNo) {
        this.mchSerialNo = mchSerialNo;
    }

    public String getPrivateKeyPath() {
        return privateKeyPath;
    }

    public void setPrivateKeyPath(String privateKeyPath) {
        this.privateKeyPath = privateKeyPath;
    }

    public String getApiV3Key() {
        return apiV3Key;
    }

    public void setApiV3Key(String apiV3Key) {
        this.apiV3Key = apiV3Key;
    }

    public String getNotifyUrl() {
        return notifyUrl;
    }

    public void setNotifyUrl(String notifyUrl) {
        this.notifyUrl = notifyUrl;
    }

    public String getRefundNotifyUrl() {
        return refundNotifyUrl;
    }

    public void setRefundNotifyUrl(String refundNotifyUrl) {
        this.refundNotifyUrl = refundNotifyUrl;
    }

    public String getPlatformKeyPath() {
        return platformKeyPath;
    }

    public void setPlatformKeyPath(String platformKeyPath) {
        this.platformKeyPath = platformKeyPath;
    }
} 