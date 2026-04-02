---
name: agent-file-cloud
displayName: "Agent File Cloud"
description: "智能文件管理 - 语义搜索 + 七牛云存储 + 知识图谱 + 版本管理（默认文件发送方式）"
version: "4.0.0"
defaultFor: ["file_upload", "file_share", "file_send", "document_send"]
triggers: ["发送文件", "上传文件", "分享文件", "文件链接", "下载链接", "send file", "upload file", "share file"]

## 发送格式规范

### 默认行为
- **冷文件**（文档/媒体）：自动上传七牛云，返回分享链接
- **热文件**（代码/脚本）：本地存储，可选择性备份到云端
- **温文件**（数据/配置）：本地存储，根据传播需求决定

### 分享链接格式
```
https://cdn.lingxiangluo.tech/<file_key>
```

### 有效期
- **默认：** 7 天
- **可配置：** 1-365 天
- **过期后：** 自动清理（可禁用）

### 支持的文件格式
- **文档：** .md, .pdf, .docx, .pptx, .xlsx, .txt
- **图片：** .png, .jpg, .jpeg, .gif, .webp, .svg
- **视频：** .mp4, .avi, .mov, .mkv
- **音频：** .mp3, .wav, .ogg
- **代码：** .py, .sh, .js, .ts, .go, .rs, .java, .c, .cpp
- **数据：** .json, .xml, .csv, .yaml, .yml
- **压缩包：** .zip, .tar, .gz, .rar, .7z
---

# Agent File Cloud - 智能文件管理技能

> 基于阿里云 Embedding 的语义搜索 + 七牛云存储 + 云地冷热智能管理
>
> **整合了原 qiniu_file_sender 技能的所有功能**

---

## 📋 技能概述

**Agent File Cloud** 是一个智能文件管理系统，提供语义搜索、相似推荐和云地冷热智能存储服务。

### 核心特性

- 🔍 **语义搜索** - 理解查询意图，不只是关键词匹配
- 📌 **相似推荐** - 基于向量相似度推荐相关文件
- ☁️ **七牛云存储** - 文件上传、版本管理、批量操作
- 🔥 **热文件管理** - 脚本/代码本地存储，快速执行
- ☁️ **冷文件管理** - 文档/传播文件云端存储，便于分享
- 💾 **智能决策** - 自动分析文件类型，给出存储建议
---

## 📋 技能概述

**Agent File Cloud** 是一个智能文件管理系统，提供语义搜索、相似推荐和云地冷热智能存储服务。

### 核心特性

- 🔍 **语义搜索** - 理解查询意图，不只是关键词匹配
- 📌 **相似推荐** - 基于向量相似度推荐相关文件
- ☁️ **七牛云存储** - 文件上传、版本管理、批量操作
- 🔥 **热文件管理** - 脚本/代码本地存储，快速执行
- ☁️ **冷文件管理** - 文档/传播文件云端存储，便于分享
- 💾 **智能决策** - 自动分析文件类型，给出存储建议
- 🏷️ **标签系统** - 多层级标签体系，支持搜索筛选
- 🔄 **文件去重** - 基于 hash 识别重复文件

---

## 🚀 初始化设置

### 首次使用 - 创建必要目录和配置

在使用本技能前，需要创建必要的工作目录和配置文件：

```bash
# 1. 创建工作目录
mkdir -p ~/.openclaw/skills/agent-file-cloud/{workspace/inbox,workspace/archive,workspace/temp,config}

# 2. 创建配置文件
cat > ~/.openclaw/skills/agent-file-cloud/config/config.json << 'EOF'
{
  "version": "3.0",
  "api": {
    "dashscope_api_key": "sk-xxx",
    "embedding_model": "text-embedding-v4",
    "dimension": 1024
  },
  "directories": {
    "inbox": "/home/node/.openclaw/skills/agent-file-cloud/workspace/inbox",
    "archive": "/home/node/.openclaw/skills/agent-file-cloud/workspace/archive",
    "temp": "/home/node/.openclaw/skills/agent-file-cloud/workspace/temp"
  },
  "storage_policy": {
    "hot_extensions": [".py", ".sh", ".js", ".yaml", ".yml"],
    "cold_extensions": [".md", ".pdf", ".png", ".jpg", ".mp4"],
    "warm_extensions": [".json", ".xml", ".log"]
  }
}
EOF

# 3. 安装依赖
pip3 install --break-system-packages dashscope faiss-cpu numpy networkx openai

# 4. 测试安装
~/.openclaw/skills/agent-file-cloud/venv/bin/python3 -c "import dashscope, faiss, numpy; print('✅ 依赖安装成功')"
```

### 环境变量（可选）

```bash
# 设置 API Key（如果不在 config.json 中配置）
export DASHSCOPE_API_KEY="sk-xxx"

# 设置工作目录（默认在技能目录内）
export AGENT_FILE_CLOUD_WORKSPACE="/path/to/workspace"
```

---

## 📚 使用方法

### 基础命令

```bash
cd ~/.openclaw/skills/agent-file-cloud

# 添加文件
python3 agent_file_cloud.py add inbox/report.md \
  --tags "报告，财务，2026Q1" \
  --desc "2026 年第一季度财务报告" \
  --category "01-documents/reports"

# 语义搜索
python3 agent_file_cloud.py search "财务报告"

# 列出文件
python3 agent_file_cloud.py list --limit 20

# 查看统计
python3 agent_file_cloud.py stats

# 推荐相似文件
python3 agent_file_cloud.py recommend <file_id>
```

### 存储管理

```bash
# 查看存储统计
python3 storage_manager.py stats

# 分析所有文件
python3 storage_manager.py analyze

# 获取需要执行的操作
python3 storage_manager.py actions

# 分析单个文件
python3 storage_manager.py file <file_id>
```

### 工具脚本

```bash
# 上传到七牛云
./scripts/upload_to_cloud.sh <file_path> --desc "描述" --tags "标签"

# 备份热文件
./scripts/backup_hot_files.sh

# 云地同步
./scripts/sync_files.sh --check   # 检查差异
./scripts/sync_files.sh --sync    # 执行同步
```

---

## 🔥☁️ 存储策略

### 文件分类

| 类型 | 标识 | 扩展名示例 | 存储位置 | 说明 |
|------|------|-----------|---------|------|
| **热文件** | 🔥 | .py, .sh, .js, .yaml | 💻 本地 | 脚本/代码，需要执行 |
| **温文件** | ⚡ | .json, .xml, .log | 💻 本地 | 数据/日志/其他 |
| **冷文件** | ☁️ | .md, .pdf, .png, .mp4 | ☁️ 云端 | 文档/媒体，用于传播 |

### 决策流程

```
1. 检查文件扩展名 → 判断文件类型
2. 检查标签/描述 → 判断传播需求
3. 生成存储建议 → 本地/云端/双存
4. 生成操作列表 → 上传/备份/恢复
```

### 示例

```python
# 🔥 热文件 - 脚本
deploy.py → 本地存储（需要执行）+ 云端备份

# ☁️ 冷文件 - 文档
report.pdf → 云端存储（用于分享）

# ⚡ 温文件 - 数据
config.json → 本地存储（配置数据）
```

---

## 📁 文件结构

```
~/.openclaw/skills/agent-file-cloud/
├── SKILL.md                  ⭐ 技能说明（本文件）
├── agent_file_cloud.py       ⭐ 主程序
├── storage_manager.py        ⭐ 存储管理
├── embedding_api.py          ⭐ Embedding API
├── file_manager.py           文件整理
├── vector_index.py           向量索引
├── meta_database.py          元数据数据库
├── smart_search.py           智能搜索
│
├── scripts/                  脚本工具
│   ├── upload_to_cloud.sh    云端上传
│   ├── backup_hot_files.sh   热文件备份
│   └── sync_files.sh         云地同步
│
├── config/                   配置目录
│   └── config.json           主配置
│
├── workspace/                工作目录（初始化时创建）
│   ├── inbox/                待处理文件
│   ├── archive/              已归档文件
│   └── temp/                 临时文件
│
└── references/               参考资料
    └── API_DOCUMENTATION.md  API 文档
```

---

## 🔧 配置说明

### 统一配置文件

**位置：** `config/config.json`

所有配置（阿里云 API、七牛云、存储策略）都在一个文件中管理：

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

### 配置项说明

| 配置组 | 字段 | 说明 | 必填 |
|--------|------|------|------|
| **api** | `dashscope_api_key` | 阿里云 API Key | 语义搜索必填 |
| **api** | `embedding_model` | Embedding 模型 | 默认 text-embedding-v4 |
| **api** | `dimension` | 向量维度 | 默认 1024 |
| **qiniu** | `access_key` | 七牛云访问密钥 | 云上传必填 |
| **qiniu** | `secret_key` | 七牛云密钥 | 云上传必填 |
| **qiniu** | `bucket` | 七牛云存储空间 | 云上传必填 |
| **qiniu** | `domain` | 七牛云域名 | 云上传必填 |
| **qiniu** | `default_expiry_days` | 默认有效期 | 默认 7 天 |
| **storage_policy** | `hot_extensions` | 热文件扩展名 | 可选 |
| **storage_policy** | `cold_extensions` | 冷文件扩展名 | 可选 |
| **storage_policy** | `warm_extensions` | 温文件扩展名 | 可选 |

### 环境变量（可选）

| 变量 | 说明 | 优先级 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云 API Key | 高于配置文件 |
| `AGENT_FILE_CLOUD_WORKSPACE` | 工作目录路径 | 高于配置文件 |

---

## 💡 使用场景

### 场景 1：项目管理

```bash
# 添加项目文档
python3 agent_file_cloud.py add inbox/plan.md \
  --tags "项目 A，计划" \
  --desc "项目 A 开发计划" \
  --category "03-projects/project_a"

# 搜索相关文件
python3 agent_file_cloud.py search "项目 A 开发"

# 查看存储状态
python3 storage_manager.py stats
```

### 场景 2：文档分享

```bash
# 添加要分享的文档
python3 agent_file_cloud.py add inbox/report.pdf \
  --tags "报告，分享，public" \
  --desc "季度报告，需要分享给团队"

# 查看需要上传的文件
python3 storage_manager.py actions

# 输出：
# ⬆️ 上传 report.pdf
#    原因：有传播需求，应保存在云端
```

### 场景 3：代码管理

```bash
# 添加脚本文件
python3 agent_file_cloud.py add scripts/deploy.py \
  --tags "脚本，部署" \
  --desc "部署脚本"

# 分析存储建议
python3 storage_manager.py file <file_id>

# 输出：
# 🔥 热文件 (脚本/代码)
# 推荐：💻 本地
# 原因：脚本/代码文件，需要本地执行
# 建议：💾 云端备份
```

---

## ⚠️ 注意事项

### API 调用成本

- **免费额度：** 阿里云提供一定免费额度
- **计费：** 超出后按 tokens 计费
- **优化：** 批量处理时注意控制调用次数

### 存储成本

- **七牛云：** 10GB 免费存储 + 10GB 免费流量/月
- **超出后：** ¥0.12/GB/月 存储费
- **建议：** 定期清理不需要的文件

### 性能优化

- **小数据量：** < 1000 文件，秒级响应
- **大数据量：** 考虑使用 FAISS 索引加速
- **批量操作：** 使用脚本批量处理

---

## 🔧 依赖安装

### 方法 1：使用安装脚本（推荐）

```bash
cd ~/.openclaw/skills/agent-file-cloud
./install.sh
```

### 方法 2：手动安装

```bash
# 使用 requirements.txt
pip3 install -r requirements.txt

# 或单独安装
pip3 install numpy qiniu networkx faiss-cpu
```

### 方法 3：使用激活脚本

```bash
# 激活技能环境
source activate_skill.sh

# 然后运行
python3 agent_file_cloud.py search "关键词"
```

---

## 📊 统计信息

### 文件统计

```bash
python3 agent_file_cloud.py stats
```

**输出示例：**
```
📊 文件统计:
   总文件数：10
   总大小：1.23 MB
   已向量：8 个文件

   按分类:
      01-documents: 5 个
      03-projects: 3 个

💾 智能存储统计:
   🔥 热文件 (脚本/代码): 3 个
   ⚡ 温文件 (数据/其他): 2 个
   ☁️ 冷文件 (文档/传播): 5 个
```

---

## 🎉 版本历史

### v3.0 (2026-03-30)

- ✅ 新存储策略（热/温/冷）
- ✅ 传播需求识别
- ✅ 操作建议生成
- ✅ Skill 标准化
- ✅ 初始化流程文档化

### v2.0 (2026-03-30)

- ✅ 语义搜索
- ✅ 向量推荐
- ✅ 基础存储管理

---

## 📚 相关资源

- [阿里云百炼文档](https://help.aliyun.com/zh/model-studio/)
- [七牛云文档](https://developer.qiniu.com/)
- [OpenClaw 文档](https://docs.openclaw.ai/)

---

**Agent File Cloud - 让文件管理更智能！** 🚀
