package com.aozhiai.javap.common;

import com.wechat.pay.java.core.exception.HttpException;
import com.wechat.pay.java.core.exception.MalformedMessageException;
import com.wechat.pay.java.core.exception.ServiceException;
import com.wechat.pay.java.core.exception.ValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 */
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);
    
    /**
     * 处理参数校验异常
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public R<Void> handleValidException(MethodArgumentNotValidException e) {
        log.error("参数校验失败", e);
        return R.error(400, e.getBindingResult().getAllErrors().get(0).getDefaultMessage());
    }
    
    /**
     * 处理微信HTTP请求异常
     */
    @ExceptionHandler(HttpException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public R<Void> handleHttpException(HttpException e) {
        log.error("微信支付请求异常: {}", e.getMessage(), e);
        return R.error("微信支付API调用异常: " + e.getMessage());
    }
    
    /**
     * 处理微信服务异常
     */
    @ExceptionHandler(ServiceException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public R<Void> handleServiceException(ServiceException e) {
        log.error("微信支付服务异常: {}, HTTP状态码: {}, 错误码: {}, 错误描述: {}",
                e.getMessage(), e.getHttpStatusCode(), e.getErrorCode(), e.getErrorMessage(), e);
        return R.error("微信支付服务异常: " + e.getErrorMessage());
    }
    
    /**
     * 处理微信消息格式异常
     */
    @ExceptionHandler(MalformedMessageException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public R<Void> handleMalformedMessageException(MalformedMessageException e) {
        log.error("微信支付消息格式异常: {}", e.getMessage(), e);
        return R.error("微信支付响应格式异常: " + e.getMessage());
    }
    
    /**
     * 处理微信验证异常
     */
    @ExceptionHandler(ValidationException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public R<Void> handleValidationException(ValidationException e) {
        log.error("微信支付验证异常: {}", e.getMessage(), e);
        return R.error("微信支付验证失败: " + e.getMessage());
    }
    
    /**
     * 处理所有其他异常
     */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public R<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return R.error("系统异常，请稍后重试");
    }
} 