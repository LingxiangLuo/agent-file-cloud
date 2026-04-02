# 统一配置说明

> 所有配置在一个文件中管理

---

## 📁 配置文件位置

```
~/.openclaw/skills/agent-file-cloud/config/config.json
```

---

## 📋 配置结构

```json
{
  "version": "3.0",
  
  "api": {
    "dashscope_api_key": "sk-xxx",
    "embedding_model": "text-embedding-v4",
    "dimension": 1024
  },
  
  "qiniu": {
    "access_key": "your_access_key",
    "secret_key": "your_secret_key",
    "bucket": "your_bucket",
    "domain": "https://your-domain.com",
    "default_expiry_days": 7
  },
  
  "directories": {
    "inbox": "workspace/inbox",
    "archive": "workspace/archive",
    "temp": "workspace/temp"
  },
  
  "storage_policy": {
    "hot_extensions": [".py", ".sh", ".js", ".yaml", ".yml"],
    "cold_extensions": [".md", ".pdf", ".png", ".jpg", ".mp4"],
    "warm_extensions": [".json", ".xml", ".log"]
  },
  
  "features": {
    "enable_semantic_search": true,
    "enable_auto_upload": false,
    "enable_duplicate_check": true,
    "enable_version_control": true
  }
}
```

---

## 🔧 配置项详解

### 1. API 配置（阿里云 Embedding）

```json
"api": {
  "dashscope_api_key": "sk-xxx",
  "embedding_model": "text-embedding-v4",
  "dimension": 1024
}
```

| 字段 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `dashscope_api_key` | 阿里云 API Key | - | ✅ 语义搜索必填 |
| `embedding_model` | Embedding 模型 | text-embedding-v4 | - |
| `dimension` | 向量维度 | 1024 | - |

**获取 API Key：**
1. 访问 https://dashscope.console.aliyun.com/
2. 登录阿里云账号
3. 创建 API Key
4. 复制到配置中

---

### 2. 七牛云配置

```json
"qiniu": {
  "access_key": "your_access_key",
  "secret_key": "your_secret_key",
  "bucket": "your_bucket",
  "domain": "https://your-domain.com",
  "default_expiry_days": 7
}
```

| 字段 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `access_key` | 七牛云访问密钥 | - | ✅ 云上传必填 |
| `secret_key` | 七牛云密钥 | - | ✅ 云上传必填 |
| `bucket` | 存储空间名称 | - | ✅ 云上传必填 |
| `domain` | 七牛云域名 | - | ✅ 云上传必填 |
| `default_expiry_days` | 默认有效期（天） | 7 | - |

**获取七牛云凭证：**
1. 访问 https://portal.qiniu.com/
2. 登录七牛云账号
3. 创建存储空间（Bucket）
4. 获取密钥和域名
5. 复制到配置中

---

### 3. 目录配置

```json
"directories": {
  "inbox": "workspace/inbox",
  "archive": "workspace/archive",
  "temp": "workspace/temp"
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `inbox` | 待处理文件目录 | workspace/inbox |
| `archive` | 已归档文件目录 | workspace/archive |
| `temp` | 临时文件目录 | workspace/temp |

**说明：**
- 路径相对于技能根目录
- 或使用绝对路径

---

### 4. 存储策略配置

```json
"storage_policy": {
  "hot_extensions": [".py", ".sh", ".js", ".yaml", ".yml"],
  "cold_extensions": [".md", ".pdf", ".png", ".jpg", ".mp4"],
  "warm_extensions": [".json", ".xml", ".log"]
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `hot_extensions` | 热文件扩展名（本地执行） | .py, .sh, .js |
| `cold_extensions` | 冷文件扩展名（云端传播） | .md, .pdf, .png |
| `warm_extensions` | 温文件扩展名（本地存储） | .json, .xml, .log |

**存储策略：**
- 🔥 **热文件**：脚本/代码，本地存储 + 云端备份
- ☁️ **冷文件**：文档/媒体，云端存储（便于分享）
- ⚡ **温文件**：数据/日志，本地存储

---

### 5. 功能开关

```json
"features": {
  "enable_semantic_search": true,
  "enable_auto_upload": false,
  "enable_duplicate_check": true,
  "enable_version_control": true
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `enable_semantic_search` | 启用语义搜索 | true |
| `enable_auto_upload` | 自动上传云端 | false |
| `enable_duplicate_check` | 文件去重检查 | true |
| `enable_version_control` | 版本控制 | true |

---

## 🔐 环境变量（可选）

环境变量优先级 **高于** 配置文件：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 阿里云 API Key | `export DASHSCOPE_API_KEY="sk-xxx"` |
| `AGENT_FILE_CLOUD_WORKSPACE` | 工作目录 | `export AGENT_FILE_CLOUD_WORKSPACE="/path/to/workspace"` |

---

## 📝 配置示例

### 最小配置（仅语义搜索）

```json
{
  "api": {
    "dashscope_api_key": "sk-xxx"
  }
}
```

### 完整配置（语义搜索 + 七牛云）

```json
{
  "version": "3.0",
  
  "api": {
    "dashscope_api_key": "sk-xxx",
    "embedding_model": "text-embedding-v4",
    "dimension": 1024
  },
  
  "qiniu": {
    "access_key": "your_access_key",
    "secret_key": "your_secret_key",
    "bucket": "your_bucket",
    "domain": "https://your-domain.com",
    "default_expiry_days": 7
  },
  
  "directories": {
    "inbox": "workspace/inbox",
    "archive": "workspace/archive",
    "temp": "workspace/temp"
  },
  
  "storage_policy": {
    "hot_extensions": [".py", ".sh", ".js"],
    "cold_extensions": [".md", ".pdf", ".png"],
    "warm_extensions": [".json", ".xml", ".log"]
  },
  
  "features": {
    "enable_semantic_search": true,
    "enable_auto_upload": false,
    "enable_duplicate_check": true,
    "enable_version_control": true
  }
}
```

---

## ⚠️ 注意事项

### 安全性

- **不要**将配置文件提交到 Git
- **不要**公开分享 API Key
- 使用 `.gitignore` 忽略配置文件

```bash
# .gitignore
config/config.json
```

### 配置验证

```bash
# 测试配置是否生效
python3 agent_file_cloud.py stats

# 如果 API Key 无效会提示错误
```

### 配置更新

修改配置后无需重启，下次执行时自动加载新配置。

---

## 🔧 配置管理命令

```bash
# 创建配置模板
cp config/config.template.json config/config.json

# 编辑配置
vim config/config.json

# 验证配置
python3 -c "import json; json.load(open('config/config.json'))"
```

---

**统一配置管理 - 简单、清晰、高效！** 🎉
