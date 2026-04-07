import yaml
from pathlib import Path
import pandas as pd
import uuid


def build_execution_index(base_path):
    records = []
    base = Path(base_path)

    if not base.exists():
        return pd.DataFrame()

    for program_dir in base.iterdir():
        if not program_dir.is_dir():
            continue

        for oem_dir in program_dir.iterdir():
            if not oem_dir.is_dir():
                continue

            for firmware_dir in oem_dir.glob("Firmware_*_Official"):
                firmware_name = firmware_dir.name.replace("Firmware_", "").replace("_Official", "")

                # Official logs
                logs_path = firmware_dir / "05_Logs"
                if logs_path.exists():
                    scan_logs(
                        logs_path,
                        records,
                        program_dir.name,
                        oem_dir.name,
                        firmware_name,
                        er_id=None,
                    )

                # ER logs
                er_root = firmware_dir / "04_Engineering_Requests_ERs"
                if er_root.exists():
                    for er_dir in er_root.glob("ER_*"):
                        er_logs = er_dir / "Logs"
                        if er_logs.exists():
                            scan_logs(
                                er_logs,
                                records,
                                program_dir.name,
                                oem_dir.name,
                                firmware_name,
                                er_id=er_dir.name.replace("ER_", ""),
                            )

    if records:
        df = pd.DataFrame(records)
        df["Execution Date"] = pd.to_datetime(
            df["Execution Date"], errors="coerce"
        )
        return df.sort_values(by="Execution Date", ascending=False)
    else:
        return pd.DataFrame()


def scan_logs(path, records, program, oem, firmware, er_id):
    for platform_dir in path.iterdir():
        if not platform_dir.is_dir():
            continue

        for execution_dir in platform_dir.glob("Execution_*"):
            yaml_file = execution_dir / "execution.yaml"

            if yaml_file.exists():
                try:
                    with open(yaml_file, "r") as f:
                        data = yaml.safe_load(f)

                    # Ensure execution_id exists
                    execution_id = data.get("execution_id")
                    if not execution_id:
                        execution_id = str(uuid.uuid4())
                        data["execution_id"] = execution_id
                        with open(yaml_file, "w") as f:
                            yaml.dump(data, f, sort_keys=False)

                    record = flatten_execution(
                        data,
                        program,
                        oem,
                        firmware,
                        er_id,
                        platform_dir.name,
                        execution_id,
                    )
                    records.append(record)
                except Exception:
                    continue


def flatten_execution(data, program, oem, firmware, er_id, platform, execution_id):
    record = {}
    
    history = data.get("history", [])

    if history:
        latest = history[-1]
        record["Result"] = latest.get("result")
        record["TTF (min)"] = latest.get("ttf")
    else:
        record["Result"] = test.get("result")
        record["TTF (min)"] = test.get("ttf_minutes")

    test = data.get("test", {})
    classification = data.get("classification", {})
    drive = data.get("drive_details", {})
    metadata = data.get("execution_metadata", {})

    record["Execution ID"] = execution_id

    record["Program"] = program
    record["OEM"] = oem
    record["Firmware"] = firmware
    record["ER"] = er_id
    record["Platform"] = platform
    record["Platform Variant"] = data.get("platform_metadata", {}).get("variant_id")

    record["Test Name"] = test.get("name")
    record["Result"] = test.get("result")
    record["TTF (min)"] = test.get("ttf_minutes")

    record["Iteration"] = metadata.get("iteration")
    record["Test Category"] = metadata.get("test_category")
    record["Run Type"] = metadata.get("run_type", "Initial")

    record["Severity"] = classification.get("severity")
    record["Failure Type"] = classification.get("failure_type")
    record["Failure Stage"] = classification.get("failure_stage")
    record["Regression"] = classification.get("regression")
    record["Reproducibility"] = classification.get("reproducibility")

    record["Capacity"] = drive.get("capacity")
    record["Form Factor"] = drive.get("form_factor")
    record["Windows"] = drive.get("windows_version")
    record["BIOS Enum"] = drive.get("bios_enumeration")
    record["JIRA"] = data.get("analysis", {}).get("jira")

    record["Execution Date"] = data.get("execution_date_utc")

    return record