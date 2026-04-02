# Agent File Cloud 🦞

智能文件云存储管理技能 - 为 AI Agent 提供语义搜索、知识图谱和云存储能力

## 功能特性

- 🔍 **语义搜索** - 基于向量的文件内容搜索
- 🕸️ **知识图谱** - 可视化文件关系网络
- ☁️ **云存储** - 七牛云自动上传和分享
- 📊 **智能分类** - 热/温/冷文件自动分层
- 🔗 **分享链接** - 自动生成 CDN 分享链接

## 安装

```bash
# 使用 skillhub 安装
skillhub install agent-file-cloud

# 或手动安装
git clone https://github.com/LingxiangLuo/agent-file-cloud.git ~/.openclaw/skills/agent-file-cloud
```

## 配置

1. 复制配置模板：
```bash
cp config/config.example.json config/config.json
```

2. 编辑 `config/config.json`，填入你的 API 密钥：
- `dashscope_api_key` - 阿里云 DashScope API Key
- `qiniu.access_key` - 七牛云 Access Key
- `qiniu.secret_key` - 七牛云 Secret Key
- `qiniu.bucket` - 七牛云存储桶名称

## 使用

```bash
# 激活技能
use-skill agent-file-cloud

# 上传文件
upload-file /path/to/file.pdf

# 语义搜索
search-files "机器学习相关文档"

# 生成知识图谱
generate-graph
```

## 依赖

- Python 3.8+
- 阿里云 DashScope (文本嵌入)
- 七牛云存储

## 许可证

MIT License
