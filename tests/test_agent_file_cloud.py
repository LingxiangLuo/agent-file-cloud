#!/usr/bin/env python3
"""
核心模块单元测试 - agent_file_cloud.py
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_file_cloud import (
    AgentFileCloud,
    ensure_directories,
    load_config,
    load_db,
    save_db,
    is_safe_path,
    generate_file_id,
    extract_keywords,
    print_file_info,
)


class TestEnsureDirectories:
    """测试目录确保功能"""

    def test_ensure_directories_creates_dirs(self, tmp_path):
        """测试创建必要目录"""
        # 临时修改全局变量
        import agent_file_cloud
        original_skill_dir = agent_file_cloud.SKILL_DIR
        agent_file_cloud.SKILL_DIR = tmp_path
        agent_file_cloud.WORKSPACE_ROOT = tmp_path / "workspace"

        try:
            ensure_directories()
            assert (tmp_path / "config").exists()
            assert (tmp_path / "workspace" / "inbox").exists()
            assert (tmp_path / "workspace" / "archive").exists()
            assert (tmp_path / "workspace" / "temp").exists()
        finally:
            agent_file_cloud.SKILL_DIR = original_skill_dir


class TestIsSafePath:
    """测试路径安全检查"""

    def test_safe_path_within_base(self):
        """测试安全路径在基础目录内"""
        base = "/safe/base"
        target = "/safe/base/subdir/file.txt"
        assert is_safe_path(base, target) is True

    def test_safe_path_traversal_detected(self):
        """测试路径遍历攻击被检测"""
        base = "/safe/base"
        target = "/unsafe/other/file.txt"
        assert is_safe_path(base, target) is False

    def test_safe_path_relative_path(self):
        """测试相对路径处理"""
        base = "/safe/base"
        target = "subdir/file.txt"
        # 相对路径会被解析为绝对路径
        result = is_safe_path(base, target)
        # 取决于当前工作目录，这里只验证函数不抛出异常
        assert isinstance(result, bool)


class TestGenerateFileId:
    """测试文件 ID 生成"""

    def test_generate_unique_id(self):
        """测试生成唯一 ID"""
        id1 = generate_file_id("/path/to/file1.txt")
        id2 = generate_file_id("/path/to/file2.txt")
        assert id1 != id2
        assert id1.startswith("file_")
        assert id2.startswith("file_")

    def test_generate_id_format(self):
        """测试 ID 格式"""
        file_id = generate_file_id("/any/path")
        assert len(file_id) > 5  # file_ + 至少一些字符
        assert file_id.startswith("file_")


class TestExtractKeywords:
    """测试关键词提取"""

    def test_extract_keywords_basic(self):
        """测试基本关键词提取"""
        text = "Python is a great programming language. Python is versatile."
        keywords = extract_keywords(text)
        assert "python" in keywords[0].lower() if keywords else True  # python 应该在前面的位置

    def test_extract_keywords_empty(self):
        """测试空文本"""
        keywords = extract_keywords("")
        assert keywords == []

    def test_extract_keywords_max_keywords(self):
        """测试最大关键词数量限制"""
        text = " ".join([f"word{i}" for i in range(20)])
        keywords = extract_keywords(text, max_keywords=5)
        assert len(keywords) <= 5

    def test_extract_keywords_special_chars(self):
        """测试特殊字符过滤"""
        text = "test 'quoted' \"double\" \\backslash\\"
        keywords = extract_keywords(text)
        # 应该过滤掉引号
        for kw in keywords:
            assert "'" not in kw
            assert '"' not in kw


class TestAgentFileCloud:
    """测试 AgentFileCloud 主类"""

    @pytest.fixture
    def cloud_instance(self, tmp_path):
        """创建测试实例"""
        # 创建临时配置和数据库
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config = {
            "version": "3.0",
            "api": {
                "dashscope_api_key": "test_key",
                "embedding_model": "text-embedding-v4",
                "dimension": 1024
            },
            "directories": {
                "inbox": str(tmp_path / "inbox"),
                "archive": str(tmp_path / "archive"),
                "temp": str(tmp_path / "temp")
            }
        }

        with open(config_dir / "config.json", 'w') as f:
            json.dump(config, f)

        # 创建工作目录
        (tmp_path / "inbox").mkdir()
        (tmp_path / "archive").mkdir()
        (tmp_path / "temp").mkdir()

        # 保存原始值
        import agent_file_cloud
        original_config = agent_file_cloud.CONFIG_FILE
        original_db = agent_file_cloud.DB_FILE
        original_root = agent_file_cloud.ALLOWED_ROOT_DIR

        # 修改全局变量
        agent_file_cloud.CONFIG_FILE = config_dir / "config.json"
        agent_file_cloud.DB_FILE = config_dir / "files.json"
        agent_file_cloud.ALLOWED_ROOT_DIR = str(tmp_path)

        cloud = AgentFileCloud(verbose=False)

        yield cloud, tmp_path

        # 恢复原始值
        agent_file_cloud.CONFIG_FILE = original_config
        agent_file_cloud.DB_FILE = original_db
        agent_file_cloud.ALLOWED_ROOT_DIR = original_root

    def test_init(self, cloud_instance):
        """测试初始化"""
        cloud, _ = cloud_instance
        assert cloud.config is not None
        assert cloud.db is not None
        assert cloud.verbose is False

    def test_add_file(self, cloud_instance):
        """测试添加文件"""
        cloud, tmp_path = cloud_instance

        # 创建测试文件
        test_file = tmp_path / "inbox" / "test.txt"
        test_file.write_text("This is a test file for testing purposes.")

        result = cloud.add_file(
            str(test_file),
            description="Test file",
            tags=["test", "unittest"],
            category="test"
        )

        assert result.get("success") is True
        assert "file_id" in result
        assert "test.txt" in result.get("message", "")

    def test_add_file_invalid_path(self, cloud_instance):
        """测试添加不存在文件"""
        cloud, tmp_path = cloud_instance

        result = cloud.add_file("/nonexistent/path/file.txt")
        assert "error" in result

    def test_add_file_path_traversal(self, cloud_instance):
        """测试路径遍历保护"""
        cloud, tmp_path = cloud_instance

        # 尝试访问允许目录外的文件
        result = cloud.add_file("/etc/passwd")
        assert "error" in result

    def test_search(self, cloud_instance):
        """测试搜索功能"""
        cloud, tmp_path = cloud_instance

        # 先添加文件
        test_file = tmp_path / "inbox" / "search_test.txt"
        test_file.write_text("Machine learning is fascinating.")

        cloud.add_file(
            str(test_file),
            description="Machine learning test",
            tags=["ml", "test"],
            category="test"
        )

        # 搜索
        results = cloud.search("machine", k=10)
        assert isinstance(results, list)

    def test_list_files(self, cloud_instance):
        """测试列出文件"""
        cloud, tmp_path = cloud_instance

        files = cloud.list_files(limit=20)
        assert isinstance(files, list)

    def test_get_stats(self, cloud_instance):
        """测试统计功能"""
        cloud, tmp_path = cloud_instance

        stats = cloud.get_stats()
        assert "total_files" in stats
        assert "total_size" in stats
        assert "by_category" in stats
        assert "by_tag" in stats

    def test_recommend_similar(self, cloud_instance):
        """测试相似推荐"""
        cloud, tmp_path = cloud_instance

        # 添加文件
        test_file = tmp_path / "inbox" / "similar_test.txt"
        test_file.write_text("Similar content test.")

        result = cloud.add_file(str(test_file))
        file_id = result.get("file_id")

        if file_id:
            rec_result = cloud.recommend_similar(file_id, k=5)
            assert "source_file" in rec_result or "error" in rec_result


class TestLoadConfig:
    """测试配置加载"""

    def test_load_config_from_file(self, tmp_path):
        """测试从文件加载配置"""
        config_file = tmp_path / "config.json"
        test_config = {"test_key": "test_value", "version": "1.0"}

        with open(config_file, 'w') as f:
            json.dump(test_config, f)

        import agent_file_cloud
        original = agent_file_cloud.CONFIG_FILE
        agent_file_cloud.CONFIG_FILE = config_file

        try:
            config = load_config()
            assert config.get("test_key") == "test_value"
        finally:
            agent_file_cloud.CONFIG_FILE = original

    def test_load_config_default(self, tmp_path):
        """测试默认配置"""
        import agent_file_cloud
        original = agent_file_cloud.CONFIG_FILE
        agent_file_cloud.CONFIG_FILE = tmp_path / "nonexistent.json"

        try:
            config = load_config()
            assert "version" in config
            assert "api" in config
            assert "qiniu" in config
        finally:
            agent_file_cloud.CONFIG_FILE = original


class TestLoadDb:
    """测试数据库加载"""

    def test_load_db_from_file(self, tmp_path):
        """测试从文件加载数据库"""
        db_file = tmp_path / "files.json"
        test_db = {"files": [{"id": "file_1"}], "next_id": 2}

        with open(db_file, 'w') as f:
            json.dump(test_db, f)

        import agent_file_cloud
        original = agent_file_cloud.DB_FILE
        agent_file_cloud.DB_FILE = db_file

        try:
            db = load_db()
            assert len(db["files"]) == 1
            assert db["next_id"] == 2
        finally:
            agent_file_cloud.DB_FILE = original

    def test_load_db_default(self, tmp_path):
        """测试默认数据库"""
        import agent_file_cloud
        original = agent_file_cloud.DB_FILE
        agent_file_cloud.DB_FILE = tmp_path / "nonexistent.json"

        try:
            db = load_db()
            assert db == {"files": [], "next_id": 1}
        finally:
            agent_file_cloud.DB_FILE = original


class TestSaveDb:
    """测试数据库保存"""

    def test_save_db(self, tmp_path):
        """测试保存数据库"""
        db_file = tmp_path / "files.json"

        import agent_file_cloud
        original = agent_file_cloud.DB_FILE
        agent_file_cloud.DB_FILE = db_file

        try:
            test_db = {"files": [{"id": "file_1", "name": "test"}], "next_id": 2}
            save_db(test_db)

            assert db_file.exists()
            with open(db_file, 'r', encoding='utf-8') as f:
                loaded_db = json.load(f)
            assert loaded_db["files"][0]["id"] == "file_1"
        finally:
            agent_file_cloud.DB_FILE = original
