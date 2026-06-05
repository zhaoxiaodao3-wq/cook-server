# 菜品小程序服务端

一个面向小群体共享的菜品记录小程序后端，支持菜品 CRUD、食材与步骤管理、星级评分和做菜建议。

## 技术栈

| 技术 | 说明 |
|---|---|
| Python 3.12+ | 开发语言 |
| FastAPI | Web 框架（异步） |
| SQLAlchemy 2.0 | ORM（异步） |
| PostgreSQL 18 | 数据库 |
| psycopg | 异步驱动 |
| Alembic | 数据库迁移 |
| JWT | 身份认证 |
| pytest | 测试框架 |

## 项目结构

```
cookbook-server/
├── app/
│   ├── main.py                 # 应用入口
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置读取
│   │   ├── database.py         # 数据库连接
│   │   ├── security.py         # JWT 生成与校验
│   │   └── deps.py             # 依赖注入
│   ├── models/                 # 数据库模型
│   │   ├── base.py             # 基类 + Mixin
│   │   ├── user.py             # 用户表
│   │   ├── category.py         # 分类表
│   │   ├── dish.py             # 菜品表
│   │   ├── ingredient.py       # 食材表
│   │   ├── step.py             # 步骤表
│   │   ├── rating.py           # 评分表
│   │   └── suggestion.py       # 建议表
│   ├── schemas/                # Pydantic 校验模型
│   │   ├── common.py           # 统一响应
│   │   ├── user.py             # 用户
│   │   ├── category.py         # 分类
│   │   ├── dish.py             # 菜品
│   │   ├── rating.py           # 评分
│   │   └── suggestion.py       # 建议
│   ├── api/v1/                 # 路由层
│   │   ├── __init__.py         # 路由聚合
│   │   ├── auth.py             # 认证
│   │   ├── users.py            # 用户
│   │   ├── categories.py       # 分类
│   │   ├── dishes.py           # 菜品
│   │   ├── ratings.py          # 评分
│   │   └── suggestions.py      # 建议
│   └── services/               # 业务逻辑层
│       ├── user.py
│       ├── category.py
│       ├── dish.py
│       ├── rating.py
│       └── suggestion.py
├── alembic/                    # 数据库迁移
├── tests/                      # 测试
├── run.py                      # 启动脚本
├── init_db.py                  # 一键建表脚本
├── requirements.txt            # 依赖
├── pyproject.toml              # 项目配置
├── .env.example                # 配置模板
└── README.md
```

## 数据库表（7 张）

```
users ────────────┐
   │ 1:N          │
   ▼              │
dishes ◄──────────┘
   │ 1:N
   ├── ingredients  (食材清单)
   ├── steps        (制作步骤)
   ├── ratings      (星级评分，每用户每个菜品一次)
   └── suggestions  (做菜建议)

categories ─── 1:N ─── dishes
```

## API 接口

### 统一响应格式

```json
// 成功
{ "code": 200, "message": "ok", "data": {} }

// 列表
{ "code": 200, "message": "ok", "data": { "items": [], "total": 42, "page": 1, "page_size": 20 } }

// 错误
{ "code": 401, "message": "未登录", "data": null }
```

### 认证 & 用户

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/v1/auth/wechat-login` | 微信登录 | 否 |
| GET | `/api/v1/users/me` | 当前用户信息 | 是 |
| PUT | `/api/v1/users/me` | 更新昵称/头像 | 是 |
| GET | `/api/v1/users/{id}` | 查看用户主页 | 否 |

### 菜品

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/v1/dishes` | 菜品列表 | 否 |
| GET | `/api/v1/dishes/{id}` | 菜品详情 | 否 |
| POST | `/api/v1/dishes` | 新增菜品 | 是 |
| PUT | `/api/v1/dishes/{id}` | 编辑菜品 | 是（仅作者） |
| DELETE | `/api/v1/dishes/{id}` | 删除菜品 | 是（仅作者） |

列表支持参数：`?category_id=1&difficulty=2&keyword=红烧&page=1&page_size=20`

### 分类 / 评分 / 建议

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/v1/categories` | 分类列表 | 否 |
| POST | `/api/v1/dishes/{id}/ratings` | 评分（1-5星） | 是 |
| PUT | `/api/v1/dishes/{id}/ratings` | 修改评分 | 是 |
| POST | `/api/v1/dishes/{id}/suggestions` | 提交建议 | 是 |

## 快速开始

### 1. 环境要求

- Python 3.12+
- PostgreSQL 18

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 配置

```powershell
copy .env.example .env
```

`.env` 文件说明：

```
DATABASE_URL=postgresql+psycopg://用户名:密码@localhost:5432/数据库名
SECRET_KEY=随机密钥（生产环境请更换）
WECHAT_APP_ID=       # 留空使用开发模式模拟登录
WECHAT_APP_SECRET=   # 留空使用开发模式模拟登录
```

### 4. 创建数据库

在 psql 中执行：

```sql
CREATE DATABASE cookbook;
```

### 5. 建表

```powershell
python init_db.py
```

### 6. 启动服务

双击 `start.bat`，或在终端运行：

```powershell
python run.py
```

服务运行在 `http://localhost:8000`

### 7. 查看文档

浏览器打开 `http://localhost:8000/docs`，可以直接在 Swagger 页面上测试所有接口。

### 8. 开发模式登录

由于微信 AppID 未配置，登录时直接传任意字符串作为 code：

```json
POST /api/v1/auth/wechat-login
{ "code": "test123" }
```

返回 JWT token 后，点击页面右上角 "Authorize" 按钮，填入 `Bearer <token>` 即可认证。

## 测试

```powershell
python -m pytest tests/ -v
```

测试使用内存 SQLite，无需数据库环境。共 11 个测试用例，覆盖认证、分类、菜品 CRUD、评分和建议。

## 插入示例分类

```powershell
# 在 psql 中执行
INSERT INTO categories (name, sort_order) VALUES
  ('川菜', 1), ('粤菜', 2), ('鲁菜', 3),
  ('苏菜', 4), ('闽菜', 5), ('浙菜', 6),
  ('湘菜', 7), ('徽菜', 8);
```

## 部署注意事项

1. **更换 JWT 密钥**：将 `.env` 中 `SECRET_KEY` 改为随机字符串
2. **配置微信小程序**：填入 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET`
3. **关闭调试模式**：`run.py` 中 `reload=False`，改用生产级服务器（如 gunicorn）
4. **HTTPS**：生产环境部署 Nginx 反向代理，启用 HTTPS
