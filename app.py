import pandas as pd
from pathlib import Path

import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

clean_path = DATA_DIR / "clean_specimen_records.csv"
flagged_path = DATA_DIR / "flagged_quality_issues.csv"
project_summary_path = OUTPUT_DIR / "project_summary.txt"
sql_results_path = OUTPUT_DIR / "sql_query_results.txt"

st.set_page_config(
    page_title="Clinical Diagnostics Quality Dashboard",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #102a43 0%, #243b53 45%, #486581 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .muted { color: #d9e2ec; }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "Not available yet. Run the analysis script first."


required_paths = [clean_path, flagged_path]
missing_paths = [path for path in required_paths if not path.exists()]

if missing_paths:
    missing_names = "\n".join(path.name for path in missing_paths)
    st.error("Missing input files:\n" + missing_names)
    st.stop()


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    clean_df = pd.read_csv(clean_path)
    flagged_df = pd.read_csv(flagged_path)
    return clean_df, flagged_df


clean_df, flagged_df = load_data()

for col in ["collection_date", "received_date", "accession_date", "report_date"]:
    clean_df[col] = pd.to_datetime(clean_df[col])

total_records = len(clean_df)
quality_issues = int(clean_df["quality_issue_flag"].sum())
issue_rate = round((quality_issues / total_records) * 100, 2)
avg_tat = round(clean_df["turnaround_time_hours"].mean(), 2)
avg_quality_score = round(clean_df["quality_score"].mean(), 2)
pending_reports = int(clean_df[clean_df["report_status"].isin(["Pending", "On Hold", "In Review"])].shape[0])

st.markdown(
    """
    <div class="hero">
        <h1>Clinical Diagnostics Data Quality & Specimen Tracking</h1>
        <p class="muted">Synthetic pathology workflow analysis, quality validation, and review prioritization.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(5)
metric_cols[0].metric("Total Records", f"{total_records:,}")
metric_cols[1].metric("Quality Issue Records", f"{quality_issues:,}")
metric_cols[2].metric("Issue Rate", f"{issue_rate:.2f}%")
metric_cols[3].metric("Avg Turnaround Time", f"{avg_tat:.2f} hrs")
metric_cols[4].metric("Avg Quality Score", f"{avg_quality_score:.2f}")

metric_cols_2 = st.columns(2)
metric_cols_2[0].metric("Pending / On Hold / In Review", f"{pending_reports:,}")
metric_cols_2[1].metric("Records Requiring Manual Review", f"{len(flagged_df):,}")

left, right = st.columns([1.15, 0.85])

with left:
    st.subheader("Validation Rules")
    st.write(
        """
        The dataset flags duplicate specimen IDs, missing physician/client/diagnosis information,
        invalid date sequences, delayed reports beyond 168 hours, and specimen/test mismatches.
        Patient identifiers are synthetic and masked, so the project is safe for demo and workflow analysis.
        """
    )
    st.markdown("**Business/Lab Impact**")
    st.write(
        """
        This dashboard helps lab staff prioritize records that need manual review before final reporting, reducing risks related to duplicate accession IDs, missing provider details, delayed reports, incomplete diagnostic documentation, and specimen/test mismatches.
        """
    )

with right:
    st.subheader("Project Notes")
    st.text_area("Project Summary", read_text(project_summary_path), height=220)

st.divider()

issue_by_category = (
    clean_df[clean_df["final_issue_category"] != "None"]
    .groupby("final_issue_category")
    .size()
    .reset_index(name="record_count")
    .sort_values("record_count", ascending=False)
)

report_status_distribution = clean_df["report_status"].value_counts().reset_index()
report_status_distribution.columns = ["report_status", "record_count"]

tat_by_priority = (
    clean_df.groupby("priority")["turnaround_time_hours"]
    .mean()
    .reset_index()
    .sort_values("turnaround_time_hours", ascending=False)
)

specimen_volume_by_type = (
    clean_df.groupby("specimen_type")
    .size()
    .reset_index(name="record_count")
    .sort_values("record_count", ascending=False)
)

daily_volume = (
    clean_df.groupby("received_date")
    .size()
    .reset_index(name="specimen_count")
)

chart1, chart2 = st.columns(2)
with chart1:
    st.subheader("Quality Issues by Category")
    st.plotly_chart(
        px.bar(
            issue_by_category,
            x="final_issue_category",
            y="record_count",
            color="record_count",
            color_continuous_scale="Blues",
        ),
        use_container_width=True,
    )

with chart2:
    st.subheader("Report Status Distribution")
    st.plotly_chart(
        px.pie(report_status_distribution, names="report_status", values="record_count", hole=0.45),
        use_container_width=True,
    )

chart3, chart4 = st.columns(2)
with chart3:
    st.subheader("Turnaround Time by Priority")
    st.plotly_chart(
        px.bar(
            tat_by_priority,
            x="priority",
            y="turnaround_time_hours",
            color="turnaround_time_hours",
            color_continuous_scale="Tealgrn",
        ),
        use_container_width=True,
    )

with chart4:
    st.subheader("Specimen Volume by Type")
    st.plotly_chart(
        px.bar(
            specimen_volume_by_type,
            x="specimen_type",
            y="record_count",
            color="record_count",
            color_continuous_scale="Viridis",
        ),
        use_container_width=True,
    )

st.subheader("Daily Specimen Volume Trend")
st.plotly_chart(
    px.line(daily_volume, x="received_date", y="specimen_count", markers=True),
    use_container_width=True,
)

st.subheader("Flagged Records Requiring Review")
st.write(
    "These records are prioritized for manual review based on missing information, duplicate IDs, invalid dates, delayed reports, or specimen/test mismatches."
)
review_columns = [
    "specimen_id",
    "patient_id_masked",
    "client_facility",
    "physician_name",
    "specimen_type",
    "test_type",
    "priority",
    "report_status",
    "turnaround_time_hours",
    "final_issue_category",
    "resolution_status",
    "quality_score",
]
visible_review_columns = [col for col in review_columns if col in flagged_df.columns]
st.dataframe(flagged_df[visible_review_columns], use_container_width=True, height=420)

sql_text = read_text(sql_results_path)
with st.expander("SQL Query Results"):
    st.text(sql_text)
