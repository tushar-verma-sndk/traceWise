import uuid
import yaml
from pathlib import Path
from datetime import datetime


def log_execution(
    base_path,
    program,
    oem,
    firmware_name,
    scope,
    platform,
    execution_payload,
    er_id=None,
    build="Official"
):

    firmware_folder = f"Firmware_{firmware_name}_{build}"
    firmware_path = Path(base_path) / program / oem / firmware_folder

    # Determine storage location
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

    target_path.mkdir(parents=True, exist_ok=True)

    iteration = execution_payload.get("execution_metadata", {}).get("iteration")
    test_name = execution_payload.get("test", {}).get("name")

    # ================================
    # CHECK FOR RE-RUN
    # ================================
    if iteration == "Re-Run":

        for exec_dir in target_path.glob("Execution_*"):

            yaml_file = exec_dir / "execution.yaml"

            if not yaml_file.exists():
                continue

            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            if data.get("test", {}).get("name") == test_name:

                # add history
                history = data.get("history", [])

                history.append({
                    "iteration": iteration,
                    "result": execution_payload["test"]["result"],
                    "ttf": execution_payload["test"].get("ttf_minutes"),
                    "timestamp": datetime.utcnow().isoformat()
                })

                data["history"] = history

                # update latest result
                data["test"]["result"] = execution_payload["test"]["result"]
                data["test"]["ttf_minutes"] = execution_payload["test"].get("ttf_minutes")

                data["execution_date_utc"] = datetime.utcnow().isoformat()

                with open(yaml_file, "w") as f:
                    yaml.dump(data, f, sort_keys=False)

                return True, f"Re-run updated: {exec_dir}"

    # ================================
    # NEW EXECUTION
    # ================================
    execution_id = f"Execution_{uuid.uuid4().hex[:8]}"
    execution_path = target_path / execution_id
    execution_path.mkdir(parents=True, exist_ok=True)

    execution_payload["execution_id"] = execution_id
    execution_payload["execution_date_utc"] = datetime.utcnow().isoformat()

    # initialize history
    execution_payload["history"] = [{
        "iteration": execution_payload.get("execution_metadata", {}).get("iteration"),
        "result": execution_payload["test"]["result"],
        "ttf": execution_payload["test"].get("ttf_minutes"),
        "timestamp": execution_payload["execution_date_utc"]
    }]

    yaml_path = execution_path / "execution.yaml"

    with open(yaml_path, "w") as f:
        yaml.dump(execution_payload, f, sort_keys=False)

    return True, f"Execution logged at {execution_path}"