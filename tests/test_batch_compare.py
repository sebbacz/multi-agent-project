
import pytest
import httpx
from datetime import date
from app.main import app

@pytest.mark.asyncio
async def test_compare_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "Q1 Product Planning",
            "meeting_date": date.today().isoformat(),
            "transcript_text": "Alice: We agreed to ship next week.\nBob: I'll fix the bug by Friday."
        }
        r = await client.post("/analyze/compare", json=payload, timeout=30.0)
        assert r.status_code == 200
        data = r.json()
        assert "multi_agent" in data and "single_agent" in data
        for side in ["multi_agent", "single_agent"]:
            assert set(data[side].keys()) >= {"topics", "decisions", "action_items", "attendee_insights", "meta"}

@pytest.mark.asyncio
async def test_batch_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        items = [{
            "title": f"Meeting {i}",
            "meeting_date": date.today().isoformat(),
            "transcript_text": "Alice: We agreed to delay.\nChen: I'm waiting on design.\nBob: I'll update docs."
        } for i in range(5)]
        r = await client.post("/analyze/batch", json={"items": items}, timeout=60.0)
        assert r.status_code == 200
        batch = r.json()
        assert isinstance(batch, list)
        assert len(batch) == 5
        for report in batch:
            assert set(report.keys()) >= {"topics", "decisions", "action_items", "attendee_insights", "meta"}
