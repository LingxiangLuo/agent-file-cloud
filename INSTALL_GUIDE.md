# Agent File Cloud 技能安装说明

> 智能文件管理 - 语义搜索 + 七牛云存储 + 知识图谱

---

## 📦 安装步骤

### 1. 确认技能位置

技能已安装在：
```
~/.openclaw/skills/agent-file-cloud/
```

### 2. 安装 Python 依赖

```bash
# 必需依赖
pip3 install --break-system-packages \
  dashscope \
  faiss-cpu \
  numpy \
  networkx \
  openai

# 可选依赖（七牛云上传）
pip3 install --break-system-packages qiniu
```

### 3. 配置 API Key

编辑配置文件：
```bash
vim ~/.openclaw/skills/agent-file-cloud/config/config.json
```

添加阿里云 API Key：
```json
{
  "api": {
    "dashscope_api_key": "sk-你的 API Key"
  },
  "qiniu": {
    "access_key": "你的七牛云 Access Key",
    "secret_key": "你的七牛云 Secret Key",
    "bucket": "你的 Bucket 名称",
    "domain": "https://你的域名.com"
  }
}
```

### 4. 测试安装

```bash
cd ~/.openclaw/skills/agent-file-cloud

# 测试数据管理
python3 data_manager.py stats

# 测试存储管理
python3 storage_manager.py stats

# 测试检索推荐
python3 search_recommend.py stats

# 测试主程序
python3 agent_file_cloud.py --help
```

---

## 🚀 快速开始

### 添加文件

```bash
cd ~/.openclaw/skills/agent-file-cloud

# 添加文件到系统
python3 agent_file_cloud.py add inbox/file.md \
  --tags "标签 1，标签 2" \
  --desc "文件描述"
```

### 语义搜索

```bash
# 搜索文件
python3 agent_file_cloud.py search "关键词"
```

### 智能上传

```bash
# 上传到七牛云（自动决策）
python3 agent_file_cloud.py upload inbox/file.md \
  --tags "重要，分享" \
  --desc "文件描述"
```

### 生成分享消息

```bash
# 生成包含下载链接的分享消息
python3 agent_file_cloud.py share <file_id>
```

### 推荐相似文件

```bash
# 推荐相似文件
python3 search_recommend.py recommend <file_id>
```

---

## 📁 技能文件结构

```
agent-file-cloud/
├── SKILL.md                      ⭐ 技能说明
├── USAGE.md                      ⭐ 使用指南
├── agent_file_cloud.py           ⭐ 主程序
├── data_manager.py               ⭐ 数据管理器
├── search_recommend.py           ⭐ 检索推荐系统
├── storage_manager.py            ⭐ 存储管理
├── embedding_api.py              ⭐ Embedding API
├── install.sh                    ⭐ 安装脚本
└── config/
    ├── config.json               ⭐ 统一配置
    ├── config.template.json      ⭐ 配置模板
    ├── metadata.json             📄 元数据
    ├── versions.json             📚 版本
    ├── history.json              📜 历史
    ├── vectors.json              🔗 向量
    └── graph.json                🕸️ 图谱
```

---

## 🔧 核心功能

| 功能 | 命令 | 说明 |
|------|------|------|
| **添加文件** | `add <file>` | 添加文件元数据 |
| **语义搜索** | `search <query>` | 基于 Embedding 搜索 |
| **文件列表** | `list` | 列出文件 |
| **统计信息** | `stats` | 查看统计 |
| **推荐相似** | `recommend <id>` | 推荐相关文件 |
| **智能上传** | `upload <file>` | 上传到七牛云 |
| **分享消息** | `share <id>` | 生成分享消息 |
| **数据管理** | `data_manager.py` | 数据管理工具 |
| **检索推荐** | `search_recommend.py` | 检索推荐工具 |

---

## ⚠️ 注意事项

### 1. 配置文件安全

```bash
# 保护配置文件
chmod 600 ~/.openclaw/skills/agent-file-cloud/config/config.json

# 不要提交到 Git
echo "config/config.json" >> ~/.openclaw/skills/agent-file-cloud/.gitignore
```

### 2. API Key 获取

**阿里云 API Key：**
1. 访问 https://dashscope.console.aliyun.com/
2. 登录阿里云账号
3. 创建 API Key
4. 复制到配置文件

**七牛云凭证：**
1. 访问 https://portal.qiniu.com/
2. 登录七牛云账号
3. 创建存储空间
4. 获取密钥和域名

### 3. 依赖问题

如果遇到依赖安装问题：
```bash
# 使用 --break-system-packages
pip3 install --break-system-packages <package>

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install dashscope faiss-cpu numpy networkx openai qiniu
```

---

## 📊 技能对比

| 功能 | 旧技能 (qiniu_file_sender) | 新技能 (agent-file-cloud) |
|------|--------------------------|--------------------------|
| **文件上传** | ✅ | ✅ |
| **语义搜索** | ❌ | ✅ |
| **知识图谱** | ❌ | ✅ |
| **版本管理** | ⚠️ 基础 | ✅ 完整 |
| **智能推荐** | ❌ | ✅ |
| **存储策略** | ❌ | ✅ |
| **数据管理** | ❌ | ✅ |

---

## 🎯 使用示例

### 完整工作流

```bash
cd ~/.openclaw/skills/agent-file-cloud

# 1. 添加文件
python3 agent_file_cloud.py add inbox/report.md \
  --tags "报告，财务" \
  --desc "2026Q1 财务报告"

# 2. 上传到云端
python3 agent_file_cloud.py upload inbox/report.md \
  --tags "重要，分享"

# 3. 生成分享消息
python3 agent_file_cloud.py share <file_id>

# 4. 查看统计
python3 data_manager.py stats

# 5. 推荐相似文件
python3 search_recommend.py recommend <file_id>
```

---

## 📚 相关文档

- **SKILL.md** - 技能详细说明
- **USAGE.md** - 快速使用指南
- **config/CONFIG_GUIDE.md** - 配置详解

---

## ✅ 安装完成检查清单

- [ ] 依赖已安装
- [ ] 配置文件已编辑
- [ ] API Key 已配置
- [ ] 测试命令通过
- [ ] 旧技能已删除

---

**Agent File Cloud 技能安装完成！** 🎉
