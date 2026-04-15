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

# Enhanced CSS
st.markdown("""
<style>
/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}

/* Tab styling */
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

/* Card stack styling - MAX 3 cards with overlap */
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
.status-scheduled { background: linear-gradient(135deg, #0d6efd 0%, #17a2b8 100%); }

/* Coverage matrix table */
#coverage-matrix {
    width: 100%;
    border-collapse: separate;
    border-spacing: 2px;
}

#coverage-matrix td {
    vertical-align: top !important;
    padding: 4px 8px !important;
    white-space: nowrap;
    background: #1e1e1e;
}

#coverage-matrix th {
    background: #2d2d2d !important;
    color: white !important;
    padding: 8px !important;
    position: sticky;
    top: 0;
}

/* History queue container */
.history-queue {
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    gap: 15px;
    padding: 10px 5px;
    scroll-behavior: smooth;
}

.history-queue::-webkit-scrollbar {
    height: 8px;
}

.history-queue::-webkit-scrollbar-track {
    background: #1e1e1e;
    border-radius: 4px;
}

.history-queue::-webkit-scrollbar-thumb {
    background: #ff4b4b;
    border-radius: 4px;
}

/* Button styling */
.stButton > button {
    transition: all 0.3s ease;
    border-radius: 8px;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Scrollbar */
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

/* Category section styling */
.category-section {
    background: #1a1a1a;
    border-radius: 12px;
    padding: 15px;
    margin: 15px 0;
    border-left: 4px solid #ff4b4b;
}

.category-header {
    color: #ff4b4b;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Platform View Enhanced Styles */
.platform-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 25px;
    margin-bottom: 20px;
    border: 1px solid #2a2a4a;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.platform-title {
    font-size: 28px;
    font-weight: bold;
    color: #fff;
    margin-bottom: 5px;
}

.platform-subtitle {
    font-size: 14px;
    color: #888;
}

.stat-card {
    background: linear-gradient(145deg, #1e1e2e 0%, #2a2a3e 100%);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid #333;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.stat-value {
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 5px;
}

.stat-label {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.health-indicator {
    width: 100%;
    height: 8px;
    background: #333;
    border-radius: 4px;
    margin-top: 10px;
    overflow: hidden;
}

.health-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}

.test-card {
    background: #1a1a2e;
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
    border-left: 4px solid;
    transition: all 0.3s ease;
}

.test-card:hover {
    transform: translateX(5px);
    box-shadow: 0 5px 20px rgba(0,0,0,0.2);
}

.test-card-pass { border-left-color: #28a745; }
.test-card-fail { border-left-color: #dc3545; }
.test-card-progress { border-left-color: #ffc107; }
.test-card-scheduled { border-left-color: #17a2b8; }

.info-box {
    background: linear-gradient(135deg, #1a1a2e 0%, #252540 100%);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #333;
}

.info-box-title {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.info-box-value {
    font-size: 16px;
    color: #fff;
    font-weight: 600;
}

.firmware-badge {
    display: inline-block;
    background: linear-gradient(135deg, #4a4a6a 0%, #3a3a5a 100%);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    color: #fff;
    margin: 2px;
}

.oem-badge {
    display: inline-block;
    background: linear-gradient(135deg, #ff4b4b 0%, #ff6b6b 100%);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    color: #fff;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Execution Dashboard")

# Build execution index
df = build_execution_index(BASE_PATH)

# Add Is Scheduled column
if not df.empty:
    df["Is Scheduled"] = False

# Merge scheduled tests
scheduled_records = get_all_scheduled_as_dataframe_records(BASE_PATH)
if scheduled_records:
    scheduled_df = pd.DataFrame(scheduled_records)
    scheduled_df["Execution Date"] = pd.to_datetime(scheduled_df["Execution Date"])
    if df.empty:
        df = scheduled_df
    else:
        df = pd.concat([df, scheduled_df], ignore_index=True)

# Sort dataframe
if not df.empty:
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
if "selected_card_cell" not in st.session_state:
    st.session_state.selected_card_cell = None
if "editing_history_card_id" not in st.session_state:
    st.session_state.editing_history_card_id = None

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
        iteration_filter = st.multiselect("Iteration", df["Iteration"].dropna().unique())
    with f6:
        category_filter = st.multiselect("Test Category", df["Test Category"].dropna().unique())

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
# TABS
# ============================================================
schedule_tab, table_tab, platform_tab, analytics_tab, coverage_overview_tab, coverage_matrix_grouped_tab = st.tabs([
    "📅 Scheduled Overview",
    "📋 Execution Records",
    "🖥️ Platform View",
    "📈 Analytics",
    "📊 Coverage Overview",
    "📉 Graph Grouped"
])

# ============================================================
# TAB 0 — SCHEDULED OVERVIEW
# ============================================================
with schedule_tab:
    st.subheader("📅 Scheduled Tests Overview")
    st.info("💡 To schedule new tests, go to the main app → Quick Schedule tab")

    test_mapping, test_list = load_test_registry("test_registry.xlsx")
    platform_data = load_mastersheet("MasterSheet.xlsx")
    schedule_summary = get_platform_schedule_summary(BASE_PATH)

    if schedule_summary:
        view_platform = st.selectbox(
            "Select Platform to View Scheduled Tests",
            ["All Platforms"] + list(schedule_summary.keys()),
            key="view_platform"
        )

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

        st.markdown("#### Scheduled Entries")

        all_entries = []
        if view_platform == "All Platforms":
            for plat, data in schedule_summary.items():
                all_entries.extend(data["entries"])
        else:
            all_entries = schedule_summary.get(view_platform, {}).get("entries", [])

        all_entries = sorted(
            all_entries,
            key=lambda x: (
                0 if x.get("status") == "IN_PROGRESS" else (1 if x.get("status") == "SCHEDULED" else 2),
            )
        )

        if all_entries:
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

                entry_id = entry.get("id", entry.get("execution_id"))
                if cols[7].button("🗑️", key=f"del_sched_{entry_id}"):
                    remove_scheduled_entry(BASE_PATH, entry_id)
                    st.success("Entry removed!")
                    st.rerun()

            st.divider()

            st.markdown("#### 📊 Schedule Visualization")
            viz_df = pd.DataFrame(all_entries)

            if not viz_df.empty:
                col1, col2 = st.columns(2)

                with col1:
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
        header = st.columns([2, 2, 1, 1, 1.5, 1, 1])
        header[0].markdown("**Platform**")
        header[1].markdown("**Test Name**")
        header[2].markdown("**Iteration**")
        header[3].markdown("**Run Type**")
        header[4].markdown("**Result**")
        header[5].markdown("**Severity**")
        header[6].markdown("**Details**")
        st.divider()

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

            new_result = cols[4].selectbox(
                "",
                ["PASS", "FAIL", "IN_PROGRESS"],
                index=["PASS", "FAIL", "IN_PROGRESS"].index(current_result),
                key=f"result_{execution_id}_{idx}"
            )

            if new_result != current_result:
                if new_result == "PASS":
                    if is_scheduled:
                        update_scheduled_entry_status(BASE_PATH, execution_id, "PASS")
                        st.success("Status updated to PASS")
                        st.rerun()
                    else:
                        program = row["Program"]
                        oem = row["OEM"]
                        firmware = row["Firmware"]
                        firmware_path = Path(BASE_PATH) / program / oem / f"Firmware_{firmware}_Official"
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

            # Expanded view
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

                history_df = filtered_df[
                    (filtered_df["Platform"] == row["Platform"]) &
                    (filtered_df["Test Name"] == row["Test Name"])
                ]

                st.markdown("##### Run History")
                history_display = history_df[["Iteration", "Result", "Execution Date"]].copy()
                history_display = history_display.sort_values("Execution Date", ascending=False)
                st.dataframe(history_display, use_container_width=True)

                if not is_scheduled:
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✏️ Edit Details", key=f"edit_{execution_id}_{idx}"):
                            st.session_state.editing_id = execution_id
                st.divider()

            # Failure detail panel
            if st.session_state.fail_edit_id == execution_id:
                st.markdown(f"### ❌ Record Failure Details: {row['Platform']} | {row['Test Name']}")

                is_scheduled_entry = row.get("Is Scheduled", False)

                st.markdown("#### Failure Classification")
                fc1, fc2, fc3 = st.columns(3)

                with fc1:
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

                with fc2:
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

                with fc3:
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
                                program = row["Program"]
                                oem = row["OEM"]
                                firmware = row["Firmware"]
                                firmware_path = Path(BASE_PATH) / program / oem / f"Firmware_{firmware}_Official"

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

            # Edit panel
            if st.session_state.editing_id == execution_id and not is_scheduled:
                st.markdown(f"### ✏️ Editing: {row['Platform']} | {row['Test Name']}")

                program = row["Program"]
                oem = row["OEM"]
                firmware = row["Firmware"]
                firmware_path = Path(BASE_PATH) / program / oem / f"Firmware_{firmware}_Official"

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
# TAB 2 — ENHANCED PLATFORM VIEW
# ============================================================
with platform_tab:
    if not filtered_df.empty:
        # Platform selector
        st.markdown("### 🖥️ Select Platform")
        platform = st.selectbox(
            "",
            filtered_df["Platform"].unique(),
            key="platform_view_select",
            label_visibility="collapsed"
        )

        platform_df = filtered_df[filtered_df["Platform"] == platform]

        # Get platform statistics
        total_executions = len(platform_df)
        pass_count = len(platform_df[platform_df["Result"] == "PASS"])
        fail_count = len(platform_df[platform_df["Result"] == "FAIL"])
        in_progress_count = len(platform_df[platform_df["Result"] == "IN_PROGRESS"])
        scheduled_count = len(platform_df[platform_df["Result"] == "SCHEDULED"])

        # Calculate health score
        if total_executions > 0:
            health_score = round((pass_count / total_executions) * 100, 1)
        else:
            health_score = 0

        # Get platform metadata
        platform_oem = platform_df["OEM"].iloc[0] if not platform_df.empty else "N/A"
        platform_program = platform_df["Program"].iloc[0] if not platform_df.empty else "N/A"
        unique_firmwares = platform_df["Firmware"].dropna().unique()
        unique_categories = platform_df["Test Category"].dropna().unique()

        # Latest execution date
        latest_exec = platform_df["Execution Date"].max() if not platform_df.empty else None
        if latest_exec:
            if hasattr(latest_exec, 'strftime'):
                latest_exec_str = latest_exec.strftime("%Y-%m-%d %H:%M")
            else:
                latest_exec_str = str(latest_exec)[:16]
        else:
            latest_exec_str = "N/A"

        # =============================
        # PLATFORM HEADER SECTION
        # =============================
        health_color = '#28a745' if health_score >= 80 else '#ffc107' if health_score >= 50 else '#dc3545'

        st.markdown(f"""
        <div class="platform-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="platform-title">🖥️ {platform}</div>
                    <div class="platform-subtitle">
                        <span class="oem-badge">{platform_oem}</span>
                        <span style="color: #888; margin: 0 10px;">|</span>
                        <span style="color: #888;">Program: {platform_program}</span>
                        <span style="color: #888; margin: 0 10px;">|</span>
                        <span style="color: #888;">Last Activity: {latest_exec_str}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 48px; font-weight: bold; color: {health_color};">
                        {health_score}%
                    </div>
                    <div style="font-size: 12px; color: #888; text-transform: uppercase;">Health Score</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =============================
        # KEY METRICS ROW
        # =============================
        st.markdown("### 📊 Key Metrics")

        m1, m2, m3, m4, m5, m6 = st.columns(6)

        with m1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color: #fff;">{total_executions}</div>
                <div class="stat-label">Total Runs</div>
            </div>
            """, unsafe_allow_html=True)

        with m2:
            pass_pct = (pass_count / total_executions * 100) if total_executions > 0 else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">{pass_count}</div>
                <div class="stat-label">Passed</div>
                <div class="health-indicator">
                    <div class="health-bar" style="width: {pass_pct}%; background: #28a745;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            fail_pct = (fail_count / total_executions * 100) if total_executions > 0 else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">{fail_count}</div>
                <div class="stat-label">Failed</div>
                <div class="health-indicator">
                    <div class="health-bar" style="width: {fail_pct}%; background: #dc3545;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with m4:
            progress_pct = (in_progress_count / total_executions * 100) if total_executions > 0 else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color: #ffc107;">{in_progress_count}</div>
                <div class="stat-label">In Progress</div>
                <div class="health-indicator">
                    <div class="health-bar" style="width: {progress_pct}%; background: #ffc107;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with m5:
            sched_pct = (scheduled_count / total_executions * 100) if total_executions > 0 else 0
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color: #17a2b8;">{scheduled_count}</div>
                <div class="stat-label">Scheduled</div>
                <div class="health-indicator">
                    <div class="health-bar" style="width: {sched_pct}%; background: #17a2b8;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with m6:
            unique_tests = platform_df["Test Name"].nunique()
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value" style="color: #9b59b6;">{unique_tests}</div>
                <div class="stat-label">Unique Tests</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =============================
        # CONFIGURATION & FIRMWARE INFO
        # =============================
        st.markdown("### ⚙️ Configuration Details")

        cfg1, cfg2, cfg3 = st.columns(3)

        with cfg1:
            st.markdown("""
            <div class="info-box">
                <div class="info-box-title">📦 Firmware Versions</div>
            </div>
            """, unsafe_allow_html=True)
            for fw in list(unique_firmwares)[:5]:
                fw_count = len(platform_df[platform_df["Firmware"] == fw])
                st.markdown(f'<span class="firmware-badge">{fw} ({fw_count})</span>', unsafe_allow_html=True)
            if len(unique_firmwares) > 5:
                st.markdown(f'<span style="color: #888; font-size: 12px;">+{len(unique_firmwares) - 5} more</span>', unsafe_allow_html=True)

        with cfg2:
            st.markdown("""
            <div class="info-box">
                <div class="info-box-title">🧪 Test Categories</div>
            </div>
            """, unsafe_allow_html=True)
            for cat in list(unique_categories)[:5]:
                cat_count = len(platform_df[platform_df["Test Category"] == cat])
                cat_pass = len(platform_df[(platform_df["Test Category"] == cat) & (platform_df["Result"] == "PASS")])
                cat_rate = round((cat_pass / cat_count * 100), 0) if cat_count > 0 else 0
                color = "#28a745" if cat_rate >= 80 else "#ffc107" if cat_rate >= 50 else "#dc3545"
                cat_display = cat[:25] + '...' if len(str(cat)) > 25 else cat
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #333;">
                    <span style="color: #fff; font-size: 13px;">{cat_display}</span>
                    <span style="color: {color}; font-weight: bold;">{cat_rate}%</span>
                </div>
                """, unsafe_allow_html=True)
            if len(unique_categories) > 5:
                st.markdown(f'<span style="color: #888; font-size: 12px;">+{len(unique_categories) - 5} more categories</span>', unsafe_allow_html=True)

        with cfg3:
            st.markdown("""
            <div class="info-box">
                <div class="info-box-title">💾 Hardware Configurations</div>
            </div>
            """, unsafe_allow_html=True)

            capacities = platform_df["Capacity"].dropna().unique()
            form_factors = platform_df["Form Factor"].dropna().unique()

            cap_badges = ''.join([f'<span class="firmware-badge">{c}</span>' for c in list(capacities)[:4]])
            ff_badges = ''.join([f'<span class="firmware-badge">{ff}</span>' for ff in list(form_factors)[:4]])

            st.markdown(f"""
            <div style="padding: 5px 0;">
                <span style="color: #888; font-size: 12px;">Capacities:</span><br>
                {cap_badges}
            </div>
            <div style="padding: 5px 0;">
                <span style="color: #888; font-size: 12px;">Form Factors:</span><br>
                {ff_badges}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =============================
        # VISUAL ANALYTICS ROW
        # =============================
        st.markdown("### 📈 Visual Analytics")

        chart1, chart2 = st.columns(2)

        with chart1:
            # Result distribution pie chart
            result_data = platform_df["Result"].value_counts().reset_index()
            result_data.columns = ["Result", "Count"]

            color_map = {
                "PASS": "#28a745",
                "FAIL": "#dc3545",
                "IN_PROGRESS": "#ffc107",
                "SCHEDULED": "#17a2b8"
            }

            fig = px.pie(
                result_data,
                values="Count",
                names="Result",
                color="Result",
                color_discrete_map=color_map,
                hole=0.6
            )
            fig.update_layout(
                title="Result Distribution",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        with chart2:
            # Test category performance bar chart
            cat_perf = platform_df.groupby("Test Category").agg(
                Total=("Result", "count"),
                Passed=("Result", lambda x: (x == "PASS").sum())
            ).reset_index()
            cat_perf["Pass Rate"] = (cat_perf["Passed"] / cat_perf["Total"] * 100).round(1)
            cat_perf = cat_perf.sort_values("Pass Rate", ascending=True).tail(8)

            fig = px.bar(
                cat_perf,
                x="Pass Rate",
                y="Test Category",
                orientation="h",
                color="Pass Rate",
                color_continuous_scale=["#dc3545", "#ffc107", "#28a745"]
            )
            fig.update_layout(
                title="Pass Rate by Test Category",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="white",
                xaxis_title="Pass Rate (%)",
                yaxis_title="",
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =============================
        # EXECUTION TIMELINE
        # =============================
        st.markdown("### 🕐 Recent Execution Timeline")

        # Get last 10 executions sorted by date
        recent_executions = platform_df.sort_values("Execution Date", ascending=False).head(10)

        if not recent_executions.empty:
            for idx, (_, row) in enumerate(recent_executions.iterrows()):
                result = row["Result"]

                # Determine colors and icons
                if result == "PASS":
                    dot_color = "#28a745"
                    icon = "✅"
                    card_class = "test-card-pass"
                elif result == "FAIL":
                    dot_color = "#dc3545"
                    icon = "❌"
                    card_class = "test-card-fail"
                elif result == "SCHEDULED":
                    dot_color = "#17a2b8"
                    icon = "⏳"
                    card_class = "test-card-scheduled"
                else:
                    dot_color = "#ffc107"
                    icon = "🔄"
                    card_class = "test-card-progress"

                exec_date = row["Execution Date"]
                if hasattr(exec_date, 'strftime'):
                    exec_date_str = exec_date.strftime("%Y-%m-%d %H:%M")
                else:
                    exec_date_str = str(exec_date)[:16] if exec_date else "N/A"

                test_name = row.get("Test Name", "N/A")
                test_name_display = test_name[:50] + '...' if len(str(test_name)) > 50 else test_name

                st.markdown(f"""
                <div class="test-card {card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <span style="font-size: 24px;">{icon}</span>
                            <div>
                                <div style="font-weight: bold; color: #fff; font-size: 14px;">
                                    {test_name_display}
                                </div>
                                <div style="color: #888; font-size: 12px;">
                                    {row.get("Test Category", "N/A")} | Iteration: {row.get("Iteration", "N/A")}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: {dot_color}; font-weight: bold;">{result}</div>
                            <div style="color: #888; font-size: 11px;">{exec_date_str}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent executions found.")

        st.markdown("<br>", unsafe_allow_html=True)

        # =============================
        # FAILURE ANALYSIS (if failures exist)
        # =============================
        fail_df = platform_df[platform_df["Result"] == "FAIL"]

        if not fail_df.empty:
            st.markdown("### ⚠️ Failure Analysis")

            fa1, fa2, fa3 = st.columns(3)

            with fa1:
                st.markdown("""
                <div class="info-box">
                    <div class="info-box-title">🔴 Top Failing Tests</div>
                </div>
                """, unsafe_allow_html=True)

                top_failing = fail_df.groupby("Test Name").size().reset_index(name="Failures")
                top_failing = top_failing.sort_values("Failures", ascending=False).head(5)

                for _, row in top_failing.iterrows():
                    test_name = row['Test Name']
                    test_display = test_name[:30] + '...' if len(str(test_name)) > 30 else test_name
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333;">
                        <span style="color: #fff; font-size: 12px;">{test_display}</span>
                        <span style="color: #dc3545; font-weight: bold; background: rgba(220, 53, 69, 0.2); padding: 2px 8px; border-radius: 10px;">{row['Failures']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with fa2:
                st.markdown("""
                <div class="info-box">
                    <div class="info-box-title">📊 Failures by Category</div>
                </div>
                """, unsafe_allow_html=True)

                fail_by_cat = fail_df.groupby("Test Category").size().reset_index(name="Failures")
                fail_by_cat = fail_by_cat.sort_values("Failures", ascending=False).head(5)

                for _, row in fail_by_cat.iterrows():
                    cat_name = row['Test Category']
                    cat_display = cat_name[:25] + '...' if len(str(cat_name)) > 25 else cat_name
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333;">
                        <span style="color: #fff; font-size: 12px;">{cat_display}</span>
                        <span style="color: #dc3545; font-weight: bold;">{row['Failures']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            with fa3:
                st.markdown("""
                <div class="info-box">
                    <div class="info-box-title">🎯 Severity Distribution</div>
                </div>
                """, unsafe_allow_html=True)

                if "Severity" in fail_df.columns:
                    severity_counts = fail_df["Severity"].value_counts()
                    severity_colors = {"S1": "#dc3545", "S2": "#fd7e14", "S3": "#ffc107", "S4": "#28a745"}

                    for sev, count in severity_counts.items():
                        if sev and str(sev) != "nan" and str(sev).strip():
                            color = severity_colors.get(sev, "#888")
                            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333;">
                                <span style="color: {color}; font-weight: bold;">{sev}</span>
                                <span style="color: #fff;">{count} failures</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color: #888;">No severity data available</span>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =============================
        # DETAILED DATA TABLE
        # =============================
        with st.expander("📋 View All Execution Records", expanded=False):
            st.markdown("#### Complete Execution History")

            # Add filters within expander
            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                result_filter_platform = st.multiselect(
                    "Filter by Result",
                    platform_df["Result"].unique(),
                    key="platform_result_filter"
                )

            with filter_col2:
                category_filter_platform = st.multiselect(
                    "Filter by Category",
                    platform_df["Test Category"].unique(),
                    key="platform_category_filter"
                )

            with filter_col3:
                firmware_filter_platform = st.multiselect(
                    "Filter by Firmware",
                    platform_df["Firmware"].unique(),
                    key="platform_firmware_filter"
                )

            # Apply filters
            display_df = platform_df.copy()
            if result_filter_platform:
                display_df = display_df[display_df["Result"].isin(result_filter_platform)]
            if category_filter_platform:
                display_df = display_df[display_df["Test Category"].isin(category_filter_platform)]
            if firmware_filter_platform:
                display_df = display_df[display_df["Firmware"].isin(firmware_filter_platform)]

            # Display table
            display_cols = ["Test Name", "Test Category", "Result", "Firmware", "Iteration", "Capacity", "Form Factor", "Execution Date"]
            available_cols = [col for col in display_cols if col in display_df.columns]

            st.dataframe(
                display_df[available_cols].sort_values("Execution Date", ascending=False),
                use_container_width=True,
                height=400
            )

            # Export option
            csv = display_df[available_cols].to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"{platform}_executions.csv",
                mime="text/csv"
            )

    else:
        st.info("No execution data available. Run some tests to see platform statistics.")

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
                color_discrete_map={
                    "PASS": "#28a745",
                    "FAIL": "#dc3545",
                    "IN_PROGRESS": "#ffc107"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

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
# TAB 5 — GROUPED COVERAGE MATRIX (WITH CATEGORY-WISE QUEUE HISTORY)
# ============================================================
with coverage_matrix_grouped_tab:
    st.subheader("📉 OEM Coverage Matrix")
    st.markdown("**💡 View the matrix below, then use the filters to view full history organized by Test Category**")

    if not filtered_df.empty:
        df2 = filtered_df.copy()
        df2["Config"] = df2["Capacity"].astype(str) + "-" + df2["Form Factor"].astype(str)

        # Build card function - MAX 3 CARDS with overlapping
        def build_card(group_df):
            """Build HTML card stack from a DataFrame group - MAX 3 cards."""
            group_df = group_df.sort_values("Execution Date", ascending=False)
            cards = []
            for _, r in group_df.head(3).iterrows():
                result = r["Result"]
                if result == "PASS":
                    status_class = "status-pass"
                elif result == "FAIL":
                    status_class = "status-fail"
                elif result == "SCHEDULED":
                    status_class = "status-scheduled"
                else:
                    status_class = "status-progress"

                cfg = f"{r['Capacity']}-{r['Form Factor']}"
                firmware = r.get("Firmware", "N/A")
                card = f'<div class="card {status_class}"><b>{result}</b><br>{firmware}<br><small>{cfg}</small></div>'
                cards.append(card)

            if cards:
                return '<div class="card-stack">' + ''.join(cards) + '</div>'
            return ""

        # Build and display the original HTML matrix
        try:
            cell_df = df2.groupby(
                ["OEM", "Platform", "Test Category", "Test Name"],
                as_index=False
            ).apply(build_card)
            cell_df.columns = ["OEM", "Platform", "Test Category", "Test Name", "Cell"]

            if not cell_df.empty:
                pivot = cell_df.pivot(
                    index=["OEM", "Platform"],
                    columns=["Test Category", "Test Name"],
                    values="Cell"
                ).fillna("")

                html_table = pivot.to_html(escape=False, border=0, table_id="coverage-matrix")
                st.markdown(html_table, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error building matrix: {str(e)}")

        st.divider()

        # ============================================================
        # HISTORY SECTION WITH FILTERS
        # ============================================================
        st.markdown("### 📜 View Execution History")
        st.markdown("*Select OEM, Platform, and optionally Test Category. History is organized by category with latest entries on the left (queue order).*")

        # Get unique values for filters
        available_oems = sorted(df2["OEM"].dropna().unique().tolist())
        available_platforms = sorted(df2["Platform"].dropna().unique().tolist())
        available_categories = sorted(df2["Test Category"].dropna().unique().tolist())

        # Filter dropdowns in columns
        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            selected_oem = st.selectbox(
                "Select OEM",
                ["-- Select --"] + available_oems,
                key="hist_oem_select"
            )

        # Filter platforms based on OEM selection
        if selected_oem != "-- Select --":
            filtered_platforms = sorted(
                df2[df2["OEM"] == selected_oem]["Platform"].dropna().unique().tolist()
            )
        else:
            filtered_platforms = available_platforms

        with filter_col2:
            selected_platform = st.selectbox(
                "Select Platform",
                ["-- Select --"] + filtered_platforms,
                key="hist_platform_select"
            )

        # Filter categories based on OEM and Platform selection
        if selected_oem != "-- Select --" and selected_platform != "-- Select --":
            filtered_categories = sorted(
                df2[
                    (df2["OEM"] == selected_oem) &
                    (df2["Platform"] == selected_platform)
                ]["Test Category"].dropna().unique().tolist()
            )
        elif selected_oem != "-- Select --":
            filtered_categories = sorted(
                df2[df2["OEM"] == selected_oem]["Test Category"].dropna().unique().tolist()
            )
        else:
            filtered_categories = available_categories

        with filter_col3:
            selected_category = st.selectbox(
                "Select Test Category",
                ["-- All Categories --"] + filtered_categories,
                key="hist_category_select"
            )

        # Show history button
        if selected_oem != "-- Select --" and selected_platform != "-- Select --":
            if st.button("🔍 Show History", type="primary", key="show_history_btn"):
                st.session_state.selected_card_cell = {
                    "oem": selected_oem,
                    "platform": selected_platform,
                    "test_category": selected_category if selected_category != "-- All Categories --" else None
                }

        # ============================================================
        # DISPLAY HISTORY WHEN CELL IS SELECTED - CATEGORY WISE QUEUE
        # ============================================================
        if st.session_state.selected_card_cell:
            cell_data = st.session_state.selected_card_cell

            # Build query based on selections
            history_query = df2[
                (df2["OEM"] == cell_data["oem"]) &
                (df2["Platform"] == cell_data["platform"])
            ]

            if cell_data.get("test_category"):
                history_query = history_query[
                    history_query["Test Category"] == cell_data["test_category"]
                ]
                category_label = cell_data["test_category"]
            else:
                category_label = "All Categories"

            # Sort by execution date descending (latest first - for queue order)
            history_data = history_query.sort_values(
                "Execution Date",
                ascending=False
            ).reset_index(drop=True)

            # Header
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #ff4b4b 0%, #ff6b6b 100%);
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
            ">
                <h3 style="color: white; margin: 0;">📜 Execution History (Queue Order)</h3>
                <p style="color: white; margin: 10px 0 0 0;">
                    <strong>OEM:</strong> {cell_data['oem']} |
                    <strong>Platform:</strong> {cell_data['platform']} |
                    <strong>Test Category:</strong> {category_label}
                </p>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 12px;">
                    ⬅️ Latest entries appear on the left, older entries on the right (like a queue)
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Close button
            if st.button("❌ Close History", key="close_history"):
                st.session_state.selected_card_cell = None
                st.session_state.editing_history_card_id = None
                st.rerun()

            # Summary metrics
            st.markdown("---")
            summary_cols = st.columns(5)
            total_records = len(history_data)
            pass_count = len(history_data[history_data["Result"] == "PASS"])
            fail_count = len(history_data[history_data["Result"] == "FAIL"])
            in_progress_count = len(history_data[history_data["Result"] == "IN_PROGRESS"])
            scheduled_count = len(history_data[history_data["Result"] == "SCHEDULED"])

            summary_cols[0].metric("📊 Total", total_records)
            summary_cols[1].metric("✅ Passed", pass_count)
            summary_cols[2].metric("❌ Failed", fail_count)
            summary_cols[3].metric("🔄 In Progress", in_progress_count)
            summary_cols[4].metric("⏳ Scheduled", scheduled_count)

            unique_tests = history_data["Test Name"].nunique()
            unique_categories = history_data["Test Category"].nunique()
            st.markdown(f"**📋 Found {unique_tests} unique tests across {unique_categories} categories**")
            st.markdown("---")

            if not history_data.empty:
                # Group by Test Category
                categories_in_data = sorted(history_data["Test Category"].unique())

                for category in categories_in_data:
                    category_data = history_data[history_data["Test Category"] == category]

                    # Sort by execution date descending (latest first - queue order)
                    category_data = category_data.sort_values("Execution Date", ascending=False)

                    # Category header with count
                    cat_pass = len(category_data[category_data["Result"] == "PASS"])
                    cat_fail = len(category_data[category_data["Result"] == "FAIL"])
                    cat_progress = len(category_data[category_data["Result"] == "IN_PROGRESS"])
                    cat_scheduled = len(category_data[category_data["Result"] == "SCHEDULED"])

                    st.markdown(f"""
                    <div class="category-section">
                        <div class="category-header">
                            📁 {category}
                            <span style="font-size: 12px; color: #888; font-weight: normal;">
                                ({len(category_data)} executions |
                                ✅ {cat_pass} | ❌ {cat_fail} | 🔄 {cat_progress} | ⏳ {cat_scheduled})
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Display cards in horizontal queue (latest on left)
                    num_cards = len(category_data)

                    if num_cards > 0:
                        # Create a container for horizontal scrolling
                        with st.container():
                            # Determine number of columns (max 6 visible, rest scrollable)
                            visible_cols = min(6, num_cards)
                            cols = st.columns(visible_cols)

                            for card_idx, (df_idx, row) in enumerate(category_data.iterrows()):
                                col_idx = card_idx % visible_cols

                                with cols[col_idx]:
                                    result = row["Result"]
                                    execution_id = row["Execution ID"]
                                    is_scheduled = row.get("Is Scheduled", False)
                                    card_unique_id = f"{execution_id}_{category}_{card_idx}_{df_idx}"

                                    # Determine colors
                                    if result == "PASS":
                                        bg_color = "#28a745"
                                        border_color = "#1f7a1f"
                                        icon = "✅"
                                    elif result == "FAIL":
                                        bg_color = "#dc3545"
                                        border_color = "#b30000"
                                        icon = "❌"
                                    elif result == "SCHEDULED":
                                        bg_color = "#17a2b8"
                                        border_color = "#0d6efd"
                                        icon = "⏳"
                                    else:
                                        bg_color = "#ffc107"
                                        border_color = "#d4a017"
                                        icon = "🔄"

                                    # Format date
                                    exec_date = row["Execution Date"]
                                    if hasattr(exec_date, 'strftime'):
                                        exec_date_str = exec_date.strftime("%Y-%m-%d %H:%M")
                                    else:
                                        exec_date_str = str(exec_date)[:16] if exec_date else "N/A"

                                    is_editing = st.session_state.editing_history_card_id == card_unique_id
                                    card_border = "3px solid #00d4ff" if is_editing else "none"

                                    # Queue position indicator
                                    position_label = "🆕 Latest" if card_idx == 0 else f"#{card_idx + 1}"

                                    # Card HTML
                                    st.markdown(f"""
                                    <div style="
                                        background: linear-gradient(135deg, {bg_color} 0%, {border_color} 100%);
                                        color: white;
                                        padding: 15px;
                                        border-radius: 12px;
                                        margin: 5px 0;
                                        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                                        border: {card_border};
                                        min-height: 200px;
                                    ">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                            <span style="font-size: 10px; background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">{position_label}</span>
                                            <span style="font-size: 24px;">{icon}</span>
                                        </div>
                                        <div style="text-align: center; margin-bottom: 8px;">
                                            <strong style="font-size: 16px;">{result}</strong>
                                        </div>
                                        <hr style="border-color: rgba(255,255,255,0.3); margin: 8px 0;">
                                        <div style="font-size: 11px;">
                                            <div><strong>🧪</strong> {row.get("Test Name", "N/A")[:20]}{'...' if len(str(row.get("Test Name", ""))) > 20 else ''}</div>
                                            <div><strong>📦</strong> {row.get("Firmware", "N/A")}</div>
                                            <div><strong>💾</strong> {row.get("Capacity", "N/A")}-{row.get("Form Factor", "N/A")}</div>
                                            <div><strong>🔄</strong> {row.get("Iteration", "N/A")}</div>
                                            <div><strong>📅</strong> {exec_date_str}</div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # Edit button
                                    edit_btn_key = f"edit_hist_{card_unique_id}"
                                    if st.button(
                                        "✏️" if not is_editing else "📝",
                                        key=edit_btn_key,
                                        use_container_width=True,
                                        type="primary" if is_editing else "secondary"
                                    ):
                                        if is_editing:
                                            st.session_state.editing_history_card_id = None
                                        else:
                                            st.session_state.editing_history_card_id = card_unique_id
                                        st.rerun()

                                    # Inline edit form
                                    if is_editing:
                                        st.markdown("---")
                                        st.markdown("##### ✏️ Edit")

                                        form_key = f"edit_form_{card_unique_id}"

                                        with st.form(key=form_key):
                                            current_result_idx = ["PASS", "FAIL", "IN_PROGRESS"].index(result) if result in ["PASS", "FAIL", "IN_PROGRESS"] else 2

                                            edit_result = st.selectbox(
                                                "Result",
                                                ["PASS", "FAIL", "IN_PROGRESS"],
                                                index=current_result_idx,
                                                key=f"res_{card_unique_id}"
                                            )

                                            if edit_result == "FAIL":
                                                edit_severity = st.selectbox(
                                                    "Severity",
                                                    ["S1", "S2", "S3", "S4"],
                                                    key=f"sev_{card_unique_id}"
                                                )
                                                edit_fail_type = st.selectbox(
                                                    "Failure Type",
                                                    ["BSOD", "Hang", "Reset", "Power", "Performance", "Other"],
                                                    key=f"ftype_{card_unique_id}"
                                                )
                                                edit_fail_stage = st.selectbox(
                                                    "Failure Stage",
                                                    ["Boot", "Init", "IO", "Power", "Reset", "Runtime", "Unknown"],
                                                    key=f"fstage_{card_unique_id}"
                                                )
                                                edit_repro = st.selectbox(
                                                    "Reproducibility",
                                                    ["Always", "Intermittent", "Rare", "Not Reproducible"],
                                                    key=f"repro_{card_unique_id}"
                                                )
                                                edit_regression = st.selectbox(
                                                    "Regression",
                                                    ["Yes", "No", "Unknown"],
                                                    key=f"reg_{card_unique_id}"
                                                )
                                                edit_observed = st.text_area(
                                                    "Observed",
                                                    key=f"obs_{card_unique_id}"
                                                )
                                                edit_artifacts = st.text_area(
                                                    "Artifacts",
                                                    key=f"art_{card_unique_id}"
                                                )
                                                edit_jira = st.text_input(
                                                    "JIRA",
                                                    key=f"jira_{card_unique_id}"
                                                )
                                            else:
                                                edit_severity = "S1"
                                                edit_fail_type = "Other"
                                                edit_fail_stage = "Unknown"
                                                edit_repro = "Not Reproducible"
                                                edit_regression = "Unknown"
                                                edit_observed = ""
                                                edit_artifacts = ""
                                                edit_jira = ""

                                            edit_ttf = st.number_input(
                                                "TTF (min)",
                                                min_value=0,
                                                value=int(row.get("TTF (min)", 0) or 0),
                                                key=f"ttf_{card_unique_id}"
                                            )

                                            submitted = st.form_submit_button(
                                                "💾 Save",
                                                type="primary",
                                                use_container_width=True
                                            )

                                            if submitted:
                                                try:
                                                    if is_scheduled:
                                                        additional_data = {"ttf_minutes": edit_ttf}
                                                        if edit_result == "FAIL":
                                                            additional_data.update({
                                                                "classification": {
                                                                    "severity": edit_severity,
                                                                    "failure_type": edit_fail_type,
                                                                    "failure_stage": edit_fail_stage,
                                                                    "reproducibility": edit_repro,
                                                                    "regression": edit_regression
                                                                },
                                                                "analysis": {
                                                                    "observed": edit_observed,
                                                                    "xplorer_url": edit_artifacts,
                                                                    "jira": edit_jira
                                                                },
                                                                "severity": edit_severity
                                                            })
                                                        update_scheduled_entry_status(
                                                            BASE_PATH,
                                                            execution_id,
                                                            edit_result,
                                                            additional_data
                                                        )
                                                        st.success("✅ Updated!")
                                                        st.session_state.editing_history_card_id = None
                                                        st.rerun()
                                                    else:
                                                        program = row.get("Program")
                                                        oem = row.get("OEM")
                                                        firmware = row.get("Firmware")

                                                        if program and oem and firmware:
                                                            firmware_path = (
                                                                Path(BASE_PATH)
                                                                / program
                                                                / oem
                                                                / f"Firmware_{firmware}_Official"
                                                            )

                                                            yaml_found = False
                                                            for path in firmware_path.rglob("execution.yaml"):
                                                                try:
                                                                    with open(path, "r") as f:
                                                                        data = yaml.safe_load(f)
                                                                    if data and data.get("execution_id") == execution_id:
                                                                        data["test"]["result"] = edit_result
                                                                        data["test"]["ttf_minutes"] = edit_ttf

                                                                        if edit_result == "FAIL":
                                                                            data["classification"] = {
                                                                                "severity": edit_severity,
                                                                                "failure_type": edit_fail_type,
                                                                                "failure_stage": edit_fail_stage,
                                                                                "reproducibility": edit_repro,
                                                                                "regression": edit_regression
                                                                            }
                                                                            data["analysis"] = {
                                                                                "observed": edit_observed,
                                                                                "xplorer_url": edit_artifacts,
                                                                                "jira": edit_jira
                                                                            }

                                                                        with open(path, "w") as f:
                                                                            yaml.dump(data, f, sort_keys=False)

                                                                        yaml_found = True
                                                                        st.success("✅ Saved!")
                                                                        st.session_state.editing_history_card_id = None
                                                                        st.rerun()
                                                                        break
                                                                except Exception:
                                                                    continue

                                                            if not yaml_found:
                                                                st.error("❌ File not found.")
                                                        else:
                                                            st.error("❌ Missing info.")
                                                except Exception as e:
                                                    st.error(f"❌ Error: {str(e)}")

                                        # Cancel button
                                        if st.button("❌ Cancel", key=f"cancel_{card_unique_id}"):
                                            st.session_state.editing_history_card_id = None
                                            st.rerun()

                            # If there are more cards than visible columns, show remaining in next rows
                            if num_cards > visible_cols:
                                remaining_cards = list(category_data.iterrows())[visible_cols:]

                                for batch_start in range(0, len(remaining_cards), visible_cols):
                                    batch = remaining_cards[batch_start:batch_start + visible_cols]
                                    cols = st.columns(visible_cols)

                                    for batch_idx, (df_idx, row) in enumerate(batch):
                                        card_idx = visible_cols + batch_start + batch_idx

                                        with cols[batch_idx]:
                                            result = row["Result"]
                                            execution_id = row["Execution ID"]
                                            is_scheduled = row.get("Is Scheduled", False)
                                            card_unique_id = f"{execution_id}_{category}_{card_idx}_{df_idx}"

                                            # Determine colors
                                            if result == "PASS":
                                                bg_color = "#28a745"
                                                border_color = "#1f7a1f"
                                                icon = "✅"
                                            elif result == "FAIL":
                                                bg_color = "#dc3545"
                                                border_color = "#b30000"
                                                icon = "❌"
                                            elif result == "SCHEDULED":
                                                bg_color = "#17a2b8"
                                                border_color = "#0d6efd"
                                                icon = "⏳"
                                            else:
                                                bg_color = "#ffc107"
                                                border_color = "#d4a017"
                                                icon = "🔄"

                                            exec_date = row["Execution Date"]
                                            if hasattr(exec_date, 'strftime'):
                                                exec_date_str = exec_date.strftime("%Y-%m-%d %H:%M")
                                            else:
                                                exec_date_str = str(exec_date)[:16] if exec_date else "N/A"

                                            is_editing = st.session_state.editing_history_card_id == card_unique_id
                                            card_border = "3px solid #00d4ff" if is_editing else "none"
                                            position_label = f"#{card_idx + 1}"

                                            st.markdown(f"""
                                            <div style="
                                                background: linear-gradient(135deg, {bg_color} 0%, {border_color} 100%);
                                                color: white;
                                                padding: 15px;
                                                border-radius: 12px;
                                                margin: 5px 0;
                                                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                                                border: {card_border};
                                                min-height: 200px;
                                            ">
                                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                    <span style="font-size: 10px; background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px;">{position_label}</span>
                                                    <span style="font-size: 24px;">{icon}</span>
                                                </div>
                                                <div style="text-align: center; margin-bottom: 8px;">
                                                    <strong style="font-size: 16px;">{result}</strong>
                                                </div>
                                                <hr style="border-color: rgba(255,255,255,0.3); margin: 8px 0;">
                                                <div style="font-size: 11px;">
                                                    <div><strong>🧪</strong> {row.get("Test Name", "N/A")[:20]}{'...' if len(str(row.get("Test Name", ""))) > 20 else ''}</div>
                                                    <div><strong>📦</strong> {row.get("Firmware", "N/A")}</div>
                                                    <div><strong>💾</strong> {row.get("Capacity", "N/A")}-{row.get("Form Factor", "N/A")}</div>
                                                    <div><strong>🔄</strong> {row.get("Iteration", "N/A")}</div>
                                                    <div><strong>📅</strong> {exec_date_str}</div>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)

                                            edit_btn_key = f"edit_hist_{card_unique_id}"
                                            if st.button(
                                                "✏️" if not is_editing else "📝",
                                                key=edit_btn_key,
                                                use_container_width=True,
                                                type="primary" if is_editing else "secondary"
                                            ):
                                                if is_editing:
                                                    st.session_state.editing_history_card_id = None
                                                else:
                                                    st.session_state.editing_history_card_id = card_unique_id
                                                st.rerun()

                                            if is_editing:
                                                st.markdown("---")
                                                st.markdown("##### ✏️ Edit")

                                                form_key = f"edit_form_{card_unique_id}"

                                                with st.form(key=form_key):
                                                    current_result_idx = ["PASS", "FAIL", "IN_PROGRESS"].index(result) if result in ["PASS", "FAIL", "IN_PROGRESS"] else 2

                                                    edit_result = st.selectbox(
                                                        "Result",
                                                        ["PASS", "FAIL", "IN_PROGRESS"],
                                                        index=current_result_idx,
                                                        key=f"res_{card_unique_id}"
                                                    )

                                                    if edit_result == "FAIL":
                                                        edit_severity = st.selectbox("Severity", ["S1", "S2", "S3", "S4"], key=f"sev_{card_unique_id}")
                                                        edit_fail_type = st.selectbox("Failure Type", ["BSOD", "Hang", "Reset", "Power", "Performance", "Other"], key=f"ftype_{card_unique_id}")
                                                        edit_fail_stage = st.selectbox("Failure Stage", ["Boot", "Init", "IO", "Power", "Reset", "Runtime", "Unknown"], key=f"fstage_{card_unique_id}")
                                                        edit_repro = st.selectbox("Reproducibility", ["Always", "Intermittent", "Rare", "Not Reproducible"], key=f"repro_{card_unique_id}")
                                                        edit_regression = st.selectbox("Regression", ["Yes", "No", "Unknown"], key=f"reg_{card_unique_id}")
                                                        edit_observed = st.text_area("Observed", key=f"obs_{card_unique_id}")
                                                        edit_artifacts = st.text_area("Artifacts", key=f"art_{card_unique_id}")
                                                        edit_jira = st.text_input("JIRA", key=f"jira_{card_unique_id}")
                                                    else:
                                                        edit_severity, edit_fail_type, edit_fail_stage = "S1", "Other", "Unknown"
                                                        edit_repro, edit_regression = "Not Reproducible", "Unknown"
                                                        edit_observed, edit_artifacts, edit_jira = "", "", ""

                                                    edit_ttf = st.number_input("TTF (min)", min_value=0, value=int(row.get("TTF (min)", 0) or 0), key=f"ttf_{card_unique_id}")

                                                    submitted = st.form_submit_button("💾 Save", type="primary", use_container_width=True)

                                                    if submitted:
                                                        try:
                                                            if is_scheduled:
                                                                additional_data = {"ttf_minutes": edit_ttf}
                                                                if edit_result == "FAIL":
                                                                    additional_data.update({
                                                                        "classification": {"severity": edit_severity, "failure_type": edit_fail_type, "failure_stage": edit_fail_stage, "reproducibility": edit_repro, "regression": edit_regression},
                                                                        "analysis": {"observed": edit_observed, "xplorer_url": edit_artifacts, "jira": edit_jira},
                                                                        "severity": edit_severity
                                                                    })
                                                                update_scheduled_entry_status(BASE_PATH, execution_id, edit_result, additional_data)
                                                                st.success("✅ Updated!")
                                                                st.session_state.editing_history_card_id = None
                                                                st.rerun()
                                                            else:
                                                                program, oem, firmware = row.get("Program"), row.get("OEM"), row.get("Firmware")
                                                                if program and oem and firmware:
                                                                    firmware_path = Path(BASE_PATH) / program / oem / f"Firmware_{firmware}_Official"
                                                                    for path in firmware_path.rglob("execution.yaml"):
                                                                        try:
                                                                            with open(path, "r") as f:
                                                                                data = yaml.safe_load(f)
                                                                            if data and data.get("execution_id") == execution_id:
                                                                                data["test"]["result"] = edit_result
                                                                                data["test"]["ttf_minutes"] = edit_ttf
                                                                                if edit_result == "FAIL":
                                                                                    data["classification"] = {"severity": edit_severity, "failure_type": edit_fail_type, "failure_stage": edit_fail_stage, "reproducibility": edit_repro, "regression": edit_regression}
                                                                                    data["analysis"] = {"observed": edit_observed, "xplorer_url": edit_artifacts, "jira": edit_jira}
                                                                                with open(path, "w") as f:
                                                                                    yaml.dump(data, f, sort_keys=False)
                                                                                st.success("✅ Saved!")
                                                                                st.session_state.editing_history_card_id = None
                                                                                st.rerun()
                                                                                break
                                                                        except:
                                                                            continue
                                                        except Exception as e:
                                                            st.error(f"❌ Error: {str(e)}")

                                                if st.button("❌ Cancel", key=f"cancel_{card_unique_id}"):
                                                    st.session_state.editing_history_card_id = None
                                                    st.rerun()

                    st.markdown("---")

            else:
                st.info("No history found for this selection.")
        else:
            # No selection made yet
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #2d2d2d 0%, #1e1e1e 100%);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                border: 2px dashed #555;
            ">
                <h4 style="color: #ff4b4b;">👆 Select from the dropdowns above</h4>
                <p style="color: #888; font-size: 14px;">
                    Choose OEM and Platform (required), optionally select a Test Category,<br>
                    then click "Show History" to view execution details organized by category.<br><br>
                    <strong>Queue Order:</strong> Latest entries appear on the left ⬅️, older entries on the right ➡️
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No data available for matrix view.")