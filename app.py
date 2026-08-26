import io
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Sportime Chatbot QA & System Reliability Dashboard",
    page_icon="📊",
    layout="wide",
)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def clean_text_column(df, column, case="normal"):
    """Clean text values in a DataFrame column."""
    if column not in df.columns:
        return df

    df[column] = df[column].fillna("").astype(str).str.strip()

    if case == "upper":
        df[column] = df[column].str.upper()
    elif case == "title":
        df[column] = df[column].str.title()

    return df

def calculate_reliability(pass_rate):
    """Return reliability level based on pass rate."""
    if pass_rate >= 90:
        return "High Reliability"
    elif pass_rate >= 75:
        return "Good Reliability"
    elif pass_rate >= 50:
        return "Needs Improvement"
    else:
        return "Low Reliability"

# =========================================================
# FILE UPLOAD AND WORKBOOK LOADING
# =========================================================
@st.cache_data
def load_all_sheets(file_bytes):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheets = {}

    for name in xls.sheet_names:
        # -------------------------------------------------
        # QA & MASTER AUDIT
        # Header is on Excel row 4 (0-indexed header=3)
        # -------------------------------------------------
        if name == "QA & Master Audit":
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=name,
                header=3
            )
            df = df.dropna(how="all")
            df.columns = df.columns.astype(str).str.strip()

            # Map Excel column name to dashboard standard name
            if "Pass and Failure Reason" in df.columns:
                df = df.rename(
                    columns={"Pass and Failure Reason": "Failure Reason"}
                )

            # Filter valid test case rows
            if "Test Case ID" in df.columns:
                df = df[df["Test Case ID"].notna()].copy()

            # Standardize key text columns
            df = clean_text_column(df, "Status", "upper")
            df = clean_text_column(df, "Relevance", "title")
            df = clean_text_column(df, "Category")
            df = clean_text_column(df, "Subcategory")
            df = clean_text_column(df, "Question Type")

            sheets[name] = df

        # -------------------------------------------------
        # TOPIC WISE MASTER AUDIT
        # Header is on Excel row 4 (0-indexed header=3)
        # -------------------------------------------------
        elif name == "Topic Wise Master Audit":
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=name,
                header=3
            )
            df = df.dropna(how="all")
            df.columns = df.columns.astype(str).str.strip()
            sheets[name] = df

        # -------------------------------------------------
        # EXECUTIVE DASHBOARD AND OTHER SHEETS
        # -------------------------------------------------
        else:
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=name,
                header=None
            )
            sheets[name] = df

    return sheets

# =========================================================
# HEADER
# =========================================================
st.title("🏀 Sportime Chatbot QA & System Reliability Dashboard")
st.markdown(
    """
    Upload the Sportime QA Excel workbook to analyze chatbot
    performance, pass/fail rates, intent relevance, failure reasons,
    and topic-wise system reliability.
    """
)

# =========================================================
# FILE UPLOAD
# =========================================================
uploaded_file = st.file_uploader(
    "📁 Upload Sportime QA Excel Workbook",
    type=["xlsx"],
    key="excel_uploader"
)

if uploaded_file is None:
    st.info("Please upload the Sportime QA Excel workbook to start the dashboard.")
    st.stop()

# =========================================================
# LOAD WORKBOOK
# =========================================================
try:
    file_bytes = uploaded_file.getvalue()
    workbook = load_all_sheets(file_bytes)
except Exception as e:
    st.error(f"Unable to read the Excel workbook: {e}")
    st.stop()

# =========================================================
# GET MASTER AUDIT DATA
# =========================================================
df_master = workbook.get("QA & Master Audit", pd.DataFrame())

if df_master.empty:
    st.error("QA & Master Audit sheet was not loaded correctly.")
    st.stop()

# Re-verify clean formatting
df_master.columns = df_master.columns.astype(str).str.strip()
df_master = clean_text_column(df_master, "Status", "upper")
df_master = clean_text_column(df_master, "Relevance", "title")
df_master = clean_text_column(df_master, "Category")
df_master = clean_text_column(df_master, "Subcategory")
df_master = clean_text_column(df_master, "Question Type")

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("🔍 Global Data Filters")

# Category Filter
if "Category" in df_master.columns:
    cat_values = df_master["Category"].replace("", pd.NA).dropna().unique().tolist()
    cat_options = ["All"] + sorted(cat_values)
else:
    cat_options = ["All"]
selected_cat = st.sidebar.selectbox("Filter Category / Topic", cat_options)

# Question Type Filter
if "Question Type" in df_master.columns:
    qtype_values = df_master["Question Type"].replace("", pd.NA).dropna().unique().tolist()
    qtype_options = ["All"] + sorted(qtype_values)
else:
    qtype_options = ["All"]
selected_qtype = st.sidebar.selectbox("Filter Question Type", qtype_options)

# Status Filter
if "Status" in df_master.columns:
    status_values = df_master["Status"].replace("", pd.NA).dropna().unique().tolist()
    status_options = ["All"] + sorted(status_values)
else:
    status_options = ["All"]
selected_status = st.sidebar.selectbox("Filter Status", status_options)

# Relevance Filter
if "Relevance" in df_master.columns:
    relevance_values = df_master["Relevance"].replace("", pd.NA).dropna().unique().tolist()
    relevance_options = ["All"] + sorted(relevance_values)
else:
    relevance_options = ["All"]
selected_relevance = st.sidebar.selectbox("Filter Intent Relevance", relevance_options)

# =========================================================
# APPLY FILTERS
# =========================================================
filtered_df = df_master.copy()

if selected_cat != "All" and "Category" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Category"] == selected_cat]

if selected_qtype != "All" and "Question Type" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Question Type"] == selected_qtype]

if selected_status != "All" and "Status" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Status"] == selected_status]

if selected_relevance != "All" and "Relevance" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Relevance"] == selected_relevance]

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive KPIs & Reliability",
    "📈 Topic-Wise Accuracy Breakdown",
    "❌ Failure Reason Deep Dive",
    "🔍 Sequential Test Case Inspector",
    "📄 Raw Workbook Sheets",
])

# =========================================================
# TAB 1: EXECUTIVE KPIs & RELIABILITY
# =========================================================
with tab1:
    st.subheader("Key Performance Indicators")

    total_eval = len(filtered_df)
    pass_cnt = filtered_df["Status"].eq("PASS").sum() if "Status" in filtered_df.columns else 0
    fail_cnt = filtered_df["Status"].eq("FAIL").sum() if "Status" in filtered_df.columns else 0
    relevant_cnt = filtered_df["Relevance"].eq("Relevant").sum() if "Relevance" in filtered_df.columns else 0

    pass_rate = (pass_cnt / total_eval * 100) if total_eval > 0 else 0
    fail_rate = (fail_cnt / total_eval * 100) if total_eval > 0 else 0
    relevance_rate = (relevant_cnt / total_eval * 100) if total_eval > 0 else 0
    reliability = calculate_reliability(pass_rate)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Test Cases", total_eval)
    c2.metric("Passed", pass_cnt)
    c3.metric("Failed", fail_cnt)
    c4.metric("Pass Rate", f"{pass_rate:.2f}%")
    c5.metric("Fail Rate", f"{fail_rate:.2f}%")
    c6.metric("Relevance Rate", f"{relevance_rate:.2f}%")

    st.markdown("---")
    st.subheader("System Reliability")

    if pass_rate >= 90:
        st.success(f"System Reliability: {reliability}")
    elif pass_rate >= 50:
        st.warning(f"System Reliability: {reliability}")
    else:
        st.error(f"System Reliability: {reliability}")

    # Charts
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Overall Status Distribution")
        if "Status" in filtered_df.columns and not filtered_df.empty:
            status_counts = filtered_df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            fig_status = px.pie(
                status_counts,
                names="Status",
                values="Count",
                color="Status",
                color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
                hole=0.45,
            )
            st.plotly_chart(fig_status, use_container_width=True)

    with g2:
        st.subheader("Intent Relevance Distribution")
        if "Relevance" in filtered_df.columns and not filtered_df.empty:
            relevance_counts = filtered_df["Relevance"].value_counts().reset_index()
            relevance_counts.columns = ["Relevance", "Count"]

            fig_rel = px.pie(
                relevance_counts,
                names="Relevance",
                values="Count",
                color="Relevance",
                color_discrete_map={"Relevant": "#1f77b4", "Not Relevant": "#ff7f0e"},
                hole=0.45,
            )
            st.plotly_chart(fig_rel, use_container_width=True)

# =========================================================
# TAB 2: TOPIC-WISE ACCURACY BREAKDOWN
# =========================================================
with tab2:
    st.subheader("Pass vs Fail Performance by Category")

    if "Category" in filtered_df.columns and "Status" in filtered_df.columns and not filtered_df.empty:
        cat_perf = filtered_df.groupby(["Category", "Status"]).size().reset_index(name="Count")

        fig_cat = px.bar(
            cat_perf,
            x="Category",
            y="Count",
            color="Status",
            barmode="group",
            color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
            title="Pass vs Fail Count Across Categories"
        )
        st.plotly_chart(fig_cat, use_container_width=True)

        st.subheader("Category Performance Matrix")

        category_summary = (
            filtered_df.groupby("Category")
            .agg(
                Total=("Status", "size"),
                Passed=("Status", lambda x: (x == "PASS").sum()),
                Failed=("Status", lambda x: (x == "FAIL").sum()),
            )
            .reset_index()
        )

        category_summary["Pass Rate (%)"] = (category_summary["Passed"] / category_summary["Total"] * 100).round(2)
        category_summary["Fail Rate (%)"] = (category_summary["Failed"] / category_summary["Total"] * 100).round(2)
        category_summary["Reliability"] = category_summary["Pass Rate (%)"].apply(calculate_reliability)

        st.dataframe(category_summary, use_container_width=True, hide_index=True)

    st.subheader("Question Type Reliability Impact")

    if "Question Type" in filtered_df.columns and "Status" in filtered_df.columns and not filtered_df.empty:
        qt_perf = filtered_df.groupby(["Question Type", "Status"]).size().reset_index(name="Count")

        fig_qt = px.bar(
            qt_perf,
            x="Question Type",
            y="Count",
            color="Status",
            barmode="stack",
            color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
            title="Status Breakdown by Question Type"
        )
        st.plotly_chart(fig_qt, use_container_width=True)

# =========================================================
# TAB 3: FAILURE REASON DEEP DIVE
# =========================================================
with tab3:
    st.subheader("Root Cause Analysis for Failed Test Cases")

    if "Status" in filtered_df.columns and not filtered_df.empty:
        fail_df = filtered_df[filtered_df["Status"] == "FAIL"].copy()

        if fail_df.empty:
            st.success("No failed test cases present in current filters.")
        else:
            if "Failure Reason" in fail_df.columns:
                reason_counts = (
                    fail_df["Failure Reason"]
                    .replace("", pd.NA)
                    .dropna()
                    .value_counts()
                    .reset_index()
                )
                reason_counts.columns = ["Failure Reason", "Count"]

                if not reason_counts.empty:
                    fig_fail = px.bar(
                        reason_counts,
                        y="Failure Reason",
                        x="Count",
                        orientation="h",
                        color="Count",
                        color_continuous_scale="Reds",
                        title="Failure Drivers Distribution"
                    )
                    fig_fail.update_layout(yaxis={"autorange": "reversed"})
                    st.plotly_chart(fig_fail, use_container_width=True)

            st.subheader("Failed Test Case Details")

            fail_display_cols = [
                "Test Case ID",
                "Category",
                "Subcategory",
                "User Question",
                "Chatbot Answer",
                "Expected Answer",
                "Failure Reason",
                "Relevance",
            ]

            available_cols = [col for col in fail_display_cols if col in fail_df.columns]
            st.dataframe(fail_df[available_cols], use_container_width=True, height=500, hide_index=True)

# =========================================================
# TAB 4: SEQUENTIAL TEST CASE INSPECTOR
# =========================================================
with tab4:
    st.subheader("Sequential Test Case Inspector")

    display_cols = [
        "Test Case ID",
        "Category",
        "Subcategory",
        "Question Type",
        "Status",
        "Relevance",
        "User Question",
        "Chatbot Answer",
        "Expected Answer",
        "Failure Reason",
    ]

    available_cols = [col for col in display_cols if col in filtered_df.columns]

    st.dataframe(filtered_df[available_cols], use_container_width=True, height=600, hide_index=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Current View to CSV",
        data=csv_data,
        file_name="Sportime_Filtered_QA_Export.csv",
        mime="text/csv",
    )

# =========================================================
# TAB 5: RAW WORKBOOK SHEETS
# =========================================================
with tab5:
    st.subheader("Workbook Sheet Explorer")
    selected_sheet = st.selectbox("Select Sheet to View", list(workbook.keys()))
    st.dataframe(workbook[selected_sheet], use_container_width=True, hide_index=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("Sportime Chatbot QA & System Reliability Dashboard")