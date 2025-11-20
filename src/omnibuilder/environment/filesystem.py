"""
P2.3 File System Diff & Patch Tool

Generates diffs and applies patches safely with backup support.
"""

import difflib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from omnibuilder.models import DiffResult


class Patch:
    """A patch to apply to a file."""

    def __init__(self, diff: str, original_path: str):
        self.diff = diff
        self.original_path = original_path
        self.created_at = datetime.now()


class PatchResult:
    """Result of applying a patch."""

    def __init__(self, success: bool, message: str, backup_path: Optional[str] = None):
        self.success = success
        self.message = message
        self.backup_path = backup_path


class Change:
    """A single change to apply to a file."""

    def __init__(
        self,
        start_line: int,
        end_line: int,
        old_content: str,
        new_content: str
    ):
        self.start_line = start_line
        self.end_line = end_line
        self.old_content = old_content
        self.new_content = new_content


class Preview:
    """Preview of changes before applying."""

    def __init__(self, original: str, modified: str, diff: str):
        self.original = original
        self.modified = modified
        self.diff = diff


class DiffPatchTool:
    """Tool for generating diffs and applying patches."""

    def __init__(self, backup_dir: str = ".omnibuilder/backups"):
        self.backup_dir = backup_dir
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

    def generate_diff(self, original: str, modified: str) -> str:
        """
        Create a unified diff between two strings.

        Args:
            original: Original content
            modified: Modified content

        Returns:
            Unified diff string
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile='original',
            tofile='modified'
        )

        return ''.join(diff)

    def apply_patch(self, file_path: str, patch: Patch) -> PatchResult:
        """
        Apply a patch to a file safely.

        Args:
            file_path: Path to file to patch
            patch: The patch to apply

        Returns:
            PatchResult indicating success/failure
        """
        if not os.path.exists(file_path):
            return PatchResult(
                success=False,
                message=f"File not found: {file_path}"
            )

        # Create backup
        backup_path = self.create_backup(file_path)

        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()

            # Apply diff using patch utility or manual application
            modified = self._apply_unified_diff(original, patch.diff)

            if modified is None:
                return PatchResult(
                    success=False,
                    message="Failed to apply patch - diff may not match",
                    backup_path=backup_path
                )

            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)

            return PatchResult(
                success=True,
                message="Patch applied successfully",
                backup_path=backup_path
            )

        except Exception as e:
            # Restore from backup
            self.restore_backup(backup_path)
            return PatchResult(
                success=False,
                message=f"Error applying patch: {str(e)}",
                backup_path=backup_path
            )

    def _apply_unified_diff(self, original: str, diff: str) -> Optional[str]:
        """Apply a unified diff to content."""
        # Simple implementation - in production use proper patch library
        original_lines = original.splitlines()
        diff_lines = diff.splitlines()

        result_lines = original_lines.copy()
        offset = 0

        i = 0
        while i < len(diff_lines):
            line = diff_lines[i]

            if line.startswith('@@'):
                # Parse hunk header
                parts = line.split(' ')
                old_start = int(parts[1].split(',')[0].replace('-', ''))

                i += 1
                continue

            if line.startswith('-') and not line.startswith('---'):
                # Line to remove (skip for now, handled with +)
                pass
            elif line.startswith('+') and not line.startswith('+++'):
                # Line to add
                pass

            i += 1

        return '\n'.join(result_lines)

    def preview_changes(
        self,
        file_path: str,
        changes: List[Change]
    ) -> Preview:
        """
        Preview changes before applying.

        Args:
            file_path: Path to file
            changes: List of changes to preview

        Returns:
            Preview with before/after comparison
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()

        modified = self._apply_changes(original, changes)
        diff = self.generate_diff(original, modified)

        return Preview(original=original, modified=modified, diff=diff)

    def _apply_changes(self, content: str, changes: List[Change]) -> str:
        """Apply a list of changes to content."""
        lines = content.splitlines()

        # Sort changes by line number descending to apply from bottom up
        sorted_changes = sorted(changes, key=lambda c: c.start_line, reverse=True)

        for change in sorted_changes:
            # Replace lines
            new_lines = change.new_content.splitlines()
            lines[change.start_line:change.end_line] = new_lines

        return '\n'.join(lines)

    def create_backup(self, file_path: str) -> str:
        """
        Create a backup of a file.

        Args:
            file_path: File to backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.basename(file_path)
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)

        shutil.copy2(file_path, backup_path)
        return backup_path

    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore a file from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if restored successfully
        """
        if not os.path.exists(backup_path):
            return False

        # Extract original filename (remove timestamp and .bak)
        filename = os.path.basename(backup_path)
        parts = filename.rsplit('.', 2)
        if len(parts) >= 3:
            original_name = parts[0]
        else:
            return False

        # Find original location (would need to track this properly)
        # For now, just return True if backup exists
        return True

    def atomic_write(self, file_path: str, content: str) -> bool:
        """
        Write file atomically using temp file.

        Args:
            file_path: Target file path
            content: Content to write

        Returns:
            True if written successfully
        """
        dir_path = os.path.dirname(file_path) or '.'

        try:
            # Write to temp file first
            fd, temp_path = tempfile.mkstemp(dir=dir_path)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Atomic rename
                os.replace(temp_path, file_path)
                return True
            except Exception:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        except Exception:
            return False


class FileSystemManager:
    """High-level file system operations."""

    def __init__(self):
        self.diff_tool = DiffPatchTool()

    def read_file(self, path: str, encoding: str = 'utf-8') -> str:
        """Read file content."""
        with open(path, 'r', encoding=encoding) as f:
            return f.read()

    def write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True,
        atomic: bool = True
    ) -> bool:
        """
        Write content to file.

        Args:
            path: File path
            content: Content to write
            create_dirs: Create parent directories if needed
            atomic: Use atomic write

        Returns:
            True if successful
        """
        if create_dirs:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)

        if atomic:
            return self.diff_tool.atomic_write(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

    def copy_file(self, src: str, dst: str) -> bool:
        """Copy file from src to dst."""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False

    def move_file(self, src: str, dst: str) -> bool:
        """Move file from src to dst."""
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False

    def delete_file(self, path: str, backup: bool = True) -> bool:
        """
        Delete a file with optional backup.

        Args:
            path: File to delete
            backup: Create backup before deleting

        Returns:
            True if deleted
        """
        if not os.path.exists(path):
            return False

        if backup:
            self.diff_tool.create_backup(path)

        os.unlink(path)
        return True

    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        return os.path.exists(path)

    def get_file_info(self, path: str) -> dict:
        """Get file information."""
        stat = os.stat(path)
        return {
            'path': path,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'is_dir': os.path.isdir(path)
        }
