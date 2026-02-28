"""
Centralized prompt templates for LLM agents.
"""

SYSTEM_BASE = """You are a specialized agent in a multi-agent meeting assistant.
Return ONLY valid JSON that matches the schema provided.
Do not include markdown code fences or explanations.
Do not invent facts. If unsure, set fields to null and confidence low.
Use turn_refs/source_turn_refs to cite where information came from."""

TOPIC_AGENT_TASK = """Extract 5–12 main topics from the meeting transcript.
Group related turns together.
Keep titles short and descriptive.
Provide 2-4 sentence summaries.
Include key points mentioned for each topic."""

DECISION_AGENT_TASK = """Extract explicit decisions only (agreements, approvals, choices).
Look for phrases like "we agreed", "decided to", "approved".
Link each decision to the best matching topic_id from the provided topics.
Include who made the decision and their rationale if mentioned."""

ACTION_AGENT_TASK = """Extract actionable tasks with clear owners when possible.
If no owner is mentioned, set owner to null and lower confidence.
Resolve relative due dates (like "next Tuesday") to ISO format using meeting_date as reference.
Identify priority based on language (urgent, ASAP, etc.).
Mark dependencies between action items if mentioned."""

INSIGHTS_AGENT_TASK = """For each participant, summarize:
- Overall sentiment (Positive/Neutral/Concerned/Negative)
- Signals: key contributions or concerns they raised
- Blockers: obstacles they mentioned
- Open questions: questions they asked that weren't resolved

Only include insights supported by the transcript.
No personal judgments or assumptions.
Keep it professional and factual."""

def get_topic_prompt() -> dict:
    return {
        "system": SYSTEM_BASE,
        "task": TOPIC_AGENT_TASK,
    }

def get_decision_prompt() -> dict:
    return {
        "system": SYSTEM_BASE,
        "task": DECISION_AGENT_TASK,
    }

def get_action_prompt() -> dict:
    return {
        "system": SYSTEM_BASE,
        "task": ACTION_AGENT_TASK,
    }

def get_insights_prompt() -> dict:
    return {
        "system": SYSTEM_BASE,
        "task": INSIGHTS_AGENT_TASK,
    }
