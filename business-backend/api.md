# 管理员API文档

## 商品管理接口

### 获取商品列表

- **HTTP方法**: GET
- **路径**: `/api/super/products`
- **描述**: 获取商品列表，支持分页和筛选

#### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-----|-----|-----|-----|
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认20 |
| is_active | bool | 否 | 是否上架筛选 |
| search | string | 否 | 商品名称搜索 |

#### 返回数据

```json
{
  "items": [
    {
      "id": 1,
      "name": "积分套餐A",
      "description": "100积分",
      "credits": 100,
      "price": 10.0,
      "image_url": "https://example.com/image.jpg",
      "is_active": true,
      "sort_order": 0,
      "created_at": "2023-01-01T12:00:00",
      "updated_at": "2023-01-01T12:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### 获取单个商品

- **HTTP方法**: GET
- **路径**: `/api/super/products/{product_id}`
- **描述**: 获取单个商品详情

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| product_id | int | 商品ID |

#### 返回数据

```json
{
  "id": 1,
  "name": "积分套餐A",
  "description": "100积分",
  "credits": 100,
  "price": 10.0,
  "image_url": "https://example.com/image.jpg",
  "is_active": true,
  "sort_order": 0,
  "created_at": "2023-01-01T12:00:00",
  "updated_at": "2023-01-01T12:00:00"
}
```

### 创建商品

- **HTTP方法**: POST
- **路径**: `/api/super/products`
- **描述**: 创建新商品

#### 请求体

```json
{
  "name": "积分套餐B",
  "description": "200积分",
  "credits": 200,
  "price": 18.0,
  "image_url": "https://example.com/image2.jpg",
  "is_active": true,
  "sort_order": 1
}
```

#### 返回数据

```json
{
  "id": 2,
  "name": "积分套餐B",
  "description": "200积分",
  "credits": 200,
  "price": 18.0,
  "image_url": "https://example.com/image2.jpg",
  "is_active": true,
  "sort_order": 1,
  "created_at": "2023-01-02T12:00:00",
  "updated_at": "2023-01-02T12:00:00"
}
```

### 更新商品

- **HTTP方法**: PUT
- **路径**: `/api/super/products/{product_id}`
- **描述**: 更新商品信息

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| product_id | int | 商品ID |

#### 请求体

```json
{
  "name": "积分套餐B优惠版",
  "price": 16.0,
  "is_active": true
}
```

#### 返回数据

```json
{
  "id": 2,
  "name": "积分套餐B优惠版",
  "description": "200积分",
  "credits": 200,
  "price": 16.0,
  "image_url": "https://example.com/image2.jpg",
  "is_active": true,
  "sort_order": 1,
  "created_at": "2023-01-02T12:00:00",
  "updated_at": "2023-01-02T12:30:00"
}
```

### 删除商品

- **HTTP方法**: DELETE
- **路径**: `/api/super/products/{product_id}`
- **描述**: 删除商品（软删除）

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| product_id | int | 商品ID |

#### 返回数据

- 状态码: 204 No Content

## 订单管理接口

### 获取订单列表

- **HTTP方法**: GET
- **路径**: `/api/super/orders`
- **描述**: 获取订单列表，支持分页和筛选

#### 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|-----|-----|-----|-----|
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认20 |
| status | string | 否 | 订单状态筛选 (pending/paid/completed/cancelled/refunded) |
| user_id | int | 否 | 用户ID筛选 |
| order_no | string | 否 | 订单号筛选 |
| date_start | datetime | 否 | 创建时间起始 |
| date_end | datetime | 否 | 创建时间结束 |

#### 返回数据

```json
{
  "items": [
    {
      "id": 1,
      "order_no": "P202301010001",
      "user_id": 101,
      "user_nickname": "张三",
      "product_id": 1,
      "product_name": "积分套餐A",
      "amount": 10.0,
      "credits": 100,
      "status": "completed",
      "payment_id": "4200001234202301011234567890",
      "payment_time": "2023-01-01T12:10:00",
      "refund_time": null,
      "remark": null,
      "created_at": "2023-01-01T12:00:00",
      "updated_at": "2023-01-01T12:10:00"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

### 获取订单详情

- **HTTP方法**: GET
- **路径**: `/api/super/orders/{order_id}`
- **描述**: 获取订单详情信息

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| order_id | int | 订单ID |

#### 返回数据

```json
{
  "id": 1,
  "order_no": "P202301010001",
  "user_id": 101,
  "user_nickname": "张三",
  "user_avatar": "https://example.com/avatar.jpg",
  "product_id": 1,
  "product_name": "积分套餐A",
  "product_description": "100积分",
  "product_image_url": "https://example.com/image.jpg",
  "amount": 10.0,
  "credits": 100,
  "status": "completed",
  "payment_id": "4200001234202301011234567890",
  "payment_time": "2023-01-01T12:10:00",
  "refund_time": null,
  "remark": null,
  "created_at": "2023-01-01T12:00:00",
  "updated_at": "2023-01-01T12:10:00"
}
```

### 更新订单

- **HTTP方法**: PUT
- **路径**: `/api/super/orders/{order_id}`
- **描述**: 更新订单状态或信息

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| order_id | int | 订单ID |

#### 请求体

```json
{
  "status": "completed",
  "remark": "已手动标记为完成"
}
```

#### 返回数据

```json
{
  "id": 1,
  "order_no": "P202301010001",
  "status": "completed",
  "message": "订单更新成功"
}
```

### 删除订单

- **HTTP方法**: DELETE
- **路径**: `/api/super/orders/{order_id}`
- **描述**: 删除订单（软删除）

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| order_id | int | 订单ID |

#### 返回数据

- 状态码: 204 No Content

### 订单退款

- **HTTP方法**: POST
- **路径**: `/api/super/orders/{order_id}/refund`
- **描述**: 对已支付或已完成的订单进行退款

#### 路径参数

| 参数名 | 类型 | 描述 |
|-----|-----|-----|
| order_id | int | 订单ID |

#### 返回数据

```json
{
  "order_id": 1,
  "order_no": "P202301010001",
  "status": "refunded",
  "message": "订单退款成功"
}
```
