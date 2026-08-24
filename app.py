import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Sportime Chatbot QA Master Dashboard",
    page_icon="📊",
    layout="wide"
)

FILE_PATH = "Sportime_Chatbot_QA_Filtered_Evaluated_6.xlsx"

@st.cache_data
def load_all_sheets(path):
    if not os.path.exists(path):
        return None
    xls = pd.ExcelFile(path)
    sheets = {}
    for name in xls.sheet_names:
        sheets[name] = pd.read_excel(path, sheet_name=name)
    return sheets

workbook = load_all_sheets(FILE_PATH)

if workbook is None:
    st.error(f"File '{FILE_PATH}' not found in directory. Please upload the file:")
    uploaded_file = st.file_uploader("Upload Excel Document", type=["xlsx"])
    if uploaded_file:
        xls = pd.ExcelFile(uploaded_file)
        workbook = {name: pd.read_excel(uploaded_file, sheet_name=name) for name in xls.sheet_names}

if workbook:
    df_qa = workbook.get("QA Evaluation", pd.DataFrame())
    df_eval_sum = workbook.get("Evaluation Summary", pd.DataFrame())
    df_master = workbook.get("Q&A Master", pd.DataFrame())
    df_summary = workbook.get("Summary", pd.DataFrame())
    df_seq = workbook.get("Original Sequence", pd.DataFrame())
    df_audit = workbook.get("Question Mark Audit", pd.DataFrame())

    # Merge QA Evaluation with Master Metadata for enriched analytics
    if not df_qa.empty and not df_master.empty:
        df_merged = pd.merge(
            df_qa, 
            df_master[['Test Case ID', 'Category', 'Subcategory', 'Question Type', 'Original Has ?']], 
            on='Test Case ID', 
            how='left'
        )
    else:
        df_merged = df_qa.copy()

    # Header Controls
    st.title("🏀 Sportime Chatbot QA Analytics Dashboard")
    st.markdown("Real-time performance evaluation and error breakdown across all workbook sheets.")

    # Sidebar Controls
    st.sidebar.header("🔍 Global Data Filters")
    
    categories = ["All"] + list(df_merged['Category'].dropna().unique()) if 'Category' in df_merged else ["All"]
    selected_cat = st.sidebar.selectbox("Filter Category", categories)
    
    qtypes = ["All"] + list(df_merged['Question Type'].dropna().unique()) if 'Question Type' in df_merged else ["All"]
    selected_qtype = st.sidebar.selectbox("Filter Question Type", qtypes)
    
    statuses = ["All"] + list(df_merged['Status'].dropna().unique()) if 'Status' in df_merged else ["All"]
    selected_status = st.sidebar.selectbox("Filter Evaluation Status", statuses)

    # Filter Application
    filtered_df = df_merged.copy()
    if selected_cat != "All":
        filtered_df = filtered_df[filtered_df['Category'] == selected_cat]
    if selected_qtype != "All":
        filtered_df = filtered_df[filtered_df['Question Type'] == selected_qtype]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]

    # Dashboard Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Executive KPI Summary", 
        "🏷️ Category & Taxonomy Analysis", 
        "❌ Failure Reason Deep Dive", 
        "📑 QA Test Case Inspector", 
        "📁 Raw Sheet Viewer"
    ])

    # TAB 1: EXECUTIVE KPIS
    with tab1:
        st.subheader("Key Evaluation Metrics")
        c1, c2, c3, c4 = st.columns(4)
        
        total_eval = len(filtered_df)
        pass_cnt = (filtered_df['Status'] == 'PASS').sum() if 'Status' in filtered_df else 0
        fail_cnt = (filtered_df['Status'] == 'FAIL').sum() if 'Status' in filtered_df else 0
        pass_rate = (pass_cnt / total_eval * 100) if total_eval > 0 else 0

        c1.metric("Evaluated Test Cases", total_eval)
        c2.metric("Passed Responses", pass_cnt)
        c3.metric("Failed Responses", fail_cnt)
        c4.metric("Pass Rate", f"{pass_rate:.1f}%")

        st.markdown("---")
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("Overall Status Breakdown")
            if 'Status' in filtered_df and not filtered_df.empty:
                fig_status = px.pie(
                    filtered_df, 
                    names='Status', 
                    color='Status',
                    color_discrete_map={'PASS': '#2ea44f', 'FAIL': '#cb2431'},
                    hole=0.4
                )
                st.plotly_chart(fig_status, use_container_width=True)

        with g2:
            st.subheader("Relevance Distribution")
            if 'Relevance' in filtered_df and not filtered_df.empty:
                fig_rel = px.pie(
                    filtered_df, 
                    names='Relevance', 
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.4
                )
                st.plotly_chart(fig_rel, use_container_width=True)

    # TAB 2: CATEGORY & TAXONOMY
    with tab2:
        st.subheader("Performance Across Categories")
        if 'Category' in filtered_df and not filtered_df.empty:
            cat_perf = filtered_df.groupby(['Category', 'Status']).size().reset_index(name='Count')
            fig_cat = px.bar(
                cat_perf, 
                x='Category', 
                y='Count', 
                color='Status',
                color_discrete_map={'PASS': '#2ea44f', 'FAIL': '#cb2431'},
                barmode='group',
                title="Pass vs Fail by Functional Category"
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        st.subheader("Performance by Question Type")
        if 'Question Type' in filtered_df and not filtered_df.empty:
            qt_perf = filtered_df.groupby(['Question Type', 'Status']).size().reset_index(name='Count')
            fig_qt = px.bar(
                qt_perf, 
                x='Question Type', 
                y='Count', 
                color='Status',
                color_discrete_map={'PASS': '#2ea44f', 'FAIL': '#cb2431'},
                barmode='stack',
                title="Question Type Impact on Status"
            )
            st.plotly_chart(fig_qt, use_container_width=True)

    # TAB 3: FAILURE REASON AUDIT
    with tab3:
        st.subheader("Failure Reason Analysis")
        if 'Failure Reason' in filtered_df and not filtered_df.empty:
            fail_df = filtered_df[filtered_df['Status'] == 'FAIL']
            if not fail_df.empty:
                reason_counts = fail_df['Failure Reason'].value_counts().reset_index()
                reason_counts.columns = ['Failure Reason', 'Count']
                
                fig_fail = px.bar(
                    reason_counts, 
                    y='Failure Reason', 
                    x='Count', 
                    orientation='h',
                    color='Count',
                    color_continuous_scale='Reds',
                    title="Top Root Causes for Chatbot Failure"
                )
                st.plotly_chart(fig_fail, use_container_width=True)
            else:
                st.success("No failed test cases in current selection.")

    # TAB 4: TEST CASE INSPECTOR
    with tab4:
        st.subheader("Interactive Evaluation Inspector")
        display_cols = ['Test Case ID', 'Category', 'Question Type', 'Status', 'Question', 'Chatbot Answer', 'Expected Answer', 'Failure Reason']
        avail_cols = [c for c in display_cols if c in filtered_df.columns]
        st.dataframe(filtered_df[avail_cols], use_container_width=True, height=500)
        
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Current Filtered Table to CSV",
            data=csv_data,
            file_name="Sportime_Filtered_QA_Export.csv",
            mime="text/csv"
        )

    # TAB 5: RAW SHEET VIEWER
    with tab5:
        st.subheader("Workbook Sheet Selector")
        selected_sheet = st.selectbox("Select Sheet to Inspect Raw Content", list(workbook.keys()))
        st.dataframe(workbook[selected_sheet], use_container_width=True)