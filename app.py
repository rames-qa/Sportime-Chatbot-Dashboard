import io
import pandas as pd
import plotly.express as px
import streamlit as st
st.set_page_config(
    page_title="Sportime Chatbot QA & System Reliability Dashboard",
    page_icon="📊",
    layout="wide",
)
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
    """Return reliability level based on pass rate numeric value."""
    if pass_rate >= 90:
        return "High Reliability"
    elif pass_rate >= 75:
        return "Good Reliability"
    elif pass_rate >= 50:
        return "Needs Improvement"
    else:
        return "Low Reliability"
def truncate_text(text, max_len=45):
    """Truncate long text for axis labels."""
    text = str(text)
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text
def clean_raw_sheet(df):
    """Clean unformatted sheets by dropping empty rows and promoting true headers."""
    temp_df = df.dropna(how="all").copy()
    if any(str(col).startswith("Unnamed") or str(col).isdigit() for col in temp_df.columns):
        header_idx = None
        for i in range(min(10, len(temp_df))):
            row_vals = temp_df.iloc[i].dropna().astype(str).str.strip().tolist()
            if len(row_vals) >= 3 and not any("Sportime" in v for v in row_vals):
                header_idx = i
                break
        if header_idx is not None:
            new_headers = temp_df.iloc[header_idx].astype(str).str.strip().tolist()
            temp_df = temp_df.iloc[header_idx + 1:].copy()
            temp_df.columns = new_headers
    cols = []
    col_counts = {}
    for idx, col in enumerate(temp_df.columns):
        col_str = str(col).strip()
        if col_str in ["nan", "None", "", "Unnamed"]:
            col_str = f"Unnamed_{idx}"
        if col_str in col_counts:
            col_counts[col_str] += 1
            col_str = f"{col_str}_{col_counts[col_str]}"
        else:
            col_counts[col_str] = 0
        cols.append(col_str)
    temp_df.columns = cols
    temp_df = temp_df.dropna(how="all").loc[:, temp_df.notna().any()]
    temp_df = temp_df.fillna("-")
    for col in temp_df.columns:
        col_str = str(col).lower()
        if any(kw in col_str for kw in ["rate", "accuracy", "pass %", "fail %", "relevance"]):
            converted_series = pd.to_numeric(temp_df[col], errors="coerce")
            if converted_series.notna().any():
                temp_df[col] = converted_series.apply(
                    lambda x: f"{x * 100:.2f}%" if pd.notna(x) and isinstance(x, (int, float)) and 0 <= x <= 1 else x
                )
    return temp_df
@st.cache_data
def load_all_sheets(file_bytes):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheets = {}
    for name in xls.sheet_names:
        if name == "QA & Master Audit":
            # Read without forcing header=3 first to find actual header row dynamically
            raw_df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=name, header=None)
            header_row = 3
            for r in range(min(10, len(raw_df))):
                row_str = " ".join(raw_df.iloc[r].dropna().astype(str).tolist()).lower()
                if "test case id" in row_str or "category" in row_str or "status" in row_str:
                    header_row = r
                    break  
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=name, header=header_row)
            df = df.dropna(how="all")
            df.columns = df.columns.astype(str).str.strip()
            if "Pass and Failure Reason" in df.columns:
                df = df.rename(columns={"Pass and Failure Reason": "Failure Reason"})
            if "Test Case ID" in df.columns:
                df = df[df["Test Case ID"].notna()].copy()
            df = clean_text_column(df, "Status", "upper")
            df = clean_text_column(df, "Relevance", "title")
            df = clean_text_column(df, "Category")
            df = clean_text_column(df, "Subcategory")
            df = clean_text_column(df, "Question Type")
            sheets[name] = df
        elif name == "Topic Wise Master Audit":
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=name, header=3)
            df = df.dropna(how="all")
            df.columns = df.columns.astype(str).str.strip()
            sheets[name] = df
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=name, header=None)
            sheets[name] = df
    return sheets
st.title(" Sportime Chatbot QA & System Reliability Dashboard")
st.markdown("Analyze chatbot evaluation data, failure root causes, and domain accuracy metrics.")
uploaded_file = st.file_uploader("📁 Upload Sportime QA Excel Workbook", type=["xlsx"], key="excel_uploader")
if uploaded_file is None:
    st.info("Please upload the Sportime QA Excel workbook to start the dashboard.")
    st.stop()
try:
    file_bytes = uploaded_file.getvalue()
    workbook = load_all_sheets(file_bytes)
except Exception as e:
    st.error(f"Unable to read the Excel workbook: {e}")
    st.stop()
# Fallback: if 'QA & Master Audit' doesn't exist or is empty, select first non-empty sheet
sheet_names = list(workbook.keys())
master_sheet_name = "QA & Master Audit" if "QA & Master Audit" in workbook else sheet_names[0]
df_master = workbook.get(master_sheet_name, pd.DataFrame())
if isinstance(df_master, pd.DataFrame) and not df_master.empty:
    if any(str(c).startswith("Unnamed") for c in df_master.columns):
        df_master = clean_raw_sheet(df_master)
df_master.columns = df_master.columns.astype(str).str.strip()
df_master = clean_text_column(df_master, "Status", "upper")
df_master = clean_text_column(df_master, "Relevance", "title")
df_master = clean_text_column(df_master, "Category")
df_master = clean_text_column(df_master, "Subcategory")
df_master = clean_text_column(df_master, "Question Type")
# Dynamic Column Helper
def get_col(df, target):
    for col in df.columns:
        if str(col).lower().strip() == target.lower().strip():
            return col
    return None
cat_col = get_col(df_master, "Category")
qtype_col = get_col(df_master, "Question Type")
status_col = get_col(df_master, "Status")
rel_col = get_col(df_master, "Relevance")
st.sidebar.header("🔍 Global Data Filters")
cat_options = ["All"] + sorted([x for x in df_master[cat_col].unique() if str(x).strip() not in ["", "nan", "-"]]) if cat_col else ["All"]
selected_cat = st.sidebar.selectbox("Filter Category / Topic", cat_options)
qtype_options = ["All"] + sorted([x for x in df_master[qtype_col].unique() if str(x).strip() not in ["", "nan", "-"]]) if qtype_col else ["All"]
selected_qtype = st.sidebar.selectbox("Filter Question Type", qtype_options)
status_options = ["All"] + sorted([x for x in df_master[status_col].unique() if str(x).strip() not in ["", "nan", "-"]]) if status_col else ["All"]
selected_status = st.sidebar.selectbox("Filter Status", status_options)
relevance_options = ["All"] + sorted([x for x in df_master[rel_col].unique() if str(x).strip() not in ["", "nan", "-"]]) if rel_col else ["All"]
selected_relevance = st.sidebar.selectbox("Filter Intent Relevance", relevance_options)
filtered_df = df_master.copy()
if selected_cat != "All" and cat_col:
    filtered_df = filtered_df[filtered_df[cat_col].astype(str).str.strip() == str(selected_cat).strip()]
if selected_qtype != "All" and qtype_col:
    filtered_df = filtered_df[filtered_df[qtype_col].astype(str).str.strip() == str(selected_qtype).strip()]
if selected_status != "All" and status_col:
    filtered_df = filtered_df[filtered_df[status_col].astype(str).str.strip() == str(selected_status).strip()]
if selected_relevance != "All" and rel_col:
    filtered_df = filtered_df[filtered_df[rel_col].astype(str).str.strip() == str(selected_relevance).strip()]
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    " Executive KPIs & Reliability",
    " Topic-Wise Accuracy Breakdown",
    " Failure Reason Deep Dive",
    " Sequential Test Case Inspector",
    " Raw Workbook Sheets",
])
with tab1:
    st.subheader("Key Performance Indicators")
    total_eval = len(filtered_df)
    pass_cnt = filtered_df[status_col].eq("PASS").sum() if status_col else 0
    fail_cnt = filtered_df[status_col].eq("FAIL").sum() if status_col else 0
    relevant_cnt = filtered_df[rel_col].str.lower().eq("relevant").sum() if rel_col else 0
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
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Overall Status Distribution")
        if status_col and not filtered_df.empty:
            status_counts = filtered_df[status_col].value_counts().reset_index()
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
        if rel_col and not filtered_df.empty:
            relevance_counts = filtered_df[rel_col].value_counts().reset_index()
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
with tab2:
    st.subheader("Pass vs Fail Performance by Category")
    if cat_col and status_col and not filtered_df.empty:
        cat_perf = filtered_df.groupby([cat_col, status_col]).size().reset_index(name="Count")
        fig_cat = px.bar(
            cat_perf,
            x=cat_col,
            y="Count",
            color=status_col,
            barmode="group",
            color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
            title="Pass vs Fail Count Across Categories"
        )
        st.plotly_chart(fig_cat, use_container_width=True)
        st.subheader("Category Performance Matrix")
        category_summary = (
            filtered_df.groupby(cat_col)
            .agg(
                Total=(status_col, "size"),
                Passed=(status_col, lambda x: (x == "PASS").sum()),
                Failed=(status_col, lambda x: (x == "FAIL").sum()),
            )
            .reset_index()
        )
        category_summary["Pass Rate Num"] = (category_summary["Passed"] / category_summary["Total"] * 100).round(2)
        category_summary["Pass Rate (%)"] = category_summary["Pass Rate Num"].map("{:.2f}%".format)
        category_summary["Fail Rate (%)"] = (category_summary["Failed"] / category_summary["Total"] * 100).map("{:.2f}%".format)
        category_summary["Reliability"] = category_summary["Pass Rate Num"].apply(calculate_reliability)
        display_cat_summary = category_summary.drop(columns=["Pass Rate Num"])
        st.dataframe(display_cat_summary, use_container_width=True, hide_index=True)
    st.subheader("Question Type Reliability Impact")
    if qtype_col and status_col and not filtered_df.empty:
        qt_perf = filtered_df.groupby([qtype_col, status_col]).size().reset_index(name="Count")
        fig_qt = px.bar(
            qt_perf,
            x=qtype_col,
            y="Count",
            color=status_col,
            barmode="stack",
            color_discrete_map={"PASS": "#2ea44f", "FAIL": "#cb2431"},
            title="Status Breakdown by Question Type"
        )
        st.plotly_chart(fig_qt, use_container_width=True)
with tab3:
    st.subheader("🎯 Failure Root Cause Analysis")    
    reason_col = get_col(filtered_df, "Failure Reason")
    fail_df = filtered_df[filtered_df[status_col] == "FAIL"].copy() if status_col else pd.DataFrame()
    if fail_df.empty:
        st.success("🎉 No failed test cases found under current filter selection.")
    else:
        top_reason = fail_df[reason_col].mode()[0] if reason_col and not fail_df[reason_col].empty else "N/A"
        top_cat = fail_df[cat_col].mode()[0] if cat_col and not fail_df[cat_col].empty else "N/A" 
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Failed Cases", len(fail_df))
        m2.metric("Primary Failure Category", top_cat)
        m3.metric("Most Frequent Failure Type", truncate_text(top_reason, 30))
        st.markdown("---")
        if reason_col:
            reason_counts = (
                fail_df[reason_col]
                .replace("", pd.NA)
                .dropna()
                .value_counts()
                .reset_index()
            )
            reason_counts.columns = ["Full Failure Reason", "Count"]
            reason_counts["Short Label"] = reason_counts["Full Failure Reason"].apply(lambda x: truncate_text(x, 42))
            chart_height = max(400, len(reason_counts) * 35)
            fig_fail = px.bar(
                reason_counts,
                y="Short Label",
                x="Count",
                orientation="h",
                color="Count",
                color_continuous_scale="Reds",
                custom_data=["Full Failure Reason"],
                title="<b>Failure Reasons Distribution (Sorted by Occurrence)</b>",
            )
            fig_fail.update_traces(
                hovertemplate="<b>Reason:</b> %{customdata[0]}<br><b>Count:</b> %{x}<extra></extra>"
            )
            fig_fail.update_layout(
                yaxis={"autorange": "reversed", "title": ""},
                xaxis_title="Number of Failed Test Cases",
                height=chart_height,
                margin=dict(l=10, r=20, t=40, b=40),
            )
            st.plotly_chart(fig_fail, use_container_width=True)
        st.subheader("📋 Failed Test Case Breakdown Table")
        fail_display_cols = ["Test Case ID", "Category", "Subcategory", "User Question", "Chatbot Answer", "Expected Answer", "Failure Reason"]
        avail_cols = [c for c in fail_display_cols if get_col(fail_df, c)]
        st.dataframe(fail_df[[get_col(fail_df, c) for c in avail_cols]], use_container_width=True, height=450, hide_index=True)
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
    available_cols = [col for col in display_cols if get_col(filtered_df, col)]
    mapped_cols = [get_col(filtered_df, col) for col in available_cols]
    st.dataframe(filtered_df[mapped_cols], use_container_width=True, height=600, hide_index=True)
    csv_data = filtered_df[mapped_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Current View to CSV",
        data=csv_data,
        file_name="Sportime_Filtered_QA_Export.csv",
        mime="text/csv",
    )
with tab5:
    st.subheader("📄 Raw Workbook Sheet Explorer")
    col_sheet, col_info = st.columns([2, 3])
    with col_sheet:
        selected_sheet = st.selectbox("Select Sheet to Inspect", list(workbook.keys()))
    raw_sheet_df = workbook[selected_sheet].copy()
    cleaned_df = clean_raw_sheet(raw_sheet_df)
    with col_info:
        st.caption(f"**Sheet Stats:** {cleaned_df.shape[0]} Rows × {cleaned_df.shape[1]} Columns")
    st.markdown("---") 
    st.dataframe(
        cleaned_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )
st.markdown("---")
st.caption("Sportime Chatbot QA & System Reliability Dashboard")
