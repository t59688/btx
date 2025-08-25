package com.aozhiai.javap.model.payment;

import io.swagger.v3.oas.annotations.media.Schema;

import java.io.Serializable;

/**
 * 订单查询请求
 */
@Schema(description = "订单查询请求")
public class QueryOrderRequest implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    @Schema(description = "商户订单号", example = "order_20240401123456")
    private String outTradeNo;
    
    @Schema(description = "微信支付订单号", example = "4200000913202004163033663538")
    private String transactionId;

    /**
     * 验证请求参数，至少需要提供商户订单号或微信支付订单号其中之一
     * @return 是否有效
     */
    public boolean isValid() {
        return (outTradeNo != null && !outTradeNo.isEmpty()) 
                || (transactionId != null && !transactionId.isEmpty());
    }

    public String getOutTradeNo() {
        return outTradeNo;
    }

    public void setOutTradeNo(String outTradeNo) {
        this.outTradeNo = outTradeNo;
    }

    public String getTransactionId() {
        return transactionId;
    }

    public void setTransactionId(String transactionId) {
        this.transactionId = transactionId;
    }
} 