# 菜品小程序 API 对接文档

## 基础约定

### 根路径

```
http://localhost:8000/api/v1
```

### 统一响应格式

所有接口返回格式为：

```json
{
  "code": 0,        // 0=成功，非0=业务错误
  "message": "ok",   // 提示信息
  "data": { ... }    // 响应数据，可能为 null
}
```

### 分页响应格式

分页接口的 `data` 字段结构为：

```json
{
  "items": [ ... ],   // 数据列表
  "total": 25,        // 总条数
  "page": 1,          // 当前页码
  "pageSize": 10,     // 每页数量
  "hasMore": true     // 是否有更多数据
}
```

### 鉴权

- 需要登录的接口：前端传入 `Authorization: Bearer <token>` 请求头
- token 通过微信登录接口获取
- 部分接口（菜谱列表、详情）支持可选登录：传了 token 会返回用户的收藏/评分状态，不传也能正常调用

### 通用约定

- **category** 字段使用英文 key：`breakfast`（早餐）、`lunch`（午餐）、`dinner`（晚餐）、`dessert`（甜品）
- **difficulty** 字段使用中文：`简单`、`中等`、`困难`
- 图片上传后返回相对路径（如 `/uploads/abc.jpg`），前端拼接完整 URL 访问
- `createdAt` / `updatedAt` / `savedAt` 等时间为 ISO 8601 字符串

---

## 1. 认证模块

### 1.1 微信登录

> **需要登录：** 否

```
POST /auth/wechat-login
```

**请求体：**

```json
{
  "code": "微信wx.login()返回的code",
  "nickName": "用户填写的昵称",
  "avatarUrl": "微信头像URL（https CDN地址才传入，否则传空字符串）"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 微信登录凭证，`wx.login()` 返回 |
| nickName | string | 是 | 用户昵称，1-32字符 |
| avatarUrl | string | 否 | 头像URL，传 `""` 或不传 |

**成功响应 (200)：**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "token": "eyJhbGci...",
    "expiresIn": 2592000,
    "user": {
      "id": "uuid-string",
      "name": "用户昵称",
      "avatar": "",
      "bio": ""
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | JWT 令牌，后续请求放入 Authorization 头 |
| expiresIn | int | 过期时间（秒），默认 43200 分钟 = 30 天 |
| user.id | string | 用户唯一标识 |
| user.name | string | 昵称 |
| user.avatar | string | 头像URL |
| user.bio | string | 个人简介 |

**错误响应：**

| 状态码 | 说明 |
|--------|------|
| 400 | 昵称为空或超过32字 / 微信 code 无效 |

---

## 2. 用户模块

> **以下接口均需登录**

### 2.1 获取当前用户信息

```
GET /users/me
```

**响应：**

```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "name": "昵称",
    "avatar": "/uploads/avatar.jpg",
    "bio": "个人简介",
    "stats": {
      "uploads": 5,
      "reviews": 12,
      "suggestions": 3,
      "favorites": 20
    }
  }
}
```

### 2.2 更新用户信息

```
PATCH /users/me
```

**请求体：**

```json
{
  "name": "新昵称",
  "bio": "新简介"
}
```

> 字段均可选，传了哪个更新哪个

**响应：** 同 2.1 结构

### 2.3 上传头像

```
POST /users/me/avatar
Content-Type: multipart/form-data
```

**请求：**
- `file` — 图片文件，支持 `.jpg` / `.jpeg` / `.png` / `.webp`，最大 10MB

**响应：**

```json
{
  "code": 0,
  "data": {
    "avatarUrl": "/uploads/avatar_abc123.jpg"
  }
}
```

### 2.4 我的菜谱

```
GET /users/me/recipes?page=1&pageSize=10
```

**响应：** `data` 为分页格式，`items` 结构同 [菜谱列表项](#菜谱列表项格式)

### 2.5 我的评价

```
GET /users/me/reviews?page=1&pageSize=10
```

**响应 `items` 中每条：**

```json
{
  "recipeId": "dish-uuid",
  "rating": 4,
  "date": "2026-06-04T12:00:00",
  "recipe": {
    "id": "dish-uuid",
    "title": "番茄炒蛋",
    "coverImage": "/uploads/xxx.jpg"
  }
}
```

### 2.6 我的收藏

```
GET /users/me/favorites?page=1&pageSize=10
```

**响应：** `data` 为分页格式，`items` 结构同 [菜谱列表项](#菜谱列表项格式)，`isFavorite` 均为 `true`

---

## 3. 分类模块

### 3.1 分类列表

> **需要登录：** 否

```
GET /categories
```

**响应：**

```json
{
  "code": 0,
  "data": [
    { "id": 1, "name": "早餐", "key": "breakfast", "icon": "sunrise", "sort_order": 1 },
    { "id": 2, "name": "午餐", "key": "lunch", "icon": "sun", "sort_order": 2 },
    { "id": 3, "name": "晚餐", "key": "dinner", "icon": "moon", "sort_order": 3 },
    { "id": 4, "name": "甜品", "key": "dessert", "icon": "cake", "sort_order": 4 }
  ]
}
```

---

## 4. 菜谱模块

### 菜谱列表项格式

以下接口中菜谱列表共用此结构：

```json
{
  "id": "uuid",
  "title": "番茄炒蛋",
  "coverImage": "/uploads/xxx.jpg",
  "author": {
    "id": "user-uuid",
    "name": "作者昵称",
    "avatar": ""
  },
  "rating": 4.5,
  "ratingCount": 12,
  "createdAt": "2026-06-04T10:00:00",
  "duration": 15,
  "difficulty": "简单",
  "category": "lunch",
  "cuisine": "川菜",
  "tags": ["快手菜", "减脂"],
  "servings": 2,
  "isFavorite": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 菜谱ID |
| title | string | 标题 |
| coverImage | string\|null | 封面图URL |
| author | object\|null | 作者信息 |
| rating | float | 平均评分 (0.0-5.0) |
| ratingCount | int | 评分人数 |
| createdAt | string | 创建时间 ISO 8601 |
| duration | int\|null | 烹饪时长（分钟） |
| difficulty | string\|null | 难度：`简单` `中等` `困难` |
| category | string\|null | 分类 key：`breakfast` `lunch` `dinner` `dessert` |
| cuisine | string\|null | 菜系：`川菜` `粤菜` `鲁菜` `苏菜` `其他` |
| tags | string[] | 标签列表 |
| servings | int\|null | 份量 |
| isFavorite | bool\|null | 当前用户是否收藏（未登录为 null） |

### 4.1 菜谱列表

> **需要登录：** 否（可选登录以获取收藏状态）

```
GET /recipes?page=1&pageSize=10&q=番茄&category=lunch&cuisine=川菜&tag=快手菜&sort=createdAt
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| pageSize | int | 10 | 每页数量（最大 50） |
| q | string | — | 关键词搜索（匹配标题 / 食材 / 标签） |
| category | string | — | 分类过滤，传 `all` 表示全部 |
| cuisine | string | — | 菜系过滤 |
| tag | string | — | 标签过滤 |
| sort | string | createdAt | 排序：`createdAt`（最新）/ `rating`（评分最高） |

**响应：** `data` 为分页格式，`items` 为菜谱列表项数组

### 4.2 评分榜

> **需要登录：** 否（可选登录）

```
GET /recipes/ranked?limit=10
```

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 10 | 返回数量（最大 50） |

**响应：**

```json
{
  "code": 0,
  "data": [ /* 菜谱列表项数组，按评分降序 */ ]
}
```

### 4.3 菜谱详情

> **需要登录：** 否（登录后会返回当前用户的收藏、评分、建议状态）

```
GET /recipes/{recipe_id}
```

**响应：**

```json
{
  "code": 0,
  "data": {
    "id": "uuid",
    "title": "番茄炒蛋",
    "coverImage": "/uploads/xxx.jpg",
    "author": {
      "id": "user-uuid",
      "name": "作者昵称",
      "avatar": ""
    },
    "rating": 4.5,
    "ratingCount": 12,
    "createdAt": "2026-06-04T10:00:00",
    "duration": 15,
    "difficulty": "简单",
    "category": "lunch",
    "cuisine": "川菜",
    "tags": ["快手菜", "减脂"],
    "servings": 2,
    "ingredients": [
      { "name": "番茄", "amount": "2", "unit": "个" },
      { "name": "鸡蛋", "amount": "3", "unit": "个" }
    ],
    "steps": [
      { "id": 1, "desc": "番茄切块备用", "image": null },
      { "id": 2, "desc": "鸡蛋打散炒熟盛出", "image": null }
    ],
    "tips": "鸡蛋不要炒太老",
    "crowd": "老少皆宜",
    "reviews": [
      {
        "id": "review-uuid",
        "userId": "user-uuid",
        "userName": "评分用户",
        "userAvatar": "",
        "rating": 5,
        "date": "2026-06-04T11:00:00"
      }
    ],
    "suggestions": [
      {
        "id": "sug-uuid",
        "userId": "user-uuid",
        "userName": "建议用户",
        "userAvatar": "",
        "content": "加点糖更提鲜",
        "date": "2026-06-04T11:30:00"
      }
    ],
    "isFavorite": false,
    "myReview": null,
    "mySuggestion": null
  }
}
```

**需要登录才有的字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| isFavorite | bool | 是否已收藏 |
| myReview | object\|null | 我的评分 `{"id": "rating_id", "rating": 4}` |
| mySuggestion | object\|null | 我的建议 `{"id": "sug_id", "content": "..."}` |

### 4.4 发布菜谱

> **需要登录**

```
POST /recipes
```

**请求体：**

```json
{
  "title": "番茄炒蛋",
  "coverImage": null,
  "duration": 15,
  "difficulty": "简单",
  "category": "lunch",
  "cuisine": "川菜",
  "tags": ["快手菜"],
  "servings": 2,
  "ingredients": [
    { "name": "番茄", "amount": "2", "unit": "个" },
    { "name": "鸡蛋", "amount": "3", "unit": "个" }
  ],
  "steps": [
    { "id": null, "desc": "番茄切块备用", "image": null },
    { "id": null, "desc": "鸡蛋炒熟盛出", "image": null }
  ],
  "tips": "鸡蛋不要炒太老",
  "crowd": "老少皆宜"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 菜谱名称，最大 128 字符 |
| coverImage | string\|null | 否 | 封面图 URL（先调上传接口拿到URL再传入） |
| duration | int | 否 | 烹饪时长（分钟） |
| difficulty | string | 否 | `简单` / `中等` / `困难` |
| category | string | 是 | `breakfast` / `lunch` / `dinner` / `dessert` |
| cuisine | string | 否 | `川菜` / `粤菜` / `鲁菜` / `苏菜` / `其他` |
| tags | string[] | 否 | 标签 |
| servings | int | 否 | 份量 |
| ingredients | array | 是 | 至少一项 name 不为空 |
| ingredients[].name | string | 是 | 食材名称 |
| ingredients[].amount | string | 否 | 用量 |
| ingredients[].unit | string | 否 | 单位 |
| steps | array | 是 | 至少一项 desc 不为空 |
| steps[].desc | string | 是 | 步骤描述 |
| steps[].image | string\|null | 否 | 步骤配图URL |
| tips | string | 否 | 小贴士 |
| crowd | string | 否 | 适合人群 |

**响应：** `data` 为 [菜谱详情](#43-菜谱详情) 结构

**错误：**

| 状态码 | 说明 |
|--------|------|
| 400 | 名称/食材/步骤为空 |
| 401 | 未登录 |

### 4.5 编辑菜谱

> **需要登录（仅作者本人可编辑）**

```
PATCH /recipes/{recipe_id}
```

**请求体：** 与发布菜谱相同，但所有字段均可选，只传要修改的字段

**响应：** `data` 为 [菜谱详情](#43-菜谱详情) 结构

**错误：**

| 状态码 | 说明 |
|--------|------|
| 403 | 不是自己的菜谱 |
| 404 | 菜谱不存在 |

### 4.6 删除菜谱

> **需要登录（仅作者本人可删除）**

```
DELETE /recipes/{recipe_id}
```

**响应：**

```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

---

## 5. 评分模块

### 5.1 提交/修改评分

> **需要登录**

每个用户对每个菜谱最多一条评分，重复提交会覆盖之前的评分。

```
POST /recipes/{recipe_id}/reviews
```

**请求体：**

```json
{
  "rating": 4
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| rating | int | 评分 1-5 |

**响应：**

```json
{
  "code": 0,
  "data": {
    "review": {
      "id": "review-uuid",
      "userId": "user-uuid",
      "userName": "昵称",
      "userAvatar": "",
      "rating": 4,
      "date": "2026-06-04T12:00:00"
    },
    "recipeRating": 4.2,
    "ratingCount": 13
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| review | object | 本次提交的评分记录 |
| recipeRating | float | 菜谱最新平均分 |
| ratingCount | int | 菜谱累计评分人数 |

### 5.2 删除我的评分

> **需要登录**

```
DELETE /recipes/{recipe_id}/reviews/me
```

**响应：**

```json
{
  "code": 0,
  "data": {
    "recipeRating": 4.0,
    "ratingCount": 12
  }
}
```

---

## 6. 建议模块

### 6.1 提交/修改建议

> **需要登录**

每个用户对每个菜谱最多一条建议，重复提交会覆盖。

```
POST /recipes/{recipe_id}/suggestions
```

**请求体：**

```json
{
  "content": "加点糖更提鲜"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| content | string | 建议内容，1-500 字 |

**响应：**

```json
{
  "code": 0,
  "data": {
    "id": "sug-uuid",
    "userId": "user-uuid",
    "userName": "昵称",
    "userAvatar": "",
    "content": "加点糖更提鲜",
    "date": "2026-06-04T12:00:00"
  }
}
```

### 6.2 删除我的建议

> **需要登录**

```
DELETE /recipes/{recipe_id}/suggestions/me
```

**响应：**

```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

---

## 7. 收藏模块

### 7.1 添加收藏

> **需要登录**

重复调用不会报错（幂等）。

```
POST /recipes/{recipe_id}/favorite
```

**响应：**

```json
{
  "code": 0,
  "data": { "favorited": true }
}
```

### 7.2 取消收藏

> **需要登录**

```
DELETE /recipes/{recipe_id}/favorite
```

**响应：**

```json
{
  "code": 0,
  "data": { "favorited": false }
}
```

---

## 8. 建议模块（菜谱改进建议）

### 8.1 提交/修改建议

> **需要登录**

```
POST /recipes/{recipe_id}/suggestions
```

**请求体：**

```json
{
  "content": "建议小火慢炖口感更好"
}
```

### 8.2 删除我的建议

> **需要登录**

```
DELETE /recipes/{recipe_id}/suggestions/me
```

---

## 9. 草稿模块

### 9.1 我的草稿列表

> **需要登录**

```
GET /drafts
```

**响应：**

```json
{
  "code": 0,
  "data": [
    {
      "id": "draft-uuid",
      "title": "未完成的菜谱",
      "step": 3,
      "coverImage": "",
      "duration": 30,
      "difficulty": "中等",
      "servings": 3,
      "ingredients": [
        { "name": "鸡腿", "amount": "2", "unit": "个" }
      ],
      "steps": [
        { "id": 1, "desc": "第一步", "image": null }
      ],
      "category": "dinner",
      "cuisine": "粤菜",
      "tags": [],
      "crowd": "",
      "tips": "",
      "savedAt": "2026-06-04T10:30:00"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 草稿ID |
| title | string | 标题（可空） |
| step | int | 当前填写到的步骤编号 |
| coverImage | string | 封面图 |
| duration | int\|null | 烹饪时长 |
| difficulty | string | 难度 |
| servings | int\|null | 份量 |
| ingredients | array | 食材列表 |
| steps | array | 步骤列表 |
| category | string | 分类 key |
| cuisine | string | 菜系 |
| tags | string[] | 标签 |
| crowd | string | 适合人群 |
| tips | string | 小贴士 |
| savedAt | string | 最后保存时间 |

### 9.2 保存草稿

> **需要登录**

如果 `id` 对应的草稿已存在则更新，否则新建。

```
PUT /drafts/{draft_id}
```

> `{draft_id}` 可以是前端生成的临时ID（首次保存时），也可以是已有草稿ID（更新时）

**请求体：**

```json
{
  "id": "draft-uuid",
  "title": "我的草稿",
  "step": 2,
  "coverImage": "/uploads/xxx.jpg",
  "duration": 30,
  "difficulty": "中等",
  "servings": 3,
  "ingredients": [
    { "name": "鸡腿", "amount": "2", "unit": "个" }
  ],
  "steps": [
    { "id": 1, "desc": "焯水", "image": null },
    { "id": 2, "desc": "红烧", "image": null }
  ],
  "category": "dinner",
  "cuisine": "粤菜",
  "tags": ["精选"],
  "crowd": "",
  "tips": ""
}
```

> 所有字段都可以为空/空字符串，适合分步保存

**响应：** `data` 为草稿结构（同 9.1 单条）

### 9.3 删除草稿

> **需要登录**

```
DELETE /drafts/{draft_id}
```

**响应：** `{"code": 0, "message": "删除成功", "data": null}`

### 9.4 发布草稿

> **需要登录**

将草稿转为正式菜谱并发布。

```
POST /drafts/{draft_id}/publish
```

**响应：** `data` 为 [菜谱详情](#43-菜谱详情) 结构（新创建的菜谱）

**错误：**

| 状态码 | 说明 |
|--------|------|
| 404 | 草稿不存在 |

---

## 10. 文件上传

### 10.1 上传图片

> **需要登录**

```
POST /upload/image
Content-Type: multipart/form-data
```

**请求：**
- `file` — 图片文件，支持 `.jpg` / `.jpeg` / `.png` / `.webp`，最大 10MB

**响应：**

```json
{
  "code": 0,
  "data": {
    "url": "/uploads/abc123.jpg",
    "filename": "abc123.jpg"
  }
}
```

> `url` 为相对路径，前端拼接服务器地址（如 `http://localhost:8000/uploads/abc123.jpg`）访问

**错误：**

| 状态码 | 说明 |
|--------|------|
| 400 | 不支持的图片格式 / 图片超过 10MB |
| 401 | 未登录 |

---

## 11. 元数据

### 11.1 筛选项

> **需要登录：** 否

```
GET /meta/filters
```

**响应：**

```json
{
  "code": 0,
  "data": {
    "categories": [
      { "key": "all", "label": "全部" },
      { "key": "breakfast", "label": "早餐" },
      { "key": "lunch", "label": "午餐" },
      { "key": "dinner", "label": "晚餐" },
      { "key": "dessert", "label": "甜品" }
    ],
    "cuisines": ["川菜", "粤菜", "鲁菜", "苏菜", "其他"],
    "tags": ["减脂", "素食", "精选", "快手菜"],
    "difficulties": ["简单", "中等", "困难"]
  }
}
```

> 筛选项可以直接用于前端下拉/标签选择器，`categories[0]` 的 `"all"` 代表不限制分类。

---

## 接口汇总表

| 方法 | 路径 | 登录 | 说明 |
|------|------|------|------|
| POST | `/auth/wechat-login` | — | 微信登录 |
| GET | `/users/me` | 是 | 当前用户信息+统计 |
| PATCH | `/users/me` | 是 | 更新用户信息 |
| POST | `/users/me/avatar` | 是 | 上传头像 |
| GET | `/users/me/recipes` | 是 | 我的菜谱 |
| GET | `/users/me/reviews` | 是 | 我的评价 |
| GET | `/users/me/favorites` | 是 | 我的收藏 |
| GET | `/categories` | — | 分类列表 |
| GET | `/recipes` | 可选 | 菜谱列表 |
| GET | `/recipes/ranked` | 可选 | 评分榜 |
| GET | `/recipes/{id}` | 可选 | 菜谱详情 |
| POST | `/recipes` | 是 | 发布菜谱 |
| PATCH | `/recipes/{id}` | 是 | 编辑菜谱 |
| DELETE | `/recipes/{id}` | 是 | 删除菜谱 |
| POST | `/recipes/{id}/reviews` | 是 | 提交评分 |
| DELETE | `/recipes/{id}/reviews/me` | 是 | 删除我的评分 |
| POST | `/recipes/{id}/suggestions` | 是 | 提交建议 |
| DELETE | `/recipes/{id}/suggestions/me` | 是 | 删除我的建议 |
| POST | `/recipes/{id}/favorite` | 是 | 添加收藏 |
| DELETE | `/recipes/{id}/favorite` | 是 | 取消收藏 |
| GET | `/drafts` | 是 | 草稿列表 |
| PUT | `/drafts/{id}` | 是 | 保存草稿 |
| DELETE | `/drafts/{id}` | 是 | 删除草稿 |
| POST | `/drafts/{id}/publish` | 是 | 发布草稿 |
| POST | `/upload/image` | 是 | 上传图片 |
| GET | `/meta/filters` | — | 筛选项元数据 |

---

## 前端开发流程建议

### 登录流程

```
1. 调用 wx.login() 获取 code
2. wx.getUserProfile() 获取用户昵称和头像（或让用户填写昵称）
3. POST /auth/wechat-login 传入 code + nickName + avatarUrl
4. 将返回的 token 存储到本地（wx.setStorageSync）
5. 后续所有请求在 Authorization 头带上 "Bearer " + token
```

### 发布菜谱流程

```
1. 用户填写菜谱表单
2. 有图片时先调 POST /upload/image 上传，拿到 url 填入表单
3. 填完后 POST /recipes 提交完整数据
```

### 草稿保存流程

```
1. 前端生成临时ID（如 uuid）
2. 用户填写过的分步表单时调用 PUT /drafts/{id} 保存每一步
3. 用户可随时返回草稿列表 GET /drafts 继续编辑
4. 编辑完成后 POST /drafts/{id}/publish 发布
```

### 菜谱列表页加载

```
1. GET /meta/filters 获取筛选项（分类、菜系、标签）
2. GET /recipes?page=1&pageSize=10 获取首页数据
3. 用户选择筛选项后重新请求（带 category / cuisine / tag 参数）
4. 滚动到底部时，page+1 加载更多
```
