# API 参考文档

Agent File Cloud 提供了一套完整的文件管理 API，包括文件上传、语义搜索、知识图谱和云存储功能。

## 核心类

### AgentFileCloud

主类，提供文件管理和搜索功能。

#### 初始化

```python
from agent_file_cloud import AgentFileCloud

cloud = AgentFileCloud(verbose=True)
```

**参数:**
- `verbose` (bool): 是否显示详细输出

#### 方法

##### add_file(filepath, description, tags, category, project)

添加文件到数据库。

**参数:**
- `filepath` (str): 文件路径
- `description` (str): 文件描述
- `tags` (List[str], optional): 标签列表
- `category` (str): 分类
- `project` (str): 所属项目

**返回:**
```python
{
    "success": True,
    "file_id": "file_xxx",
    "message": "已添加文件：xxx"
}
```

##### search(query, k)

搜索文件。

**参数:**
- `query` (str): 搜索查询
- `k` (int): 返回数量

**返回:**
```python
[
    {
        "file": {...},
        "score": 0.85,
        "type": "semantic"  # 或 "keyword"
    }
]
```

##### recommend_similar(file_id, k)

推荐相似文件。

**参数:**
- `file_id` (str): 源文件 ID
- `k` (int): 推荐数量

**返回:**
```python
{
    "source_file": {...},
    "similar_files": [...],
    "count": 5
}
```

##### get_stats()

获取统计信息。

**返回:**
```python
{
    "total_files": 100,
    "total_size_mb": 50.5,
    "by_category": {"code": 50, "docs": 30},
    "by_tag": {"python": 20},
    "with_embedding": 80
}
```

##### list_files(limit)

列出文件。

**参数:**
- `limit` (int): 返回数量限制

---

### EmbeddingAPI

阿里云 DashScope Embedding API 封装。

#### 初始化

```python
from embedding_api import EmbeddingAPI

api = EmbeddingAPI(
    api_key="your-api-key",
    model="text-embedding-v4",
    dimension=1024
)
```

#### 方法

##### create_embedding(text, text_type, max_retries)

创建文本向量。

**参数:**
- `text` (str): 输入文本
- `text_type` (str): 'document' 或 'query'
- `max_retries` (int): 最大重试次数

**返回:**
```python
[0.123, -0.456, 0.789, ...]  # 1024 维向量
```

##### cosine_similarity(vec1, vec2)

计算余弦相似度。

**参数:**
- `vec1` (List[float]): 向量 1
- `vec2` (List[float]): 向量 2

**返回:**
```python
0.85  # 相似度值，范围 [-1, 1]
```

##### get_stats()

获取使用统计。

---

### DataManager

核心数据管理器。

#### 主要方法

##### add_file_metadata(filepath, filename, description, tags, category, project)

添加文件元数据。

**返回:** `file_id` (str)

##### get_file_metadata(file_id)

获取文件元数据。

**返回:** `Dict` 或 `None`

##### update_file_metadata(file_id, **updates)

更新文件元数据。

**返回:** `bool`

##### delete_file_metadata(file_id)

删除文件元数据。

**返回:** `bool`

##### list_files(limit, category, tags)

列出文件。

**返回:** `List[Dict]`

##### create_version(file_id, version_path, version_name, description, change_type)

创建新版本。

**返回:** `version_id` (str)

##### get_version_history(file_id)

获取版本历史。

**返回:** `List[Dict]`

##### restore_version(version_id)

恢复指定版本。

**返回:** `bool`

##### save_embedding(file_id, embedding, model)

保存文件向量。

**返回:** `bool`

##### get_embedding(file_id)

获取文件向量。

**返回:** `List[float]` 或 `None`

---

### StorageManager

智能存储管理器。

#### 初始化

```python
from storage_manager import StorageManager

manager = StorageManager()
```

#### 方法

##### get_file_category(filepath)

判断文件类型。

**返回:** `'hot'`, `'warm'`, 或 `'cold'`

##### should_upload_to_cloud(file_metadata)

智能决策是否上传云端。

**返回:** `(bool, str)` - (是否上传，原因)

##### upload_to_qiniu(filepath, tags, description, expiry_days, force_upload)

上传文件到七牛云。

**返回:**
```python
{
    "success": True,
    "file_id": "qiniu_xxx",
    "download_url": "https://...",
    "expiry_time": "2026-04-09T00:00:00"
}
```

##### get_download_url(file_id)

获取下载链接。

**返回:** `str` 或 `None`

##### format_share_message(file_id)

生成分享消息。

**返回:** `str` 或 `None`

##### format_batch_share_message(file_ids)

生成批量分享消息。

**返回:** `str` 或 `None`

##### analyze_file(file_record)

分析文件存储策略。

**返回:**
```python
{
    "file_id": "...",
    "file_type": "hot",
    "current_location": "local",
    "recommended_location": "both",
    "action_required": "upload_to_cloud"
}
```

##### analyze_all_files()

分析所有文件。

**返回:** `List[Dict]`

##### get_storage_stats()

获取存储统计。

---

## CLI 命令

### agent_file_cloud.py

```bash
# 添加文件
python3 agent_file_cloud.py add <file> [--tags <tags>] [--desc <desc>]

# 搜索文件
python3 agent_file_cloud.py search <keyword>

# 列出文件
python3 agent_file_cloud.py list [--limit <n>]

# 统计信息
python3 agent_file_cloud.py stats

# 推荐相似文件
python3 agent_file_cloud.py recommend <file_id>

# 上传到七牛云
python3 agent_file_cloud.py upload <file>

# 分享文件
python3 agent_file_cloud.py share <file_id>

# 批量分享
python3 agent_file_cloud.py share-batch <id1,id2,...>

# 图谱可视化
python3 agent_file_cloud.py graph [file_id]
```

### storage_manager.py

```bash
# 存储统计
python3 storage_manager.py stats

# 分析所有文件
python3 storage_manager.py analyze

# 智能上传
python3 storage_manager.py upload <file>

# 生成分享消息
python3 storage_manager.py share <id>
```

### data_manager.py

```bash
# 数据统计
python3 data_manager.py stats

# 添加文件
python3 data_manager.py add <file>

# 列出文件
python3 data_manager.py list

# 操作历史
python3 data_manager.py history [file_id]

# 图谱关联
python3 data_manager.py graph <file_id>
```

## 错误处理

所有方法在失败时返回包含 `error` 字段的字典：

```python
{
    "error": "错误描述",
    "download_url": None
}
```

或者抛出异常：
- `FileNotFoundError`: 文件不存在
- `ValueError`: 参数错误
- `Exception`: API 调用失败

## 配置

配置文件位于 `config/config.json`：

```json
{
    "api": {
        "dashscope_api_key": "your-api-key",
        "embedding_model": "text-embedding-v4",
        "dimension": 1024
    },
    "qiniu": {
        "access_key": "your-access-key",
        "secret_key": "your-secret-key",
        "bucket": "your-bucket",
        "domain": "your-domain",
        "default_expiry_days": 7
    }
}
```
