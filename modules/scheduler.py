import json
from pathlib import Path
from datetime import datetime
import uuid

SCHEDULER_FILE = "scheduled_tests.json"

def load_scheduled_tests(base_path: str) -> dict:
    """Load all scheduled tests from JSON file."""
    scheduler_path = Path(base_path) / SCHEDULER_FILE
    if scheduler_path.exists():
        try:
            with open(scheduler_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"scheduled": []}
    return {"scheduled": []}

def save_scheduled_tests(base_path: str, data: dict):
    """Save scheduled tests to JSON file."""
    scheduler_path = Path(base_path) / SCHEDULER_FILE
    with open(scheduler_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def add_scheduled_entry(base_path: str, entry: dict) -> str:
    """Add a new scheduled test entry with IN_PROGRESS status."""
    data = load_scheduled_tests(base_path)
    entry_id = str(uuid.uuid4())[:8]
    entry["id"] = entry_id
    entry["execution_id"] = f"SCHED_{entry_id}"
    entry["created_at"] = datetime.now().isoformat()
    entry["status"] = "IN_PROGRESS"  # Set to IN_PROGRESS by default
    entry["result"] = "IN_PROGRESS"
    data["scheduled"].append(entry)
    save_scheduled_tests(base_path, data)
    return entry_id

def remove_scheduled_entry(base_path: str, entry_id: str):
    """Remove a scheduled entry by ID."""
    data = load_scheduled_tests(base_path)
    data["scheduled"] = [e for e in data["scheduled"] if e.get("id") != entry_id and e.get("execution_id") != entry_id]
    save_scheduled_tests(base_path, data)

def update_scheduled_entry_status(base_path: str, entry_id: str, status: str, additional_data: dict = None):
    """Update status of a scheduled entry."""
    data = load_scheduled_tests(base_path)
    for entry in data["scheduled"]:
        if entry.get("id") == entry_id or entry.get("execution_id") == entry_id:
            entry["status"] = status
            entry["result"] = status
            entry["updated_at"] = datetime.now().isoformat()
            if additional_data:
                entry.update(additional_data)
            break
    save_scheduled_tests(base_path, data)

def get_scheduled_by_platform(base_path: str, platform: str = None) -> list:
    """Get scheduled tests, optionally filtered by platform."""
    data = load_scheduled_tests(base_path)
    if platform:
        return [e for e in data["scheduled"] if e.get("platform") == platform]
    return data["scheduled"]

def get_platform_schedule_summary(base_path: str) -> dict:
    """Get summary of scheduled tests grouped by platform."""
    data = load_scheduled_tests(base_path)
    summary = {}
    for entry in data["scheduled"]:
        platform = entry.get("platform", "Unknown")
        if platform not in summary:
            summary[platform] = {
                "total": 0,
                "scheduled": 0,
                "in_progress": 0,
                "completed": 0,
                "passed": 0,
                "failed": 0,
                "entries": []
            }
        summary[platform]["total"] += 1
        status = entry.get("status", "IN_PROGRESS")
        if status == "SCHEDULED":
            summary[platform]["scheduled"] += 1
        elif status == "IN_PROGRESS":
            summary[platform]["in_progress"] += 1
        elif status == "PASS":
            summary[platform]["completed"] += 1
            summary[platform]["passed"] += 1
        elif status == "FAIL":
            summary[platform]["completed"] += 1
            summary[platform]["failed"] += 1
        summary[platform]["entries"].append(entry)
    return summary

def get_all_scheduled_as_dataframe_records(base_path: str) -> list:
    """Get all scheduled tests as records that can be merged with execution dataframe."""
    data = load_scheduled_tests(base_path)
    records = []
    for entry in data["scheduled"]:
        # Get classification data if exists
        classification = entry.get("classification", {})
        analysis = entry.get("analysis", {})
        
        record = {
            "Execution ID": entry.get("execution_id", entry.get("id")),
            "Program": entry.get("program", "N/A"),
            "OEM": entry.get("oem", "N/A"),
            "Firmware": entry.get("firmware", "N/A"),
            "Platform": entry.get("platform", "N/A"),
            "Test Name": entry.get("test_name", "N/A"),
            "Test Category": entry.get("test_category", "N/A"),
            "Iteration": entry.get("iteration", "N/A"),
            "Result": entry.get("status", "IN_PROGRESS"),
            "Capacity": entry.get("capacity", "N/A"),
            "Form Factor": entry.get("form_factor", "N/A"),
            "Run Type": "Scheduled",
            "Severity": classification.get("severity", entry.get("severity", "")),
            "Failure Type": classification.get("failure_type", ""),
            "Failure Stage": classification.get("failure_stage", ""),
            "Regression": classification.get("regression", ""),
            "Reproducibility": classification.get("reproducibility", ""),
            "TTF (min)": entry.get("ttf_minutes", ""),
            "Windows": "",
            "Execution Date": entry.get("created_at", datetime.now().isoformat()),
            "Is Scheduled": True
        }
        records.append(record)
    return records