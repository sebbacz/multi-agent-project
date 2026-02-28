
from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import date
import time
import asyncio
from typing import List

from app.core.preprocess import preprocess_transcript
from app.core.llm_client import build_llm_client
from app.core.agents import (
    run_topic_agent,
    run_decision_agent,
    run_action_agent,
    run_insights_agent,
)
from app.core.merge import merge_report
from app.core.single_agent import run_single_agent
from app.models.outputs import FinalReportOut

router = APIRouter()

class AnalyzeRequest(BaseModel):
    title: str = Field(default="Meeting")
    meeting_date: date
    transcript_text: str

class BatchAnalyzeRequest(BaseModel):
    items: List[AnalyzeRequest]

class CompareOut(BaseModel):
    multi_agent: FinalReportOut
    single_agent: FinalReportOut

@router.post("/analyze", response_model=FinalReportOut)
async def analyze(req: AnalyzeRequest) -> FinalReportOut:
    t0 = time.time()
    transcript = preprocess_transcript(
        title=req.title,
        meeting_date=req.meeting_date,
        transcript_text=req.transcript_text,
    )
    llm = build_llm_client()

    # Parallel execution of agents
    topics = await run_topic_agent(transcript, llm)
    decisions_task = run_decision_agent(transcript, topics, llm)
    actions_task = run_action_agent(transcript, topics, llm)
    insights_task = run_insights_agent(transcript, llm)
    decisions, actions, insights = await asyncio.gather(decisions_task, actions_task, insights_task)

    final = merge_report(transcript, topics, decisions, actions, insights)
    latency_ms = int((time.time() - t0) * 1000)
    final.meta = {
        "latency_ms": latency_ms,
        "llm_mode": llm.mode_name,
        "meeting_id": transcript.meeting_id,
        "mode": "multi_agent",
    }
    return final

@router.post("/analyze/batch", response_model=List[FinalReportOut])
async def analyze_batch(req: BatchAnalyzeRequest) -> List[FinalReportOut]:
    """
    Process 5–10 transcripts in one call. Each item uses the multi-agent pipeline.
    """
    async def run_one(item: AnalyzeRequest) -> FinalReportOut:
        return await analyze(item)

    # Limit batch size to prevent overload
    items = req.items[:10]
    return await asyncio.gather(*[run_one(it) for it in items])

@router.post("/analyze/compare", response_model=CompareOut)
async def analyze_compare(req: AnalyzeRequest) -> CompareOut:
    """
    Returns both multi-agent and single-agent outputs for the same input.
    Enables evaluation and deliverables comparison.
    """
    multi = await analyze(req)
    single = await run_single_agent(req.title, req.meeting_date, req.transcript_text)
    return CompareOut(multi_agent=multi, single_agent=single)
