package com.aozhiai.javap.model.payment;

import io.swagger.v3.oas.annotations.media.Schema;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.io.Serializable;

/**
 * 创建支付请求
 */
@Schema(description = "创建支付请求")
public class CreatePaymentRequest implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    @Schema(description = "商户订单号", required = true, example = "order_20240401123456")
    @NotBlank(message = "商户订单号不能为空")
    private String outTradeNo;
    
    @Schema(description = "商品描述", required = true, example = "iPhone 15 Pro Max")
    @NotBlank(message = "商品描述不能为空")
    private String description;
    
    @Schema(description = "支付金额（单位：分）", required = true, example = "100")
    @NotNull(message = "支付金额不能为空")
    @Min(value = 1, message = "支付金额必须大于0")
    private Integer amount;
    
    @Schema(description = "用户OpenID", required = true, example = "oUpF8uMuAJO_M2pxb1Q9zNjWeS6o")
    @NotBlank(message = "用户OpenID不能为空")
    private String openid;
    
    @Schema(description = "附加数据", example = "extra_data")
    private String attach;
    
    @Schema(description = "订单失效时间，格式为ISO 8601格式，如：2025-12-31T23:59:59+08:00", example = "2025-12-31T23:59:59+08:00")
    private String timeExpire;

    public String getOutTradeNo() {
        return outTradeNo;
    }

    public void setOutTradeNo(String outTradeNo) {
        this.outTradeNo = outTradeNo;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Integer getAmount() {
        return amount;
    }

    public void setAmount(Integer amount) {
        this.amount = amount;
    }

    public String getOpenid() {
        return openid;
    }

    public void setOpenid(String openid) {
        this.openid = openid;
    }

    public String getAttach() {
        return attach;
    }

    public void setAttach(String attach) {
        this.attach = attach;
    }

    public String getTimeExpire() {
        return timeExpire;
    }

    public void setTimeExpire(String timeExpire) {
        this.timeExpire = timeExpire;
    }
} 