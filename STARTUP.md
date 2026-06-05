# 后端服务启动指南

## 环境要求

- **Python** 3.12 及以上
- **PostgreSQL**（本地安装并运行中）

---

## 首次搭建

以下步骤只需要做一次。

### 1. 安装 PostgreSQL

如果还没装，下载安装：https://www.postgresql.org/download/windows/

安装时记住设置的 **postgres 用户的密码**（建议先用 `postgres`，和配置保持一致）。

安装完成后：

1. 打开 **开始菜单 → pgAdmin 4**
2. 连接本地服务器
3. 右键点击 "Databases" → "Create" → "Database"
4. 数据库名填 `cookbook`，点击 Save

验证连接：

```powershell
# 打开 PowerShell，用 psql 测试连接
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d cookbook
# 提示输入密码，输入 postgres
# 看到 cookbook=# 表示成功，输入 \q 退出
```

### 2. 创建虚拟环境

在项目目录打开终端（PowerShell）：

```powershell
cd E:\code\minipro\cookbook-server
py -3 -m venv .venv
```

### 3. 激活虚拟环境

```powershell
# 必须先有 .venv（没有则先执行：py -3 -m venv .venv）
.\.venv\Scripts\Activate.ps1
```

如果报错 "无法加载文件...因为在此系统上禁止运行脚本"，先执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

激活成功后，终端左侧会显示 `(.venv)`。

### 4. 安装依赖

```powershell
pip install -r requirements.txt
```

### 5. 创建数据库表

方式一：用初始化脚本（推荐）

```powershell
python init_db.py
# 看到「建表完成！9 张表已成功创建」即成功
```

方式二：已有旧表时用迁移脚本更新

如果之前已经建过表（比如拉取了最新代码），旧表缺少新字段会报错。用迁移脚本补上：

```powershell
python migrate_db.py
# 看到「Done! All schema upgrades applied.」即成功
```

> 这个脚本可以安全地多次运行，不会破坏已有数据。

---

## 日常启动

以后每次开发时只需要三步：

### 第 1 步：启动 PostgreSQL

PostgreSQL 装好之后默认会作为 Windows 服务自动运行。如果没启动：

```powershell
# 以管理员身份打开 PowerShell
net start postgresql-x64-17
```

> 版本号 `17` 替换为你安装的实际版本。不确定的话去"服务"（services.msc）里找 postgres 相关的服务名。

### 第 2 步：激活虚拟环境并启动服务

```powershell
cd E:\code\minipro\cookbook-server
.venv\Scripts\Activate.ps1
```

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

看到以下输出表示启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

### 第 3 步：验证服务

新开一个终端窗口：

```powershell
# 分类接口不需要登录，直接测
curl http://localhost:8000/api/v1/categories
```

返回 JSON 数据就是正常的。也可以浏览器打开：

- API 文档（Swagger）：http://localhost:8000/docs
- 筛选项接口：http://localhost:8000/api/v1/meta/filters

---

## 快速启动命令总结

```powershell
# 对新手：每次开发复制下面两行即可
cd E:\code\minipro\cookbook-server && .venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 运行测试

```powershell
cd E:\code\minipro\cookbook-server
.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

> 测试用 SQLite 内存数据库，不需要 PostgreSQL，不会影响正式数据。

---

## 常见问题

### Q: 启动报 `ModuleNotFoundError`

说明有新的依赖没装：

```powershell
pip install -r requirements.txt
```

### Q: 启动报 `could not translate host name "localhost" to address`

PostgreSQL 没有运行，把它启动就行。

### Q: `.env` 里的微信配置

当前 `.env` 中 `WECHAT_APP_ID` 和 `WECHAT_APP_SECRET` 已填入真实值。如果暂时不需要微信登录调试，可以把这两项改为空字符串，这样任何 code 都可以直接登录（开发模式）：

```
WECHAT_APP_ID=
WECHAT_APP_SECRET=
```

### Q: 改代码后没生效

`--reload` 参数会让 uvicorn 监听文件变化自动重启。注意这只对 `.py` 文件生效，如果改了 `.env` 需要手动 Ctrl+C 退出再重启。

### Q: 端口 8000 被占用

换一个端口：

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

然后前端请求地址也要对应改成 `http://localhost:8080`。
