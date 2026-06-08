# 后端操作手册（cookbook-server）

本文档说明 **本地开发如何启动服务**，以及 **如何发布 / 维护线上服务**。

---

## 一、服务架构（线上）

| 组件 | 平台 | 地址 / 说明 |
|------|------|-------------|
| API 服务 | [Render](https://render.com) | https://cookbook-server-qdi6.onrender.com |
| 数据库 | [Supabase](https://supabase.com) | 项目 `cookbook`（ref: `uqiwkxzjlwlcrvwktcfa`） |
| 代码仓库 | GitHub | https://github.com/zhaoxiaodao3-wq/cook-server |

**常用线上地址：**

- 健康检查：`https://cookbook-server-qdi6.onrender.com/health`
- API 文档：`https://cookbook-server-qdi6.onrender.com/docs`
- API 根路径：`https://cookbook-server-qdi6.onrender.com/api/v1`

---

## 二、本地开发

### 2.1 环境要求

- Python 3.12+
- PostgreSQL（本地）或 Supabase 远程库（二选一）

### 2.2 首次配置

```powershell
cd E:\code\minipro\cookbook-server

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
copy .env.example .env
```

编辑 `.env`：

```env
# 本地 PostgreSQL
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/cookbook

SECRET_KEY=change-me-to-a-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=43200

# 本地调试可留空，走模拟登录 dev_{code}
WECHAT_APP_ID=
WECHAT_APP_SECRET=
```

若使用本地库，需先建库并建表：

```sql
CREATE DATABASE cookbook;
```

```powershell
py init_db.py
```

### 2.3 启动服务

**方式一：双击 `start.bat`**

**方式二：终端**

```powershell
cd E:\code\minipro\cookbook-server
py run.py
```

启动成功后：

- 服务地址：`http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`

控制台无报错、浏览器能打开 `/docs` 即表示启动成功。

### 2.4 本地登录调试

`.env` 中 `WECHAT_APP_ID` / `WECHAT_APP_SECRET` 留空时，任意 `code` 可模拟登录：

```http
POST http://localhost:8000/api/v1/auth/wechat-login
Content-Type: application/json

{ "code": "test123" }
```

返回 JWT 后，在 Swagger 右上角 **Authorize** 填入 `Bearer <token>`。

### 2.5 运行测试

```powershell
py -m pytest tests/ -v
```

---

## 三、发布到线上（Render + Supabase）

### 3.1 整体流程

```
改代码 → push 到 GitHub main → Render 自动部署 → 验证 /health
```

数据库在 Supabase，**一般不需要随每次代码发布而变更**；只有表结构变化时才需执行迁移。

### 3.2 Supabase 数据库

**控制台：** https://supabase.com/dashboard/project/uqiwkxzjlwlcrvwktcfa

| 操作 | 位置 |
|------|------|
| 查看表数据 | Table Editor |
| 获取连接串 | 项目首页 **Connect** → Type 选 **Transaction**（端口 6543） |
| 重置数据库密码 | Project Settings → Database → Reset database password |

**`DATABASE_URL` 格式（Render 环境变量用）：**

```
postgresql+psycopg://postgres.uqiwkxzjlwlcrvwktcfa:你的密码@aws-0-区域.pooler.supabase.com:6543/postgres
```

注意：

- 前缀必须是 `postgresql+psycopg://`（不是 `postgresql://`）
- 使用 **Transaction pooler（6543）**，适合 Render 无状态部署

**新增表 / 改表结构：**

1. 本地编写 Alembic 迁移并测试：`py -m alembic upgrade head`
2. 同步到远程：`py scripts/sync_db.py schema push`（需 `DB_SYNC_ENABLED=true`）
3. 详见 [DATABASE_SYNC.md](DATABASE_SYNC.md)

### 3.2.1 数据库同步（本地 ↔ 线上）

完整说明见 **[docs/DATABASE_SYNC.md](DATABASE_SYNC.md)**，包括配置、四条命令、常见场景与排错。

**速查：**

```powershell
py scripts/sync_db.py status              # 对比行数（不用开开关）
py scripts/sync_db.py schema push         # 表结构 本地→线上
py scripts/sync_db.py data push --yes     # 数据 本地→线上（覆盖）
py scripts/sync_db.py data pull --yes     # 数据 线上→本地（覆盖）
```

同步前在 `.env` 配置 `REMOTE_DATABASE_URL`，并将 `DB_SYNC_ENABLED=true`（`status` 除外）。

### 3.3 Render 应用服务

**控制台：** https://dashboard.render.com

Blueprint 名称：`mia-fly`  
Web 服务名称：`cookbook-server`

| 操作 | 步骤 |
|------|------|
| 查看部署状态 | Render → `cookbook-server` → Events / Logs |
| 手动重新部署 | 服务页 → **Manual Deploy** → Deploy latest commit |
| 修改环境变量 | 服务页 → **Environment** → 编辑 → Save（会自动 redeploy） |

**必须配置的环境变量：**

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | Supabase Transaction pooler 连接串 |
| `SECRET_KEY` | JWT 签名密钥（随机长字符串） |
| `WECHAT_APP_ID` | 小程序 AppID |
| `WECHAT_APP_SECRET` | 小程序 AppSecret |
| `JWT_ALGORITHM` | `HS256`（render.yaml 已默认） |
| `JWT_EXPIRE_MINUTES` | `43200`（render.yaml 已默认） |

### 3.4 发布新版本

```powershell
cd E:\code\minipro\cookbook-server

git add .
git commit -m "描述你的改动"
git push origin main
```

Push 后 Render 会自动拉取 `main` 分支并重新部署，约 2–5 分钟。

### 3.5 发布验证清单

部署完成后逐项检查：

```powershell
# 1. 健康检查
curl https://cookbook-server-qdi6.onrender.com/health
# 期望：{"status":"ok"}

# 2. 分类接口（验证数据库连通）
curl https://cookbook-server-qdi6.onrender.com/api/v1/categories
# 期望：返回 8 个分类
```

浏览器打开 `https://cookbook-server-qdi6.onrender.com/docs` 确认 Swagger 可访问。

### 3.6 Render 免费版注意事项

- **15 分钟无访问会休眠**，首次请求可能等待 30–60 秒唤醒
- 上传的图片存在容器本地 `uploads/`，**重启后会丢失**；生产环境建议后续接入对象存储（如 Supabase Storage）

---

## 四、配置文件说明

| 文件 | 用途 |
|------|------|
| `.env` | 本地环境变量（勿提交 Git） |
| `.env.example` | 环境变量模板 |
| `render.yaml` | Render Blueprint 部署配置 |
| `Dockerfile` | Docker 部署（可选，当前 Render 使用 Python runtime） |
| `run.py` | 本地开发启动（带 hot reload） |
| `init_db.py` | 本地 / 远程一次性建表脚本 |

---

## 五、常见问题

### 服务启动失败：数据库连接错误

- 检查 `.env` 中 `DATABASE_URL` 是否正确
- 本地：确认 PostgreSQL 已启动、库 `cookbook` 已创建
- 线上：确认 Render 环境变量中 `DATABASE_URL` 密码、区域是否正确

### Render 部署成功但接口 500

1. 打开 Render → Logs 查看报错
2. 常见原因：`DATABASE_URL` 未配置或格式错误
3. 确认使用 `postgresql+psycopg://` 前缀

### 微信登录失败（线上）

- Render 环境变量中 `WECHAT_APP_ID` / `WECHAT_APP_SECRET` 必须与小程序 AppID 一致
- 小程序须使用 **体验版或正式版** 才能拿到有效 `code`（开发者工具开发版 + 本地后端除外）

### 修改线上域名

若更换 Render 服务域名，需同步修改：

1. 小程序 `config/env.profiles.ts` 中的 `PRODUCTION_HOST`
2. 微信公众平台 → 服务器域名

---

## 六、相关项目

- 小程序前端：`E:\code\菜谱小程序\大`
- 前端操作手册：`E:\code\菜谱小程序\大\docs\OPERATIONS.md`
