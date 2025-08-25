# AI-Art-Miniprogram

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**一个由 AI 编写的、功能完整的 AI 图片风格化微信小程序全栈项目。**

## 👋 简介

这是一个完整的 AI 艺术风格转换解决方案，它包含了一个用户友好的微信小程序前端、一个强大的 FastAPI 后端，以及一个功能齐全的 Vue 3 管理后台。

**本项目的所有代码，从前端到后端，几乎完全由 AI 辅助生成**。开源此项目，希望能为社区提供一个完整的、可落地的参考案例，并与大家一同探索 AI 在软件开发领域的应用潜力。

## ✨ 项目截图

## 🚀 主要功能

### 小程序端 (用户)

- **微信授权登录**：一键创建用户账户。
- **图片上传与处理**：支持图片压缩，优化体验。
- **AI 风格转换**：选择不同艺术风格，生成创意图片。
- **作品画廊**：管理和展示个人创作，可设为公开或私密。
- **积分系统**：通过消耗积分进行创作。
- **在线支付**：集成微信支付，可直接购买积分套餐。
- **订单与积分记录**：清晰追踪消费历史。

### 管理后台 (管理员)

- **仪表盘**：核心数据一览，掌握应用动态。
- **用户管理**：查看、搜索、封禁用户，调整用户积分。
- **风格管理**：创建、编辑、上架/下架艺术风格，自定义AI提示词。
- **作品管理**：审查用户生成内容，管理公开作品。
- **订单管理**：查看所有交易订单状态。
- **商品管理**：配置不同的积分充值套餐。
- **卡密管理**：生成和管理积分兑换码，用于营销活动。
- **系统配置**：动态配置应用的关键参数，如API密钥、积分消耗等。

## 🛠️ 技术栈

- **后端 (Backend)**
  - Python 3.x
  - FastAPI: 高性能的 Web 框架
  - MySQL / MariaDB: 数据存储
  - Java: 独立模块，用于处理微信支付回调等复杂逻辑 (可选，可替换为Python实现)

- **小程序端 (Mini Program)**
  - 微信原生小程序 (WXML, WXSS, JavaScript)

- **管理后台 (Admin Panel)**
  - Vue 3
  - Vite
  - Naive UI: 一套美观且功能强大的组件库
  - TypeScript

- **依赖服务**
  - **OpenAI API** (或类似的图像生成AI API)
  - **微信支付**
  - **腾讯云对象存储 (COS)**: 用于图片资源的存储与分发

## 📁 项目结构

本仓库是一个 monorepo，包含三个核心部分：

```md
.
├── admin-frontend/         # Vue 3 管理后台
├── business-backend/       # FastAPI 后端服务
└── wx-app/   # 微信小程序前端
└── wxpay-gateway/ # 微信支付网关
└── README.md      # 就是你正在看的这个文件
```

# 快速开始

## 系统架构

本系统由三个服务组成：

- **wx-backend**: Python后端服务
- **wx-javap**: Java支付网关服务
- **mysql**: 数据库服务

## 环境要求

- Docker 20.10.0+
- Docker Compose 2.0.0+

## 部署步骤

### 准备工作

1. 复制环境变量示例文件并进行配置：

```bash
cp env.example .env
```

2. 修改`.env`文件中的配置（如数据库密码等）。

3. 准备微信支付证书文件：

```bash
# 创建证书目录
mkdir -p wx-javap/cert

# 将微信支付证书文件复制到证书目录
cp /path/to/your/certificates/apiclient_key.pem wx-javap/cert/
cp /path/to/your/certificates/wechatpay_platform_cert.pem wx-javap/cert/
```

### 部署所有服务

```bash
docker-compose up -d
```

这将构建并启动所有三个服务。首次运行可能需要较长时间。

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

查看所有服务的日志：

```bash
docker-compose logs -f
```

查看特定服务的日志：

```bash
docker-compose logs -f wx-backend
docker-compose logs -f wx-javap
docker-compose logs -f mysql
```

## 单独更新服务

### 更新后端服务

```bash
docker-compose up -d --build wx-backend
```

### 更新支付网关服务

```bash
docker-compose up -d --build wx-javap
```

### 更新数据库服务（慎用）

```bash
docker-compose up -d --build mysql
```

注意：更新数据库服务可能导致数据丢失，除非你已正确配置持久化存储。

## 服务访问

- wx-backend: <http://localhost:8000>
- wx-javap: <http://localhost:8081/api>
- Swagger UI: <http://localhost:8081/api/swagger-ui.html>
- mysql: localhost:3306

## 环境变量配置

### 数据库配置

- `MYSQL_ROOT_PASSWORD`: MySQL root密码
- `MYSQL_DATABASE`: 数据库名称
- `MYSQL_USER`: 数据库用户名
- `MYSQL_PASSWORD`: 数据库密码

### 业务后端配置

- `PAYMENT_GATEWAY_URL`: 支付网关URL
- `PAYMENT_CALLBACK_TOKEN`: 用于验证支付网关回调的安全令牌（必须与支付网关的BUSINESS_PAYMENT_TOKEN一致）

### 支付网关配置

- `BUSINESS_PAYMENT_TOKEN`: 业务系统与支付网关间的安全令牌

### 微信支付配置

- `WX_PAY_APP_ID`: 微信支付AppID
- `WX_PAY_MCH_ID`: 微信支付商户号
- `WX_PAY_MCH_SERIAL_NO`: 微信支付证书序列号
- `WX_PAY_API_V3_KEY`: 微信支付APIv3密钥
- `WX_PAY_NOTIFY_URL`: 支付通知回调URL
- `WX_PAY_REFUND_NOTIFY_URL`: 退款通知回调URL

## 服务停止与删除

停止所有服务：

```bash
docker-compose down
```

停止并删除所有数据（包括数据库数据）：

```bash
docker-compose down -v
```

## 常见问题

### 端口冲突

如果出现端口冲突，请修改`docker-compose.yml`文件中的端口映射。例如：

```yaml
ports:
  - "8001:8000"  # 将本地8001端口映射到容器内8000端口
```

### 数据持久化

数据库数据已配置为持久化存储在Docker卷中（mysql-data）。你也可以修改配置，使用主机目录进行持久化：

```yaml
volumes:
  - ./data/mysql:/var/lib/mysql
```

### 证书问题

如果遇到证书相关错误，请确认：

1. 证书文件已正确放置在`wx-javap/cert/`目录下
2. 证书文件的权限设置正确
3. 文件名与`docker-compose.yml`中的环境变量设置一致

### 安全令牌配置

确保`PAYMENT_CALLBACK_TOKEN`和`BUSINESS_PAYMENT_TOKEN`设置为相同的值，否则支付回调验证将失败。这两个令牌用于后端服务和支付网关之间的安全通信。
