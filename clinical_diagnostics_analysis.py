import pandas as pd
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt

# -----------------------------
# PATH SETUP
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

clean_path = DATA_DIR / "clean_specimen_records.csv"
flagged_path = DATA_DIR / "flagged_quality_issues.csv"
summary_path = DATA_DIR / "quality_summary_metrics.csv"

missing_inputs = [path for path in [clean_path, flagged_path, summary_path] if not path.exists()]
if missing_inputs:
    missing_list = "\n".join(str(path) for path in missing_inputs)
    raise FileNotFoundError(
        f"Missing input data files in {DATA_DIR}. Expected these files:\n{missing_list}"
    )

# -----------------------------
# LOAD DATA
# -----------------------------

clean_df = pd.read_csv(clean_path)
flagged_df = pd.read_csv(flagged_path)
summary_df = pd.read_csv(summary_path)

date_cols = ["collection_date", "received_date", "accession_date", "report_date"]

for col in date_cols:
    clean_df[col] = pd.to_datetime(clean_df[col])

print("Data loaded successfully.")
print("Clean records:", clean_df.shape)
print("Flagged records:", flagged_df.shape)

# -----------------------------
# BASIC PROJECT METRICS
# -----------------------------

total_records = len(clean_df)
quality_issues = clean_df["quality_issue_flag"].sum()
issue_rate = round((quality_issues / total_records) * 100, 2)
avg_tat = round(clean_df["turnaround_time_hours"].mean(), 2)
avg_quality_score = round(clean_df["quality_score"].mean(), 2)

pending_reports = clean_df[
    clean_df["report_status"].isin(["Pending", "On Hold", "In Review"])
].shape[0]

duplicate_records = clean_df["duplicate_flag"].sum()
missing_info_records = clean_df["missing_info_flag"].sum()
delayed_reports = clean_df["delayed_report_flag"].sum()
invalid_dates = clean_df["invalid_date_flag"].sum()
mismatch_records = clean_df["specimen_test_mismatch_flag"].sum()

print("\n--- KEY METRICS ---")
print(f"Total Records: {total_records}")
print(f"Quality Issue Records: {quality_issues}")
print(f"Issue Rate: {issue_rate}%")
print(f"Average Turnaround Time: {avg_tat} hours")
print(f"Average Quality Score: {avg_quality_score}")
print(f"Pending / On Hold / In Review Reports: {pending_reports}")
print(f"Duplicate Specimen Records: {duplicate_records}")
print(f"Missing Info Records: {missing_info_records}")
print(f"Delayed Reports: {delayed_reports}")
print(f"Invalid Date Records: {invalid_dates}")
print(f"Specimen/Test Mismatches: {mismatch_records}")

# -----------------------------
# GROUPED ANALYSIS
# -----------------------------

issue_by_category = (
    clean_df[clean_df["final_issue_category"] != "None"]
    .groupby("final_issue_category")
    .size()
    .reset_index(name="record_count")
    .sort_values("record_count", ascending=False)
)

tat_by_priority = (
    clean_df.groupby("priority")["turnaround_time_hours"]
    .mean()
    .reset_index()
    .sort_values("turnaround_time_hours", ascending=False)
)

status_distribution = (
    clean_df["report_status"]
    .value_counts()
    .reset_index()
)

status_distribution.columns = ["report_status", "record_count"]

facility_quality = (
    clean_df.groupby("client_facility")
    .agg(
        total_records=("specimen_id", "count"),
        quality_issues=("quality_issue_flag", "sum"),
        avg_quality_score=("quality_score", "mean"),
        avg_tat_hours=("turnaround_time_hours", "mean")
    )
    .reset_index()
)

facility_quality["issue_rate_percent"] = round(
    (facility_quality["quality_issues"] / facility_quality["total_records"]) * 100, 2
)

facility_quality = facility_quality.sort_values("issue_rate_percent", ascending=False)

daily_volume = (
    clean_df.groupby("received_date")
    .size()
    .reset_index(name="specimen_count")
)

# -----------------------------
# SAVE ANALYSIS TABLES
# -----------------------------

issue_by_category.to_csv(OUTPUT_DIR / "issue_by_category.csv", index=False)
tat_by_priority.to_csv(OUTPUT_DIR / "tat_by_priority.csv", index=False)
status_distribution.to_csv(OUTPUT_DIR / "report_status_distribution.csv", index=False)
facility_quality.to_csv(OUTPUT_DIR / "facility_quality_summary.csv", index=False)
daily_volume.to_csv(OUTPUT_DIR / "daily_specimen_volume.csv", index=False)

print("\nAnalysis tables saved inside outputs folder.")

# -----------------------------
# CREATE SQL DATABASE
# -----------------------------

db_path = OUTPUT_DIR / "clinical_diagnostics_quality.db"

conn = sqlite3.connect(db_path)

clean_df.to_sql("clean_specimen_records", conn, if_exists="replace", index=False)
flagged_df.to_sql("flagged_quality_issues", conn, if_exists="replace", index=False)

print(f"SQLite database created: {db_path}")

# -----------------------------
# SQL QUERIES
# -----------------------------

queries = {
    "total_records": """
        SELECT COUNT(*) AS total_records
        FROM clean_specimen_records;
    """,

    "quality_issue_rate": """
        SELECT 
            COUNT(*) AS total_records,
            SUM(CASE WHEN quality_issue_flag = 1 THEN 1 ELSE 0 END) AS quality_issue_records,
            ROUND(
                100.0 * SUM(CASE WHEN quality_issue_flag = 1 THEN 1 ELSE 0 END) / COUNT(*), 
                2
            ) AS issue_rate_percent
        FROM clean_specimen_records;
    """,

    "issue_category_summary": """
        SELECT 
            final_issue_category,
            COUNT(*) AS record_count
        FROM clean_specimen_records
        WHERE final_issue_category != 'None'
        GROUP BY final_issue_category
        ORDER BY record_count DESC;
    """,

    "turnaround_time_by_priority": """
        SELECT 
            priority,
            ROUND(AVG(turnaround_time_hours), 2) AS avg_turnaround_time_hours,
            COUNT(*) AS total_records
        FROM clean_specimen_records
        GROUP BY priority
        ORDER BY avg_turnaround_time_hours DESC;
    """,

    "client_facility_quality": """
        SELECT 
            client_facility,
            COUNT(*) AS total_records,
            SUM(CASE WHEN quality_issue_flag = 1 THEN 1 ELSE 0 END) AS quality_issue_records,
            ROUND(AVG(quality_score), 2) AS avg_quality_score,
            ROUND(AVG(turnaround_time_hours), 2) AS avg_tat_hours
        FROM clean_specimen_records
        GROUP BY client_facility
        ORDER BY quality_issue_records DESC;
    """,

    "records_needing_review": """
        SELECT 
            specimen_id,
            patient_id_masked,
            client_facility,
            physician_name,
            specimen_type,
            test_type,
            report_status,
            final_issue_category,
            quality_score
        FROM clean_specimen_records
        WHERE quality_issue_flag = 1
        ORDER BY quality_score ASC
        LIMIT 25;
    """
}

sql_report = []

for query_name, query in queries.items():
    result = pd.read_sql_query(query, conn)
    result.to_csv(OUTPUT_DIR / f"{query_name}.csv", index=False)

    sql_report.append(f"\n--- {query_name.upper()} ---\n")
    sql_report.append(result.to_string(index=False))

conn.close()

with open(OUTPUT_DIR / "sql_query_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_report))

print("SQL query outputs saved.")

# -----------------------------
# CHARTS
# -----------------------------

plt.figure(figsize=(10, 6))
plt.bar(issue_by_category["final_issue_category"], issue_by_category["record_count"])
plt.title("Quality Issues by Category")
plt.xlabel("Issue Category")
plt.ylabel("Record Count")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "quality_issues_by_category.png")
plt.close()

plt.figure(figsize=(8, 5))
plt.bar(tat_by_priority["priority"], tat_by_priority["turnaround_time_hours"])
plt.title("Average Turnaround Time by Priority")
plt.xlabel("Priority")
plt.ylabel("Average TAT Hours")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "tat_by_priority.png")
plt.close()

plt.figure(figsize=(8, 5))
plt.bar(status_distribution["report_status"], status_distribution["record_count"])
plt.title("Report Status Distribution")
plt.xlabel("Report Status")
plt.ylabel("Record Count")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "report_status_distribution.png")
plt.close()

plt.figure(figsize=(12, 6))
plt.plot(daily_volume["received_date"], daily_volume["specimen_count"])
plt.title("Daily Specimen Volume")
plt.xlabel("Received Date")
plt.ylabel("Specimen Count")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "daily_specimen_volume.png")
plt.close()

top_facilities = facility_quality.head(10)

plt.figure(figsize=(12, 6))
plt.bar(top_facilities["client_facility"], top_facilities["issue_rate_percent"])
plt.title("Top Client Facilities by Quality Issue Rate")
plt.xlabel("Client Facility")
plt.ylabel("Issue Rate Percent")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "facility_issue_rate.png")
plt.close()

print("Charts saved inside outputs folder.")

# -----------------------------
# FINAL WRITTEN SUMMARY
# -----------------------------

summary_text = f"""
Clinical Diagnostics Data Quality Analysis Summary

Project Overview:
This project simulates a pathology laboratory workflow focused on specimen accessioning,
diagnostic reporting accuracy, discrepancy tracking, turnaround time monitoring, and
HIPAA-safe patient identifier handling.

Dataset:
- Total synthetic specimen records analyzed: {total_records}
- Patient identifiers are masked and synthetic.
- Data includes specimen type, test type, physician/client details, report status,
  turnaround time, diagnosis text, and quality-control flags.

Key Findings:
- {quality_issues} records were flagged with at least one data quality issue.
- Overall issue rate was {issue_rate}%.
- Average turnaround time was {avg_tat} hours.
- Average quality score was {avg_quality_score}.
- {pending_reports} records were still Pending, On Hold, or In Review.
- {duplicate_records} records had duplicate specimen ID concerns.
- {missing_info_records} records had missing physician, client, or diagnosis information.
- {delayed_reports} records were delayed beyond the 168-hour threshold.
- {invalid_dates} records had invalid date sequences.
- {mismatch_records} records had specimen/test mismatch issues.

Operational Relevance:
The analysis supports a clinical diagnostics workflow by identifying records that require
manual review before final reporting. These checks reduce risk from duplicate accession IDs,
missing provider information, delayed reports, incomplete diagnostic text, and specimen/test
classification errors.

Skills Demonstrated:
- Healthcare data quality analysis
- Specimen tracking workflow simulation
- Reporting accuracy checks
- SQL query development
- Python data cleaning
- Operational dashboard preparation
- HIPAA-safe masked patient data handling
"""

with open(OUTPUT_DIR / "project_summary.txt", "w", encoding="utf-8") as f:
    f.write(summary_text)

print("Project summary saved.")
print("\nProject analysis complete. Check the outputs folder.")
print("\nExact output locations:")
print(f"Outputs folder: {OUTPUT_DIR.resolve()}")
print(f"Project summary: {(OUTPUT_DIR / 'project_summary.txt').resolve()}")
print(f"SQL query results: {(OUTPUT_DIR / 'sql_query_results.txt').resolve()}")
print(f"Chart: {(OUTPUT_DIR / 'quality_issues_by_category.png').resolve()}")
print(f"Chart: {(OUTPUT_DIR / 'tat_by_priority.png').resolve()}")
print(f"Chart: {(OUTPUT_DIR / 'report_status_distribution.png').resolve()}")
print(f"Chart: {(OUTPUT_DIR / 'daily_specimen_volume.png').resolve()}")
print(f"Chart: {(OUTPUT_DIR / 'facility_issue_rate.png').resolve()}")
print(f"Database: {(OUTPUT_DIR / 'clinical_diagnostics_quality.db').resolve()}")
