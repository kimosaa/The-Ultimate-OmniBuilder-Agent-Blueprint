"""
Tests for filesystem operations.
"""

import pytest
import tempfile
import os
from pathlib import Path

from omnibuilder.environment.filesystem import FileSystemManager, DiffPatchTool


class TestDiffPatchTool:
    """Tests for DiffPatchTool."""

    @pytest.fixture
    def diff_tool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = DiffPatchTool(backup_dir=tmpdir)
            yield tool

    def test_generate_diff(self, diff_tool):
        """Test generating a diff."""
        original = "line 1\nline 2\nline 3\n"
        modified = "line 1\nline 2 modified\nline 3\n"

        diff = diff_tool.generate_diff(original, modified)

        assert "line 2" in diff or "modified" in diff
        assert diff.startswith("---") or diff == ""  # Empty if no changes

    def test_create_backup(self, diff_tool):
        """Test creating a backup."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            backup_path = diff_tool.create_backup(temp_path)
            assert os.path.exists(backup_path)

            with open(backup_path) as f:
                content = f.read()
            assert content == "test content"
        finally:
            os.unlink(temp_path)
            if os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_atomic_write(self, diff_tool):
        """Test atomic write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")

            success = diff_tool.atomic_write(file_path, "test content")
            assert success
            assert os.path.exists(file_path)

            with open(file_path) as f:
                assert f.read() == "test content"


class TestFileSystemManager:
    """Tests for FileSystemManager."""

    @pytest.fixture
    def fs_manager(self):
        return FileSystemManager()

    def test_read_file(self, fs_manager):
        """Test reading a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            content = fs_manager.read_file(temp_path)
            assert content == "test content"
        finally:
            os.unlink(temp_path)

    def test_write_file(self, fs_manager):
        """Test writing a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")

            success = fs_manager.write_file(file_path, "test content")
            assert success
            assert os.path.exists(file_path)

            with open(file_path) as f:
                assert f.read() == "test content"

    def test_write_file_create_dirs(self, fs_manager):
        """Test writing file with directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "subdir", "test.txt")

            success = fs_manager.write_file(file_path, "test content", create_dirs=True)
            assert success
            assert os.path.exists(file_path)

    def test_copy_file(self, fs_manager):
        """Test copying a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "source.txt")
            dst = os.path.join(tmpdir, "dest.txt")

            with open(src, 'w') as f:
                f.write("test content")

            success = fs_manager.copy_file(src, dst)
            assert success
            assert os.path.exists(dst)

            with open(dst) as f:
                assert f.read() == "test content"

    def test_move_file(self, fs_manager):
        """Test moving a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "source.txt")
            dst = os.path.join(tmpdir, "dest.txt")

            with open(src, 'w') as f:
                f.write("test content")

            success = fs_manager.move_file(src, dst)
            assert success
            assert not os.path.exists(src)
            assert os.path.exists(dst)

    def test_delete_file(self, fs_manager):
        """Test deleting a file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        success = fs_manager.delete_file(temp_path, backup=False)
        assert success
        assert not os.path.exists(temp_path)

    def test_file_exists(self, fs_manager):
        """Test checking if file exists."""
        with tempfile.NamedTemporaryFile() as f:
            assert fs_manager.file_exists(f.name)

        assert not fs_manager.file_exists("/nonexistent/file.txt")

    def test_get_file_info(self, fs_manager):
        """Test getting file information."""
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"test content")
            f.flush()

            info = fs_manager.get_file_info(f.name)

            assert info['path'] == f.name
            assert info['size'] > 0
            assert 'modified' in info
            assert not info['is_dir']
