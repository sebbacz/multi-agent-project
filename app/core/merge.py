from typing import List, Optional, Tuple
import re

from app.models.transcript import Transcript
from app.models.outputs import TopicsOut, DecisionsOut, ActionsOut, InsightsOut, FinalReportOut, ActionItem, Decision

def _overlap(a: List[int], b: List[int]) -> int:
    return len(set(a).intersection(b))

def _link_topic_id(turn_refs: List[int], topics: TopicsOut) -> Optional[str]:
    best = None
    best_score = 0
    for t in topics.topics:
        score = _overlap(turn_refs, t.turn_refs)
        if score > best_score:
            best_score = score
            best = t.topic_id
    return best if best_score > 0 else None

def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def _similar(a: str, b: str) -> float:
    ta = set(_norm(a).split())
    tb = set(_norm(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))

def _dedupe_actions(items: List[ActionItem]) -> List[ActionItem]:
    kept: List[ActionItem] = []
    for it in items:
        merged = False
        for j, ex in enumerate(kept):
            # same owner (or both None) + similar text
            if (it.owner == ex.owner) and _similar(it.task, ex.task) >= 0.65:
                # keep higher confidence, but merge refs/due date if missing
                better, worse = (it, ex) if it.confidence >= ex.confidence else (ex, it)
                combined_refs = sorted(set(better.source_turn_refs + worse.source_turn_refs))
                due = better.due_date or worse.due_date
                kept[j] = better.model_copy(update={"source_turn_refs": combined_refs, "due_date": due})
                merged = True
                break
        if not merged:
            kept.append(it)
    return kept

def merge_report(
    transcript: Transcript,
    topics: TopicsOut,
    decisions: DecisionsOut,
    actions: ActionsOut,
    insights: InsightsOut,
) -> FinalReportOut:

    # Link topic_id if missing
    linked_decisions: List[Decision] = []
    for d in decisions.decisions:
        if not d.topic_id:
            d = d.model_copy(update={"topic_id": _link_topic_id(d.turn_refs, topics)})
        linked_decisions.append(d)

    linked_actions: List[ActionItem] = []
    for a in actions.action_items:
        if not a.topic_id:
            a = a.model_copy(update={"topic_id": _link_topic_id(a.source_turn_refs, topics)})
        linked_actions.append(a)

    # Dedupe action items
    linked_actions = _dedupe_actions(linked_actions)

    return FinalReportOut(
        topics=topics.topics,
        decisions=linked_decisions,
        action_items=linked_actions,
        attendee_insights=insights.attendee_insights,
        meta={},
    )
