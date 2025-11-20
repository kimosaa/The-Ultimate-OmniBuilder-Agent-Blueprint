"""
P3.1 Version Control Tools

Git operations and code management.
"""

import os
from typing import List, Optional

from omnibuilder.models import ExecutionResult


class CloneResult:
    """Result of a git clone operation."""
    def __init__(self, success: bool, path: str, message: str):
        self.success = success
        self.path = path
        self.message = message


class CommitResult:
    """Result of a git commit operation."""
    def __init__(self, success: bool, hash: str, message: str):
        self.success = success
        self.hash = hash
        self.message = message


class PushResult:
    """Result of a git push operation."""
    def __init__(self, success: bool, remote: str, branch: str, message: str):
        self.success = success
        self.remote = remote
        self.branch = branch
        self.message = message


class PullResult:
    """Result of a git pull operation."""
    def __init__(self, success: bool, message: str, changes: int = 0):
        self.success = success
        self.message = message
        self.changes = changes


class BranchResult:
    """Result of a branch operation."""
    def __init__(self, success: bool, name: str, message: str):
        self.success = success
        self.name = name
        self.message = message


class StatusResult:
    """Result of git status."""
    def __init__(self, branch: str, staged: List[str], modified: List[str], untracked: List[str]):
        self.branch = branch
        self.staged = staged
        self.modified = modified
        self.untracked = untracked


class PRResult:
    """Result of creating a pull request."""
    def __init__(self, success: bool, number: int, url: str, message: str):
        self.success = success
        self.number = number
        self.url = url
        self.message = message


class GitTools:
    """Git version control operations."""

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    async def git_clone(
        self,
        repo_url: str,
        dest: str,
        branch: Optional[str] = None
    ) -> CloneResult:
        """Clone a repository."""
        import asyncio

        cmd = f"git clone {repo_url} {dest}"
        if branch:
            cmd = f"git clone -b {branch} {repo_url} {dest}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        return CloneResult(
            success=process.returncode == 0,
            path=os.path.join(self.working_dir, dest),
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def git_commit(
        self,
        message: str,
        files: Optional[List[str]] = None
    ) -> CommitResult:
        """Commit changes."""
        import asyncio

        # Stage files
        if files:
            for file in files:
                await asyncio.create_subprocess_shell(
                    f"git add {file}",
                    cwd=self.working_dir
                )
        else:
            await asyncio.create_subprocess_shell(
                "git add -A",
                cwd=self.working_dir
            )

        # Commit
        process = await asyncio.create_subprocess_shell(
            f'git commit -m "{message}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        # Get commit hash
        hash_process = await asyncio.create_subprocess_shell(
            "git rev-parse HEAD",
            stdout=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        hash_out, _ = await hash_process.communicate()

        return CommitResult(
            success=process.returncode == 0,
            hash=hash_out.decode().strip() if process.returncode == 0 else "",
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def git_push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None
    ) -> PushResult:
        """Push to remote."""
        import asyncio

        cmd = f"git push {remote}"
        if branch:
            cmd = f"git push {remote} {branch}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        return PushResult(
            success=process.returncode == 0,
            remote=remote,
            branch=branch or "current",
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def git_pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None
    ) -> PullResult:
        """Pull from remote."""
        import asyncio

        cmd = f"git pull {remote}"
        if branch:
            cmd = f"git pull {remote} {branch}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        return PullResult(
            success=process.returncode == 0,
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def git_branch(
        self,
        name: str,
        checkout: bool = True
    ) -> BranchResult:
        """Create and optionally checkout a branch."""
        import asyncio

        if checkout:
            cmd = f"git checkout -b {name}"
        else:
            cmd = f"git branch {name}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        return BranchResult(
            success=process.returncode == 0,
            name=name,
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def git_status(self) -> StatusResult:
        """Get repository status."""
        import asyncio

        # Get current branch
        branch_process = await asyncio.create_subprocess_shell(
            "git branch --show-current",
            stdout=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        branch_out, _ = await branch_process.communicate()
        branch = branch_out.decode().strip()

        # Get status
        process = await asyncio.create_subprocess_shell(
            "git status --porcelain",
            stdout=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, _ = await process.communicate()

        staged = []
        modified = []
        untracked = []

        for line in stdout.decode().splitlines():
            if len(line) >= 3:
                status = line[:2]
                file = line[3:]

                if status[0] in ['A', 'M', 'D', 'R']:
                    staged.append(file)
                if status[1] == 'M':
                    modified.append(file)
                if status == '??':
                    untracked.append(file)

        return StatusResult(
            branch=branch,
            staged=staged,
            modified=modified,
            untracked=untracked
        )

    async def git_diff(
        self,
        ref1: Optional[str] = None,
        ref2: Optional[str] = None
    ) -> str:
        """Get diff between refs."""
        import asyncio

        if ref1 and ref2:
            cmd = f"git diff {ref1} {ref2}"
        elif ref1:
            cmd = f"git diff {ref1}"
        else:
            cmd = "git diff"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, _ = await process.communicate()
        return stdout.decode()

    async def create_pull_request(
        self,
        title: str,
        body: str,
        base: str,
        head: str
    ) -> PRResult:
        """Create a pull request using gh CLI."""
        import asyncio

        cmd = f'gh pr create --title "{title}" --body "{body}" --base {base} --head {head}'

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            # Parse PR URL to get number
            url = stdout.decode().strip()
            number = int(url.split('/')[-1]) if '/' in url else 0
            return PRResult(
                success=True,
                number=number,
                url=url,
                message="Pull request created"
            )
        else:
            return PRResult(
                success=False,
                number=0,
                url="",
                message=stderr.decode()
            )

    async def git_stash(
        self,
        action: str = "push",
        message: Optional[str] = None
    ) -> ExecutionResult:
        """Manage git stash."""
        import asyncio

        if action == "push" and message:
            cmd = f'git stash push -m "{message}"'
        else:
            cmd = f"git stash {action}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.working_dir
        )
        stdout, stderr = await process.communicate()

        return ExecutionResult(
            success=process.returncode == 0,
            output=stdout.decode(),
            error=stderr.decode() if stderr else None,
            return_code=process.returncode
        )
