
import time
from app.core.preprocess import preprocess_transcript
from app.core.llm_client import build_llm_client
from app.core.agents import (
    run_topic_agent,
    run_decision_agent,
    run_action_agent,
    run_insights_agent,
)
from app.core.merge import merge_report
from app.models.outputs import FinalReportOut
from app.models.transcript import Transcript

async def run_single_agent(title: str, meeting_date, transcript_text: str) -> FinalReportOut:
    """
    Single-agent baseline: executes all extraction agents sequentially
    with shared transcript context, then merges into FinalReportOut.
    """
    t0 = time.time()
    transcript: Transcript = preprocess_transcript(
        title=title,
        meeting_date=meeting_date,
        transcript_text=transcript_text,
    )

    llm = build_llm_client()
    topics = await run_topic_agent(transcript, llm)
    decisions = await run_decision_agent(transcript, topics, llm)
    actions = await run_action_agent(transcript, topics, llm)
    insights = await run_insights_agent(transcript, llm)

    final = merge_report(transcript, topics, decisions, actions, insights)
    latency_ms = int((time.time() - t0) * 1000)
    final.meta = {
        "latency_ms": latency_ms,
        "llm_mode": llm.mode_name,
        "meeting_id": transcript.meeting_id,
        "mode": "single_agent",
    }
    return final
