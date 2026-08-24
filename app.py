import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Sportime Chatbot QA & System Reliability Dashboard",
    page_icon="📊",
    layout="wide",
)

# File configuration - set default name matching your file
FILE_PATH = "Sportime_Chatbot_QA_TopicWise_Accurate (2).xlsx"


@st.cache_data
def load_all_sheets(path):
    if not os.path.exists(path):
        return None
    xls = pd.ExcelFile(path)
    sheets = {name: pd.read_excel(path, sheet_name=name) for name in xls.sheet_names}
    return sheets


# Load Workbook Data
workbook = load_all_sheets(FILE_PATH)

if workbook is None:
    st.error(f"File '{FILE_PATH}' not found in current directory.")
    uploaded_file = st.file_uploader(
        "Upload Excel Document (Sportime_Chatbot_QA_TopicWise_Accurate.xlsx)",
        type=["xlsx"],
    )
    if uploaded_file:
        xls = pd.ExcelFile(uploaded_file)
        workbook = {
            name: pd.read_excel(uploaded_file, sheet_name=name)
            for name in xls.sheet_names
        }

if workbook:
    # Map sheets from the updated workbook structure
    df_dash = workbook.get("Executive Dashboard", pd.DataFrame())

    # Primary data sheet containing complete audited records
    if "QA & Master Audit" in workbook:
        df_master = workbook.get("QA & Master Audit", pd.DataFrame())
    else:
        # Fallback to topic-wise sheet filtered from headers
        raw_topic = workbook.get("Topic-Wise Master Audit", pd.DataFrame())
        df_master = raw_topic[
            raw_topic["Test Case ID"].notna()
            & (~raw_topic["Topic Seq"].astype(str).str.startswith("CATEGORY:"))
        ].copy()

    # Header Title
    st.title("🏀 Sportime Chatbot QA & System Reliability Dashboard")
    st.markdown(
        "Topic-Wise Accuracy Breakdown, Sequential Audit, and System Reliability Analytics"
    )

    # Sidebar Data Filters
    st.sidebar.header("🔍 Global Data Filters")

    cat_options = (
        ["All"] + sorted(list(df_master["Category"].dropna().unique()))
        if "Category" in df_master
        else ["All"]
    )
    selected_cat = st.sidebar.selectbox("Filter Category / Topic", cat_options)

    qtype_options = (
        ["All"] + sorted(list(df_master["Question Type"].dropna().unique()))
        if "Question Type" in df_master
        else ["All"]
    )
    selected_qtype = st.sidebar.selectbox("Filter Question Type", qtype_options)

    status_options = (
        ["All"] + sorted(list(df_master["Status"].dropna().unique()))
        if "Status" in df_master
        else ["All"]
    )
    selected_status = st.sidebar.selectbox("Filter Status (PASS/FAIL)", status_options)

    relevance_options = (
        ["All"] + sorted(list(df_master["Relevance"].dropna().unique()))
        if "Relevance" in df_master
        else ["All"]
    )
    selected_relevance = st.sidebar.selectbox(
        "Filter Intent Relevance", relevance_options
    )

    # Apply Filters
    filtered_df = df_master.copy()
    if selected_cat != "All":
        filtered_df = filtered_df[filtered_df["Category"] == selected_cat]
    if selected_qtype != "All":
        filtered_df = filtered_df[filtered_df["Question Type"] == selected_qtype]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["Status"] == selected_status]
    if selected_relevance != "All":
        filtered_df = filtered_df[filtered_df["Relevance"] == selected_relevance]

    # Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Executive KPIs & Reliability",
        "🎯 Topic-Wise Accuracy Breakdown",
        "❌ Failure Reason Deep Dive",
        "📑 Sequential Test Case Inspector",
        "📁 Raw Workbook Sheets",
    ])

    # TAB 1: EXECUTIVE KPIS & RELIABILITY
    with tab1:
        st.subheader("Key Performance Indicators (KPIs)")
        c1, c2, c3, c4, c5 = st.columns(5)

        total_eval = len(filtered_df)
        pass_cnt = (
            (filtered_df["Status"] == "PASS").sum() if "Status" in filtered_df else 0
        )
        fail_cnt = (
            (filtered_df["Status"] == "FAIL").sum() if "Status" in filtered_df else 0
        )
        pass_rate = (pass_cnt / total_eval * 100) if total_eval > 0 else 0.0

        rel_cnt = (
            (filtered_df["Relevance"] == "Relevant").sum()
            if "Relevance" in filtered_df
            else 0
        )
        rel_rate = (rel_cnt / total_eval * 100) if total_eval > 0 else 0.0

        c1.metric("Evaluated Test Cases", total_eval)
        c2.metric("Passed Cases (PASS)", pass_cnt)
        c3.metric("Failed Cases (FAIL)", fail_cnt)
        c4.metric("System Pass Rate", f"{pass_rate:.2f}%")
        c5.metric("Intent Relevance Rate", f"{rel_rate:.2f}%")

        st.markdown("---")
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("Overall Status Distribution")
            if "Status" in filtered_df and not filtered_df.empty:
                fig_status = px.pie(
                    filtered_df,
                    names="Status",
                    color="Status",
                    color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
                    hole=0.4,
                )
                st.plotly_chart(fig_status, use_container_width=True)

        with g2:
            st.subheader("Intent Relevance Distribution")
            if "Relevance" in filtered_df and not filtered_df.empty:
                fig_rel = px.pie(
                    filtered_df,
                    names="Relevance",
                    color="Relevance",
                    color_discrete_map={
                        "Relevant": "#1f77b4",
                        "Not Relevant": "#ff7f0e",
                    },
                    hole=0.4,
                )
                st.plotly_chart(fig_rel, use_container_width=True)

    # TAB 2: TOPIC-WISE BREAKDOWN
    with tab2:
        st.subheader("Accuracy & Pass/Fail Rate by Domain Topic")
        if "Category" in filtered_df and not filtered_df.empty:
            cat_perf = (
                filtered_df.groupby(["Category", "Status"])
                .size()
                .reset_index(name="Count")
            )
            fig_cat = px.bar(
                cat_perf,
                x="Category",
                y="Count",
                color="Status",
                color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
                barmode="group",
                title="Pass vs Fail Count Across Categories",
            )
            fig_cat.update_layout(xaxis={"categoryorder": "total descending"})
            st.plotly_chart(fig_cat, use_container_width=True)

            # Category Accuracy Table
            st.subheader("Category Accuracy Percentage Matrix")
            cat_matrix = (
                filtered_df.groupby("Category")["Status"]
                .value_counts()
                .unstack(fill_value=0)
            )
            if "PASS" not in cat_matrix.columns:
                cat_matrix["PASS"] = 0
            if "FAIL" not in cat_matrix.columns:
                cat_matrix["FAIL"] = 0
            cat_matrix["Total"] = cat_matrix["PASS"] + cat_matrix["FAIL"]
            cat_matrix["Pass Rate (%)"] = (
                cat_matrix["PASS"] / cat_matrix["Total"] * 100
            ).round(2)
            cat_matrix = cat_matrix.sort_values(
                by="Pass Rate (%)", ascending=False
            ).reset_index()
            st.dataframe(cat_matrix, use_container_width=True)

        st.subheader("Question Type Reliability Impact")
        if "Question Type" in filtered_df and not filtered_df.empty:
            qt_perf = (
                filtered_df.groupby(["Question Type", "Status"])
                .size()
                .reset_index(name="Count")
            )
            fig_qt = px.bar(
                qt_perf,
                x="Question Type",
                y="Count",
                color="Status",
                color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
                barmode="stack",
                title="Status Breakdown by Question Type",
            )
            st.plotly_chart(fig_qt, use_container_width=True)

    # TAB 3: FAILURE REASON AUDIT
    with tab3:
        st.subheader("Root Cause Analysis for Failed Test Cases")
        if "Failure Reason" in filtered_df and not filtered_df.empty:
            fail_df = filtered_df[filtered_df["Status"] == "FAIL"]
            if not fail_df.empty:
                reason_counts = (
                    fail_df["Failure Reason"].value_counts().reset_index()
                )
                reason_counts.columns = ["Failure Reason", "Count"]

                fig_fail = px.bar(
                    reason_counts,
                    y="Failure Reason",
                    x="Count",
                    orientation="h",
                    color="Count",
                    color_continuous_scale="Reds",
                    title="Failure Drivers Distribution",
                )
                fig_fail.update_layout(yaxis={"autorange": "reversed"})
                st.plotly_chart(fig_fail, use_container_width=True)

                st.subheader("Failed Queries Detail Table")
                fail_display_cols = [
                    "S. No",
                    "Test Case ID",
                    "Category",
                    "User Question",
                    "Chatbot Answer",
                    "Expected Answer",
                    "Failure Reason",
                ]
                avail_fail_cols = [
                    c for c in fail_display_cols if c in fail_df.columns
                ]
                st.dataframe(
                    fail_df[avail_fail_cols],
                    use_container_width=True,
                    height=400,
                )
            else:
                st.success("No failed test cases present in current filters.")

    # TAB 4: SEQUENTIAL TEST CASE INSPECTOR
    with tab4:
        st.subheader(
            "Sequential Test Case Inspector (Exact S. No 1 to 154 Order)"
        )

        display_cols = [
            "S. No",
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
        avail_cols = [c for c in display_cols if c in filtered_df.columns]

        # Display dataframe sorted by Sequential S. No
        if "S. No" in filtered_df.columns:
            sorted_filtered = filtered_df.sort_values(by="S. No")
        else:
            sorted_filtered = filtered_df

        st.dataframe(
            sorted_filtered[avail_cols], use_container_width=True, height=550
        )

        csv_data = sorted_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Current View to CSV",
            data=csv_data,
            file_name="Sportime_Filtered_QA_Export.csv",
            mime="text/csv",
        )

    # TAB 5: RAW SHEET VIEWER
    with tab5:
        st.subheader("Workbook Sheet Explorer")
        selected_sheet = st.selectbox(
            "Select Sheet to View Raw Data", list(workbook.keys())
        )
        st.dataframe(workbook[selected_sheet], use_container_width=True)