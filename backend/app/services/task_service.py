import re
from typing import List, Dict

TASK_PATTERNS = [
    r"\b(todo|task|action item):?\s*(.+)$",
    r"\bdue (on )?(?P<date>\d{4}-\d{2}-\d{2})\b",
]


def extract_tasks_from_text(text: str) -> List[Dict]:
    results = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for pat in TASK_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                entry = {"line": i + 1, "text": line.strip(), "match": m.group(0)}
                results.append(entry)
    # Also look for simple checklist hyphen items
    checklist = re.findall(r"^-\s+\[?\s?\]?\s*(.+)$", text, re.MULTILINE)
    for c in checklist:
        results.append({"line": None, "text": c.strip(), "match": c.strip()})
    return results
