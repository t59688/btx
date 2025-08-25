
# 积分商品与支付系统API文档

## 1. 商品相关接口

### 1.1 获取商品列表

- **接口URL**: `/api/products/`
- **HTTP方法**: `GET`
- **请求参数**:
  | 参数 | 类型 | 是否必须 | 默认值 | 描述 |
  |-----|------|---------|-------|------|
  | skip | int | 否 | 0 | 分页起始位置 |
  | limit | int | 否 | 20 | 每页数量 |

- **返回示例**:
```json
[
  {
    "id": 1,
    "name": "100积分套餐",
    "description": "购买100积分",
    "credits": 100,
    "price": 9.9,
    "image_url": "https://example.com/images/credits-100.png",
    "is_active": true,
    "sort_order": 1,
    "created_at": "2023-07-01T12:00:00",
    "updated_at": "2023-07-01T12:00:00"
  },
  {
    "id": 2,
    "name": "500积分套餐",
    "description": "购买500积分",
    "credits": 500,
    "price": 39.9,
    "image_url": "https://example.com/images/credits-500.png",
    "is_active": true,
    "sort_order": 2,
    "created_at": "2023-07-01T12:00:00",
    "updated_at": "2023-07-01T12:00:00"
  }
]
```

### 1.2 获取商品详情

- **接口URL**: `/api/products/{product_id}`
- **HTTP方法**: `GET`
- **请求参数**:
  | 参数 | 类型 | 是否必须 | 描述 |
  |-----|------|---------|------|
  | product_id | int | 是 | 商品ID |

- **返回示例**:
```json
{
  "id": 1,
  "name": "100积分套餐",
  "description": "购买100积分",
  "credits": 100,
  "price": 9.9,
  "image_url": "https://example.com/images/credits-100.png",
  "is_active": true,
  "sort_order": 1,
  "created_at": "2023-07-01T12:00:00",
  "updated_at": "2023-07-01T12:00:00"
}
```

## 2. 订单相关接口

### 2.1 创建订单

- **接口URL**: `/api/orders/create`
- **HTTP方法**: `POST`
- **请求头**:
  | 参数 | 值 | 是否必须 | 描述 |
  |-----|---|---------|------|
  | Authorization | Bearer {token} | 是 | 用户认证Token |

- **请求参数**:
```json
{
  "product_id": 1
}
```

- **返回示例**:
```json
{
  "order_id": 100,
  "order_no": "P202307011200001234abcd",
  "amount": 9.9,
  "credits": 100,
  "message": "订单创建成功"
}
```

### 2.2 发起支付

- **接口URL**: `/api/orders/pay/{order_id}`
- **HTTP方法**: `POST`
- **请求头**:
  | 参数 | 值 | 是否必须 | 描述 |
  |-----|---|---------|------|
  | Authorization | Bearer {token} | 是 | 用户认证Token |

- **请求参数**:
  | 参数 | 类型 | 是否必须 | 描述 |
  |-----|------|---------|------|
  | order_id | int | 是 | 订单ID |

- **返回示例**:
```json
{
  "payment_data": {
    "appId": "wx123456789",
    "timeStamp": "1627436982",
    "nonceStr": "abcdefg12345",
    "packageValue": "prepay_id=wx12345678901234567890",
    "signType": "RSA",
    "paySign": "abcdefghijklmnopqrstuvwxyz123456789",
    "outTradeNo": "P202307011200001234abcd"
  },
  "message": "创建支付成功"
}
```

### 2.3 获取用户订单列表

- **接口URL**: `/api/orders/`
- **HTTP方法**: `GET`
- **请求头**:
  | 参数 | 值 | 是否必须 | 描述 |
  |-----|---|---------|------|
  | Authorization | Bearer {token} | 是 | 用户认证Token |

- **请求参数**:
  | 参数 | 类型 | 是否必须 | 默认值 | 描述 |
  |-----|------|---------|-------|------|
  | skip | int | 否 | 0 | 分页起始位置 |
  | limit | int | 否 | 20 | 每页数量 |

- **返回示例**:
```json
[
  {
    "id": 100,
    "order_no": "P202307011200001234abcd",
    "user_id": 1,
    "product_id": 1,
    "amount": 9.9,
    "credits": 100,
    "status": "completed",
    "payment_id": "4200001234202307011234567890",
    "payment_time": "2023-07-01T12:05:00",
    "refund_time": null,
    "remark": null,
    "created_at": "2023-07-01T12:00:00",
    "updated_at": "2023-07-01T12:05:30"
  },
  {
    "id": 101,
    "order_no": "P202307021300005678efgh",
    "user_id": 1,
    "product_id": 2,
    "amount": 39.9,
    "credits": 500,
    "status": "pending",
    "payment_id": null,
    "payment_time": null,
    "refund_time": null,
    "remark": null,
    "created_at": "2023-07-02T13:00:00",
    "updated_at": "2023-07-02T13:00:00"
  }
]
```

### 2.4 获取订单详情

- **接口URL**: `/api/orders/{order_id}`
- **HTTP方法**: `GET`
- **请求头**:
  | 参数 | 值 | 是否必须 | 描述 |
  |-----|---|---------|------|
  | Authorization | Bearer {token} | 是 | 用户认证Token |

- **请求参数**:
  | 参数 | 类型 | 是否必须 | 描述 |
  |-----|------|---------|------|
  | order_id | int | 是 | 订单ID |

- **返回示例**:
```json
{
  "id": 100,
  "order_no": "P202307011200001234abcd",
  "amount": 9.9,
  "credits": 100,
  "status": "completed",
  "payment_id": "4200001234202307011234567890",
  "payment_time": "2023-07-01T12:05:00",
  "refund_time": null,
  "remark": null,
  "created_at": "2023-07-01T12:00:00",
  "updated_at": "2023-07-01T12:05:30",
  "product_name": "100积分套餐",
  "product_description": "购买100积分",
  "product_image_url": "https://example.com/images/credits-100.png"
}
```


你需要添加支付状态查询接口。以下是实现代码：

## 1. 在OrderService中添加查询方法

在`app/services/order.py`中添加：

```python
@staticmethod
async def query_payment_status(db: Session, order_id: int) -> Tuple[bool, Dict[str, Any]]:
    """查询支付状态并更新订单"""
    try:
        # 查询订单
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return False, {"error": "订单不存在"}
            
        if order.status != OrderStatus.PENDING:
            # 订单已处理，直接返回状态
            return True, {
                "order_id": order.id, 
                "status": order.status,
                "paid": order.status in [OrderStatus.PAID, OrderStatus.COMPLETED]
            }
            
        # 调用Java支付网关查询订单状态
        payment_url = "http://localhost:8081/api/pay/query-status"
        
        payment_data = {
            "outTradeNo": order.order_no
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(payment_url, json=payment_data)
            result = response.json()
        
        if response.status_code != 200 or result.get("code") != 200:
            return False, {"error": f"查询支付状态失败: {result.get('message', '未知错误')}"}
            
        payment_result = result.get("data", {})
        trade_state = payment_result.get("trade_state", "")
        
        # 处理支付结果
        if trade_state == "SUCCESS":
            # 更新订单为已支付
            order.status = OrderStatus.PAID
            order.payment_id = payment_result.get("transaction_id")
            order.payment_time = datetime.now()
            
            # 给用户增加积分
            success, credit_result = CreditService.update_credits(
                db=db,
                user_id=order.user_id,
                amount=order.credits,
                type="purchase",
                description=f"购买{order.credits}积分",
                related_id=order.id
            )
            
            if success:
                order.status = OrderStatus.COMPLETED
                db.commit()
                return True, {
                    "order_id": order.id,
                    "status": order.status,
                    "paid": True,
                    "message": "支付成功"
                }
            else:
                db.rollback()
                return False, {"error": f"支付成功但增加积分失败: {credit_result.get('error')}"}
        
        elif trade_state in ["CLOSED", "REVOKED", "PAYERROR"]:
            # 支付失败或取消
            order.status = OrderStatus.CANCELLED
            db.commit()
            return True, {
                "order_id": order.id,
                "status": order.status,
                "paid": False,
                "message": "支付失败或已取消"
            }
            
        else:
            # 支付处理中或其他状态
            return True, {
                "order_id": order.id,
                "status": order.status,
                "paid": False,
                "message": f"支付进行中，状态: {trade_state}"
            }
            
    except Exception as e:
        db.rollback()
        logger.error(f"查询支付状态失败: {str(e)}")
        return False, {"error": f"查询支付状态失败: {str(e)}"}
```

## 2. 在订单接口中添加查询接口

在`app/api/endpoints/orders.py`中添加：

```python
@router.get("/payment-status/{order_id}", response_model=Dict[str, Any])
async def check_payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    查询支付状态
    """
    # 验证订单属于当前用户
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 查询支付状态
    success, result = await OrderService.query_payment_status(db=db, order_id=order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "查询支付状态失败")
        )
    
    return result
```



**接口URL**: `/api/orders/payment-status/{order_id}`  
**HTTP方法**: `GET`  
**请求头**:  
- Authorization: Bearer {token} (必须)

**返回示例**:
```json
{
  "order_id": 100,
  "status": "completed",
  "paid": true,
  "message": "支付成功"
}
```

前端调用流程：
1. 用户完成微信支付后
2. 前端调用此接口查询实际支付状态
3. 根据返回的paid字段判断支付是否成功
4. 如成功，则刷新用户积分余额


## 3. 支付回调接口

### 3.1 支付回调接口

*注意：此接口主要用于支付网关回调，前端通常不需要直接调用*

- **接口URL**: `/api/orders/callback`
- **HTTP方法**: `POST`
- **请求参数**:
```json
{
  "order_no": "P202307011200001234abcd",
  "payment_id": "4200001234202307011234567890",
  "status": "SUCCESS",
  "amount": 9.9
}
```

- **返回示例**:
```json
{
  "message": "处理支付回调成功"
}
```

## 4. 状态码说明

| 状态码 | 描述 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token无效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 5. 订单状态说明

| 状态值 | 描述 |
|-------|------|
| pending | 待支付 |
| paid | 已支付 |
| completed | 已完成 |
| cancelled | 已取消 |
| refunded | 已退款 |

## 6. 集成示例

### 创建订单并发起支付流程

1. 调用创建订单接口获取订单信息
2. 调用支付接口获取支付参数
3. 使用微信小程序API发起支付

```javascript
// 创建订单
async function createOrder(productId) {
  const response = await wx.request({
    url: 'https://your-api-domain.com/api/orders/create',
    method: 'POST',
    data: { product_id: productId },
    header: { 'Authorization': 'Bearer ' + wx.getStorageSync('token') }
  });
  
  if (response.statusCode === 200) {
    return response.data;
  } else {
    throw new Error(response.data.detail || '创建订单失败');
  }
}

// 发起支付
async function payOrder(orderId) {
  const response = await wx.request({
    url: `https://your-api-domain.com/api/orders/pay/${orderId}`,
    method: 'POST',
    header: { 'Authorization': 'Bearer ' + wx.getStorageSync('token') }
  });
  
  if (response.statusCode === 200) {
    const paymentData = response.data.payment_data;
    
    // 调用微信支付
    wx.requestPayment({
      timeStamp: paymentData.timeStamp,
      nonceStr: paymentData.nonceStr,
      package: paymentData.packageValue,
      signType: paymentData.signType,
      paySign: paymentData.paySign,
      success(res) {
        console.log('支付成功', res);
        // 支付成功后刷新用户积分
      },
      fail(err) {
        console.error('支付失败', err);
      }
    });
    
    return true;
  } else {
    throw new Error(response.data.detail || '发起支付失败');
  }
}
```
