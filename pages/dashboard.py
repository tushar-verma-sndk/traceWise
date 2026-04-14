import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yaml
from pathlib import Path
from datetime import datetime
from modules.index_builder import build_execution_index
from modules.utils import load_config
from modules.scheduler import (
    load_scheduled_tests,
    remove_scheduled_entry,
    get_platform_schedule_summary,
    update_scheduled_entry_status,
    get_all_scheduled_as_dataframe_records
)
from modules.test_registry import load_test_registry
from modules.mastersheet_loader import load_mastersheet

config = load_config()
BASE_PATH = config["root_data_path"]

# Enhanced CSS for better tab visibility and card interactions
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

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px;
}

/* ============================================ */
/* CARD STACK STYLING */
/* ============================================ */
.card-stack {
    display: flex;
    flex-direction: row;
    position: relative;
    min-height: 50px;
    align-items: center;
    cursor: pointer;
}

.card-stack .card {
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 10px;
    color: white;
    margin-right: -16px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    cursor: pointer;
    min-width: 70px;
    text-align: center;
}

.card-stack:hover .card {
    margin-right: 4px;
}

.card:hover {
    transform: translateY(-4px) scale(1.08);
    z-index: 999;
    box-shadow: 0 8px 16px rgba(0,0,0,0.3);
}

.status-pass { background: linear-gradient(135deg, #1f7a1f 0%, #28a745 100%); }
.status-fail { background: linear-gradient(135deg, #b30000 0%, #dc3545 100%); }
.status-progress { background: linear-gradient(135deg, #d4a017 0%, #ffc107 100%); }

/* ============================================ */
/* MODAL/DIALOG FOR HISTORY */
/* ============================================ */
.history-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 10000;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 40px;
    overflow-y: auto;
}

.history-modal {
    background: #1e1e1e;
    border-radius: 16px;
    padding: 30px;
    max-width: 900px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.history-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #333;
}

.history-modal-title {
    font-size: 24px;
    font-weight: bold;
    color: white;
}

.history-card {
    padding: 20px;
    border-radius: 12px;
    margin: 12px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    transition: transform 0.2s ease;
}

.history-card:hover {
    transform: translateX(5px);
}

.history-card-pass { background: linear-gradient(135deg, #1f7a1f 0%, #28a745 100%); }
.history-card-fail { background: linear-gradient(135deg, #b30000 0%, #dc3545 100%); }
.history-card-progress { background: linear-gradient(135deg, #d4a017 0%, #ffc107 100%); }

/* ============================================ */
/* BUTTON ENHANCEMENTS */
/* ============================================ */
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

st.title("📊 Execution Dashboard")

# Build execution index
df = build_execution_index(BASE_PATH)

# Add Is Scheduled column to existing df if not empty
if not df.empty:
    df["Is Scheduled"] = False

# Merge scheduled tests into the dataframe
scheduled_records = get_all_scheduled_as_dataframe_records(BASE_PATH)
if scheduled_records:
    scheduled_df = pd.DataFrame(scheduled_records)
    scheduled_df["Execution Date"] = pd.to_datetime(scheduled_df["Execution Date"])
    if df.empty:
        df = scheduled_df
    else:
        # Merge
        df = pd.concat([df, scheduled_df], ignore_index=True)

# Sort dataframe: IN_PROGRESS and scheduled first, then by date descending
if not df.empty:
    # Create a priority column for sorting
    df["_sort_priority"] = df["Result"].apply(
        lambda x: 0 if x == "IN_PROGRESS" else (1 if x == "SCHEDULED" else 2)
    )
    df = df.sort_values(
        by=["_sort_priority", "Execution Date"],
        ascending=[True, False]
    ).drop(columns=["_sort_priority"])
    df = df.reset_index(drop=True)

# Initialize session states
if "scheduled_entries" not in st.session_state:
    st.session_state.scheduled_entries = []
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None
if "expanded_rows" not in st.session_state:
    st.session_state.expanded_rows = set()
if "fail_edit_id" not in st.session_state:
    st.session_state.fail_edit_id = None
if "show_history_modal" not in st.session_state:
    st.session_state.show_history_modal = False
if "history_modal_data" not in st.session_state:
    st.session_state.history_modal_data = None

# ============================================================
# GLOBAL FILTERS
# ============================================================
st.subheader("🔍 Global Filters")
f1, f2, f3, f4, f5, f6 = st.columns(6)

if not df.empty:
    with f1:
        program_filter = st.multiselect("Program", df["Program"].dropna().unique())
    with f2:
        oem_filter = st.multiselect("OEM", df["OEM"].dropna().unique())
    with f3:
        firmware_filter = st.multiselect("Firmware", df["Firmware"].dropna().unique())
    with f4:
        result_filter = st.multiselect("Result", df["Result"].dropna().unique())
    with f5:
        iteration_values = df["Iteration"].dropna().unique()
        iteration_filter = st.multiselect("Iteration", iteration_values)
    with f6:
        category_values = df["Test Category"].dropna().unique()
        category_filter = st.multiselect("Test Category", category_values)

    filtered_df = df.copy()
    if program_filter:
        filtered_df = filtered_df[filtered_df["Program"].isin(program_filter)]
    if oem_filter:
        filtered_df = filtered_df[filtered_df["OEM"].isin(oem_filter)]
    if firmware_filter:
        filtered_df = filtered_df[filtered_df["Firmware"].isin(firmware_filter)]
    if result_filter:
        filtered_df = filtered_df[filtered_df["Result"].isin(result_filter)]
    if iteration_filter:
        filtered_df = filtered_df[filtered_df["Iteration"].isin(iteration_filter)]
    if category_filter:
        filtered_df = filtered_df[filtered_df["Test Category"].isin(category_filter)]
else:
    filtered_df = df

st.divider()

# ============================================================
# TABS - Removed "Schedule New Tests" section, only viewing
# ============================================================
schedule_tab, table_tab, platform_tab, analytics_tab, coverage_overview_tab, coverage_matrix_grouped_tab = st.tabs(
    [
        "📅 Scheduled Overview",
        "📋 Execution Records",
        "🖥️ Platform View",
        "📈 Analytics",
        "📊 Coverage Overview",
        "📉 Graph Grouped"
    ]
)

# ============================================================
# TAB 0 — SCHEDULED OVERVIEW (View Only - No Creation)
# ============================================================
with schedule_tab:
    st.subheader("📅 Scheduled Tests Overview")
    st.info("💡 To schedule new tests, go to the main app → Quick Schedule tab")
    
    # Load test registry and mastersheet
    test_mapping, test_list = load_test_registry("test_registry.xlsx")
    platform_data = load_mastersheet("mastersheet.xlsx")
    
    schedule_summary = get_platform_schedule_summary(BASE_PATH)
    
    if schedule_summary:
        # Platform selector for viewing
        view_platform = st.selectbox(
            "Select Platform to View Scheduled Tests",
            ["All Platforms"] + list(schedule_summary.keys()),
            key="view_platform"
        )
        
        # Display summary cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        if view_platform == "All Platforms":
            total = sum(s["total"] for s in schedule_summary.values())
            in_progress = sum(s["in_progress"] for s in schedule_summary.values())
            passed = sum(s["passed"] for s in schedule_summary.values())
            failed = sum(s["failed"] for s in schedule_summary.values())
            scheduled = sum(s["scheduled"] for s in schedule_summary.values())
        else:
            stats = schedule_summary.get(view_platform, {})
            total = stats.get("total", 0)
            in_progress = stats.get("in_progress", 0)
            passed = stats.get("passed", 0)
            failed = stats.get("failed", 0)
            scheduled = stats.get("scheduled", 0)
        
        col1.metric("📊 Total", total)
        col2.metric("🔄 In Progress", in_progress)
        col3.metric("✅ Passed", passed)
        col4.metric("❌ Failed", failed)
        col5.metric("⏳ Scheduled", scheduled)
        
        # Display scheduled entries
        st.markdown("#### Scheduled Entries")
        
        all_entries = []
        if view_platform == "All Platforms":
            for plat, data in schedule_summary.items():
                all_entries.extend(data["entries"])
        else:
            all_entries = schedule_summary.get(view_platform, {}).get("entries", [])
        
        # Sort entries: IN_PROGRESS first, then by created_at descending
        all_entries = sorted(
            all_entries,
            key=lambda x: (
                0 if x.get("status") == "IN_PROGRESS" else (1 if x.get("status") == "SCHEDULED" else 2),
                x.get("created_at", "")
            ),
            reverse=False
        )
        # Reverse to get newest first within same priority
        all_entries = sorted(
            all_entries,
            key=lambda x: (
                0 if x.get("status") == "IN_PROGRESS" else (1 if x.get("status") == "SCHEDULED" else 2),
            )
        )
        
        if all_entries:
            # Header
            header_cols = st.columns([2, 1.5, 1.5, 1, 1, 1, 1, 1])
            header_cols[0].markdown("**Test Name**")
            header_cols[1].markdown("**Platform**")
            header_cols[2].markdown("**OEM/Firmware**")
            header_cols[3].markdown("**Iteration**")
            header_cols[4].markdown("**Capacity**")
            header_cols[5].markdown("**Form Factor**")
            header_cols[6].markdown("**Status**")
            header_cols[7].markdown("**Action**")
            
            st.divider()
            
            for entry in all_entries:
                cols = st.columns([2, 1.5, 1.5, 1, 1, 1, 1, 1])
                cols[0].write(entry.get('test_name', 'N/A'))
                cols[1].write(entry.get("platform", "N/A"))
                cols[2].write(f"{entry.get('oem', 'N/A')} / {entry.get('firmware', 'N/A')}")
                cols[3].write(entry.get("iteration", "N/A"))
                cols[4].write(entry.get("capacity", "N/A"))
                cols[5].write(entry.get("form_factor", "N/A"))
                
                status = entry.get("status", "IN_PROGRESS")
                status_emoji = {
                    "SCHEDULED": "⏳",
                    "IN_PROGRESS": "🔄",
                    "PASS": "✅",
                    "FAIL": "❌"
                }.get(status, "🔄")
                
                status_color = {
                    "SCHEDULED": "#17a2b8",
                    "IN_PROGRESS": "#ffc107",
                    "PASS": "#28a745",
                    "FAIL": "#dc3545"
                }.get(status, "#ffc107")
                
                cols[6].markdown(
                    f'<span style="color: {status_color}; font-weight: bold;">{status_emoji} {status}</span>',
                    unsafe_allow_html=True
                )
                
                # Delete button
                entry_id = entry.get("id", entry.get("execution_id"))
                if cols[7].button("🗑️", key=f"del_sched_{entry_id}"):
                    remove_scheduled_entry(BASE_PATH, entry_id)
                    st.success("Entry removed!")
                    st.rerun()
            
            st.divider()
            
            # Visualization
            st.markdown("#### 📊 Schedule Visualization")
            viz_df = pd.DataFrame(all_entries)
            
            if not viz_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # By Platform
                    if "platform" in viz_df.columns:
                        platform_counts = viz_df["platform"].value_counts().reset_index()
                        platform_counts.columns = ["Platform", "Count"]
                        fig1 = px.pie(
                            platform_counts,
                            values="Count",
                            names="Platform",
                            title="Scheduled Tests by Platform",
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    # By Status with proper colors
                    if "status" in viz_df.columns:
                        status_counts = viz_df["status"].value_counts().reset_index()
                        status_counts.columns = ["Status", "Count"]
                        color_map = {
                            "SCHEDULED": "#17a2b8",
                            "IN_PROGRESS": "#ffc107",
                            "PASS": "#28a745",
                            "FAIL": "#dc3545"
                        }
                        fig2 = px.bar(
                            status_counts,
                            x="Status",
                            y="Count",
                            color="Status",
                            color_discrete_map=color_map,
                            title="Tests by Status"
                        )
                        st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No scheduled tests found.")
    else:
        st.info("No tests scheduled yet. Go to main app → Quick Schedule tab to schedule tests.")

# ============================================================
# TAB 1 — EXECUTION RECORDS
# ============================================================
with table_tab:
    st.subheader("📋 Execution Records")
    
    if filtered_df.empty:
        st.info("No records found.")
    else:
        # ---------- HEADER ----------
        header = st.columns([2, 2, 1, 1, 1.5, 1, 1])
        header[0].markdown("**Platform**")
        header[1].markdown("**Test Name**")
        header[2].markdown("**Iteration**")
        header[3].markdown("**Run Type**")
        header[4].markdown("**Result**")
        header[5].markdown("**Severity**")
        header[6].markdown("**Details**")
        
        st.divider()
        
        # ---------- ROWS (Already sorted with IN_PROGRESS on top) ----------
        for idx, row in filtered_df.iterrows():
            execution_id = row["Execution ID"]
            current_result = row["Result"] if row["Result"] in ["PASS", "FAIL", "IN_PROGRESS"] else "IN_PROGRESS"
            is_scheduled = row.get("Is Scheduled", False)
            
            cols = st.columns([2, 2, 1, 1, 1.5, 1, 1])
            cols[0].write(row["Platform"])
            cols[1].write(row["Test Name"])
            cols[2].write(row["Iteration"])
            
            run_type = row.get("Run Type", "Initial")
            if is_scheduled:
                cols[3].markdown("🔄 **Scheduled**")
            else:
                cols[3].write(run_type)
            
            # Status selector with color coding
            new_result = cols[4].selectbox(
                "",
                ["PASS", "FAIL", "IN_PROGRESS"],
                index=["PASS", "FAIL", "IN_PROGRESS"].index(current_result),
                key=f"result_{execution_id}_{idx}"
            )
            
            # Handle status change
            if new_result != current_result:
                if new_result == "PASS":
                    if is_scheduled:
                        # Update scheduled entry
                        update_scheduled_entry_status(BASE_PATH, execution_id, "PASS")
                        st.success("Status updated to PASS")
                        st.rerun()
                    else:
                        # Auto-save PASS - update the YAML file
                        program = row["Program"]
                        oem = row["OEM"]
                        firmware = row["Firmware"]
                        firmware_path = (
                            Path(BASE_PATH)
                            / program
                            / oem
                            / f"Firmware_{firmware}_Official"
                        )
                        
                        for path in firmware_path.rglob("execution.yaml"):
                            try:
                                with open(path, "r") as f:
                                    data = yaml.safe_load(f)
                                if data and data.get("execution_id") == execution_id:
                                    data["test"]["result"] = "PASS"
                                    with open(path, "w") as f:
                                        yaml.dump(data, f, sort_keys=False)
                                    st.success("Status updated to PASS")
                                    st.rerun()
                                    break
                            except Exception:
                                continue
                
                elif new_result == "FAIL":
                    # Open failure detail panel
                    st.session_state.fail_edit_id = execution_id
                    st.session_state.expanded_rows.add(execution_id)
            
            severity_val = row.get("Severity", "")
            cols[5].write(severity_val if severity_val else "-")
            
            toggle = "▼" if execution_id not in st.session_state.expanded_rows else "▲"
            if cols[6].button(toggle, key=f"toggle_{execution_id}_{idx}"):
                if execution_id in st.session_state.expanded_rows:
                    st.session_state.expanded_rows.remove(execution_id)
                    if st.session_state.editing_id == execution_id:
                        st.session_state.editing_id = None
                    if st.session_state.fail_edit_id == execution_id:
                        st.session_state.fail_edit_id = None
                else:
                    st.session_state.expanded_rows.add(execution_id)
            
            # =============================
            # EXPANDED VIEW
            # =============================
            if execution_id in st.session_state.expanded_rows:
                st.markdown("##### Details")
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.write("**Suite:**", row.get("Test Category", "-"))
                    st.write("**Failure Type:**", row.get("Failure Type", "-"))
                    st.write("**Stage:**", row.get("Failure Stage", "-"))
                with d2:
                    st.write("**Regression:**", row.get("Regression", "-"))
                    st.write("**Repro:**", row.get("Reproducibility", "-"))
                    st.write("**TTF:**", row.get("TTF (min)", "-"))
                with d3:
                    st.write("**Capacity:**", row.get("Capacity", "-"))
                    st.write("**Form Factor:**", row.get("Form Factor", "-"))
                    st.write("**OEM:**", row.get("OEM", "-"))
                    st.write("**Firmware:**", row.get("Firmware", "-"))
                
                # =============================
                # PLATFORM HISTORY
                # =============================
                history_df = filtered_df[
                    (filtered_df["Platform"] == row["Platform"]) &
                    (filtered_df["Test Name"] == row["Test Name"])
                ]
                
                st.markdown("##### Run History")
                history_display = history_df[["Iteration", "Result", "Execution Date"]].copy()
                history_display = history_display.sort_values("Execution Date", ascending=False)
                st.dataframe(history_display, use_container_width=True)
                
                # =============================
                # EDIT BUTTON
                # =============================
                if not is_scheduled:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️ Edit Details", key=f"edit_{execution_id}_{idx}"):
                            st.session_state.editing_id = execution_id
                
                st.divider()
            
            # =============================
            # FAILURE DETAIL PANEL
            # =============================
            if st.session_state.fail_edit_id == execution_id:
                st.markdown(f"### ❌ Record Failure Details: {row['Platform']} | {row['Test Name']}")
                
                is_scheduled_entry = row.get("Is Scheduled", False)
                
                st.markdown("#### Failure Classification")
                
                f1, f2, f3 = st.columns(3)
                with f1:
                    severity = st.selectbox(
                        "Severity",
                        ["S1", "S2", "S3", "S4"],
                        key=f"fail_severity_{execution_id}_{idx}"
                    )
                    failure_type = st.selectbox(
                        "Failure Type",
                        ["BSOD", "Hang", "Reset", "Power", "Performance", "Other"],
                        key=f"fail_type_{execution_id}_{idx}"
                    )
                with f2:
                    failure_stage = st.selectbox(
                        "Failure Stage",
                        ["Boot", "Init", "IO", "Power", "Reset", "Runtime", "Unknown"],
                        key=f"fail_stage_{execution_id}_{idx}"
                    )
                    reproducibility = st.selectbox(
                        "Reproducibility",
                        ["Always", "Intermittent", "Rare", "Not Reproducible"],
                        key=f"fail_repro_{execution_id}_{idx}"
                    )
                with f3:
                    regression = st.selectbox(
                        "Regression",
                        ["Yes", "No", "Unknown"],
                        key=f"fail_regression_{execution_id}_{idx}"
                    )
                    ttf = st.number_input(
                        "TTF (minutes)",
                        min_value=0,
                        key=f"fail_ttf_{execution_id}_{idx}"
                    )
                
                st.markdown("#### Analysis Details")
                observed = st.text_area(
                    "Observed Behavior",
                    key=f"fail_observed_{execution_id}_{idx}"
                )
                xplorer_url = st.text_area(
                    "Artifacts / Links (DUI/setEvents)",
                    placeholder="Paste link",
                    key=f"fail_xplorer_{execution_id}_{idx}"
                )
                jira_id = st.text_input(
                    "JIRA ID / Link",
                    key=f"fail_jira_{execution_id}_{idx}"
                )
                
                with st.expander("🔧 Advanced Technical Details"):
                    jtag_analysis = st.text_area(
                        "JTAG Analysis",
                        key=f"fail_jtag_{execution_id}_{idx}"
                    )
                    set_event_analysis = st.text_area(
                        "Set Event Analysis",
                        key=f"fail_setevent_{execution_id}_{idx}"
                    )
                
                save_col, cancel_col = st.columns(2)
                
                with save_col:
                    if st.button("💾 Save Failure Details", key=f"save_fail_{execution_id}_{idx}", type="primary"):
                        if not observed or not xplorer_url:
                            st.error("Observed Behavior and Artifacts/Links are required.")
                        else:
                            if is_scheduled_entry:
                                # Update scheduled entry with failure details
                                additional_data = {
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
                                    },
                                    "ttf_minutes": ttf,
                                    "severity": severity
                                }
                                update_scheduled_entry_status(BASE_PATH, execution_id, "FAIL", additional_data)
                                st.success("Failure details saved successfully!")
                                st.session_state.fail_edit_id = None
                                st.rerun()
                            else:
                                # Update YAML file
                                program = row["Program"]
                                oem = row["OEM"]
                                firmware = row["Firmware"]
                                firmware_path = (
                                    Path(BASE_PATH)
                                    / program
                                    / oem
                                    / f"Firmware_{firmware}_Official"
                                )
                                
                                yaml_path = None
                                yaml_data = None
                                
                                for path in firmware_path.rglob("execution.yaml"):
                                    try:
                                        with open(path, "r") as f:
                                            data = yaml.safe_load(f)
                                        if data and data.get("execution_id") == execution_id:
                                            yaml_path = path
                                            yaml_data = data
                                            break
                                    except Exception:
                                        continue
                                
                                if yaml_data:
                                    yaml_data["test"]["result"] = "FAIL"
                                    yaml_data["test"]["ttf_minutes"] = ttf
                                    
                                    yaml_data["classification"] = {
                                        "severity": severity,
                                        "failure_type": failure_type,
                                        "failure_stage": failure_stage,
                                        "reproducibility": reproducibility,
                                        "regression": regression
                                    }
                                    
                                    yaml_data["analysis"] = {
                                        "observed": observed,
                                        "xplorer_url": xplorer_url,
                                        "jira": jira_id,
                                        "jtag_analysis": jtag_analysis,
                                        "set_event_analysis": set_event_analysis
                                    }
                                    
                                    with open(yaml_path, "w") as f:
                                        yaml.dump(yaml_data, f, sort_keys=False)
                                    
                                    st.success("Failure details saved successfully!")
                                    st.session_state.fail_edit_id = None
                                    st.rerun()
                
                with cancel_col:
                    if st.button("❌ Cancel", key=f"cancel_fail_{execution_id}_{idx}"):
                        st.session_state.fail_edit_id = None
                        st.rerun()
                
                st.divider()
            
            # =============================
            # EDIT PANEL (EXISTING)
            # =============================
            if st.session_state.editing_id == execution_id and not is_scheduled:
                st.markdown(f"### ✏️ Editing: {row['Platform']} | {row['Test Name']}")
                
                program = row["Program"]
                oem = row["OEM"]
                firmware = row["Firmware"]
                firmware_path = (
                    Path(BASE_PATH)
                    / program
                    / oem
                    / f"Firmware_{firmware}_Official"
                )
                
                yaml_path = None
                yaml_data = None
                
                for path in firmware_path.rglob("execution.yaml"):
                    try:
                        with open(path, "r") as f:
                            data = yaml.safe_load(f)
                        if data and data.get("execution_id") == execution_id:
                            yaml_path = path
                            yaml_data = data
                            break
                    except Exception:
                        continue
                
                if yaml_data:
                    st.subheader("Test")
                    yaml_data["test"]["result"] = st.selectbox(
                        "Result",
                        ["PASS", "FAIL", "IN_PROGRESS"],
                        index=["PASS", "FAIL", "IN_PROGRESS"].index(
                            yaml_data["test"].get("result", "PASS")
                        ),
                        key=f"edit_result_{execution_id}_{idx}"
                    )
                    yaml_data["test"]["ttf_minutes"] = st.number_input(
                        "TTF",
                        value=int(yaml_data["test"].get("ttf_minutes") or 0),
                        key=f"edit_ttf_{execution_id}_{idx}"
                    )
                    
                    st.subheader("Classification")
                    classification = yaml_data.get("classification", {})
                    classification["severity"] = st.selectbox(
                        "Severity",
                        ["S1", "S2", "S3", "S4"],
                        key=f"edit_severity_{execution_id}_{idx}"
                    )
                    classification["failure_type"] = st.text_input(
                        "Failure Type",
                        value=classification.get("failure_type", ""),
                        key=f"edit_failure_type_{execution_id}_{idx}"
                    )
                    classification["failure_stage"] = st.text_input(
                        "Failure Stage",
                        value=classification.get("failure_stage", ""),
                        key=f"edit_failure_stage_{execution_id}_{idx}"
                    )
                    classification["regression"] = st.selectbox(
                        "Regression",
                        ["Yes", "No", "Unknown"],
                        key=f"edit_regression_{execution_id}_{idx}"
                    )
                    yaml_data["classification"] = classification
                    
                    st.subheader("Analysis")
                    analysis = yaml_data.get("analysis", {})
                    analysis["observed"] = st.text_area(
                        "Observed",
                        value=analysis.get("observed", ""),
                        key=f"edit_observed_{execution_id}_{idx}"
                    )
                    analysis["xplorer_url"] = st.text_area(
                        "Artifacts / Links",
                        value=analysis.get("xplorer_url", ""),
                        key=f"edit_xplorer_{execution_id}_{idx}"
                    )
                    analysis["jira"] = st.text_input(
                        "JIRA",
                        value=analysis.get("jira", ""),
                        key=f"edit_jira_{execution_id}_{idx}"
                    )
                    
                    st.markdown("#### Advanced Technical Details")
                    analysis["jtag_analysis"] = st.text_area(
                        "JTAG Analysis",
                        value=analysis.get("jtag_analysis", ""),
                        key=f"edit_jtag_{execution_id}_{idx}"
                    )
                    analysis["set_event_analysis"] = st.text_area(
                        "Set Event Analysis",
                        value=analysis.get("set_event_analysis", ""),
                        key=f"edit_setevent_{execution_id}_{idx}"
                    )
                    yaml_data["analysis"] = analysis
                    
                    c1, c2 = st.columns(2)
                    if c1.button("💾 Save", key=f"save_edit_{execution_id}_{idx}"):
                        with open(yaml_path, "w") as f:
                            yaml.dump(yaml_data, f, sort_keys=False)
                        st.success("Updated")
                        st.session_state.editing_id = None
                        st.rerun()
                    if c2.button("❌ Cancel", key=f"cancel_edit_{execution_id}_{idx}"):
                        st.session_state.editing_id = None
                        st.rerun()
                
                st.divider()

# ============================================================
# TAB 2 — PLATFORM VIEW
# ============================================================
with platform_tab:
    st.subheader("🖥️ Platform Tracking")
    
    if not filtered_df.empty:
        platform = st.selectbox(
            "Select Platform",
            filtered_df["Platform"].unique(),
            key="platform_view_select"
        )
        
        platform_df = filtered_df[filtered_df["Platform"] == platform]
        
        # Show scheduled tests for this platform
        st.markdown("#### 📅 Scheduled Tests for This Platform")
        platform_scheduled = get_platform_schedule_summary(BASE_PATH).get(platform, {})
        
        if platform_scheduled:
            sched_cols = st.columns(5)
            sched_cols[0].metric("Total Scheduled", platform_scheduled.get("total", 0))
            sched_cols[1].metric("In Progress", platform_scheduled.get("in_progress", 0))
            sched_cols[2].metric("Passed", platform_scheduled.get("passed", 0))
            sched_cols[3].metric("Failed", platform_scheduled.get("failed", 0))
            sched_cols[4].metric("Pending", platform_scheduled.get("scheduled", 0))
        else:
            st.info("No scheduled tests for this platform.")
        
        st.divider()
        
        st.subheader("Latest Status")
        latest = (
            platform_df
            .sort_values("Execution Date")
            .groupby("Test Name")
            .last()
            .reset_index()
        )
        st.dataframe(latest, use_container_width=True)
        
        st.divider()
        
        st.subheader("Execution History")
        st.dataframe(
            platform_df.sort_values("Execution Date", ascending=False),
            use_container_width=True
        )
    else:
        st.info("No execution data available.")

# ============================================================
# TAB 3 — ANALYTICS
# ============================================================
with analytics_tab:
    if not filtered_df.empty:
        st.subheader("📈 KPI Overview")
        total = len(filtered_df)
        passes = len(filtered_df[filtered_df["Result"] == "PASS"])
        fails = len(filtered_df[filtered_df["Result"] == "FAIL"])
        inprog = len(filtered_df[filtered_df["Result"] == "IN_PROGRESS"])
        fail_rate = round((fails / total) * 100, 2) if total else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Runs", total)
        c2.metric("Pass", passes, delta=f"{round((passes/total)*100, 1)}%" if total else "0%")
        c3.metric("Fail", fails, delta=f"-{fail_rate}%" if fails else "0%", delta_color="inverse")
        c4.metric("In Progress", inprog)
        
        st.divider()
        
        # Result distribution pie chart with IN_PROGRESS in yellow
        st.subheader("Result Distribution")
        result_counts = filtered_df["Result"].value_counts().reset_index()
        result_counts.columns = ["Result", "Count"]
        
        color_map = {
            "PASS": "#28a745",
            "FAIL": "#dc3545",
            "IN_PROGRESS": "#ffc107"
        }
        
        fig = px.pie(
            result_counts,
            values="Count",
            names="Result",
            color="Result",
            color_discrete_map=color_map,
            title="Overall Result Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Top failing tests
        st.subheader("Top Failing Tests")
        fail_df = filtered_df[filtered_df["Result"] == "FAIL"]
        if not fail_df.empty:
            top_tests = (
                fail_df.groupby("Test Name")
                .size()
                .reset_index(name="Failures")
                .sort_values(by="Failures", ascending=False)
                .head(10)
            )
            fig = px.bar(
                top_tests,
                x="Test Name",
                y="Failures",
                color="Failures",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No failures recorded!")
        
        st.divider()
        
        # Platform Stability
        st.subheader("Platform Stability")
        platform_stats = (
            filtered_df.groupby("Platform")
            .agg(
                total=("Result", "count"),
                fails=("Result", lambda x: (x == "FAIL").sum()),
                in_progress=("Result", lambda x: (x == "IN_PROGRESS").sum())
            )
        )
        platform_stats["Stability %"] = (
            100 - (platform_stats["fails"] / platform_stats["total"] * 100)
        )
        fig = px.bar(
            platform_stats.reset_index(),
            x="Platform",
            y="Stability %",
            color="Stability %",
            color_continuous_scale="Greens"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Firmware Health
        st.subheader("Firmware Health")
        fw_stats = (
            filtered_df.groupby("Firmware")
            .agg(
                total=("Result", "count"),
                fails=("Result", lambda x: (x == "FAIL").sum())
            )
        )
        fw_stats["Failure %"] = (
            fw_stats["fails"] / fw_stats["total"] * 100
        )
        fig = px.bar(
            fw_stats.reset_index(),
            x="Firmware",
            y="Failure %",
            color="Failure %",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Trend over time
        st.subheader("Failure Trend")
        trend_df = filtered_df.copy()
        trend_df["Date"] = pd.to_datetime(trend_df["Execution Date"]).dt.date
        daily = (
            trend_df.groupby(["Date", "Result"])
            .size()
            .reset_index(name="Count")
        )
        if not daily.empty:
            fig = px.line(
                daily,
                x="Date",
                y="Count",
                color="Result",
                markers=True,
                color_discrete_map={"PASS": "#28a745", "FAIL": "#dc3545", "IN_PROGRESS": "#ffc107"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # OEM comparison
        st.subheader("OEM Comparison")
        oem_stats = (
            filtered_df.groupby("OEM")
            .agg(
                Total=("Result", "count"),
                Fails=("Result", lambda x: (x == "FAIL").sum())
            )
            .reset_index()
        )
        oem_stats["Failure %"] = (
            oem_stats["Fails"] / oem_stats["Total"] * 100
        )
        fig = px.bar(
            oem_stats,
            x="OEM",
            y="Failure %",
            text="Failure %",
            color="Failure %",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for analytics.")

# ============================================================
# TAB 4 — COVERAGE OVERVIEW
# ============================================================
with coverage_overview_tab:
    st.subheader("📊 Coverage Overview")
    
    if not filtered_df.empty:
        coverage_df = filtered_df.dropna(subset=["Capacity", "Form Factor"]).copy()
        
        if not coverage_df.empty:
            coverage_agg = (
                coverage_df
                .groupby([
                    "Program",
                    "OEM",
                    "Platform",
                    "Firmware",
                    "Capacity",
                    "Form Factor"
                ])
                .agg(Result=("Result", "last"))
                .reset_index()
            )
            
            total = len(coverage_agg)
            platforms = coverage_agg["Platform"].nunique()
            oems = coverage_agg["OEM"].nunique()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Configs", total)
            c2.metric("Platforms", platforms)
            c3.metric("OEMs", oems)
            c4.metric("Firmware", coverage_agg["Firmware"].nunique())
            
            st.divider()
            
            # Coverage by Capacity
            st.subheader("Coverage by Capacity")
            cap = (
                coverage_agg.groupby("Capacity")
                .size()
                .reset_index(name="Count")
            )
            fig = px.bar(
                cap,
                x="Capacity",
                y="Count",
                color="Count",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Coverage by Form Factor
            st.subheader("Coverage by Form Factor")
            coverage_agg["Form Factor"] = coverage_agg["Form Factor"].astype(str)
            ff_order = ["2230", "2242", "2280"]
            ff = (
                coverage_agg.groupby("Form Factor")
                .size()
                .reindex(ff_order, fill_value=0)
                .reset_index(name="Count")
            )
            fig = px.bar(
                ff,
                x="Form Factor",
                y="Count",
                color="Count",
                category_orders={"Form Factor": ff_order},
                color_continuous_scale="Purples"
            )
            fig.update_xaxes(type="category")
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Coverage by OEM
            st.subheader("Coverage by OEM")
            oem = (
                coverage_agg.groupby("OEM")
                .size()
                .reset_index(name="Count")
            )
            fig = px.bar(
                oem,
                x="OEM",
                y="Count",
                color="Count",
                color_continuous_scale="Oranges"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Coverage by Firmware
            st.subheader("Coverage by Firmware")
            fw = (
                coverage_agg.groupby("Firmware")
                .size()
                .reset_index(name="Count")
            )
            fig = px.bar(
                fw,
                x="Firmware",
                y="Count",
                color="Count",
                color_continuous_scale="Greens"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            st.subheader("Detailed Coverage Table")
            st.dataframe(coverage_agg, use_container_width=True)
        else:
            st.info("No coverage data with Capacity and Form Factor available.")
    else:
        st.info("No coverage data available.")

# ============================================================
# GROUPED COVERAGE MATRIX - WITH CLICKABLE CARDS FOR FULL HISTORY
# ============================================================

with coverage_matrix_grouped_tab:
    st.subheader("📉 OEM Coverage Matrix")
    st.markdown("**💡 Click on any cell below to view full execution history**")
    
    if not filtered_df.empty:
        df2 = filtered_df.copy()
        df2["Config"] = (
            df2["Capacity"].astype(str)
            + "-"
            + df2["Form Factor"].astype(str)
        )
        
        # FIXED: build_card function to work with DataFrame groups
        def build_card(group_df):
            """Build HTML card stack from a DataFrame group."""
            group_df = group_df.sort_values("Execution Date", ascending=False)
            cards = []
            
            for _, r in group_df.head(5).iterrows():  # Show max 5 cards
                result = r["Result"]
                if result == "PASS":
                    status_class = "status-pass"
                elif result == "FAIL":
                    status_class = "status-fail"
                else:  # IN_PROGRESS
                    status_class = "status-progress"
                
                cfg = f"{r['Capacity']}-{r['Form Factor']}"
                firmware = r.get("Firmware", "N/A")
                
                card = (
                    f'<div class="card {status_class}">'
                    f'<b>{result}</b><br>'
                    f'{firmware}<br>'
                    f'<small>{cfg}</small>'
                    f'</div>'
                )
                cards.append(card)
            
            if cards:
                return (
                    '<div class="card-stack">'
                    + ''.join(cards) +
                    '</div>'
                )
            return ""
        
        # Group and build cards
        try:
            cell_df = (
                df2
                .groupby([
                    "OEM",
                    "Platform",
                    "Test Category",
                    "Test Name"
                ], as_index=False)
                .apply(build_card)
            )
            cell_df.columns = ["OEM", "Platform", "Test Category", "Test Name", "Cell"]
            
            if not cell_df.empty:
                pivot = cell_df.pivot(
                    index=["OEM", "Platform"],
                    columns=["Test Category", "Test Name"],
                    values="Cell"
                ).fillna("")
                
                html_table = pivot.to_html(escape=False, border=0)
                st.markdown(html_table, unsafe_allow_html=True)
                
                st.markdown("""
                    <style>
                    td {
                        vertical-align: top !important;
                        padding: 4px 8px !important;
                        white-space: nowrap;
                    }
                    th {
                        background: #2d2d2d !important;
                        color: white !important;
                        padding: 8px !important;
                    }
                    .card-stack {
                        display: flex;
                        flex-direction: row;
                        position: relative;
                        min-height: 50px;
                        align-items: center;
                        cursor: pointer;
                    }
                    .card-stack .card {
                        padding: 6px 10px;
                        border-radius: 6px;
                        font-size: 10px;
                        color: white;
                        margin-right: -16px;
                        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                        cursor: pointer;
                        min-width: 70px;
                        text-align: center;
                    }
                    .card-stack:hover .card {
                        margin-right: 4px;
                    }
                    .card:hover {
                        transform: translateY(-4px) scale(1.08);
                        z-index: 999;
                        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
                    }
                    .status-pass { background: linear-gradient(135deg, #1f7a1f 0%, #28a745 100%); }
                    .status-fail { background: linear-gradient(135deg, #b30000 0%, #dc3545 100%); }
                    .status-progress { background: linear-gradient(135deg, #d4a017 0%, #ffc107 100%); }
                    </style>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error building matrix: {str(e)}")
        
        st.divider()
        
        # =============================
        # CLICKABLE CELL HISTORY - FULL SCREEN MODAL STYLE
        # =============================
        st.markdown("### 🔍 Click to View Full History")
        st.markdown("Select a cell from the matrix above to see complete execution history:")
        
        # Get unique combinations from the data
        unique_combos = df2.groupby(["OEM", "Platform", "Test Name"]).size().reset_index()[["OEM", "Platform", "Test Name"]]
        
        # Create a more intuitive selection
        col1, col2 = st.columns(2)
        
        with col1:
            # OEM + Platform selection
            oem_platform_options = df2.groupby(["OEM", "Platform"]).size().reset_index()[["OEM", "Platform"]]
            oem_platform_options["display"] = oem_platform_options["OEM"] + " → " + oem_platform_options["Platform"]
            
            selected_oem_platform = st.selectbox(
                "Select OEM & Platform",
                oem_platform_options["display"].tolist(),
                key="matrix_oem_platform"
            )
            
            if selected_oem_platform:
                selected_oem = selected_oem_platform.split(" → ")[0]
                selected_platform = selected_oem_platform.split(" → ")[1]
        
        with col2:
            # Test selection based on OEM/Platform
            if selected_oem_platform:
                available_tests = df2[
                    (df2["OEM"] == selected_oem) & 
                    (df2["Platform"] == selected_platform)
                ]["Test Name"].unique().tolist()
                
                selected_test = st.selectbox(
                    "Select Test",
                    available_tests,
                    key="matrix_test"
                )
        
        # Show full history button
        if selected_oem_platform and selected_test:
            if st.button("📋 Show Full Execution History", use_container_width=True, type="primary"):
                st.session_state.show_history_modal = True
                st.session_state.history_modal_data = {
                    "oem": selected_oem,
                    "platform": selected_platform,
                    "test": selected_test
                }
        
        # =============================
        # FULL HISTORY DISPLAY (Modal-like)
        # =============================
        if st.session_state.show_history_modal and st.session_state.history_modal_data:
            modal_data = st.session_state.history_modal_data
            
            # Find matching data
            history_data = df2[
                (df2["OEM"] == modal_data["oem"]) &
                (df2["Platform"] == modal_data["platform"]) &
                (df2["Test Name"] == modal_data["test"])
            ].sort_values("Execution Date", ascending=False)
            
            st.markdown("---")
            
            # Header with close button
            header_col1, header_col2 = st.columns([6, 1])
            with header_col1:
                st.markdown(f"""
                ### 📜 Full Execution History
                **OEM:** {modal_data['oem']} | **Platform:** {modal_data['platform']} | **Test:** {modal_data['test']}
                """)
            with header_col2:
                if st.button("❌ Close", key="close_history_modal"):
                    st.session_state.show_history_modal = False
                    st.session_state.history_modal_data = None
                    st.rerun()
            
            st.markdown(f"**Total Executions:** {len(history_data)}")
            st.markdown("---")
            
            if not history_data.empty:
                # Display all cards in a grid layout
                cards_per_row = 3
                rows = [history_data.iloc[i:i+cards_per_row] for i in range(0, len(history_data), cards_per_row)]
                
                for row_data in rows:
                    cols = st.columns(cards_per_row)
                    for col_idx, (_, row) in enumerate(row_data.iterrows()):
                        with cols[col_idx]:
                            result = row["Result"]
                            if result == "PASS":
                                bg_color = "#28a745"
                                icon = "✅"
                                border_color = "#1f7a1f"
                            elif result == "FAIL":
                                bg_color = "#dc3545"
                                icon = "❌"
                                border_color = "#b30000"
                            else:
                                bg_color = "#ffc107"
                                icon = "🔄"
                                border_color = "#d4a017"
                            
                            exec_date = row["Execution Date"]
                            if hasattr(exec_date, 'strftime'):
                                exec_date_str = exec_date.strftime("%Y-%m-%d %H:%M")
                            else:
                                exec_date_str = str(exec_date)[:16]
                            
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {bg_color} 0%, {border_color} 100%);
                                color: white;
                                padding: 20px;
                                border-radius: 12px;
                                margin: 10px 0;
                                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                                transition: transform 0.2s ease;
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <span style="font-size: 28px;">{icon}</span>
                                    <strong style="font-size: 20px;">{result}</strong>
                                </div>
                                <hr style="border-color: rgba(255,255,255,0.3); margin: 10px 0;">
                                <div style="font-size: 13px;">
                                    <div><strong>📁 Firmware:</strong> {row.get("Firmware", "N/A")}</div>
                                    <div><strong>💾 Config:</strong> {row.get("Capacity", "N/A")}-{row.get("Form Factor", "N/A")}</div>
                                    <div><strong>🔄 Iteration:</strong> {row.get("Iteration", "N/A")}</div>
                                    <div><strong>📅 Date:</strong> {exec_date_str}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
            else:
                st.info("No history found for this combination.")
    else:
        st.info("No data available for matrix view.")