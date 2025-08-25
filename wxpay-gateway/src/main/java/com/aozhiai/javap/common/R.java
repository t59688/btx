package com.aozhiai.javap.common;

import java.io.Serializable;
import java.util.UUID;

/**
 * 通用响应类
 * @param <T> 响应数据类型
 */
public class R<T> implements Serializable {
    private static final long serialVersionUID = 1L;

    /** 状态码 */
    private int code;
    
    /** 消息 */
    private String message;
    
    /** 数据 */
    private T data;
    
    /** 请求ID */
    private String requestId;

    public R() {
        this.requestId = UUID.randomUUID().toString();
    }

    /**
     * 成功响应
     * @param <T> 数据类型
     * @return 响应对象
     */
    public static <T> R<T> success() {
        return success(null);
    }

    /**
     * 成功响应
     * @param data 数据
     * @param <T> 数据类型
     * @return 响应对象
     */
    public static <T> R<T> success(T data) {
        return success(data, "操作成功");
    }

    /**
     * 成功响应
     * @param data 数据
     * @param message 消息
     * @param <T> 数据类型
     * @return 响应对象
     */
    public static <T> R<T> success(T data, String message) {
        R<T> r = new R<>();
        r.setCode(200);
        r.setData(data);
        r.setMessage(message);
        return r;
    }

    /**
     * 失败响应
     * @param <T> 数据类型
     * @return 响应对象
     */
    public static <T> R<T> error() {
        return error(500, "操作失败");
    }

    /**
     * 失败响应
     * @param message 消息
     * @param <T> 数据类型
     * @return 响应对象
     */
    public static <T> R<T> error(String message) {
        return error(500, message);
    }

    /**
     * 失败响应
     * @param code 状态码
     * @param message 消息
     * @param <T> 数据类型
     * @return 响应对象
     */
    public static <T> R<T> error(int code, String message) {
        R<T> r = new R<>();
        r.setCode(code);
        r.setMessage(message);
        return r;
    }

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }

    public String getRequestId() {
        return requestId;
    }

    public void setRequestId(String requestId) {
        this.requestId = requestId;
    }
} 