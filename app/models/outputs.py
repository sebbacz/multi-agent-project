from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class Topic(BaseModel):
    topic_id: str
    title: str
    summary: str
    key_points: List[str] = Field(default_factory=list)
    turn_refs: List[int] = Field(default_factory=list)

class TopicsOut(BaseModel):
    topics: List[Topic] = Field(default_factory=list)

class Decision(BaseModel):
    decision_id: str
    statement: str
    made_by: List[str] = Field(default_factory=list)
    timestamp: Optional[str] = None
    rationale: Optional[str] = None
    topic_id: Optional[str] = None
    confidence: float = Field(ge=0, le=1, default=0.5)
    turn_refs: List[int] = Field(default_factory=list)

class DecisionsOut(BaseModel):
    decisions: List[Decision] = Field(default_factory=list)

Priority = Literal["Low", "Medium", "High"]

class ActionItem(BaseModel):
    action_id: str
    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None  # ISO "YYYY-MM-DD"
    priority: Priority = "Medium"
    dependencies: List[str] = Field(default_factory=list)
    topic_id: Optional[str] = None
    source_turn_refs: List[int] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)

class ActionsOut(BaseModel):
    action_items: List[ActionItem] = Field(default_factory=list)

class AttendeeInsight(BaseModel):
    person: str
    sentiment: Optional[str] = None
    signals: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    turn_refs: List[int] = Field(default_factory=list)

class InsightsOut(BaseModel):
    attendee_insights: List[AttendeeInsight] = Field(default_factory=list)

class FinalReportOut(BaseModel):
    topics: List[Topic] = Field(default_factory=list)
    decisions: List[Decision] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    attendee_insights: List[AttendeeInsight] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
