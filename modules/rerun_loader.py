from pathlib import Path
import yaml


def load_last_execution(
    base_path,
    program,
    oem,
    firmware,
    platform,
    test_name
):

    firmware_path = (
        Path(base_path)
        / program
        / oem
        / f"Firmware_{firmware}_Official"
        / "05_Logs"
        / platform
    )

    if not firmware_path.exists():
        return None

    executions = []

    for exec_dir in firmware_path.glob("Execution_*"):

        yaml_file = exec_dir / "execution.yaml"

        if not yaml_file.exists():
            continue

        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        if data.get("test", {}).get("name") == test_name:
            executions.append(data)

    if not executions:
        return None

    # return latest
    executions.sort(
        key=lambda x: x.get("execution_date_utc",""),
        reverse=True
    )

    return executions[0]