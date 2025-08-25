package com.aozhiai.javap.service.impl;

import com.aozhiai.javap.config.WxPayProperties;
import com.aozhiai.javap.model.payment.CreatePaymentRequest;
import com.aozhiai.javap.model.payment.RequestPaymentResponse;
import com.aozhiai.javap.model.refund.RefundRequest;
import com.aozhiai.javap.service.WxPayService;
import com.wechat.pay.java.service.payments.jsapi.JsapiServiceExtension;
import com.wechat.pay.java.service.payments.jsapi.model.Amount;
import com.wechat.pay.java.service.payments.jsapi.model.CloseOrderRequest;
import com.wechat.pay.java.service.payments.jsapi.model.Payer;
import com.wechat.pay.java.service.payments.jsapi.model.PrepayRequest;
import com.wechat.pay.java.service.payments.jsapi.model.PrepayWithRequestPaymentResponse;
import com.wechat.pay.java.service.payments.jsapi.model.QueryOrderByIdRequest;
import com.wechat.pay.java.service.payments.jsapi.model.QueryOrderByOutTradeNoRequest;
import com.wechat.pay.java.service.payments.model.Transaction;
import com.wechat.pay.java.service.refund.RefundService;
import com.wechat.pay.java.service.refund.model.AmountReq;
import com.wechat.pay.java.service.refund.model.CreateRequest;
import com.wechat.pay.java.service.refund.model.QueryByOutRefundNoRequest;
import com.wechat.pay.java.service.refund.model.Refund;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 微信支付服务实现
 */
@Service
public class WxPayServiceImpl implements WxPayService {
    
    private static final Logger log = LoggerFactory.getLogger(WxPayServiceImpl.class);
    
    @Autowired
    private JsapiServiceExtension jsapiService;
    
    @Autowired
    private RefundService refundService;
    
    @Autowired
    private WxPayProperties wxPayProperties;

    @Override
    public RequestPaymentResponse createPayment(CreatePaymentRequest request) {
        log.info("创建支付订单: {}", request.getOutTradeNo());
        
        // 构建微信支付下单请求
        PrepayRequest prepayRequest = new PrepayRequest();
        prepayRequest.setAppid(wxPayProperties.getAppId());
        prepayRequest.setMchid(wxPayProperties.getMchId());
        prepayRequest.setDescription(request.getDescription());
        prepayRequest.setOutTradeNo(request.getOutTradeNo());
        prepayRequest.setNotifyUrl(wxPayProperties.getNotifyUrl());
        System.out.println(wxPayProperties.getNotifyUrl());
        
        // 设置支付金额
        Amount amount = new Amount();
        amount.setTotal(request.getAmount());
        prepayRequest.setAmount(amount);
        
        // 设置支付者
        Payer payer = new Payer();
        payer.setOpenid(request.getOpenid());
        prepayRequest.setPayer(payer);
        
        // 设置附加数据（可选）
        if (request.getAttach() != null && !request.getAttach().isEmpty()) {
            prepayRequest.setAttach(request.getAttach());
        }
        
        // 设置订单失效时间（可选）
        if (request.getTimeExpire() != null && !request.getTimeExpire().isEmpty()) {
            prepayRequest.setTimeExpire(request.getTimeExpire());
            System.out.println(request.getTimeExpire());
        }
        
        // 调用微信支付API创建支付订单
        PrepayWithRequestPaymentResponse response = jsapiService.prepayWithRequestPayment(prepayRequest);
        
        // 转换为API响应格式
        RequestPaymentResponse paymentResponse = new RequestPaymentResponse();
        paymentResponse.setAppId(response.getAppId());
        paymentResponse.setTimeStamp(response.getTimeStamp());
        paymentResponse.setNonceStr(response.getNonceStr());
        paymentResponse.setPackageValue(response.getPackageVal());
        paymentResponse.setSignType(response.getSignType());
        paymentResponse.setPaySign(response.getPaySign());
        paymentResponse.setOutTradeNo(request.getOutTradeNo());
        
        return paymentResponse;
    }

    @Override
    public Transaction queryOrderByTransactionId(String transactionId) {
        log.info("通过微信支付订单号查询订单: {}", transactionId);
        
        QueryOrderByIdRequest request = new QueryOrderByIdRequest();
        request.setMchid(wxPayProperties.getMchId());
        request.setTransactionId(transactionId);
        
        return jsapiService.queryOrderById(request);
    }

    @Override
    public Transaction queryOrderByOutTradeNo(String outTradeNo) {
        log.info("通过商户订单号查询订单: {}", outTradeNo);
        
        QueryOrderByOutTradeNoRequest request = new QueryOrderByOutTradeNoRequest();
        request.setMchid(wxPayProperties.getMchId());
        request.setOutTradeNo(outTradeNo);
        
        return jsapiService.queryOrderByOutTradeNo(request);
    }

    @Override
    public void closeOrder(String outTradeNo) {
        log.info("关闭订单: {}", outTradeNo);
        
        CloseOrderRequest request = new CloseOrderRequest();
        request.setMchid(wxPayProperties.getMchId());
        request.setOutTradeNo(outTradeNo);
        
        jsapiService.closeOrder(request);
    }

    @Override
    public Refund refund(RefundRequest request) {
        log.info("申请退款: {}", request.getOutRefundNo());
        
        CreateRequest refundRequest = new CreateRequest();
        
        // 设置订单信息
        if (request.getTransactionId() != null && !request.getTransactionId().isEmpty()) {
            refundRequest.setTransactionId(request.getTransactionId());
        } else {
            refundRequest.setOutTradeNo(request.getOutTradeNo());
        }
        
        refundRequest.setOutRefundNo(request.getOutRefundNo());
        refundRequest.setReason(request.getReason());
        refundRequest.setNotifyUrl(wxPayProperties.getRefundNotifyUrl());
        
        // 设置退款金额
        AmountReq amount = new AmountReq();
        amount.setRefund(request.getAmount().longValue());
        amount.setTotal(request.getTotalAmount().longValue());
        amount.setCurrency("CNY");
        refundRequest.setAmount(amount);
        
        return refundService.create(refundRequest);
    }

    @Override
    public Refund queryRefund(String outRefundNo) {
        log.info("查询退款: {}", outRefundNo);
        
        QueryByOutRefundNoRequest request = new QueryByOutRefundNoRequest();
        request.setOutRefundNo(outRefundNo);
        
        return refundService.queryByOutRefundNo(request);
    }
} 