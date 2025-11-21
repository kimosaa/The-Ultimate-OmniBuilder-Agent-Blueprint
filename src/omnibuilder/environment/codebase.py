"""
P2.1 Codebase Context Provider

Reads, indexes, and queries the entire project's file structure and content.
"""

import os
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from omnibuilder.models import FileInfo, CodeMatch


class FileTree:
    """Represents a directory tree structure."""

    def __init__(self, path: str, is_dir: bool = True):
        self.path = path
        self.name = os.path.basename(path) or path
        self.is_dir = is_dir
        self.children: List["FileTree"] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {"name": self.name, "path": self.path}
        if self.is_dir:
            result["children"] = [child.to_dict() for child in self.children]
        return result

    def to_string(self, prefix: str = "", is_last: bool = True) -> str:
        """Convert to tree string representation."""
        connector = "└── " if is_last else "├── "
        result = prefix + connector + self.name + "\n"

        if self.is_dir and self.children:
            extension = "    " if is_last else "│   "
            for i, child in enumerate(self.children):
                result += child.to_string(prefix + extension, i == len(self.children) - 1)

        return result


class CodebaseIndex:
    """Index of a codebase for efficient querying."""

    def __init__(self, root_path: str):
        self.root_path = root_path
        self.files: Dict[str, FileInfo] = {}
        self.symbols: Dict[str, List[str]] = {}  # symbol -> [file_paths]
        self.file_contents: Dict[str, str] = {}
        self.created_at = datetime.now()


class DependencyGraph:
    """Graph of file dependencies."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: List[str] = []
        self.imported_by: List[str] = []


class Definition:
    """A symbol definition location."""

    def __init__(self, symbol: str, file_path: str, line: int, content: str):
        self.symbol = symbol
        self.file_path = file_path
        self.line = line
        self.content = content


class CodebaseContextProvider:
    """Provides context about the codebase structure and content."""

    def __init__(self, root_path: str = "."):
        self.root_path = os.path.abspath(root_path)
        self._index: Optional[CodebaseIndex] = None
        self._ignore_patterns = [
            "*.pyc", "__pycache__", ".git", ".svn", "node_modules",
            "venv", ".venv", "*.egg-info", "dist", "build", ".tox",
            "*.so", "*.dylib", "*.dll", ".DS_Store"
        ]

    def index_codebase(self, root_path: Optional[str] = None) -> CodebaseIndex:
        """
        Index the entire project structure.

        Args:
            root_path: Optional override for root path

        Returns:
            CodebaseIndex with file information
        """
        root = root_path or self.root_path
        index = CodebaseIndex(root)

        for file_path in self._walk_files(root):
            rel_path = os.path.relpath(file_path, root)
            stat = os.stat(file_path)

            file_info = FileInfo(
                path=file_path,
                name=os.path.basename(file_path),
                extension=os.path.splitext(file_path)[1],
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                is_directory=False
            )

            index.files[rel_path] = file_info

            # Index content for text files
            if self._is_text_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        index.file_contents[rel_path] = content
                        self._extract_symbols(rel_path, content, index)
                except Exception:
                    pass

        self._index = index
        return index

    def _walk_files(self, root: str) -> List[str]:
        """Walk directory and return all files, respecting ignore patterns."""
        files = []

        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out ignored directories
            dirnames[:] = [
                d for d in dirnames
                if not any(fnmatch.fnmatch(d, p) for p in self._ignore_patterns)
            ]

            for filename in filenames:
                if not any(fnmatch.fnmatch(filename, p) for p in self._ignore_patterns):
                    files.append(os.path.join(dirpath, filename))

        return files

    def _is_text_file(self, file_path: str) -> bool:
        """Check if file is a text file."""
        text_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp',
            '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.html', '.css',
            '.json', '.yaml', '.yml', '.toml', '.md', '.txt', '.sh',
            '.sql', '.xml', '.vue', '.svelte'
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext in text_extensions

    def _extract_symbols(self, file_path: str, content: str, index: CodebaseIndex) -> None:
        """Extract symbols (functions, classes) from file content."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.py':
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('def '):
                    symbol = line[4:].split('(')[0].strip()
                    if symbol not in index.symbols:
                        index.symbols[symbol] = []
                    index.symbols[symbol].append(file_path)
                elif line.startswith('class '):
                    symbol = line[6:].split('(')[0].split(':')[0].strip()
                    if symbol not in index.symbols:
                        index.symbols[symbol] = []
                    index.symbols[symbol].append(file_path)

    def search_code(
        self,
        query: str,
        file_pattern: str = "*",
        path: Optional[str] = None
    ) -> List[CodeMatch]:
        """
        Search for code patterns in the codebase.

        Args:
            query: Search query (text or regex)
            file_pattern: Glob pattern for files to search
            path: Subdirectory to search in

        Returns:
            List of CodeMatch objects
        """
        if not self._index:
            self.index_codebase()

        matches = []
        search_root = path or self.root_path

        for rel_path, content in self._index.file_contents.items():
            full_path = os.path.join(self.root_path, rel_path)

            # Check path filter
            if path and not full_path.startswith(search_root):
                continue

            # Check file pattern
            if file_pattern != "*":
                if not fnmatch.fnmatch(os.path.basename(rel_path), file_pattern):
                    continue

            # Search content
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if query.lower() in line.lower():
                    # Get context
                    context_before = lines[max(0, i-2):i]
                    context_after = lines[i+1:min(len(lines), i+3)]

                    match = CodeMatch(
                        file_path=full_path,
                        line_number=i + 1,
                        content=line,
                        context_before=context_before,
                        context_after=context_after
                    )
                    matches.append(match)

        return matches

    def get_file_tree(self, path: Optional[str] = None, depth: int = -1) -> FileTree:
        """
        Get directory structure as a tree.

        Args:
            path: Starting path
            depth: Maximum depth (-1 for unlimited)

        Returns:
            FileTree representing the structure
        """
        root_path = path or self.root_path
        tree = FileTree(root_path, is_dir=True)
        self._build_tree(tree, depth, 0)
        return tree

    def _build_tree(self, node: FileTree, max_depth: int, current_depth: int) -> None:
        """Recursively build file tree."""
        if max_depth != -1 and current_depth >= max_depth:
            return

        if not os.path.isdir(node.path):
            return

        try:
            entries = sorted(os.listdir(node.path))
        except PermissionError:
            return

        for entry in entries:
            if any(fnmatch.fnmatch(entry, p) for p in self._ignore_patterns):
                continue

            full_path = os.path.join(node.path, entry)
            is_dir = os.path.isdir(full_path)
            child = FileTree(full_path, is_dir=is_dir)
            node.children.append(child)

            if is_dir:
                self._build_tree(child, max_depth, current_depth + 1)

    def analyze_dependencies(self, file_path: str) -> DependencyGraph:
        """
        Analyze imports/dependencies for a file.

        Args:
            file_path: Path to the file

        Returns:
            DependencyGraph with import information
        """
        graph = DependencyGraph(file_path)

        if not os.path.exists(file_path):
            return graph

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return graph

        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.py':
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import '):
                    module = line[7:].split(' ')[0].split('.')[0]
                    graph.imports.append(module)
                elif line.startswith('from '):
                    module = line[5:].split(' ')[0].split('.')[0]
                    graph.imports.append(module)

        return graph

    def get_symbol_definition(self, symbol: str) -> Optional[Definition]:
        """
        Find the definition of a symbol.

        Args:
            symbol: Symbol name to find

        Returns:
            Definition location or None
        """
        if not self._index:
            self.index_codebase()

        if symbol not in self._index.symbols:
            return None

        file_path = self._index.symbols[symbol][0]
        content = self._index.file_contents.get(
            os.path.relpath(file_path, self.root_path), ""
        )

        for i, line in enumerate(content.split('\n')):
            if symbol in line and ('def ' in line or 'class ' in line):
                return Definition(
                    symbol=symbol,
                    file_path=file_path,
                    line=i + 1,
                    content=line.strip()
                )

        return None

    def get_file_content(
        self,
        path: str,
        start_line: int = 0,
        end_line: int = -1
    ) -> str:
        """
        Read file content.

        Args:
            path: File path
            start_line: Starting line (0-indexed)
            end_line: Ending line (-1 for end of file)

        Returns:
            File content
        """
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if end_line == -1:
            end_line = len(lines)

        return ''.join(lines[start_line:end_line])
