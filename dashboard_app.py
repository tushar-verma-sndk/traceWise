import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from pathlib import Path
from modules.index_builder import build_execution_index
from modules.utils import load_config

config = load_config()
BASE_PATH = config["root_data_path"]

st.set_page_config(page_title="Execution Dashboard", layout="wide")

# Hide Streamlit UI
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Execution Dashboard")

df = build_execution_index(BASE_PATH)

if df.empty:
    st.warning("No executions logged yet.")
    st.stop()

# ============================================================
# GLOBAL FILTERS
# ============================================================

st.subheader("Global Filters")

f1, f2, f3, f4, f5, f6 = st.columns(6)

with f1:
    program_filter = st.multiselect("Program", df["Program"].unique())

with f2:
    oem_filter = st.multiselect("OEM", df["OEM"].unique())

with f3:
    firmware_filter = st.multiselect("Firmware", df["Firmware"].unique())

with f4:
    result_filter = st.multiselect("Result", df["Result"].unique())

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

st.divider()

# ============================================================
# TABS
# ============================================================

table_tab,platform_tab, analytics_tab,coverage_overview_tab, coverage_board_tab = st.tabs(
    [
        "Execution Records",
        "Platform View",
        "Analytics",
        "COverage",
        "Coverage Board"
    ]
)

# ============================================================
# TAB 1 — EXECUTION RECORDS
# ============================================================

with table_tab:

    st.subheader("Execution Records")

    if filtered_df.empty:
        st.info("No records found.")
        st.stop()

    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None

    if "expanded_rows" not in st.session_state:
        st.session_state.expanded_rows = set()

    # ---------- HEADER ----------
    header = st.columns([2.5, 2.5, 1, 1, 1, 1, 1])

    header[0].markdown("**Platform**")
    header[1].markdown("**Test Name**")
    header[2].markdown("**Iteration**")
    header[3].markdown("**Run Type**")
    header[4].markdown("**Result**")
    header[5].markdown("**Severity**")
    header[6].markdown("**Details**")

    st.divider()

    # ---------- ROWS ----------
    for _, row in filtered_df.iterrows():

        execution_id = row["Execution ID"]

        cols = st.columns([2.5, 2.5, 1, 1, 1, 1, 1])

        cols[0].write(row["Platform"])
        cols[1].write(row["Test Name"])
        cols[2].write(row["Iteration"])
        cols[3].write(row.get("Run Type", "Initial"))

        new_result = cols[4].selectbox(
            "",
            ["PASS", "FAIL", "IN_PROGRESS"],
            index=["PASS","FAIL","IN_PROGRESS"].index(
                row["Result"] if row["Result"] in ["PASS","FAIL","IN_PROGRESS"] else "PASS"
            ),
            key=f"result_{execution_id}"
        )

        cols[5].write(row.get("Severity",""))

        toggle = "▼" if execution_id not in st.session_state.expanded_rows else "▲"

        if cols[6].button(toggle, key=f"toggle_{execution_id}"):

            if execution_id in st.session_state.expanded_rows:
                st.session_state.expanded_rows.remove(execution_id)
            else:
                st.session_state.expanded_rows.add(execution_id)

        # =============================
        # EXPANDED VIEW
        # =============================

        if execution_id in st.session_state.expanded_rows:

            st.markdown("##### Details")

            d1, d2, d3 = st.columns(3)

            with d1:
                st.write("Suite:", row.get("Test Category"))
                st.write("Failure Type:", row.get("Failure Type"))
                st.write("Stage:", row.get("Failure Stage"))

            with d2:
                st.write("Regression:", row.get("Regression"))
                st.write("Repro:", row.get("Reproducibility"))
                st.write("TTF:", row.get("TTF (min)"))

            with d3:
                st.write("Capacity:", row.get("Capacity"))
                st.write("Form Factor:", row.get("Form Factor"))
                st.write("Windows:", row.get("Windows"))

            # =============================
            # PLATFORM HISTORY
            # =============================

            history_df = filtered_df[
                (filtered_df["Platform"] == row["Platform"]) &
                (filtered_df["Test Name"] == row["Test Name"])
            ]

            st.markdown("##### Run History")

            st.dataframe(
                history_df[
                    ["Iteration","Result","Execution Date"]
                ].sort_values("Execution Date", ascending=False)
            )

            # =============================
            # EDIT BUTTON
            # =============================

            if st.button("Edit", key=f"edit_{execution_id}"):
                st.session_state.editing_id = execution_id

            st.divider()

        # =============================
        # EDIT PANEL
        # =============================

        if st.session_state.editing_id == execution_id:

            st.markdown(f"### Editing: {row['Platform']} | {row['Test Name']}")

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
                with open(path,"r") as f:
                    data = yaml.safe_load(f)

                if data.get("execution_id") == execution_id:
                    yaml_path = path
                    yaml_data = data
                    break

            if yaml_data:

                st.subheader("Test")

                yaml_data["test"]["result"] = st.selectbox(
                    "Result",
                    ["PASS","FAIL","IN_PROGRESS"],
                    index=["PASS","FAIL","IN_PROGRESS"].index(
                        yaml_data["test"].get("result","PASS")
                    )
                )

                yaml_data["test"]["ttf_minutes"] = st.number_input(
                    "TTF",
                    value=int(yaml_data["test"].get("ttf_minutes") or 0)
                )

                st.subheader("Classification")

                classification = yaml_data.get("classification",{})

                classification["severity"] = st.selectbox(
                    "Severity", ["S1","S2","S3","S4"]
                )

                classification["failure_type"] = st.text_input(
                    "Failure Type",
                    value=classification.get("failure_type","")
                )

                classification["failure_stage"] = st.text_input(
                    "Failure Stage",
                    value=classification.get("failure_stage","")
                )

                classification["regression"] = st.selectbox(
                    "Regression",
                    ["Yes","No","Unknown"]
                )

                yaml_data["classification"] = classification

                st.subheader("Analysis")

                analysis = yaml_data.get("analysis",{})

                analysis["observed"] = st.text_area(
                    "Observed",
                    value=analysis.get("observed","")
                )

                analysis["xplorer_url"] = st.text_input(
                    "xPlorer",
                    value=analysis.get("xplorer_url","")
                )

                yaml_data["analysis"] = analysis

                c1,c2 = st.columns(2)

                if c1.button("Save"):

                    with open(yaml_path,"w") as f:
                        yaml.dump(yaml_data,f,sort_keys=False)

                    st.success("Updated")
                    st.session_state.editing_id=None
                    st.rerun()

                if c2.button("Cancel"):
                    st.session_state.editing_id=None
                    st.rerun()

            st.divider()

# ============================================================
# TAB 2 — PLATFORM VIEW
# ============================================================

with platform_tab:

    st.subheader("Platform Tracking")

    platform = st.selectbox(
        "Select Platform",
        filtered_df["Platform"].unique()
    )

    platform_df = filtered_df[
        filtered_df["Platform"] == platform
    ]

    st.subheader("Latest Status")

    latest = (
        platform_df
        .sort_values("Execution Date")
        .groupby("Test Name")
        .last()
        .reset_index()
    )

    st.dataframe(latest)

    st.divider()

    st.subheader("Execution History")

    st.dataframe(
        platform_df.sort_values(
            "Execution Date",
            ascending=False
        )
    )

# ============================================================
# TAB 3 — ANALYTICS
# ============================================================

with analytics_tab:

    st.subheader("Top Failing Tests")

    fail_df = filtered_df[filtered_df["Result"]=="FAIL"]

    top = (
        fail_df.groupby("Test Name")
        .size()
        .reset_index(name="Failures")
        .sort_values("Failures",ascending=False)
        .head(10)
    )

    st.plotly_chart(
        px.bar(top,x="Test Name",y="Failures"),
        use_container_width=True
    )

    st.divider()

    st.subheader("Platform Stability")

    stats = (
        filtered_df.groupby("Platform")
        .agg(total=("Result","count"),
             fails=("Result", lambda x:(x=="FAIL").sum()))
    )

    stats["Stability %"] = 100 - (
        stats["fails"]/stats["total"]*100
    )

    st.plotly_chart(
        px.bar(stats.reset_index(),
               x="Platform",
               y="Stability %"),
        use_container_width=True
    )
# ============================================================
# TAB 2 — ANALYTICS
# ============================================================

with analytics_tab:

    st.subheader("KPI Overview")

    total = len(filtered_df)
    passes = len(filtered_df[filtered_df["Result"] == "PASS"])
    fails = len(filtered_df[filtered_df["Result"] == "FAIL"])
    inprog = len(filtered_df[filtered_df["Result"] == "IN_PROGRESS"])

    fail_rate = round((fails / total) * 100, 2) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Runs", total)
    c2.metric("Pass", passes)
    c3.metric("Fail", fails)
    c4.metric("In Progress", inprog)

    st.divider()

    # =============================
    # Top failing tests
    # =============================

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
            color="Failures"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # Platform Stability
    # =============================

    st.subheader("Platform Stability")

    platform_stats = (
        filtered_df.groupby("Platform")
        .agg(
            total=("Result","count"),
            fails=("Result", lambda x: (x=="FAIL").sum())
        )
    )

    platform_stats["Stability %"] = (
        100 - (platform_stats["fails"] / platform_stats["total"] * 100)
    )

    fig = px.bar(
        platform_stats.reset_index(),
        x="Platform",
        y="Stability %",
        color="Stability %"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # Firmware Health
    # =============================

    st.subheader("Firmware Health")

    fw_stats = (
        filtered_df.groupby("Firmware")
        .agg(
            total=("Result","count"),
            fails=("Result", lambda x:(x=="FAIL").sum())
        )
    )

    fw_stats["Failure %"] = (
        fw_stats["fails"] / fw_stats["total"] * 100
    )

    fig = px.bar(
        fw_stats.reset_index(),
        x="Firmware",
        y="Failure %"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # Trend over time
    # =============================

    st.subheader("Failure Trend")

    trend_df = filtered_df.copy()
    trend_df["Date"] = trend_df["Execution Date"].dt.date

    daily = (
        trend_df.groupby(["Date","Result"])
        .size()
        .reset_index(name="Count")
    )

    if not daily.empty:

        fig = px.line(
            daily,
            x="Date",
            y="Count",
            color="Result",
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # OEM comparison
    # =============================

    st.subheader("OEM Comparison")

    oem_stats = (
        filtered_df.groupby("OEM")
        .agg(
            Total=("Result","count"),
            Fails=("Result", lambda x:(x=="FAIL").sum())
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
        text="Failure %"
    )

    st.plotly_chart(fig, use_container_width=True)
    
    
# ============================================================
# TAB 4 — COVERAGE OVERVIEW
# ============================================================

with coverage_overview_tab:

    st.subheader("Coverage Overview")

    coverage_df = (
        filtered_df
        .dropna(subset=["Capacity","Form Factor"])
        .groupby([
            "Program",
            "OEM",
            "Platform",
            "Firmware",
            "Capacity",
            "Form Factor"
        ])
        .agg(Result=("Result","last"))
        .reset_index()
    )

    total = len(coverage_df)

    tested = len(coverage_df)
    platforms = coverage_df["Platform"].nunique()
    oems = coverage_df["OEM"].nunique()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Configs", total)
    c2.metric("Platforms", platforms)
    c3.metric("OEMs", oems)
    c4.metric("Firmware", coverage_df["Firmware"].nunique())

    st.divider()

    # =============================
    # Coverage by Capacity
    # =============================

    st.subheader("Coverage by Capacity")

    cap = (
        coverage_df.groupby("Capacity")
        .size()
        .reset_index(name="Count")
    )

    fig = px.bar(
        cap,
        x="Capacity",
        y="Count",
        color="Count"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # Coverage by Form Factor
    # =============================

    st.subheader("Coverage by Form Factor")

    ff = (
        coverage_df.groupby("Form Factor")
        .size()
        .reset_index(name="Count")
    )

    fig = px.bar(
        ff,
        x="Form Factor",
        y="Count",
        color="Count"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # Coverage by OEM
    # =============================

    st.subheader("Coverage by OEM")

    oem = (
        coverage_df.groupby("OEM")
        .size()
        .reset_index(name="Count")
    )

    fig = px.bar(
        oem,
        x="OEM",
        y="Count",
        color="Count"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =============================
    # Coverage by Firmware
    # =============================

    st.subheader("Coverage by Firmware")

    fw = (
        coverage_df.groupby("Firmware")
        .size()
        .reset_index(name="Count")
    )

    fig = px.bar(
        fw,
        x="Firmware",
        y="Count",
        color="Count"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Detailed Coverage Table")
    st.dataframe(coverage_df, use_container_width=True)
    
# ============================================================
# COVERAGE BOARD (FULL OVERVIEW)
# ============================================================

with coverage_board_tab:

    st.subheader("Test Coverage Board")

    board = (
        filtered_df
        .groupby(["Platform","Test Category"])
        .agg(Result=("Result","last"))
        .reset_index()
    )

    pivot = board.pivot(
        index="Platform",
        columns="Test Category",
        values="Result"
    )

    def color(val):
        if val == "PASS":
            return "background-color: #1f7a1f; color: white"
        if val == "FAIL":
            return "background-color: #b30000; color: white"
        if val == "IN_PROGRESS":
            return "background-color: #e6b800"
        return "background-color: #2b2b2b; color: #999"

    styled = pivot.style.applymap(color)

    st.dataframe(
        styled,
        use_container_width=True,
        height=700
    )

    st.divider()

    st.subheader("Cell Drilldown")

    col1, col2 = st.columns(2)

    platform_sel = col1.selectbox(
        "Platform",
        pivot.index
    )

    test_sel = col2.selectbox(
        "Test",
        pivot.columns
    )

    drill = filtered_df[
        (filtered_df["Platform"] == platform_sel) &
        (filtered_df["Test Category"] == test_sel)
    ]

    st.dataframe(
        drill.sort_values("Execution Date", ascending=False),
        use_container_width=True
    )    
    
    
    
    
    
# # ============================================================
# # COVERAGE MATRIX (EXCEL STYLE)
# # ============================================================

# with coverage_matrix_tab:

#     st.subheader("Test Coverage Matrix")

#     matrix_df = (
#         filtered_df
#         .groupby([
#             "Platform",
#             "Test Category"
#         ])
#         .agg(Result=("Result","last"))
#         .reset_index()
#     )

#     pivot = matrix_df.pivot(
#         index="Platform",
#         columns="Test Category",
#         values="Result"
#     )

#     st.dataframe(
#         pivot,
#         use_container_width=True,
#         height=600
#     )

#     st.divider()

#     st.subheader("Select Cell for Drilldown")

#     c1, c2 = st.columns(2)

#     platform_sel = c1.selectbox(
#         "Platform",
#         matrix_df["Platform"].unique()
#     )

#     test_sel = c2.selectbox(
#         "Test",
#         matrix_df["Test Category"].unique()
#     )

#     drill = filtered_df[
#         (filtered_df["Platform"] == platform_sel) &
#         (filtered_df["Test Category"] == test_sel)
#     ]

#     st.subheader("Execution History")

#     st.dataframe(
#         drill.sort_values("Execution Date", ascending=False),
#         use_container_width=True
#     )