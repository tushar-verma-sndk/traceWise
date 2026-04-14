import streamlit as st
from modules.utils import load_config, ensure_root_structure
from modules.drop_engine import create_official_drop, create_er_drop
from modules.execution_engine import log_execution
from modules.mastersheet_loader import load_mastersheet
from modules.test_registry import load_test_registry
from modules.rerun_loader import load_last_execution
from modules.scheduler import add_scheduled_entry, get_platform_schedule_summary
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

# Enhanced styling
st.markdown("""
<style>
/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}

/* ============================================ */
/* ENHANCED TAB STYLING */
/* ============================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: #1e1e1e;
    padding: 10px 15px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding: 12px 24px;
    background-color: #2d2d2d;
    border-radius: 10px;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    border: 2px solid transparent;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: #3d3d3d;
    border-color: #ff4b4b;
    transform: translateY(-2px);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #ff4b4b 0%, #ff6b6b 100%);
    color: white !important;
    border-color: #ff4b4b;
    box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
}

/* Button enhancements */
.stButton > button {
    transition: all 0.3s ease;
    border-radius: 8px;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1e1e1e;
}

::-webkit-scrollbar-thumb {
    background: #ff4b4b;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #ff6b6b;
}
</style>
""", unsafe_allow_html=True)

st.title("🖥️ Platform Drop Management")

# =============================
# NAVBAR
# =============================
nav_col1, nav_col2 = st.columns([7, 1])
with nav_col2:
    if st.button("📊 Dashboard"):
        st.switch_page("pages/dashboard.py")

# =============================
# TABS
# =============================
tab1, tab2, tab3 = st.tabs(["📦 Create Drop", "📝 Log Test Execution", "📅 Quick Schedule"])

# ============================================================
# TAB 1 — CREATE DROP
# ============================================================
with tab1:
    st.header("Create New Drop")
    
    col1, col2 = st.columns(2)
    with col1:
        program = st.selectbox("Select Program", PROGRAM_LIST, key="drop_program")
    with col2:
        oem = st.selectbox("Select OEM", OEM_LIST, key="drop_oem")
    
    release_type = st.radio(
        "Release Type",
        ["Official Release", "Engineering Request (ER)"],
        horizontal=True
    )
    
    program_base_path = Path(BASE_PATH) / program
    
    if release_type == "Official Release":
        st.markdown("#### Official Release Details")
        col1, col2 = st.columns(2)
        with col1:
            firmware_name = st.text_input("Firmware Name (e.g., AO014)")
        with col2:
            build = st.text_input("Build", value="Official")
        
        if st.button("🚀 Create Official Drop", use_container_width=True):
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
            st.markdown("#### Engineering Request Details")
            col1, col2 = st.columns(2)
            with col1:
                selected_fw = st.selectbox("Select Existing Firmware", existing_fw)
            with col2:
                er_id = st.text_input("Enter ER ID (e.g., 5535AZN)")
            
            if st.button("🔧 Create ER Drop", use_container_width=True):
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
    
    st.divider()
    
    # -----------------------
    # Platform Selection
    # -----------------------
    platform_data = load_mastersheet("mastersheet.xlsx")
    platform = st.selectbox("Platform", list(platform_data.keys()))
    selected_platform = platform_data.get(platform, {})
    
    with st.expander("📋 System Info (Auto-populated)"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Model:**", selected_platform.get("model"))
            st.write("**Processor:**", selected_platform.get("processor"))
        with col2:
            st.write("**Chipset:**", selected_platform.get("chipset"))
            st.write("**PCIe:**", selected_platform.get("pcie_speed"))
    
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
            st.success("✅ Loaded previous execution details")
    
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
            index=["512GB", "1TB", "2TB", "4TB"].index(drive_capacity)
        )
        drive_ff = st.selectbox(
            "Form Factor",
            ["2280", "2242", "2230"],
            index=["2280", "2242", "2230"].index(drive_ff)
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
    
    st.divider()
    
    # -----------------------
    # Execution Result
    # -----------------------
    st.subheader("Execution Result")
    
    if "fail_mode" not in st.session_state:
        st.session_state.fail_mode = False
    
    col_pass, col_fail = st.columns(2)
    
    # PASS
    with col_pass:
        if st.button("✅ PASS", use_container_width=True, type="primary"):
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
                st.success("✅ PASS logged successfully.")
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
        st.subheader("❌ Failure Details")
        
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
        xplorer_url = st.text_area(
            "Artifacts / Links (DUI/setEvents)",
            placeholder="Paste link"
        )
        jira_id = st.text_input("JIRA ID / Link")
        
        with st.expander("🔧 Advanced Technical Details"):
            jtag_analysis = st.text_area("JTAG Analysis")
            set_event_analysis = st.text_area("Set Event Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Failure Execution", use_container_width=True, type="primary"):
                if not observed or not xplorer_url:
                    st.error("Observed Behavior and Artifacts/Links are required.")
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
                        st.success("❌ FAIL execution logged successfully.")
                        st.session_state.fail_mode = False
                        st.rerun()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.fail_mode = False
                st.rerun()

# ============================================================
# TAB 3 — QUICK SCHEDULE (With OEM, Firmware, Program)
# ============================================================
with tab3:
    st.header("📅 Quick Test Scheduling")
    
    st.markdown("""
    Schedule multiple tests for a platform. All entries will be saved 
    as **IN_PROGRESS** and appear in the Dashboard.
    """)
    
    # Load test registry and mastersheet
    test_mapping, test_list = load_test_registry("test_registry.xlsx")
    platform_data = load_mastersheet("mastersheet.xlsx")
    
    st.divider()
    
    # =============================
    # CONTEXT SELECTION (Program, OEM, Firmware)
    # =============================
    st.subheader("📋 Context Selection")
    
    ctx_col1, ctx_col2, ctx_col3 = st.columns(3)
    
    with ctx_col1:
        sched_program = st.selectbox("Program", PROGRAM_LIST, key="sched_program")
    with ctx_col2:
        sched_oem = st.selectbox("OEM", OEM_LIST, key="sched_oem")
    
    # Get available firmware for selected program/oem
    sched_program_base_path = Path(BASE_PATH) / sched_program / sched_oem
    sched_existing_fw = []
    if sched_program_base_path.exists():
        sched_existing_fw = [
            f.name.replace("Firmware_", "").replace("_Official", "")
            for f in sched_program_base_path.glob("Firmware_*_Official")
        ]
    
    with ctx_col3:
        sched_firmware = st.selectbox(
            "Firmware", 
            sched_existing_fw if sched_existing_fw else ["N/A"],
            key="sched_firmware"
        )
    
    st.divider()
    
    # Platform selection
    sched_platform = st.selectbox(
        "Select Platform",
        list(platform_data.keys()),
        key="quick_sched_platform"
    )
    
    # Initialize quick entries
    if "quick_entries" not in st.session_state:
        st.session_state.quick_entries = []
    
    st.divider()
    
    # Entry form
    st.markdown("### Add Test Entry")
    
    entry_cols = st.columns([3, 1, 1, 1, 1])
    
    with entry_cols[0]:
        quick_test_name = st.selectbox("Test Name", test_list, key="quick_test_name")
    with entry_cols[1]:
        quick_iteration = st.selectbox(
            "Iteration",
            ["Iteration-1", "Iteration-2", "Iteration-3", "Iteration-4", "Iteration-5"],
            key="quick_iteration"
        )
    with entry_cols[2]:
        quick_sed_type = st.selectbox("SED Type", ["Non-SED", "SED"], key="quick_sed_type")
    with entry_cols[3]:
        quick_capacity = st.selectbox("Capacity", ["512GB", "1TB", "2TB", "4TB"], key="quick_capacity")
    with entry_cols[4]:
        quick_form_factor = st.selectbox("Form Factor", ["2280", "2242", "2230"], key="quick_form_factor")
    
    # Buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
    
    with btn_col1:
        if st.button("➕ Add Entry", use_container_width=True, key="quick_add"):
            new_entry = {
                "program": sched_program,
                "oem": sched_oem,
                "firmware": sched_firmware,
                "platform": sched_platform,
                "test_name": quick_test_name,
                "test_category": test_mapping.get(quick_test_name, ""),
                "iteration": quick_iteration,
                "sed_type": quick_sed_type,
                "capacity": quick_capacity,
                "form_factor": quick_form_factor
            }
            st.session_state.quick_entries.append(new_entry)
            st.success(f"Added: {quick_test_name}")
            st.rerun()
    
    with btn_col2:
        if st.button("🗑️ Clear All", use_container_width=True, key="quick_clear"):
            st.session_state.quick_entries = []
            st.rerun()
    
    st.divider()
    
    # Display pending entries
    if st.session_state.quick_entries:
        st.markdown("### 📝 Pending Entries")
        
        # Header
        header_cols = st.columns([2, 1.5, 1, 1, 1, 1, 0.5])
        header_cols[0].markdown("**Test Name**")
        header_cols[1].markdown("**OEM/Firmware**")
        header_cols[2].markdown("**Iteration**")
        header_cols[3].markdown("**SED Type**")
        header_cols[4].markdown("**Capacity**")
        header_cols[5].markdown("**Form Factor**")
        header_cols[6].markdown("**Del**")
        
        st.divider()
        
        entries_to_remove = []
        for idx, entry in enumerate(st.session_state.quick_entries):
            cols = st.columns([2, 1.5, 1, 1, 1, 1, 0.5])
            cols[0].write(entry["test_name"])
            cols[1].write(f"{entry['oem']}/{entry['firmware']}")
            cols[2].write(entry["iteration"])
            cols[3].write(entry["sed_type"])
            cols[4].write(entry["capacity"])
            cols[5].write(entry["form_factor"])
            if cols[6].button("❌", key=f"quick_remove_{idx}"):
                entries_to_remove.append(idx)
        
        # Remove marked entries
        for idx in sorted(entries_to_remove, reverse=True):
            st.session_state.quick_entries.pop(idx)
        
        if entries_to_remove:
            st.rerun()
        
        st.divider()
        
        # Summary
        st.markdown(f"**Total Entries:** {len(st.session_state.quick_entries)}")
        
        # Save button
        if st.button("✅ Save All to Schedule (as IN_PROGRESS)", use_container_width=True, type="primary"):
            for entry in st.session_state.quick_entries:
                add_scheduled_entry(BASE_PATH, entry)
            count = len(st.session_state.quick_entries)
            st.session_state.quick_entries = []
            st.success(f"✅ {count} tests scheduled as IN_PROGRESS!")
            st.balloons()
            st.rerun()
    else:
        st.info("No entries added yet. Use the form above to add tests to schedule.")
    
    # Show current schedule summary
    st.divider()
    st.markdown("### 📊 Current Schedule Summary")
    
    summary = get_platform_schedule_summary(BASE_PATH)
    
    if summary:
        for plat, data in summary.items():
            with st.expander(f"🖥️ {plat} ({data['total']} tests)"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🔄 In Progress", data["in_progress"])
                col2.metric("✅ Passed", data["passed"])
                col3.metric("❌ Failed", data["failed"])
                col4.metric("⏳ Pending", data["scheduled"])
    else:
        st.info("No tests scheduled yet.")