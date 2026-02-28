from typing import List, Tuple, Optional
import re
from datetime import date
from app.models.transcript import Transcript, Turn

SPEAKER_LINE = re.compile(r"^\s*(?P<speaker>[A-Za-z][A-Za-z0-9 _.-]{0,40})\s*:\s*(?P<text>.+)\s*$")
TIME_PREFIX = re.compile(r"^\s*\[(?P<t>\d{1,2}:\d{2}:\d{2})\]\s*(?P<rest>.*)$")

def _parse_lines(transcript_text: str) -> List[Tuple[str, str, Optional[str]]]:
    """
    Returns list of (speaker, text, timestamp)
    Accepts formats:
      [00:01:12] Alice: hello
      Alice: hello
    If no speaker is found, uses "Unknown".
    """
    out: List[Tuple[str, str, Optional[str]]] = []
    for raw in transcript_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        t = None
        m_time = TIME_PREFIX.match(line)
        if m_time:
            t = m_time.group("t")
            line = m_time.group("rest").strip()

        m = SPEAKER_LINE.match(line)
        if m:
            speaker = m.group("speaker").strip()
            text = m.group("text").strip()
        else:
            speaker = "Unknown"
            text = line

        out.append((speaker, text, t))
    return out

def preprocess_transcript(title: str, meeting_date: date, transcript_text: str) -> Transcript:
    parsed = _parse_lines(transcript_text)
    turns: List[Turn] = []
    participants_set = set()

    for i, (speaker, text, t) in enumerate(parsed):
        participants_set.add(speaker)
        turns.append(Turn(idx=i, speaker=speaker, text=text, t=t))

    participants = sorted(participants_set)
    return Transcript(title=title, meeting_date=meeting_date, participants=participants, turns=turns)
