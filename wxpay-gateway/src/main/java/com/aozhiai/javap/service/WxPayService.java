package com.aozhiai.javap.service;

import com.aozhiai.javap.model.payment.CreatePaymentRequest;
import com.aozhiai.javap.model.payment.RequestPaymentResponse;
import com.aozhiai.javap.model.refund.RefundRequest;
import com.wechat.pay.java.service.payments.model.Transaction;
import com.wechat.pay.java.service.refund.model.Refund;

/**
 * 微信支付服务接口
 */
public interface WxPayService {

    /**
     * 创建支付订单并获取小程序调起支付参数
     * @param request 创建支付请求
     * @return 小程序调起支付参数
     */
    RequestPaymentResponse createPayment(CreatePaymentRequest request);

    /**
     * 查询订单信息
     * @param transactionId 微信支付订单号
     * @return 订单信息
     */
    Transaction queryOrderByTransactionId(String transactionId);

    /**
     * 查询订单信息
     * @param outTradeNo 商户订单号
     * @return 订单信息
     */
    Transaction queryOrderByOutTradeNo(String outTradeNo);

    /**
     * 关闭订单
     * @param outTradeNo 商户订单号
     */
    void closeOrder(String outTradeNo);

    /**
     * 申请退款
     * @param request 退款请求
     * @return 退款结果
     */
    Refund refund(RefundRequest request);

    /**
     * 查询退款信息
     * @param outRefundNo 商户退款单号
     * @return 退款信息
     */
    Refund queryRefund(String outRefundNo);
} 