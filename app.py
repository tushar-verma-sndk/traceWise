import streamlit as st
from modules.utils import load_config, ensure_root_structure
from modules.drop_engine import create_official_drop, create_er_drop
from modules.execution_engine import log_execution
from modules.mastersheet_loader import load_mastersheet
from modules.test_registry import load_test_registry
from modules.rerun_loader import load_last_execution
from pathlib import Path

# =============================
# CONFIG
# =============================
config = load_config()

BASE_PATH = config["root_data_path"]
PROGRAM_LIST = config["program_list"]
OEM_LIST = config["oem_list"]

ensure_root_structure(BASE_PATH)

st.set_page_config(page_title="Platform Manager", layout="wide")

# Hide Streamlit sidebar & header
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("Platform Drop Management")

# =============================
# NAVBAR
# =============================

nav_col1, nav_col2 = st.columns([8, 1])

with nav_col2:
    if st.button("Open Dashboard"):
        st.switch_page("pages/dashboard.py")
        
# =============================
# TABS
# =============================
tab1, tab2 = st.tabs(["Create Drop", "Log Test Execution"])

# ============================================================
# TAB 1 — CREATE DROP
# ============================================================
with tab1:

    st.header("Create New Drop")

    program = st.selectbox("Select Program", PROGRAM_LIST)
    oem = st.selectbox("Select OEM", OEM_LIST)

    release_type = st.radio(
        "Release Type",
        ["Official Release", "Engineering Request (ER)"]
    )

    program_base_path = Path(BASE_PATH) / program

    if release_type == "Official Release":

        firmware_name = st.text_input("Firmware Name (e.g., AO014)")
        build = st.text_input("Build", value="Official")

        if st.button("Create Official Drop"):
            if firmware_name.strip() == "":
                st.error("Firmware name required.")
            else:
                success, message = create_official_drop(
                    program_base_path, oem, firmware_name, build
                )
                if success:
                    st.success(message)
                else:
                    st.warning(message)

    else:
        firmware_root = program_base_path / oem
        existing_fw = []

        if firmware_root.exists():
            existing_fw = [
                f.name.replace("Firmware_", "").replace("_Official", "")
                for f in firmware_root.glob("Firmware_*_Official")
            ]

        if not existing_fw:
            st.warning("No Official firmware exists. Create Official first.")
        else:
            selected_fw = st.selectbox("Select Existing Firmware", existing_fw)
            er_id = st.text_input("Enter ER ID (e.g., 5535AZN)")

            if st.button("Create ER Drop"):
                if er_id.strip() == "":
                    st.error("ER ID required.")
                else:
                    success, message = create_er_drop(
                        program_base_path, oem, selected_fw, er_id
                    )
                    if success:
                        st.success(message)
                    else:
                        st.warning(message)

# ============================================================
# TAB 2 — LOG TEST EXECUTION
# ============================================================
with tab2:

    st.header("Log Test Execution")

    # -----------------------
    # Context Bar
    # -----------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        program = st.selectbox("Program", PROGRAM_LIST, key="exec_program")

    with col2:
        oem = st.selectbox("OEM", OEM_LIST, key="exec_oem")

    program_base_path = Path(BASE_PATH) / program / oem

    existing_fw = []
    if program_base_path.exists():
        existing_fw = [
            f.name.replace("Firmware_", "").replace("_Official", "")
            for f in program_base_path.glob("Firmware_*_Official")
        ]

    with col3:
        firmware = st.selectbox("Firmware", existing_fw, key="exec_fw")

    scope = st.radio("Scope", ["Official", "ER"], horizontal=True)

    er_id = None
    if scope == "ER":
        er_root = program_base_path / f"Firmware_{firmware}_Official" / "04_Engineering_Requests_ERs"
        er_list = []
        if er_root.exists():
            er_list = [p.name.replace("ER_", "") for p in er_root.glob("ER_*")]
        er_id = st.selectbox("ER", er_list)

    # -----------------------
    # Platform Selection
    # -----------------------
    platform_data = load_mastersheet("mastersheet.xlsx")
    platform = st.selectbox("Platform", list(platform_data.keys()))

    selected_platform = platform_data.get(platform, {})

    st.subheader("System Info (Auto)")
    st.write("Model:", selected_platform.get("model"))
    st.write("Processor:", selected_platform.get("processor"))
    st.write("Chipset:", selected_platform.get("chipset"))
    st.write("PCIe:", selected_platform.get("pcie_speed"))

    st.divider()


    # -----------------------
    # Execution Metadata
    # -----------------------

    test_mapping, test_list = load_test_registry("test_registry.xlsx")

    st.subheader("Execution Metadata")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        iteration = st.selectbox(
            "Iteration",
            [
                "Iteration-1",
                "Iteration-2",
                "Iteration-3",
                "Iteration-4",
                "Iteration-5",
                "Re-Run",
            ]
        )

    with col2:
        test_name = st.selectbox("Test Name", test_list)

    with col3:
        test_category = test_mapping.get(test_name, "")
        st.text_input("Test Suite", value=test_category, disabled=True)

    # ===========================
    # DEFAULT VALUES
    # ===========================

    drive_capacity = "512GB"
    drive_ff = "2280"
    drive_serial = ""
    windows_version = ""
    bios_enum = "PASS"

    # ===========================
    # RE-RUN AUTO LOAD
    # ===========================

    if iteration == "Re-Run":

        last_data = load_last_execution(
            BASE_PATH,
            program,
            oem,
            firmware,
            platform,
            test_name
        )

        if last_data:

            drive = last_data.get("drive_details", {})

            drive_capacity = drive.get("capacity", "512GB")
            drive_ff = drive.get("form_factor", "2280")
            drive_serial = drive.get("serial_number", "")
            windows_version = drive.get("windows_version", "")
            bios_enum = drive.get("bios_enumeration", "PASS")

            st.success("Loaded previous execution details")

    st.divider()

    # -----------------------
    # Drive & OS
    # -----------------------

    st.subheader("Drive & OS Details")

    d1, d2, d3 = st.columns(3)

    with d1:
        drive_capacity = st.selectbox(
            "Capacity",
            ["512GB", "1TB", "2TB", "4TB"],
            index=["512GB","1TB","2TB","4TB"].index(drive_capacity)
        )

        drive_ff = st.selectbox(
            "Form Factor",
            ["2280", "2242", "2230"],
            index=["2280","2242","2230"].index(drive_ff)
        )

    with d2:
        drive_serial = st.text_input(
            "Drive Serial Number",
            value=drive_serial
        )

        windows_version = st.text_input(
            "Windows Version (e.g., 25H2)",
            value=windows_version
        )

    with d3:
        bios_enum = st.selectbox(
            "Drive Enumeration in BIOS",
            ["PASS", "FAIL"],
            index=0 if bios_enum == "PASS" else 1
        )


    # -----------------------
    # Execution Result
    # -----------------------

    st.subheader("Execution Result")

    col_pass, col_fail = st.columns(2)

    if "fail_mode" not in st.session_state:
        st.session_state.fail_mode = False

    # PASS
    with col_pass:
        if st.button("✅ PASS", use_container_width=True):

            execution_payload = {
                "context": {
                    "program": program,
                    "oem": oem,
                    "firmware": firmware,
                    "er": er_id,
                    "platform": platform,
                },
                "execution_metadata": {
                    "iteration": iteration,
                    "test_category": test_category,
                    "run_type": "Re-Run" if iteration == "Re-Run" else "Initial",
                },
                "platform_metadata": selected_platform,
                "drive_details": {
                    "capacity": drive_capacity,
                    "form_factor": drive_ff,
                    "serial_number": drive_serial,
                    "windows_version": windows_version,
                    "bios_enumeration": bios_enum,
                },
                "test": {
                    "name": test_name,
                    "result": "PASS"
                }
            }

            success, message = log_execution(
                BASE_PATH,
                program,
                oem,
                firmware,
                scope,
                platform,
                execution_payload,
                er_id=er_id
            )

            if success:
                st.success("PASS logged successfully.")
                st.session_state.fail_mode = False
                st.rerun()

    # FAIL trigger
    with col_fail:
        if st.button("❌ FAIL", use_container_width=True):
            st.session_state.fail_mode = True

    # -----------------------
    # Failure Panel
    # -----------------------

    if st.session_state.fail_mode:

        st.divider()
        st.subheader("Failure Details")

        f1, f2, f3 = st.columns(3)

        with f1:
            severity = st.selectbox("Severity", ["S1", "S2", "S3", "S4"])
            failure_type = st.selectbox(
                "Failure Type",
                ["BSOD", "Hang", "Reset", "Power", "Performance", "Other"]
            )

        with f2:
            failure_stage = st.selectbox(
                "Failure Stage",
                ["Boot", "Init", "IO", "Power", "Reset", "Runtime", "Unknown"]
            )
            reproducibility = st.selectbox(
                "Reproducibility",
                ["Always", "Intermittent", "Rare", "Not Reproducible"]
            )

        with f3:
            regression = st.selectbox("Regression", ["Yes", "No", "Unknown"])
            ttf = st.number_input("TTF (minutes)", min_value=0)

        observed = st.text_area("Observed Behavior")
        # xplorer_url = st.text_input("xPlorer URL")
        xplorer_url = st.text_area(
            "Artifacts / Links (DUI/setEvents)",
            placeholder="Paste link"
        )
        jira_id = st.text_input("JIRA ID / Link")

        with st.expander("Advanced Technical Details"):
            jtag_analysis = st.text_area("JTAG Analysis")
            set_event_analysis = st.text_area("Set Event Analysis")

        if st.button("Save Failure Execution"):

            if not observed or not xplorer_url:
                st.error("Observed Behavior and xPlorer URL required.")
            else:

                execution_payload = {
                    "context": {
                        "program": program,
                        "oem": oem,
                        "firmware": firmware,
                        "er": er_id,
                        "platform": platform,
                    },
                    "execution_metadata": {
                        "iteration": iteration,
                        "test_category": test_category,
                    },
                    "platform_metadata": selected_platform,
                    "drive_details": {
                        "capacity": drive_capacity,
                        "form_factor": drive_ff,
                        "serial_number": drive_serial,
                        "windows_version": windows_version,
                        "bios_enumeration": bios_enum,
                    },
                    "test": {
                        "name": test_name,
                        "result": "FAIL",
                        "ttf_minutes": ttf
                    },
                    "classification": {
                        "severity": severity,
                        "failure_type": failure_type,
                        "failure_stage": failure_stage,
                        "reproducibility": reproducibility,
                        "regression": regression
                    },
                    "analysis": {
                        "observed": observed,
                        "xplorer_url": xplorer_url,
                        "jira": jira_id,
                        "jtag_analysis": jtag_analysis,
                        "set_event_analysis": set_event_analysis
                    }
                }

                success, message = log_execution(
                    BASE_PATH,
                    program,
                    oem,
                    firmware,
                    scope,
                    platform,
                    execution_payload,
                    er_id=er_id
                )

                if success:
                    st.success("FAIL execution logged successfully.")
                    st.session_state.fail_mode = False
                    st.rerun()
                    