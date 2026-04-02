# Agent File Cloud - 发送文件格式规范

**创建时间：** 2026-03-31 22:45  
**创建人：** 蒜蓉小龙虾 🦞

---

## 📋 默认发送行为

### 智能存储决策

| 文件类型 | 扩展名示例 | 存储位置 | 发送方式 |
|----------|-----------|----------|----------|
| 🔥 **热文件** | .py, .sh, .js, .ts | 本地 + 云端备份 | 本地路径 / 云链接（可选） |
| ⚡ **温文件** | .json, .xml, .csv | 本地 | 本地路径 |
| ☁️ **冷文件** | .md, .pdf, .png, .mp4 | 七牛云 | 分享链接 |

---

## 🔗 分享链接格式

### 标准格式

```
https://cdn.lingxiangluo.tech/<file_key>
```

**示例：**
```
https://cdn.lingxiangluo.tech/FgsZu9XmgkiJIo8aDb6XsBcI2RpN
```

### 链接组成

| 部分 | 说明 | 示例 |
|------|------|------|
| 域名 | 七牛云 CDN 域名 | `https://cdn.lingxiangluo.tech` |
| 文件 Key | 唯一文件标识 | `FgsZu9XmgkiJIo8aDb6XsBcI2RpN` |

---

## ⏱️ 有效期设置

### 默认配置

```json
{
  "qiniu": {
    "default_expiry_days": 7
  }
}
```

### 有效期规则

| 文件类型 | 默认有效期 | 可调整范围 |
|----------|-----------|-----------|
| 公开文档 | 7 天 | 1-365 天 |
| 临时文件 | 1 天 | 1-7 天 |
| 永久分享 | 365 天 | 1-365 天 |

### 自定义有效期

```bash
# 设置 30 天有效期
python3 agent_file_cloud.py add file.pdf --expiry 30

# 设置 7 天（默认）
python3 agent_file_cloud.py add file.pdf

# 永久（365 天）
python3 agent_file_cloud.py add file.pdf --expiry 365
```

---

## 📁 支持的文件格式

### 文档类

| 格式 | 扩展名 | 存储类型 | 说明 |
|------|--------|----------|------|
| Markdown | .md | ☁️ 冷文件 | 技术文档、笔记 |
| PDF | .pdf | ☁️ 冷文件 | 报告、论文 |
| Word | .docx | ☁️ 冷文件 | 办公文档 |
| PowerPoint | .pptx | ☁️ 冷文件 | 演示文稿 |
| Excel | .xlsx | ☁️ 冷文件 | 表格数据 |
| 纯文本 | .txt | ⚡ 温文件 | 简单文本 |

### 图片类

| 格式 | 扩展名 | 存储类型 | 说明 |
|------|--------|----------|------|
| PNG | .png | ☁️ 冷文件 | 无损压缩 |
| JPEG | .jpg, .jpeg | ☁️ 冷文件 | 有损压缩 |
| GIF | .gif | ☁️ 冷文件 | 动图 |
| WebP | .webp | ☁️ 冷文件 | 现代格式 |
| SVG | .svg | ☁️ 冷文件 | 矢量图 |

### 音视频类

| 格式 | 扩展名 | 存储类型 | 说明 |
|------|--------|----------|------|
| MP4 | .mp4 | ☁️ 冷文件 | 视频 |
| AVI | .avi | ☁️ 冷文件 | 视频 |
| MOV | .mov | ☁️ 冷文件 | 视频 |
| MP3 | .mp3 | ☁️ 冷文件 | 音频 |
| WAV | .wav | ☁️ 冷文件 | 音频 |

### 代码类

| 格式 | 扩展名 | 存储类型 | 说明 |
|------|--------|----------|------|
| Python | .py | 🔥 热文件 | 脚本 |
| Shell | .sh, .bash | 🔥 热文件 | 脚本 |
| JavaScript | .js, .ts | 🔥 热文件 | Web 代码 |
| Go | .go | 🔥 热文件 | Go 代码 |
| Rust | .rs | 🔥 热文件 | Rust 代码 |
| Java | .java | 🔥 热文件 | Java 代码 |
| C/C++ | .c, .cpp, .h | 🔥 热文件 | C 代码 |

### 数据类

| 格式 | 扩展名 | 存储类型 | 说明 |
|------|--------|----------|------|
| JSON | .json | ⚡ 温文件 | 结构化数据 |
| XML | .xml | ⚡ 温文件 | 标记数据 |
| CSV | .csv | ⚡ 温文件 | 表格数据 |
| YAML | .yaml, .yml | 🔥 热文件 | 配置文件 |

### 压缩包类

| 格式 | 扩展名 | 存储类型 | 说明 |
|------|--------|----------|------|
| ZIP | .zip | ☁️ 冷文件 | 压缩文件 |
| TAR | .tar | ☁️ 冷文件 | 归档文件 |
| GZIP | .gz | ☁️ 冷文件 | 压缩文件 |
| RAR | .rar | ☁️ 冷文件 | 压缩文件 |
| 7Z | .7z | ☁️ 冷文件 | 高压缩 |

---

## 📤 发送方式

### 方式 1：自动上传（推荐）

```bash
# 添加文件，自动判断存储位置
python3 agent_file_cloud.py add report.pdf \
  --tags "报告，财务" \
  --desc "2026 年财务报告"
```

**输出：**
```
✅ 已添加文件：report.pdf
   文件 ID: file_xxx
   存储类型：☁️ 冷文件
   分享链接：https://cdn.lingxiangluo.tech/xxx
   有效期：7 天
```

### 方式 2：强制云端

```bash
# 强制上传到七牛云
python3 agent_file_cloud.py add script.py --force-cloud
```

### 方式 3：仅本地

```bash
# 仅本地存储
python3 agent_file_cloud.py add config.json --local-only
```

### 方式 4：自定义有效期

```bash
# 设置 30 天有效期
python3 agent_file_cloud.py add document.pdf --expiry 30
```

---

## 🎯 最佳实践

### 1. 根据用途选择

| 用途 | 推荐格式 | 存储位置 | 有效期 |
|------|----------|----------|--------|
| 分享给客户 | PDF, PNG | 七牛云 | 7-30 天 |
| 团队协作文档 | MD, DOCX | 七牛云 | 30-90 天 |
| 代码审查 | PY, JS | 本地 + 备份 | 永久 |
| 临时文件 | 任意 | 七牛云 | 1-3 天 |
| 归档资料 | 任意 | 七牛云 | 365 天 |

### 2. 文件命名规范

```bash
# 推荐格式
YYYYMMDD_项目_内容_版本。扩展名

# 示例
20260331_财务报告_Q1_v1.pdf
20260331_项目计划_初稿。md
```

### 3. 标签使用

```bash
# 添加有意义的标签
python3 agent_file_cloud.py add file.pdf \
  --tags "财务，报告，2026Q1，公开"
```

---

## ⚠️ 注意事项

### 1. 文件大小限制

| 类型 | 限制 | 说明 |
|------|------|------|
| 单文件 | 500MB | 七牛云限制 |
| 批量上传 | 50 个 | 建议分批 |
| 总存储 | 10GB | 免费额度 |

### 2. 内容限制

**禁止上传：**
- ❌ 违法违规内容
- ❌ 敏感个人信息
- ❌ 商业机密（未加密）

### 3. 安全建议

```bash
# 敏感文件加密后上传
gpg -c sensitive.pdf
python3 agent_file_cloud.py add sensitive.pdf.gpg
```

---

## 📊 发送统计

### 查看上传历史

```bash
# 查看七牛云文件
python3 -c "
import json
with open('config/qiniu_files.json') as f:
    data = json.load(f)
for file in data['files']:
    print(f'{file[\"filename\"]}: {file[\"download_url\"]}')
"
```

### 查看过期文件

```bash
# 检查即将过期的文件
python3 auto_cleanup.py --check
```

---

## 🔄 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-03-31 | 初始版本 |

---

**文档完成！** 🦞
