# Agent File Cloud 技能使用指南

> 智能文件管理 - 语义搜索 + 七牛云存储 + 智能存储策略

---

## 🚀 快速开始

### 1. 配置 API Key

编辑 `config/config.json`，添加阿里云 API Key：

```json
{
  "api": {
    "dashscope_api_key": "sk-xxx"
  }
}
```

### 2. 添加文件

```bash
cd ~/.openclaw/skills/agent-file-cloud

# 添加文件到本地数据库
python3 agent_file_cloud.py add inbox/file.md \
  --tags "标签 1，标签 2" \
  --desc "文件描述"
```

### 3. 语义搜索

```bash
# 搜索文件（理解语义）
python3 agent_file_cloud.py search "关键词"
```

### 4. 上传到七牛云

```bash
# 上传文件
python3 qiniu_uploader.py upload inbox/file.md \
  --tags "重要，分享" \
  --desc "文件描述"
```

---

## 📁 文件结构

```
agent-file-cloud/
├── SKILL.md                  技能说明
├── USAGE.md                  使用指南（本文件）
├── agent_file_cloud.py       主程序（语义搜索）
├── qiniu_uploader.py         七牛云上传
├── storage_manager.py        存储管理
├── embedding_api.py          Embedding API
├── install.sh                安装脚本
├── config/
│   ├── config.json           统一配置
│   └── config.template.json  配置模板
└── workspace/
    ├── inbox/                待处理
    ├── archive/              已归档
    └── temp/                 临时
```

---

## 🔧 命令参考

### 主程序 (agent_file_cloud.py)

| 命令 | 说明 | 示例 |
|------|------|------|
| `add` | 添加文件 | `add inbox/file.md --tags "标签" --desc "描述"` |
| `search` | 语义搜索 | `search "关键词"` |
| `list` | 列出文件 | `list --limit 20` |
| `stats` | 统计信息 | `stats` |
| `recommend` | 推荐相似 | `recommend <file_id>` |

### 七牛云上传 (qiniu_uploader.py)

| 命令 | 说明 | 示例 |
|------|------|------|
| `upload` | 上传文件 | `upload inbox/file.md --tags "标签"` |
| `search` | 搜索云端 | `search --tag "标签"` |
| `list` | 列出文件 | `list` |
| `stats` | 统计信息 | `stats` |

### 存储管理 (storage_manager.py)

| 命令 | 说明 | 示例 |
|------|------|------|
| `stats` | 存储统计 | `stats` |
| `analyze` | 分析文件 | `analyze` |
| `actions` | 操作建议 | `actions` |
| `file` | 分析单个 | `file <file_id>` |

---

## 🔥☁️ 存储策略

| 类型 | 标识 | 扩展名 | 存储位置 |
|------|------|--------|---------|
| **热文件** | 🔥 | .py, .sh, .js | 💻 本地 |
| **温文件** | ⚡ | .json, .xml, .log | 💻 本地 |
| **冷文件** | ☁️ | .md, .pdf, .png | ☁️ 云端 |

---

## 📖 配置说明

### config.json

```json
{
  "api": {
    "dashscope_api_key": "sk-xxx",
    "embedding_model": "text-embedding-v4",
    "dimension": 1024
  },
  "qiniu": {
    "access_key": "xxx",
    "secret_key": "xxx",
    "bucket": "xxx",
    "domain": "https://xxx.com"
  },
  "storage_policy": {
    "hot_extensions": [".py", ".sh", ".js"],
    "cold_extensions": [".md", ".pdf", ".png"],
    "warm_extensions": [".json", ".xml", ".log"]
  }
}
```

---

## ⚠️ 注意事项

### 安全

- **不要**将 config.json 提交到 Git
- **不要**公开分享 API Key
- 使用 `chmod 600 config/config.json` 保护配置

### 依赖

```bash
pip3 install --break-system-packages \
  dashscope faiss-cpu numpy networkx openai qiniu
```

---

## 📚 相关文档

- **SKILL.md** - 技能详细说明
- **config/CONFIG_GUIDE.md** - 配置指南

---

**Agent File Cloud - 让文件管理更智能！** 🚀
