import uuid
import yaml
from pathlib import Path
from datetime import datetime


def create_failure(
    base_path,
    program,
    oem,
    firmware_name,
    scope,
    platform,
    failure_data,
    er_id=None,
    build="Official"
):

    firmware_folder = f"Firmware_{firmware_name}_{build}"
    firmware_path = Path(base_path) / program / oem / firmware_folder

    if scope == "Official":
        target_path = firmware_path / "05_Logs" / platform
    else:
        target_path = (
            firmware_path
            / "04_Engineering_Requests_ERs"
            / f"ER_{er_id}"
            / "Logs"
            / platform
        )

    failure_id = f"Failure_{uuid.uuid4().hex[:8]}"
    failure_path = target_path / failure_id

    # Create folders
    (failure_path / "logs").mkdir(parents=True, exist_ok=True)
    (failure_path / "jtag").mkdir(parents=True, exist_ok=True)
    (failure_path / "xplorer").mkdir(parents=True, exist_ok=True)

    # Add timestamps
    failure_data["first_seen_utc"] = datetime.utcnow().isoformat()
    failure_data["last_seen_utc"] = datetime.utcnow().isoformat()

    # Save YAML
    yaml_path = failure_path / "failure_artifacts.yaml"

    with open(yaml_path, "w") as f:
        yaml.dump(failure_data, f, sort_keys=False)

    return True, f"Failure created at {failure_path}"