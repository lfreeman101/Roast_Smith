import re
from typing import List, Tuple
DETECTOR_PATTERNS=[
    ('all_white', re.compile(r"\ball\s*white\b|\bwhites?\s*only\b", re.I)),
    ('iq_bait', re.compile(r"\bIQ\b|\blow\s*IQ\b|\bnot\s*smart\b|\bbrain(s| size)?\b", re.I)),
    ('crime_stats', re.compile(r"\b(FBI|UCR|crime|statistics?)\b|\brate(s)?\b.*\b(crime|violence)\b|\bper\s*capita\b", re.I)),
]
def detect(insult: str) -> List[str]:
    hits=[]
    for did,pat in DETECTOR_PATTERNS:
        if pat.search(insult or ''): hits.append(did)
    return hits[:2]
