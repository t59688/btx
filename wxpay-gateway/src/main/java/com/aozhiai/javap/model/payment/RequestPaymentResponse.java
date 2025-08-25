package com.aozhiai.javap.model.payment;

import io.swagger.v3.oas.annotations.media.Schema;

import java.io.Serializable;

/**
 * 支付下单响应
 */
@Schema(description = "支付下单响应")
public class RequestPaymentResponse implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    @Schema(description = "应用ID", example = "xxxxxxxxxxx")
    private String appId;
    
    @Schema(description = "时间戳", example = "1678888888")
    private String timeStamp;
    
    @Schema(description = "随机字符串", example = "random_nonce_string")
    private String nonceStr;
    
    @Schema(description = "订单详情扩展字符串", example = "prepay_id=xxxxxxxxxxx")
    private String packageValue;
    
    @Schema(description = "签名方式", example = "RSA")
    private String signType;
    
    @Schema(description = "签名", example = "xxxxxxxxxxxxxxxx")
    private String paySign;
    
    @Schema(description = "商户订单号", example = "order_20240401123456")
    private String outTradeNo;

    public String getAppId() {
        return appId;
    }

    public void setAppId(String appId) {
        this.appId = appId;
    }

    public String getTimeStamp() {
        return timeStamp;
    }

    public void setTimeStamp(String timeStamp) {
        this.timeStamp = timeStamp;
    }

    public String getNonceStr() {
        return nonceStr;
    }

    public void setNonceStr(String nonceStr) {
        this.nonceStr = nonceStr;
    }

    public String getPackageValue() {
        return packageValue;
    }

    public void setPackageValue(String packageValue) {
        this.packageValue = packageValue;
    }

    public String getSignType() {
        return signType;
    }

    public void setSignType(String signType) {
        this.signType = signType;
    }

    public String getPaySign() {
        return paySign;
    }

    public void setPaySign(String paySign) {
        this.paySign = paySign;
    }

    public String getOutTradeNo() {
        return outTradeNo;
    }

    public void setOutTradeNo(String outTradeNo) {
        this.outTradeNo = outTradeNo;
    }
}