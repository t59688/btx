package com.aozhiai.javap.controller;

import com.aozhiai.javap.common.R;
import com.aozhiai.javap.model.payment.CreatePaymentRequest;
import com.aozhiai.javap.model.payment.QueryOrderRequest;
import com.aozhiai.javap.model.payment.RequestPaymentResponse;
import com.aozhiai.javap.model.refund.RefundRequest;
import com.aozhiai.javap.service.WxPayService;
import com.wechat.pay.java.service.payments.model.Transaction;
import com.wechat.pay.java.service.refund.model.Refund;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

/**
 * 支付相关接口
 */
@RestController
@RequestMapping("/pay")
@Tag(name = "支付相关接口", description = "包括创建支付、查询订单、关闭订单、申请退款、查询退款等接口")
public class PayController {
    
    private static final Logger log = LoggerFactory.getLogger(PayController.class);
    
    @Autowired
    private WxPayService wxPayService;
    
    /**
     * 创建支付订单
     */
    @PostMapping("/create-payment")
    @Operation(summary = "创建支付订单", description = "创建微信支付订单，并返回小程序调起支付所需的参数")
    public R<RequestPaymentResponse> createPayment(@Valid @RequestBody CreatePaymentRequest request) {
        log.info("接收到创建支付订单请求: {}", request.getOutTradeNo());
        RequestPaymentResponse response = wxPayService.createPayment(request);
        return R.success(response);
    }
    
    /**
     * 查询订单状态
     */
    @PostMapping("/query-status")
    @Operation(summary = "查询订单状态", description = "根据商户订单号或微信支付订单号查询订单状态")
    public R<Transaction> queryOrderStatus(@RequestBody QueryOrderRequest request) {
        log.info("接收到查询订单请求");
        
        if (!request.isValid()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "商户订单号和微信支付订单号不能同时为空");
        }
        
        Transaction transaction;
        if (request.getTransactionId() != null && !request.getTransactionId().isEmpty()) {
            transaction = wxPayService.queryOrderByTransactionId(request.getTransactionId());
        } else {
            transaction = wxPayService.queryOrderByOutTradeNo(request.getOutTradeNo());
        }
        
        return R.success(transaction);
    }
    
    /**
     * 关闭订单
     */
    @PostMapping("/close-order/{outTradeNo}")
    @Operation(summary = "关闭订单", description = "关闭指定商户订单号的订单")
    public R<Void> closeOrder(@Parameter(description = "商户订单号") @PathVariable String outTradeNo) {
        log.info("接收到关闭订单请求: {}", outTradeNo);
        wxPayService.closeOrder(outTradeNo);
        return R.success();
    }
    
    /**
     * 申请退款
     */
    @PostMapping("/refund")
    @Operation(summary = "申请退款", description = "对已支付的订单发起退款申请")
    public R<Refund> refund(@Valid @RequestBody RefundRequest request) {
        log.info("接收到退款申请请求: {}", request.getOutRefundNo());
        
        if (!request.isValid()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "商户订单号和微信支付订单号不能同时为空");
        }
        
        Refund refund = wxPayService.refund(request);
        return R.success(refund);
    }
    
    /**
     * 查询退款
     */
    @GetMapping("/refund/{outRefundNo}")
    @Operation(summary = "查询退款", description = "根据商户退款单号查询退款状态")
    public R<Refund> queryRefund(@Parameter(description = "商户退款单号") @PathVariable String outRefundNo) {
        log.info("接收到查询退款请求: {}", outRefundNo);
        Refund refund = wxPayService.queryRefund(outRefundNo);
        return R.success(refund);
    }
} 