#!/usr/bin/env python3
"""
数据管理器单元测试 - data_manager.py
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_manager import DataManager


class TestDataManager:
    """测试 DataManager 类"""

    @pytest.fixture
    def data_manager(self, tmp_path):
        """创建测试用的 DataManager"""
        # 设置临时配置目录
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # 保存原始值
        import data_manager
        original_config = data_manager.CONFIG_FILE
        original_metadata = data_manager.METADATA_DB
        original_versions = data_manager.VERSIONS_DB
        original_history = data_manager.HISTORY_DB
        original_vectors = data_manager.VECTORS_DB
        original_graph = data_manager.GRAPH_DB

        # 修改全局变量
        data_manager.CONFIG_FILE = config_dir / "config.json"
        data_manager.METADATA_DB = config_dir / "metadata.json"
        data_manager.VERSIONS_DB = config_dir / "versions.json"
        data_manager.HISTORY_DB = config_dir / "history.json"
        data_manager.VECTORS_DB = config_dir / "vectors.json"
        data_manager.GRAPH_DB = config_dir / "graph.json"

        # 创建空配置
        with open(config_dir / "config.json", 'w') as f:
            json.dump({}, f)

        dm = DataManager()

        yield dm, tmp_path

        # 恢复原始值
        data_manager.CONFIG_FILE = original_config
        data_manager.METADATA_DB = original_metadata
        data_manager.VERSIONS_DB = original_versions
        data_manager.HISTORY_DB = original_history
        data_manager.VECTORS_DB = original_vectors
        data_manager.GRAPH_DB = original_graph

    def test_init(self, data_manager):
        """测试初始化"""
        dm, _ = data_manager
        assert dm.metadata is not None
        assert dm.versions is not None
        assert dm.history is not None
        assert dm.vectors is not None
        assert dm.graph is not None

    def test_generate_file_id(self, data_manager):
        """测试文件 ID 生成"""
        dm, _ = data_manager
        file_id = dm.generate_file_id("/test/path")
        assert file_id.startswith("file_")
        assert len(file_id) > 5

    def test_add_file_metadata(self, data_manager):
        """测试添加文件元数据"""
        dm, tmp_path = data_manager

        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_id = dm.add_file_metadata(
            str(test_file),
            description="Test file",
            tags=["test", "unittest"],
            category="test"
        )

        assert file_id is not None
        assert file_id.startswith("file_")

        # 验证元数据已保存
        metadata = dm.get_file_metadata(file_id)
        assert metadata is not None
        assert metadata["description"] == "Test file"
        assert "test" in metadata["tags"]

    def test_add_file_metadata_nonexistent(self, data_manager):
        """测试添加不存在的文件"""
        dm, _ = data_manager

        with pytest.raises(FileNotFoundError):
            dm.add_file_metadata("/nonexistent/file.txt")

    def test_get_file_metadata(self, data_manager):
        """测试获取文件元数据"""
        dm, tmp_path = data_manager

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_id = dm.add_file_metadata(str(test_file))
        metadata = dm.get_file_metadata(file_id)

        assert metadata is not None
        assert metadata["id"] == file_id

    def test_update_file_metadata(self, data_manager):
        """测试更新文件元数据"""
        dm, tmp_path = data_manager

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_id = dm.add_file_metadata(str(test_file))

        # 更新元数据
        result = dm.update_file_metadata(file_id, description="Updated description")
        assert result is True

        metadata = dm.get_file_metadata(file_id)
        assert metadata["description"] == "Updated description"
        assert metadata["version"] == 2  # 版本号应该增加

    def test_update_file_metadata_nonexistent(self, data_manager):
        """测试更新不存在的文件"""
        dm, _ = data_manager

        result = dm.update_file_metadata("nonexistent_id", description="test")
        assert result is False

    def test_delete_file_metadata(self, data_manager):
        """测试删除文件元数据"""
        dm, tmp_path = data_manager

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_id = dm.add_file_metadata(str(test_file))

        # 删除元数据
        result = dm.delete_file_metadata(file_id)
        assert result is True

        # 验证已删除
        metadata = dm.get_file_metadata(file_id)
        assert metadata is None

    def test_list_files(self, data_manager):
        """测试列出文件"""
        dm, tmp_path = data_manager

        # 创建多个测试文件
        for i in range(5):
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(f"Test content {i}")
            dm.add_file_metadata(
                str(test_file),
                category="test" if i % 2 == 0 else "other",
                tags=["test"]
            )

        # 列出所有文件
        files = dm.list_files(limit=10)
        assert len(files) == 5

        # 按分类筛选
        test_files = dm.list_files(category="test")
        assert len(test_files) == 3  # 0, 2, 4

        # 按标签筛选
        tagged_files = dm.list_files(tags=["test"])
        assert len(tagged_files) == 5

    def test_list_files_limit(self, data_manager):
        """测试列出文件数量限制"""
        dm, tmp_path = data_manager

        for i in range(10):
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(f"Test content {i}")
            dm.add_file_metadata(str(test_file))

        files = dm.list_files(limit=5)
        assert len(files) == 5

    def test_create_version(self, data_manager):
        """测试创建版本"""
        dm, tmp_path = data_manager

        # 创建原文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("Version 1")
        file_id = dm.add_file_metadata(str(test_file))

        # 创建版本文件
        version_file = tmp_path / "test_v1.txt"
        version_file.write_text("Version 1 content")

        version_id = dm.create_version(
            file_id,
            str(version_file),
            version_name="v1.0",
            description="Initial version"
        )

        assert version_id is not None
        assert version_id.startswith("ver_")

    def test_create_version_nonexistent_file(self, data_manager):
        """测试创建版本时文件不存在"""
        dm, tmp_path = data_manager

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")
        file_id = dm.add_file_metadata(str(test_file))

        with pytest.raises(FileNotFoundError):
            dm.create_version(file_id, "/nonexistent/version.txt")

    def test_get_version_history(self, data_manager):
        """测试获取版本历史"""
        dm, tmp_path = data_manager

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")
        file_id = dm.add_file_metadata(str(test_file))

        # 创建多个版本
        for i in range(3):
            version_file = tmp_path / f"test_v{i}.txt"
            version_file.write_text(f"Version {i}")
            dm.create_version(file_id, str(version_file), version_name=f"v{i}.0")

        history = dm.get_version_history(file_id)
        assert len(history) == 3

    def test_operation_history(self, data_manager):
        """测试操作历史记录"""
        dm, tmp_path = data_manager

        test_file = tmp_path / "test.txt"
        test_file.write_text("Test")
        file_id = dm.add_file_metadata(str(test_file))

        # 获取操作历史
        history = dm.get_operation_history(file_id=file_id)
        assert len(history) > 0
        assert history[0]["operation"] == "add_file"

    def test_save_embedding(self, data_manager):
        """测试保存向量"""
        dm, _ = data_manager

        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        file_id = "file_test"

        result = dm.save_embedding(file_id, test_embedding)
        assert result is True

        # 验证向量已保存
        embedding = dm.get_embedding(file_id)
        assert embedding == test_embedding

    def test_get_embedding_nonexistent(self, data_manager):
        """测试获取不存在的向量"""
        dm, _ = data_manager

        embedding = dm.get_embedding("nonexistent_id")
        assert embedding is None

    def test_has_embedding(self, data_manager):
        """测试检查向量存在"""
        dm, _ = data_manager

        assert dm.has_embedding("nonexistent") is False

        dm.save_embedding("test_id", [0.1, 0.2])
        assert dm.has_embedding("test_id") is True

    def test_delete_embedding(self, data_manager):
        """测试删除向量"""
        dm, _ = data_manager

        dm.save_embedding("test_id", [0.1, 0.2])
        result = dm.delete_embedding("test_id")
        assert result is True
        assert dm.has_embedding("test_id") is False

    def test_graph_stats(self, data_manager):
        """测试图谱统计"""
        dm, _ = data_manager

        stats = dm.get_graph_stats()
        assert "total_nodes" in stats
        assert "total_edges" in stats

    def test_full_stats(self, data_manager):
        """测试完整统计"""
        dm, tmp_path = data_manager

        # 添加一些测试数据
        for i in range(3):
            test_file = tmp_path / f"test_{i}.txt"
            test_file.write_text(f"Test {i}")
            file_id = dm.add_file_metadata(
                str(test_file),
                category="test",
                tags=["test"]
            )
            dm.save_embedding(file_id, [float(i)] * 5)

        stats = dm.get_full_stats()

        assert "metadata" in stats
        assert "versions" in stats
        assert "history" in stats
        assert "vectors" in stats
        assert "graph" in stats

        assert stats["metadata"]["total_files"] == 3
        assert stats["vectors"]["total_embeddings"] == 3
