# Multi-Agent Meeting Assistant

# Author: Sebastian Gondek

## Overview
A FastAPI service that processes meeting transcripts using a multi\-agent pipeline to extract:
- Topics
- Decisions
- Action items (owner, due date, priority)
- Attendee insights (sentiment, blockers, questions)

Supports a single\-agent baseline for comparison and batch processing of transcripts.

## Architecture
- `app/core/preprocess.py`: Parses transcript text into structured turns.
- `app/core/agents.py`: Rule\-based and LLM\-based agents for topics, decisions, actions, insights.
- `app/core/merge.py`: Links items to topics and deduplicates action items.
- `app/core/llm_client.py`: Wraps OpenAI Responses API; falls back to rule\-based mode if no API key.
- `app/routes/analyze.py`: FastAPI routes for analyze, batch, and compare.
- `app/models/outputs.py`: Pydantic models for structured outputs.
- `app/core/config.py`: Settings via `.env`.

## Endpoints
- `POST /analyze`
  - Request: `{ title, meeting_date, transcript_text }`
  - Response: `FinalReportOut` with topics, decisions, action items, insights, meta.
- `POST /analyze/batch`
  - Request: `{ items: AnalyzeRequest[] }` (max 10)
  - Response: `FinalReportOut[]`
- `POST /analyze/compare`
  - Request: `AnalyzeRequest`
  - Response: `{ multi_agent: FinalReportOut, single_agent: FinalReportOut }`

## Installation
- Install dependencies:
  - `pip install -r requirements.txt`

## Configuration
- Create `.env` with:
  - `OPENAI_API_KEY` \- optional; if missing, runs in rule\-based mode
  - `OPENAI_MODEL` \- default `gpt\-4o\-mini`

## Running
- Start server:
  - `uvicorn app.main:app --reload`
- Swagger UI:
  - `http://127.0.0.1:8000/docs`

## Data Models
- `FinalReportOut`:
  - `topics: Topic[]`
  - `decisions: Decision[]`
  - `action_items: ActionItem[]`
  - `attendee_insights: AttendeeInsight[]`
  - `meta: { latency_ms, llm_mode, meeting_id, mode }`

## LLM Modes
- Rule\-based: deterministic heuristics for extraction.
- OpenAI Responses API: `OpenAIResponsesLLM` when `OPENAI_API_KEY` is present.

## Testing
- `pytest`
- `tests/conftest.py` sets project root on `sys.path`.
- Sample structured output: `tests/out/analyze.json`.

