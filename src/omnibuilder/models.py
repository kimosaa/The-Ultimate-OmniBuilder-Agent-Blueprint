"""
Core data models and types for OmniBuilder.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Enums
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolCategory(str, Enum):
    CORE = "core"
    ENVIRONMENT = "environment"
    VERSION_CONTROL = "version_control"
    WEB_RESEARCH = "web_research"
    CLOUD = "cloud"
    DATA = "data"
    COMMUNICATION = "communication"
    VISUALIZATION = "visualization"
    DEBUGGING = "debugging"


# Core Models
class TaskStep(BaseModel):
    """A single step in a task execution plan."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = Field(default_factory=list)
    tool_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ExecutionPlan(BaseModel):
    """A complete execution plan for a task."""
    id: str
    goal: str
    steps: List[TaskStep]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_duration: Optional[int] = None  # in seconds


class ComplexityScore(BaseModel):
    """Score representing task complexity."""
    overall: float = Field(ge=0.0, le=10.0)
    cognitive: float = Field(ge=0.0, le=10.0)
    technical: float = Field(ge=0.0, le=10.0)
    time_estimate: int  # in minutes
    risk_level: RiskLevel


class Tool(BaseModel):
    """Represents an available tool/function."""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    required_params: List[str]
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False


class Context(BaseModel):
    """Current execution context."""
    task_id: str
    working_directory: str
    environment: Dict[str, str] = Field(default_factory=dict)
    recent_outputs: List[str] = Field(default_factory=list)
    error_history: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Memory(BaseModel):
    """A memory item for long-term storage."""
    id: str
    key: str
    value: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)
    access_count: int = 0


class ReasoningResult(BaseModel):
    """Result of a reasoning operation."""
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    chain_of_thought: List[str]
    evidence: List[str] = Field(default_factory=list)


class ErrorAnalysis(BaseModel):
    """Analysis of an error."""
    error_type: str
    root_cause: str
    suggested_fixes: List[str]
    related_errors: List[str] = Field(default_factory=list)
    severity: RiskLevel


class ExecutionResult(BaseModel):
    """Result of a command/tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    return_code: int = 0
    duration: float = 0.0  # in seconds


class FileInfo(BaseModel):
    """Information about a file."""
    path: str
    name: str
    extension: str
    size: int
    modified_at: datetime
    is_directory: bool = False


class CodeMatch(BaseModel):
    """A code search match."""
    file_path: str
    line_number: int
    content: str
    context_before: List[str] = Field(default_factory=list)
    context_after: List[str] = Field(default_factory=list)


class DiffResult(BaseModel):
    """Result of a diff operation."""
    original: str
    modified: str
    unified_diff: str
    additions: int
    deletions: int


class Message(BaseModel):
    """A message in the conversation history."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """Current state of the agent."""
    is_running: bool = False
    current_task: Optional[str] = None
    current_step: Optional[str] = None
    conversation_history: List[Message] = Field(default_factory=list)
    execution_plan: Optional[ExecutionPlan] = None
    context: Optional[Context] = None
