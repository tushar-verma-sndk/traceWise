import os
from pathlib import Path


def create_official_drop(base_path, oem, firmware_name, build="Official"):
    firmware_folder = f"Firmware_{firmware_name}_{build}"
    drop_path = Path(base_path) / oem / firmware_folder

    if drop_path.exists():
        return False, "Firmware already exists."

    # Standard folder structure
    subfolders = [
        "01_Release_Info",
        "02_Executable_and_Artifacts",
        "04_Engineering_Requests_ERs",
        "05_Logs",
        "07_UI_Tree_Data",
        "Test_Plan",
    ]

    for folder in subfolders:
        (drop_path / folder).mkdir(parents=True, exist_ok=True)

    return True, f"Official drop created at {drop_path}"


def create_er_drop(base_path, oem, firmware_name, er_id, build="Official"):
    firmware_folder = f"Firmware_{firmware_name}_{build}"
    firmware_path = Path(base_path) / oem / firmware_folder

    if not firmware_path.exists():
        return False, "Base firmware does not exist. Create Official first."

    er_folder = firmware_path / "04_Engineering_Requests_ERs" / f"ER_{er_id}"

    if er_folder.exists():
        return False, "ER already exists."

    # ER structure
    (er_folder / "Fix_Details").mkdir(parents=True, exist_ok=True)
    (er_folder / "Logs").mkdir(parents=True, exist_ok=True)

    # Create placeholder description
    desc_file = er_folder / "ER_Description.md"
    desc_file.write_text(f"# ER {er_id}\n\nDescription goes here.\n")

    return True, f"ER drop created at {er_folder}"