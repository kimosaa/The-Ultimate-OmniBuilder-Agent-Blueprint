"""
P3.5 Communication Tools

Messaging and notification operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class SendResult:
    """Result of a send operation."""
    def __init__(self, success: bool, message_id: str, message: str):
        self.success = success
        self.message_id = message_id
        self.message = message


class EventResult:
    """Result of creating a calendar event."""
    def __init__(self, success: bool, event_id: str, url: str, message: str):
        self.success = success
        self.event_id = event_id
        self.url = url
        self.message = message


class IssueResult:
    """Result of creating an issue."""
    def __init__(self, success: bool, issue_id: int, url: str, message: str):
        self.success = success
        self.issue_id = issue_id
        self.url = url
        self.message = message


class CommentResult:
    """Result of creating a comment."""
    def __init__(self, success: bool, comment_id: int, message: str):
        self.success = success
        self.comment_id = comment_id
        self.message = message


class CommunicationTools:
    """Communication and notification tools."""

    def __init__(self):
        self._email_config: Dict[str, str] = {}
        self._slack_token: Optional[str] = None

    def configure_email(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str
    ) -> None:
        """Configure email settings."""
        self._email_config = {
            "host": smtp_host,
            "port": str(smtp_port),
            "username": username,
            "password": password
        }

    def configure_slack(self, token: str) -> None:
        """Configure Slack bot token."""
        self._slack_token = token

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> SendResult:
        """
        Send an email.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            attachments: List of file paths to attach
        """
        if not self._email_config:
            return SendResult(False, "", "Email not configured")

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os

            msg = MIMEMultipart()
            msg['From'] = self._email_config['username']
            msg['To'] = to
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(filepath)}'
                            )
                            msg.attach(part)

            # Send email
            with smtplib.SMTP(
                self._email_config['host'],
                int(self._email_config['port'])
            ) as server:
                server.starttls()
                server.login(
                    self._email_config['username'],
                    self._email_config['password']
                )
                server.send_message(msg)

            return SendResult(True, "", "Email sent successfully")

        except Exception as e:
            return SendResult(False, "", str(e))

    async def send_slack(
        self,
        channel: str,
        message: str,
        blocks: Optional[List[Dict]] = None
    ) -> SendResult:
        """
        Send Slack message.

        Args:
            channel: Channel ID or name
            message: Message text
            blocks: Slack blocks for rich formatting
        """
        if not self._slack_token:
            return SendResult(False, "", "Slack not configured")

        try:
            import httpx

            payload = {
                "channel": channel,
                "text": message
            }

            if blocks:
                payload["blocks"] = blocks

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {self._slack_token}"},
                    json=payload
                )
                data = response.json()

                if data.get("ok"):
                    return SendResult(
                        True,
                        data.get("ts", ""),
                        "Message sent"
                    )
                else:
                    return SendResult(
                        False,
                        "",
                        data.get("error", "Unknown error")
                    )

        except Exception as e:
            return SendResult(False, "", str(e))

    async def create_calendar_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: Optional[List[str]] = None,
        description: str = ""
    ) -> EventResult:
        """
        Create a calendar event.

        Note: Requires calendar API integration.
        """
        # Placeholder - would integrate with Google Calendar, Outlook, etc.
        import uuid

        event_id = str(uuid.uuid4())

        return EventResult(
            success=True,
            event_id=event_id,
            url=f"calendar://event/{event_id}",
            message=f"Event '{title}' created (placeholder)"
        )

    async def send_notification(
        self,
        title: str,
        body: str,
        priority: str = "normal"
    ) -> bool:
        """
        Send system notification.

        Args:
            title: Notification title
            body: Notification body
            priority: Priority level
        """
        try:
            import subprocess

            # macOS
            subprocess.run([
                "osascript", "-e",
                f'display notification "{body}" with title "{title}"'
            ], check=False)

            return True
        except Exception:
            # Fallback to print
            print(f"[{priority.upper()}] {title}: {body}")
            return True

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> IssueResult:
        """
        Create GitHub issue.

        Args:
            repo: Repository (owner/repo)
            title: Issue title
            body: Issue body
            labels: Issue labels
        """
        import asyncio

        label_args = ""
        if labels:
            label_args = " ".join(f'--label "{l}"' for l in labels)

        cmd = f'gh issue create --repo {repo} --title "{title}" --body "{body}" {label_args}'

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            url = stdout.decode().strip()
            issue_id = int(url.split('/')[-1]) if '/' in url else 0

            return IssueResult(
                success=True,
                issue_id=issue_id,
                url=url,
                message="Issue created"
            )
        else:
            return IssueResult(
                success=False,
                issue_id=0,
                url="",
                message=stderr.decode()
            )

    async def comment_on_pr(
        self,
        repo: str,
        pr_number: int,
        comment: str
    ) -> CommentResult:
        """
        Comment on a pull request.

        Args:
            repo: Repository (owner/repo)
            pr_number: PR number
            comment: Comment text
        """
        import asyncio

        cmd = f'gh pr comment {pr_number} --repo {repo} --body "{comment}"'

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return CommentResult(
            success=process.returncode == 0,
            comment_id=0,
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )
