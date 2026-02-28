
import os
import json
from datetime import date
import pytest
import httpx
from pathlib import Path
from app.main import app

@pytest.mark.asyncio
async def test_analyze():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    transcript_path = os.path.join(project_root, "sample_data", "transcript1.txt")

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/analyze",
            json={
                "title": "Q1 Product Planning",
                "meeting_date": date.today().isoformat(),
                "transcript_text": transcript,
            },
            timeout=30.0,
        )

    assert response.status_code == 200
    data = response.json()

    # export to file
    out_dir = Path(project_root) / "tests" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "analyze.json"
    out_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    for key in ["topics", "decisions", "action_items", "attendee_insights", "meta"]:
        assert key in data
    assert isinstance(data["topics"], list)
    assert isinstance(data["decisions"], list)
    assert isinstance(data["action_items"], list)
    assert isinstance(data["attendee_insights"], list)
