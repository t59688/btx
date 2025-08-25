# 积分 (Credits) API 文档

## 基础信息

- 接口基础路径: `/api/v1/credits`
- 身份验证: 所有接口都需要用户认证，需要在请求头中包含 `Authorization: Bearer {token}`。

## 目录

- [积分 (Credits) API 文档](#积分-credits-api-文档)
  - [基础信息](#基础信息)
  - [目录](#目录)
  - [1. 获取用户积分余额](#1-获取用户积分余额)
  - [2. 获取用户积分记录](#2-获取用户积分记录)
  - [3. 从广告获取积分奖励](#3-从广告获取积分奖励)
  - [4. 管理员更新用户积分](#4-管理员更新用户积分)
  - [卡密接口](#卡密接口)
    - [卡密激活](#卡密激活)
  - [管理后台接口](#管理后台接口)
    - [卡密管理接口](#卡密管理接口)
      - [创建卡密](#创建卡密)
      - [获取卡密列表](#获取卡密列表)
      - [获取单个卡密详情](#获取单个卡密详情)
      - [更新卡密状态](#更新卡密状态)
      - [删除卡密](#删除卡密)

---

## 1. 获取用户积分余额

- **方法**: `GET`
- **路径**: `/balance`
- **描述**: 获取当前登录用户的积分余额。
- **认证**: 需要用户认证 (`Authorization: Bearer {token}`)。
- **请求参数**: 无
- **成功响应**: `200 OK`
  ```json
  {
    "balance": 100
  }
  ```
- **错误响应**:
  - `401 Unauthorized`: 未认证。
  - `404 Not Found`: 用户不存在。
    ```json
    { "detail": "用户不存在" }
    ```

---

## 2. 获取用户积分记录

- **方法**: `GET`
- **路径**: `/records`
- **描述**: 获取当前登录用户的积分记录历史，支持分页。
- **认证**: 需要用户认证 (`Authorization: Bearer {token}`)。
- **查询参数**:
  - `skip` (integer, optional, default: 0): 跳过的记录数。
  - `limit` (integer, optional, default: 20): 返回的最大记录数。
- **成功响应**: `200 OK`
  ```json
  [
    {
      "id": 123,
      "user_id": 1,
      "amount": 50,
      "balance": 150,
      "type": "ad_reward",
      "description": "观看广告奖励",
      "related_id": null,
      "created_at": "2023-10-27T10:00:00Z"
    },
    {
      "id": 124,
      "user_id": 1,
      "amount": -30,
      "balance": 120,
      "type": "artwork_creation",
      "description": "创建艺术作品",
      "related_id": 456,
      "created_at": "2023-10-28T11:00:00Z"
    }
    // ... 更多积分记录
  ]
  ```
- **错误响应**:
  - `401 Unauthorized`: 未认证。

---

## 3. 从广告获取积分奖励

- **方法**: `POST`
- **路径**: `/ad-reward`
- **描述**: 用户看完广告后调用此接口获取积分奖励。
- **认证**: 需要用户认证 (`Authorization: Bearer {token}`)。
- **请求体**: `application/json`
  ```json
  {
    "ad_type": "video"
  }
  ```
  - `ad_type` (string, required): 广告类型，例如 "video"（视频广告）、"banner"（横幅广告）等。
- **成功响应**: `200 OK`
  ```json
  {
    "reward_amount": 10,
    "balance": 160,
    "message": "奖励积分成功"
  }
  ```
- **错误响应**:
  - `400 Bad Request`: 奖励积分失败。
    ```json
    { "detail": "奖励积分失败" }
    ```
    ```json
    { "detail": "今日广告观看次数已达上限" }
    ```
  - `401 Unauthorized`: 未认证。
  - `422 Unprocessable Entity`: 请求体验证失败。

---

## 4. 管理员更新用户积分

- **方法**: `POST`
- **路径**: `/admin/update`
- **描述**: 管理员给指定用户增加或减少积分。
- **认证**: 需要管理员认证 (`Authorization: Bearer {token}`)。
- **查询参数**:
  - `user_id` (integer, required): 要更新积分的用户ID。
- **请求体**: `application/json`
  ```json
  {
    "amount": 100,
    "type": "admin_reward",
    "description": "管理员奖励",
    "related_id": null
  }
  ```
  - `amount` (integer, required): 积分变动数量，正数表示增加，负数表示减少。
  - `type` (string, required): 积分变动类型，例如 "admin_reward"、"compensation" 等。
  - `description` (string, required): 积分变动描述。
  - `related_id` (integer, optional): 相关联的ID，例如订单ID、作品ID等。
- **成功响应**: `200 OK`
  ```json
  {
    "amount": 100,
    "balance": 260,
    "message": "更新积分成功"
  }
  ```
- **错误响应**:
  - `400 Bad Request`: 更新积分失败。
    ```json
    { "detail": "更新积分失败" }
    ```
  - `401 Unauthorized`: 未认证。
  - `403 Forbidden`: 无权限执行此操作（非管理员）。
    ```json
    { "detail": "无权限执行此操作" }
    ```
  - `422 Unprocessable Entity`: 请求体验证失败。

## 卡密接口

### 卡密激活

```
POST /api/v1/card-keys/activate
```

请求体：

```json
{
  "card_key": "ABC123DEF" // 9位卡密字符串
}
```

响应：

```json
{
  "credits": 100, // 获得的积分
  "balance": 200, // 当前积分余额
  "message": "卡密激活成功"
}
```

## 管理后台接口

### 卡密管理接口

#### 创建卡密

```
POST /api/v1/super/card-keys
```

请求体：

```json
{
  "credits": 100, // 积分面值
  "count": 10, // 创建数量，1-1000
  "batch_no": "BATCH001", // 可选，批次号
  "expired_at": "2023-12-31T23:59:59", // 可选，过期时间
  "remark": "促销活动" // 可选，备注
}
```

响应：

```json
{
  "batch_no": "BN20230801123456ABCDEF",
  "count": 10,
  "credits": 100,
  "expired_at": "2023-12-31T23:59:59"
}
```

#### 获取卡密列表

```
GET /api/v1/super/card-keys
```

查询参数：

- `page`: 页码，默认1
- `per_page`: 每页数量，默认10
- `status`: 状态筛选，可选值: unused, used, invalid
- `batch_no`: 批次号筛选
- `created_start`: 创建开始时间
- `created_end`: 创建结束时间

响应：

```json
{
  "items": [
    {
      "id": 1,
      "card_key": "ABC123DEF",
      "credits": 100,
      "batch_no": "BN20230801123456ABCDEF",
      "created_by": 1,
      "created_at": "2023-08-01T12:34:56",
      "expired_at": "2023-12-31T23:59:59",
      "status": "unused",
      "used_at": null,
      "used_by": null,
      "used_by_nickname": null,
      "remark": "促销活动"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "total_pages": 10
}
```

#### 获取单个卡密详情

```
GET /api/v1/super/card-keys/{id}
```

响应：

```json
{
  "id": 1,
  "card_key": "ABC123DEF",
  "credits": 100,
  "batch_no": "BN20230801123456ABCDEF",
  "created_by": 1,
  "created_at": "2023-08-01T12:34:56",
  "expired_at": "2023-12-31T23:59:59",
  "status": "unused",
  "used_at": null,
  "used_by": null,
  "used_by_nickname": null,
  "remark": "促销活动"
}
```

#### 更新卡密状态

```
PUT /api/v1/super/card-keys/{id}/status
```

请求体：

```json
{
  "status": "invalid" // 状态: unused, used, invalid
}
```

响应：

```json
{
  "id": 1,
  "card_key": "ABC123DEF",
  "credits": 100,
  "batch_no": "BN20230801123456ABCDEF",
  "created_by": 1,
  "created_at": "2023-08-01T12:34:56",
  "expired_at": "2023-12-31T23:59:59",
  "status": "invalid",
  "used_at": null,
  "used_by": null,
  "used_by_nickname": null,
  "remark": "促销活动"
}
```

#### 删除卡密

```
DELETE /api/v1/super/card-keys/{id}
```

响应：

状态码 204，无响应体 