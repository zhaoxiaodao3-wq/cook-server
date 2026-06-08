# 数据库同步说明

本地 PostgreSQL 与线上 Supabase 之间的**表结构**和**数据**同步工具。

---

## 一、它是干什么的？

| 能力 | 命令 | 说明 |
|------|------|------|
| 查看对比 | `status` | 看本地和线上每张表有多少行 |
| 表结构同步 | `schema push` | 把本地 Alembic 迁移应用到线上 |
| 数据推到线上 | `data push` | 本地数据 → 覆盖线上 |
| 数据拉回本地 | `data pull` | 线上数据 → 覆盖本地 |

**不会自动同步。** 只有你手动执行命令时才会同步。

---

## 二、首次配置（只需做一次）

### 1. 打开项目目录

```powershell
cd E:\code\minipro\cookbook-server
```

### 2. 编辑 `.env` 文件

在项目根目录的 `.env` 里增加以下三行（可参考 `.env.example`）：

```env
# 同步总开关：平时 false，要同步时改 true
DB_SYNC_ENABLED=false

# 本地库（留空即可，会自动用 DATABASE_URL）
LOCAL_DATABASE_URL=

# 远程 Supabase 连接（见下方如何获取）
REMOTE_DATABASE_URL=postgresql+psycopg://postgres:你的密码@db.uqiwkxzjlwlcrvwktcfa.supabase.co:5432/postgres
```

### 3. 获取 REMOTE_DATABASE_URL

1. 打开 https://supabase.com/dashboard/project/uqiwkxzjlwlcrvwktcfa  
2. 点击右上角 **Connect**  
3. 选择 **Direct connection**（端口 **5432**，不是 6543）  
4. 复制连接串，格式类似：

   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.uqiwkxzjlwlcrvwktcfa.supabase.co:5432/postgres
   ```

5. 把 `postgresql://` 改成 `postgresql+psycopg://`，`[YOUR-PASSWORD]` 换成真实密码  
6. 粘贴到 `.env` 的 `REMOTE_DATABASE_URL=`

> **注意**：Render 线上服务用的是 **Transaction pooler（6543）**，同步工具要用 **Direct（5432）**，这是两个不同的连接串。

### 4. 验证配置

```powershell
py scripts/sync_db.py status
```

成功时会显示类似：

```text
同步开关: 关闭
本地: postgresql://postgres:****@localhost:5432/cookbook
远程: postgresql://postgres:****@db.uqiwkxzjlwlcrvwktcfa.supabase.co:5432/postgres

表名                   本地       远程
------------------------------------
users                     3        0
categories                8        8
dishes                   12        0
...
```

如果报错「未配置 REMOTE_DATABASE_URL」，说明 `.env` 里还没填远程连接串。

---

## 三、命令详解

所有命令都在项目根目录执行：

```powershell
cd E:\code\minipro\cookbook-server
```

也可以用快捷方式（效果相同）：

```powershell
sync_db.bat status
sync_db.bat schema push
sync_db.bat data push --yes
sync_db.bat data pull --yes
```

---

### 命令 1：查看对比（随时可用）

```powershell
py scripts/sync_db.py status
```

| 项目 | 说明 |
|------|------|
| 是否需要开开关 | **不需要**，`DB_SYNC_ENABLED=false` 也能用 |
| 会改数据吗 | **不会**，只读对比 |
| 什么时候用 | 同步前看看两边差多少；同步后确认是否一致 |

---

### 命令 2：表结构同步（本地 → 线上）

```powershell
# 1. 先在 .env 里打开开关
DB_SYNC_ENABLED=true

# 2. 执行
py scripts/sync_db.py schema push
```

| 项目 | 说明 |
|------|------|
| 作用 | 把 Alembic 迁移脚本应用到**线上** Supabase |
| 适用场景 | 本地加了新字段、新表，要同步到线上 |
| 会改数据吗 | 只改表结构，**不删数据**（但 ALTER 大表可能较慢） |
| 前提 | 本地已写好迁移并在本地跑通 `py -m alembic upgrade head` |

**完整流程示例（改了表结构）：**

```powershell
# ① 本地生成迁移
py -m alembic revision --autogenerate -m "add xxx column"

# ② 本地先应用并测试
py -m alembic upgrade head
py run.py   # 确认本地服务正常

# ③ .env 设 DB_SYNC_ENABLED=true
# ④ 推到线上
py scripts/sync_db.py schema push

# ⑤ 同步完改回 DB_SYNC_ENABLED=false
```

---

### 命令 3：数据推到线上（本地 → 线上）

```powershell
# 1. .env 里 DB_SYNC_ENABLED=true
# 2. 执行（必须加 --yes）
py scripts/sync_db.py data push --yes
```

| 项目 | 说明 |
|------|------|
| 作用 | 把**本地** 9 张业务表的数据复制到**线上** |
| 适用场景 | 本地录入了测试数据，想放到体验版给用户看 |
| ⚠️ 危险 | **会清空并覆盖线上全部业务表数据** |
| 必须参数 | `--yes`（不加则拒绝执行） |

涉及的表：`users`、`categories`、`dishes`、`ingredients`、`steps`、`ratings`、`suggestions`、`favorites`、`drafts`

---

### 命令 4：数据拉回本地（线上 → 本地）

```powershell
# 1. .env 里 DB_SYNC_ENABLED=true
# 2. 执行（必须加 --yes）
py scripts/sync_db.py data pull --yes
```

| 项目 | 说明 |
|------|------|
| 作用 | 把**线上**数据复制到**本地** |
| 适用场景 | 线上有真实用户数据，想在本地复现 bug |
| ⚠️ 危险 | **会清空并覆盖本地全部业务表数据** |
| 必须参数 | `--yes` |

---

## 四、常见场景速查

### 场景 A：我只改了代码，没动数据库

```powershell
git push origin main
```

**不需要**跑 sync_db，Render 会自动部署应用。

---

### 场景 B：本地加了数据库字段 / 新表

```powershell
py -m alembic revision --autogenerate -m "描述改动"
py -m alembic upgrade head
# .env → DB_SYNC_ENABLED=true
py scripts/sync_db.py schema push
# .env → DB_SYNC_ENABLED=false
```

---

### 场景 C：本地测试数据想同步到体验版

```powershell
py scripts/sync_db.py status          # 先看看两边行数
# .env → DB_SYNC_ENABLED=true
py scripts/sync_db.py data push --yes
py scripts/sync_db.py status          # 确认一致
# .env → DB_SYNC_ENABLED=false
```

---

### 场景 D：线上数据拉回本地调试

```powershell
py scripts/sync_db.py status
# .env → DB_SYNC_ENABLED=true
py scripts/sync_db.py data pull --yes
py scripts/sync_db.py status
# .env → DB_SYNC_ENABLED=false
py run.py   # 本地后端现在用的是线上数据
```

---

## 五、安全开关说明

```
DB_SYNC_ENABLED=false   ← 默认，禁止 schema push / data push / data pull
DB_SYNC_ENABLED=true    ← 允许执行同步（用完建议改回 false）
```

| 命令 | false 时能跑吗 |
|------|---------------|
| `status` | ✅ 可以 |
| `schema push` | ❌ 拒绝 |
| `data push` | ❌ 拒绝 |
| `data pull` | ❌ 拒绝 |

---

## 六、常见问题

### 报错：未配置 REMOTE_DATABASE_URL

`.env` 里没有填 `REMOTE_DATABASE_URL`，按「第二节」获取 Supabase Direct 连接串。

### 报错：数据库同步已关闭

把 `.env` 里 `DB_SYNC_ENABLED` 改成 `true`，执行完改回 `false`。

### 报错：请加 --yes 确认

数据同步必须加 `--yes`：

```powershell
py scripts/sync_db.py data push --yes
py scripts/sync_db.py data pull --yes
```

### 连接超时 / 连接失败

- 确认 Supabase 密码正确  
- 确认用的是 **Direct connection（5432）**，不是 pooler（6543）  
- 检查网络是否能访问 `db.uqiwkxzjlwlcrvwktcfa.supabase.co`

### schema push 失败

1. 先在本地跑通：`py -m alembic upgrade head`  
2. 看终端报错信息  
3. 若远程已有部分迁移，可在 Supabase SQL Editor 查看 `alembic_version` 表

### 日常开发用哪个库？

| 环境 | 数据库 |
|------|--------|
| 本地 `py run.py` | 本地 PostgreSQL（`DATABASE_URL`） |
| Render 线上服务 | Supabase（Render 环境变量里的 `DATABASE_URL`） |
| sync_db 工具 | 通过 `LOCAL_*` / `REMOTE_*` 在两者之间同步 |

---

## 七、命令速查表

```powershell
cd E:\code\minipro\cookbook-server

# 对比行数（随时可用，不用开开关）
py scripts/sync_db.py status

# 表结构：本地 → 线上（需 DB_SYNC_ENABLED=true）
py scripts/sync_db.py schema push

# 数据：本地 → 线上，覆盖远程（需开关 + --yes）
py scripts/sync_db.py data push --yes

# 数据：线上 → 本地，覆盖本地（需开关 + --yes）
py scripts/sync_db.py data pull --yes
```

---

## 相关文档

- [后端操作手册（部署、启动）](OPERATIONS.md)
- 环境变量模板：项目根目录 `.env.example`
