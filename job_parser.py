import re
from typing import Optional, Dict

# Pattern to extract message IDs like IEC130I, IEFC001I, IEF450I
MESSAGE_PATTERN = r'\b([A-Z]{3,4}\d{3}[A-Z])\b'

# Priority of error types (lower = higher priority)
PRIORITY = {
    "JCL_ERROR": 1,
    "DD_ERROR": 2,
    "ABEND": 3,
    "SORT_ERROR": 4,
    "IDCAMS_ERROR": 5,
    "OTHER": 99
}


def classify_message(msg_id: str) -> str:
    if msg_id.startswith("IEFC"):
        return "JCL_ERROR"
    elif msg_id.startswith("IEC"):
        return "DD_ERROR"
    elif msg_id.startswith("IEF450"):
        return "ABEND"
    elif msg_id.startswith("ICE"):
        return "SORT_ERROR"
    elif msg_id.startswith("IDC"):
        return "IDCAMS_ERROR"
    else:
        return "OTHER"


def extract_msg_id(line: str) -> Optional[str]:
    match = re.search(MESSAGE_PATTERN, line)
    return match.group(1) if match else None


def extract_step(lines, index: int) -> Optional[str]:
    """
    Try to find step name near the error line
    """
    for i in range(max(0, index - 3), min(len(lines), index + 3)):
        # Look for STEP pattern
        match = re.search(r'\bSTEP\d+\b', lines[i])
        if match:
            return match.group(0)
    return None


def extract_context(lines, index: int, window: int = 5) -> str:
    start = max(0, index - window)
    end = min(len(lines), index + window)
    return "\n".join(lines[start:end])


def parse_jes_log(log_text: str) -> Optional[Dict]:
    lines = log_text.split("\n")

    best_match = None

    for i, line in enumerate(lines):
        msg_id = extract_msg_id(line)

        if not msg_id:
            continue

        msg_type = classify_message(msg_id)

        if msg_type == "OTHER":
            continue

        current = {
            "type": msg_type,
            "message_id": msg_id,
            "message": line.strip(),
            "index": i
        }

        if (
            best_match is None or
            PRIORITY[msg_type] < PRIORITY[best_match["type"]]
        ):
            best_match = current

    if not best_match:
        return None

    # Extract step (only if not JCL error)
    step = None
    if best_match["type"] != "JCL_ERROR":
        step = extract_step(lines, best_match["index"])

    # Extract context
    context = extract_context(lines, best_match["index"])

    return {
        "type": best_match["type"],
        "message_id": best_match["message_id"],
        "message": best_match["message"],
        "step": step,
        "context": context
    }


# ------------------ TEST ------------------

if __name__ == "__main__":
    sample_log = """
    02.32.13 J0788299 RKTSW01I TS5502AS STEP1 1 00
    02.32.13 J0788299 RKTSW01I STEP2 2 00
    02.32.13 J0788299 IEC130I SYSPRINT DD STATEMENT MISSING
    02.32.13 J0788299 RKTSW01I STEP3 3 12
    02.32.13 J0788299 IEF404I TS5502AS - ENDED - TIME=02.32.13
    """

    result = parse_jes_log(sample_log)

    print("\nParsed Result:\n")
    print(result)
