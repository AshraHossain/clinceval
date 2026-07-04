"""Schema validation for golden_dataset.jsonl — bad rows fail fast, before an
eval run wastes 41 pipeline calls on a corrupt dataset."""
import json
from pathlib import Path

DATASET_VERSION = "1.0"  # bump on any case addition/removal/rewording

REQUIRED_FIELDS = ["id", "input", "expected_calculator", "category", "difficulty", "weight"]
VALID_CATEGORIES = {"core", "edge", "adversarial", "safety"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_WEIGHTS = {"normal", "high"}


def validate_case(case: dict, line_no: int) -> list[str]:
    errors = []
    for field in REQUIRED_FIELDS:
        if not case.get(field):
            errors.append(f"line {line_no} ({case.get('id', '?')}): missing '{field}'")
    if case.get("category") and case["category"] not in VALID_CATEGORIES:
        errors.append(f"line {line_no}: invalid category '{case['category']}'")
    if case.get("difficulty") and case["difficulty"] not in VALID_DIFFICULTIES:
        errors.append(f"line {line_no}: invalid difficulty '{case['difficulty']}'")
    if case.get("weight") and case["weight"] not in VALID_WEIGHTS:
        errors.append(f"line {line_no}: invalid weight '{case['weight']}'")
    if "must_cite" in case and not isinstance(case["must_cite"], list):
        errors.append(f"line {line_no}: must_cite must be a list")
    return errors


def validate_dataset(path: Path) -> list[str]:
    """Return all schema errors (empty list = valid). Also flags duplicate ids."""
    errors = []
    seen_ids = set()
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON ({exc})")
                continue
            errors.extend(validate_case(case, line_no))
            case_id = case.get("id")
            if case_id in seen_ids:
                errors.append(f"line {line_no}: duplicate id '{case_id}'")
            seen_ids.add(case_id)
    return errors
