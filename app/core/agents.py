import json
import re
from typing import Optional, List, Dict
from app.models.transcript import Transcript
from app.models.outputs import TopicsOut, DecisionsOut, ActionsOut, InsightsOut, FinalReportOut
from app.models.outputs import Topic, Decision, ActionItem, AttendeeInsight
from app.core.util_dates import resolve_due_date

JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)

SYSTEM_RULES = (
    "You are a specialized agent in a multi-agent meeting assistant.\n"
    "Return ONLY valid JSON that matches the schema. No markdown.\n"
    "Do not invent facts. If unsure, set fields null and confidence low.\n"
    "Use turn_refs/source_turn_refs to cite where info came from.\n"
)

def _strip_json(text: str) -> str:
    m = JSON_FENCE.search(text)
    return m.group(1).strip() if m else text.strip()

def _safe_json_load(text: str) -> dict:
    return json.loads(_strip_json(text))

def _transcript_payload(t: Transcript) -> dict:
    return {
        "meeting_id": t.meeting_id,
        "title": t.title,
        "meeting_date": t.meeting_date.isoformat(),
        "participants": t.participants,
        "turns": [{"idx": x.idx, "t": x.t, "speaker": x.speaker, "text": x.text} for x in t.turns],
    }



def _rule_topics(transcript: Transcript) -> TopicsOut:
    # group by keyword-ish buckets (budget, timeline, bug, hiring, release, etc.)
    buckets: Dict[str, List[int]] = {}
    keywords = [
        ("Bugs / Issues", ["bug", "error", "fail", "broken", "crash"]),
        ("Timeline / Dates", ["deadline", "due", "tuesday", "friday", "next week", "date"]),
        ("Release / Scope", ["release", "scope", "ship", "deploy"]),
        ("Tasks / Ownership", ["i will", "i'll", "assign", "take it", "owner"]),
        ("Risks / Blockers", ["blocked", "blocker", "risk", "waiting", "cannot"]),
    ]

    def pick_bucket(text: str) -> str:
        lt = text.lower()
        for title, ks in keywords:
            if any(k in lt for k in ks):
                return title
        return "General"

    for turn in transcript.turns:
        b = pick_bucket(turn.text)
        buckets.setdefault(b, []).append(turn.idx)

    topics: List[Topic] = []
    i = 1
    for title, refs in buckets.items():
        # short summary from first 1-2 turns
        sample = [transcript.turns[r].text for r in refs[:2]]
        summary = " / ".join(sample)[:250]
        topics.append(
            Topic(
                topic_id=f"T{i}",
                title=title,
                summary=summary if summary else "Discussion captured from transcript.",
                key_points=[],
                turn_refs=refs,
            )
        )
        i += 1

    return TopicsOut(topics=topics[:12])

def _rule_decisions(transcript: Transcript, topics: TopicsOut) -> DecisionsOut:
    decisions: List[Decision] = []
    patterns = [
        (re.compile(r"\bwe (agree|decided|will)\b", re.I), 0.75),
        (re.compile(r"\bagreed\b", re.I), 0.65),
        (re.compile(r"\bdecision\b", re.I), 0.7),
        (re.compile(r"\bapproved\b", re.I), 0.7),
    ]

    for turn in transcript.turns:
        for pat, conf in patterns:
            if pat.search(turn.text):
                decisions.append(
                    Decision(
                        decision_id=f"D{len(decisions)+1}",
                        statement=turn.text.strip(),
                        made_by=[turn.speaker] if turn.speaker != "Unknown" else [],
                        timestamp=turn.t,
                        rationale=None,
                        topic_id=None,
                        confidence=conf,
                        turn_refs=[turn.idx],
                    )
                )
                break

    return DecisionsOut(decisions=decisions[:30])

def _rule_actions(transcript: Transcript, topics: TopicsOut) -> ActionsOut:
    actions: List[ActionItem] = []
    # Detect simple ownership phrases
    owner_patterns = [
        re.compile(r"\b(i will|i'll|i can)\b", re.I),
        re.compile(r"\b(assign(ed)? to)\s+([A-Za-z][A-Za-z0-9_-]*)\b", re.I),
        re.compile(r"\b([A-Za-z][A-Za-z0-9_-]*)\s+will\b", re.I),
    ]

    for turn in transcript.turns:
        lt = turn.text.lower()
        if any(x in lt for x in ["i will", "i'll", "action item", "todo", "we need to", "assign"]):
            owner: Optional[str] = None
            if "i will" in lt or "i'll" in lt or "i can" in lt:
                owner = turn.speaker if turn.speaker != "Unknown" else None
            else:
                m = owner_patterns[1].search(turn.text)
                if m:
                    owner = m.group(3)

            due = resolve_due_date(turn.text, transcript.meeting_date)
            priority = "High" if any(x in lt for x in ["urgent", "asap", "block", "critical"]) else "Medium"

            actions.append(
                ActionItem(
                    action_id=f"A{len(actions)+1}",
                    task=turn.text.strip(),
                    owner=owner,
                    due_date=due,
                    priority=priority,
                    dependencies=[],
                    topic_id=None,
                    source_turn_refs=[turn.idx],
                    confidence=0.7 if owner else 0.45,
                )
            )

    return ActionsOut(action_items=actions[:50])

def _rule_insights(transcript: Transcript) -> InsightsOut:
    insights: List[AttendeeInsight] = []
    by_person: Dict[str, AttendeeInsight] = {}

    for turn in transcript.turns:
        p = turn.speaker
        if p == "Unknown":
            continue
        entry = by_person.get(p)
        if not entry:
            entry = AttendeeInsight(person=p, sentiment="Neutral", signals=[], blockers=[], open_questions=[], turn_refs=[])
            by_person[p] = entry

        lt = turn.text.lower()
        if any(x in lt for x in ["concern", "worried", "risk"]):
            entry.sentiment = "Concerned"
            entry.signals.append(turn.text.strip())
            entry.turn_refs.append(turn.idx)
        if any(x in lt for x in ["blocked", "waiting on", "can't", "cannot"]):
            entry.blockers.append(turn.text.strip())
            entry.turn_refs.append(turn.idx)
        if turn.text.strip().endswith("?"):
            entry.open_questions.append(turn.text.strip())
            entry.turn_refs.append(turn.idx)

    insights = list(by_person.values())
    return InsightsOut(attendee_insights=insights[:50])

#llm based agents
async def run_topic_agent(transcript: Transcript, llm) -> TopicsOut:
    if llm.mode_name == "rule_based":
        return _rule_topics(transcript)

    schema_hint = {
        "topics": [
            {
                "topic_id": "T1",
                "title": "Short title",
                "summary": "2-4 sentence summary",
                "key_points": ["..."],
                "turn_refs": [0, 1, 2],
            }
        ]
    }

    user = {
        "task": "Extract 5–12 topics from the meeting transcript. Group related turns. Keep titles short.",
        "schema": schema_hint,
        "transcript": _transcript_payload(transcript),
    }
    text = await llm.generate(SYSTEM_RULES, json.dumps(user))
    data = _safe_json_load(text)
    return TopicsOut.model_validate(data)

async def run_decision_agent(transcript: Transcript, topics: TopicsOut, llm) -> DecisionsOut:
    if llm.mode_name == "rule_based":
        return _rule_decisions(transcript, topics)

    schema_hint = {
        "decisions": [
            {
                "decision_id": "D1",
                "statement": "Decision text",
                "made_by": ["Alice", "Bob"],
                "timestamp": "00:01:35",
                "rationale": "Optional rationale",
                "topic_id": "T1",
                "confidence": 0.82,
                "turn_refs": [12, 13]
            }
        ]
    }

    user = {
        "task": "Extract explicit decisions only (agreement/approval/choice). Link each to the best matching topic_id.",
        "schema": schema_hint,
        "topics": topics.model_dump(),
        "transcript": _transcript_payload(transcript),
    }
    text = await llm.generate(SYSTEM_RULES, json.dumps(user))
    data = _safe_json_load(text)
    return DecisionsOut.model_validate(data)

async def run_action_agent(transcript: Transcript, topics: TopicsOut, llm) -> ActionsOut:
    if llm.mode_name == "rule_based":
        return _rule_actions(transcript, topics)

    schema_hint = {
        "action_items": [
            {
                "action_id": "A1",
                "task": "Do something",
                "owner": "Bob",
                "due_date": "2025-12-16",
                "priority": "High",
                "dependencies": [],
                "topic_id": "T1",
                "source_turn_refs": [13],
                "confidence": 0.86
            }
        ]
    }

    user = {
        "task": (
            "Extract actionable tasks. Prefer tasks with clear owner. "
            "If owner missing, set owner null and lower confidence. "
            "Resolve due dates to ISO using meeting_date as reference."
        ),
        "meeting_date": transcript.meeting_date.isoformat(),
        "schema": schema_hint,
        "topics": topics.model_dump(),
        "transcript": _transcript_payload(transcript),
    }
    text = await llm.generate(SYSTEM_RULES, json.dumps(user))
    data = _safe_json_load(text)
    return ActionsOut.model_validate(data)

async def run_insights_agent(transcript: Transcript, llm) -> InsightsOut:
    if llm.mode_name == "rule_based":
        return _rule_insights(transcript)

    schema_hint = {
        "attendee_insights": [
            {
                "person": "Chen",
                "sentiment": "Concerned",
                "signals": ["..."],
                "blockers": ["..."],
                "open_questions": ["..."],
                "turn_refs": [22, 23]
            }
        ]
    }

    user = {
        "task": (
            "For each participant, summarize concerns/blockers/open questions ONLY if supported by transcript. "
            "No personal judgments. Keep it professional."
        ),
        "schema": schema_hint,
        "transcript": _transcript_payload(transcript),
    }
    text = await llm.generate(SYSTEM_RULES, json.dumps(user))
    data = _safe_json_load(text)
    return InsightsOut.model_validate(data)
