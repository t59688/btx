package com.aozhiai.javap.model.refund;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.io.Serializable;

/**
 * 退款申请请求
 */
@Schema(description = "退款申请请求")
public class RefundRequest implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    @Schema(description = "微信支付订单号", example = "4200000913202004163033663538")
    private String transactionId;
    
    @Schema(description = "商户订单号", example = "order_20240401123456")
    private String outTradeNo;
    
    @Schema(description = "商户退款单号", required = true, example = "refund_20240401123456")
    @NotBlank(message = "商户退款单号不能为空")
    private String outRefundNo;
    
    @Schema(description = "退款原因", example = "商品已退货")
    private String reason;
    
    @Schema(description = "退款金额（单位：分）", required = true, example = "100")
    @NotNull(message = "退款金额不能为空")
    @Min(value = 1, message = "退款金额必须大于0")
    private Integer amount;
    
    @Schema(description = "原订单金额（单位：分）", required = true, example = "100")
    @NotNull(message = "原订单金额不能为空")
    @Min(value = 1, message = "原订单金额必须大于0")
    private Integer totalAmount;
    
    /**
     * 验证请求参数，至少需要提供商户订单号或微信支付订单号其中之一
     * @return 是否有效
     */
    public boolean isValid() {
        return (outTradeNo != null && !outTradeNo.isEmpty()) 
                || (transactionId != null && !transactionId.isEmpty());
    }

    public String getTransactionId() {
        return transactionId;
    }

    public void setTransactionId(String transactionId) {
        this.transactionId = transactionId;
    }

    public String getOutTradeNo() {
        return outTradeNo;
    }

    public void setOutTradeNo(String outTradeNo) {
        this.outTradeNo = outTradeNo;
    }

    public String getOutRefundNo() {
        return outRefundNo;
    }

    public void setOutRefundNo(String outRefundNo) {
        this.outRefundNo = outRefundNo;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public Integer getAmount() {
        return amount;
    }

    public void setAmount(Integer amount) {
        this.amount = amount;
    }

    public Integer getTotalAmount() {
        return totalAmount;
    }

    public void setTotalAmount(Integer totalAmount) {
        this.totalAmount = totalAmount;
    }
} 