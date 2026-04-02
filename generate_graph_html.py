#!/usr/bin/env python3
"""
生成图谱可视化 HTML 并上传到七牛云（覆盖 index.html）

功能：
1. 读取图谱数据
2. 生成 HTML 页面（力导向图，支持缩放）
3. 上传到七牛云 graph/index.html（覆盖旧文件）
4. 可通过域名直接访问
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加 venv 路径
venv_paths = [
    Path(__file__).parent / "venv" / "lib" / "python3.11" / "site-packages",
    Path(__file__).parent / "venv" / "local" / "lib" / "python3.11" / "dist-packages",
]

for venv_path in venv_paths:
    if venv_path.exists():
        sys.path.insert(0, str(venv_path))
        break

try:
    import qiniu
    from qiniu import Auth, put_file_v2
except ImportError as e:
    print(f"⚠️  七牛云 SDK 未安装：{e}")
    sys.exit(1)

# 技能目录
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config" / "config.json"
GRAPH_DB = SKILL_DIR / "config" / "graph.json"
METADATA_DB = SKILL_DIR / "config" / "metadata.json"
QINIU_HISTORY_FILE = SKILL_DIR / "config" / "qiniu_files.json"
TEMPLATE_FILE = SKILL_DIR / "graph_template.html"
OUTPUT_HTML = SKILL_DIR / "graph_index.html"


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_graph():
    """加载图谱数据（从主程序 files.json 加载并转换为图谱格式）"""
    FILES_DB = SKILL_DIR / "config" / "files.json"
    
    if FILES_DB.exists():
        with open(FILES_DB, 'r', encoding='utf-8') as f:
            files_data = json.load(f)
        
        # 转换为图谱格式
        graph = {"nodes": [], "edges": []}
        
        # 添加文件节点
        for file_rec in files_data.get("files", []):
            graph["nodes"].append({
                "id": file_rec.get("id"),
                "type": "file",
                "name": file_rec.get("filename"),
                "filename": file_rec.get("filename"),
                "size": file_rec.get("size", 0),
                "category": file_rec.get("category", "uncategorized"),
                "description": file_rec.get("description", ""),
                "embedding": file_rec.get("embedding"),
                "tags": file_rec.get("tags", []),
                "keywords": file_rec.get("keywords", [])
            })
            
            # 添加分类节点和边
            category = file_rec.get("category", "uncategorized")
            cat_id = f"category_{category}"
            
            if not any(n["id"] == cat_id for n in graph["nodes"]):
                graph["nodes"].append({
                    "id": cat_id,
                    "type": "category",
                    "name": category
                })
            
            graph["edges"].append({
                "source": file_rec.get("id"),
                "target": cat_id,
                "type": "belongs_to"
            })
            
            # 添加标签节点和边
            for tag in file_rec.get("tags", []):
                tag_id = f"tag_{tag}"
                if not any(n["id"] == tag_id for n in graph["nodes"]):
                    graph["nodes"].append({
                        "id": tag_id,
                        "type": "tag",
                        "name": tag
                    })
                
                graph["edges"].append({
                    "source": file_rec.get("id"),
                    "target": tag_id,
                    "type": "tagged_with"
                })
        
        return graph
    
    # 回退到旧的 graph.json
    if GRAPH_DB.exists():
        with open(GRAPH_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {"nodes": [], "edges": []}


def load_metadata():
    """加载元数据"""
    if METADATA_DB.exists():
        with open(METADATA_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"files": {}}


def merge_file_data(graph, metadata):
    """合并图谱数据和元数据（添加 qiniu_key 等信息）"""
    for node in graph.get("nodes", []):
        if node.get("type") == "file":
            file_id = node.get("id")
            if file_id and file_id in metadata.get("files", {}):
                file_meta = metadata["files"][file_id]
                # 从七牛云历史中查找 qiniu_key
                qiniu_history = load_qiniu_history()
                for qiniu_file in qiniu_history.get("files", []):
                    if qiniu_file.get("file_id") == file_meta.get("qiniu_id"):
                        node["qiniu_key"] = qiniu_file.get("qiniu_key")
                        node["download_url"] = qiniu_file.get("download_url")
                        break
    return graph


def load_qiniu_history():
    """加载七牛云历史"""
    if QINIU_HISTORY_FILE.exists():
        with open(QINIU_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"files": []}


def get_graph_stats(graph):
    """计算图谱统计"""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    by_type = {}
    for node in nodes:
        node_type = node.get("type", "unknown")
        by_type[node_type] = by_type.get(node_type, 0) + 1
    
    by_edge_type = {}
    for edge in edges:
        edge_type = edge.get("type", "unknown")
        by_edge_type[edge_type] = by_edge_type.get(edge_type, 0) + 1
    
    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "by_node_type": by_type,
        "by_edge_type": by_edge_type
    }


def generate_html():
    """生成 HTML 页面"""
    # 加载数据
    graph = load_graph()
    metadata = load_metadata()
    
    # 合并数据（添加 qiniu_key 等信息）
    graph = merge_file_data(graph, metadata)
    
    stats = get_graph_stats(graph)
    
    # 准备数据
    graph_data = {
        "nodes": graph["nodes"],
        "edges": graph["edges"],
        "stats": stats,
        "generated_at": datetime.now().isoformat()
    }
    
    # 读取模板
    if not TEMPLATE_FILE.exists():
        print(f"❌ 模板文件不存在：{TEMPLATE_FILE}")
        return None
    
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 清理字符串中的特殊字符（避免破坏 JavaScript 模板字符串）
    def clean_strings(obj):
        if isinstance(obj, dict):
            return {k: clean_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_strings(v) for v in obj]
        elif isinstance(obj, str):
            # 转义反引号和 ${
            return obj.replace('`', '\\`').replace('${', '\\${')
        else:
            return obj
    
    graph_data = clean_strings(graph_data)
    
    # 替换数据（使用占位符标记，避免正则表达式问题）
    json_str = json.dumps(graph_data, ensure_ascii=False, allow_nan=False)
    # 在 JSON 前后添加特殊标记，确保不会被截断
    html_content = template.replace("{{GRAPH_DATA}}", json_str)
    
    # 保存 HTML
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 已生成：{OUTPUT_HTML}")
    print(f"   数据大小：{len(json.dumps(graph_data))} 字节")
    return OUTPUT_HTML


def upload_to_qiniu(html_file):
    """上传 HTML 到七牛云根目录（公开访问，无需签名）"""
    config = load_config()
    qiniu_config = config.get("qiniu")
    
    if not qiniu_config:
        print("❌ 七牛云配置未设置")
        return None
    
    # 初始化七牛云
    auth = Auth(qiniu_config['access_key'], qiniu_config['secret_key'])
    
    # 固定文件名为 index.html（根目录，覆盖旧文件）
    qiniu_key = "index.html"
    
    # 生成上传 token（设置 overwrite 为 true 允许覆盖）
    token = auth.upload_token(qiniu_config['bucket'], expires=3600, policy={"insertOnly": 0})
    
    # 上传文件
    print(f"⬆️  上传到七牛云根目录 (index.html)...")
    ret, info = put_file_v2(token, qiniu_key, str(html_file))
    
    if info.status_code != 200:
        # 如果文件已存在，尝试先删除再上传
        if "file exists" in str(info.error):
            print(f"⚠️  文件已存在，尝试覆盖...")
            bucket = qiniu.BucketManager(auth)
            bucket.delete(qiniu_config['bucket'], qiniu_key)
            # 重新生成 token 并上传
            token = auth.upload_token(qiniu_config['bucket'], expires=3600, policy={"insertOnly": 0})
            ret, info = put_file_v2(token, qiniu_key, str(html_file))
        
        if info.status_code != 200:
            print(f"❌ 上传失败：{info.error}")
            return None
    
    print(f"✅ 上传成功（覆盖旧文件）")
    
    # 生成公开访问链接（图谱专用域名，HTTP 协议）
    public_url = qiniu_config.get('graph_domain', 'http://file.lingxiangluo.tech')
    public_url = f"{public_url}/"
    
    print(f"🌐 访问地址：{public_url}")
    
    return public_url


def main():
    """主函数"""
    print("🕸️  图谱可视化 HTML 生成器（力导向图）")
    print("=" * 50)
    
    # 生成 HTML
    html_file = generate_html()
    if not html_file:
        sys.exit(1)
    
    # 上传到七牛云
    public_url = upload_to_qiniu(html_file)
    if not public_url:
        print("\n⚠️  上传失败，但 HTML 文件已生成本地")
        print(f"   文件位置：{html_file}")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ 完成！")
    print(f"\n📊 图谱统计:")
    
    graph = load_graph()
    stats = get_graph_stats(graph)
    print(f"   总节点数：{stats['total_nodes']}")
    print(f"   总边数：{stats['total_edges']}")
    print(f"   文件数：{stats['by_node_type'].get('file', 0)}")
    print(f"   分类数：{stats['by_node_type'].get('category', 0)}")
    print(f"   标签数：{stats['by_node_type'].get('tag', 0)}")
    
    print(f"\n🌐 访问地址:")
    print(f"   {public_url}")
    
    print(f"\n💡 提示:")
    print(f"   点击链接即可在浏览器中查看力导向图")
    print(f"   支持：拖拽节点 • 滚轮缩放 • 点击查看详情")
    print(f"   每次生成会覆盖旧文件，链接永久有效")


if __name__ == "__main__":
    main()
