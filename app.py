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
    
    # Find row with most non-null entries to set as header if current headers contain "Unnamed" or numbers
    if any(str(col).startswith("Unnamed") or str(col).isdigit() for col in temp_df.columns):
        header_idx = None
        for i in range(min(10, len(temp_df))):
            row_vals = temp_df.iloc[i].dropna().astype(str).str.strip().tolist()
            if len(row_vals) >= 3 and not any("Sportime" in v for v in row_vals):
                header_idx = i
                break
        
        if header_idx is not None:
            new_headers = temp_df.iloc[header_idx].astype(str).str.strip()
            temp_df = temp_df.iloc[header_idx + 1:].copy()
            temp_df.columns = new_headers

    # Drop fully empty rows/cols and reset index
    temp_df = temp_df.dropna(how="all").loc[:, temp_df.notna().any()]
    temp_df = temp_df.fillna("-")
    
    # Format decimal percentage columns
    for col in temp_df.columns:
        col_str = str(col).lower()
        if any(kw in col_str for kw in ["rate", "accuracy", "pass %", "fail %", "relevance"]):
            temp_df[col] = pd.to_numeric(temp_df[col], errors="ignore")
            temp_df[col] = temp_df[col].apply(
                lambda x: f"{x * 100:.2f}%" if isinstance(x, (int, float)) and 0 <= x <= 1 else x
            )

    return temp_df

# =========================================================
# FILE UPLOAD AND WORKBOOK LOADING
# =========================================================
@st.cache_data
def load_all_sheets(file_bytes):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheets = {}

    for name in xls.sheet_names:
        if name == "QA & Master Audit":
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=name, header=3)
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

# =========================================================
# HEADER & UPLOAD
# =========================================================
st.title("🏀 Sportime Chatbot QA & System Reliability Dashboard")
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

df_master = workbook.get("QA & Master Audit", pd.DataFrame())
if df_master.empty:
    st.error("QA & Master Audit sheet was not loaded correctly.")
    st.stop()

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("🔍 Global Data Filters")

cat_options = ["All"] + sorted(df_master["Category"].replace("", pd.NA).dropna().unique().tolist()) if "Category" in df_master.columns else ["All"]
selected_cat = st.sidebar.selectbox("Filter Category / Topic", cat_options)

qtype_options = ["All"] + sorted(df_master["Question Type"].replace("", pd.NA).dropna().unique().tolist()) if "Question Type" in df_master.columns else ["All"]
selected_qtype = st.sidebar.selectbox("Filter Question Type", qtype_options)

status_options = ["All"] + sorted(df_master["Status"].replace("", pd.NA).dropna().unique().tolist()) if "Status" in df_master.columns else ["All"]
selected_status = st.sidebar.selectbox("Filter Status", status_options)

relevance_options = ["All"] + sorted(df_master["Relevance"].replace("", pd.NA).dropna().unique().tolist()) if "Relevance" in df_master.columns else ["All"]
selected_relevance = st.sidebar.selectbox("Filter Intent Relevance", relevance_options)

# Apply Filters
filtered_df = df_master.copy()
if selected_cat != "All": filtered_df = filtered_df[filtered_df["Category"] == selected_cat]
if selected_qtype != "All": filtered_df = filtered_df[filtered_df["Question Type"] == selected_qtype]
if selected_status != "All": filtered_df = filtered_df[filtered_df["Status"] == selected_status]
if selected_relevance != "All": filtered_df = filtered_df[filtered_df["Relevance"] == selected_relevance]

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

# Tab 1 & Tab 2 remain intact ...
# (Included in full deployment build)

# =========================================================
# TAB 3: ENHANCED FAILURE REASON DEEP DIVE
# =========================================================
with tab3:
    st.subheader("🎯 Failure Root Cause Analysis")
    
    fail_df = filtered_df[filtered_df["Status"] == "FAIL"].copy() if "Status" in filtered_df.columns else pd.DataFrame()

    if fail_df.empty:
        st.success("🎉 No failed test cases found under current filter selection.")
    else:
        # Failure Summary Metrics
        top_reason = fail_df["Failure Reason"].mode()[0] if "Failure Reason" in fail_df.columns and not fail_df["Failure Reason"].empty else "N/A"
        top_cat = fail_df["Category"].mode()[0] if "Category" in fail_df.columns and not fail_df["Category"].empty else "N/A"
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Failed Cases", len(fail_df))
        m2.metric("Primary Failure Category", top_cat)
        m3.metric("Most Frequent Failure Type", truncate_text(top_reason, 30))

        st.markdown("---")

        if "Failure Reason" in fail_df.columns:
            reason_counts = (
                fail_df["Failure Reason"]
                .replace("", pd.NA)
                .dropna()
                .value_counts()
                .reset_index()
            )
            reason_counts.columns = ["Full Failure Reason", "Count"]
            reason_counts["Short Label"] = reason_counts["Full Failure Reason"].apply(lambda x: truncate_text(x, 42))

            # Dynamic height based on number of failure reasons
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
        avail_cols = [c for c in fail_display_cols if c in fail_df.columns]
        st.dataframe(fail_df[avail_cols], use_container_width=True, height=450, hide_index=True)

# =========================================================
# TAB 5: SOPHISTICATED RAW WORKBOOK SHEETS
# =========================================================
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
    
    # Styled Data Table Display
    st.dataframe(
        cleaned_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("Sportime Chatbot QA & System Reliability Dashboard")