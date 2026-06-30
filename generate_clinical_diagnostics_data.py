import pandas as pd
import numpy as np
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------

SEED = 42
NUM_RECORDS = 10000
CURRENT_YEAR = 2026

random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# LOOKUP VALUES
# -----------------------------

client_facilities = [
    "Northview Medical Center",
    "Lakefront Oncology Clinic",
    "Midwest Family Health",
    "Buffalo Grove Surgical Center",
    "Prairie Diagnostic Partners",
    "Evergreen Women's Health",
    "Horizon Gastroenterology",
    "Sterling Primary Care",
    "Summit Urology Group",
    "Riverside Dermatology"
]

physicians = [
    "Dr. Meera Shah",
    "Dr. Daniel Brooks",
    "Dr. Priya Raman",
    "Dr. Jonathan Miller",
    "Dr. Aisha Khan",
    "Dr. Robert Chen",
    "Dr. Neha Patel",
    "Dr. William Harris",
    "Dr. Emily Stone",
    "Dr. Omar Siddiqui"
]

specimen_types = [
    "Tissue Biopsy",
    "Blood",
    "Cytology",
    "Bone Marrow",
    "Surgical Specimen",
    "Skin Shave",
    "Fine Needle Aspirate",
    "GI Biopsy",
    "Breast Core Biopsy",
    "Urine Cytology"
]

test_types = [
    "Histopathology",
    "Cytology",
    "Immunohistochemistry",
    "Molecular Testing",
    "Flow Cytometry",
    "Hematopathology"
]

priority_levels = ["Routine", "Urgent", "STAT"]

report_statuses = ["Final", "In Review", "Pending", "On Hold"]

diagnosis_texts = [
    "Benign epithelial tissue; no malignancy identified.",
    "Chronic inflammation present; negative for dysplasia.",
    "Atypical cells present; clinical correlation recommended.",
    "Findings suspicious for malignancy; additional testing recommended.",
    "Invasive carcinoma identified in submitted tissue.",
    "No diagnostic abnormality identified.",
    "Specimen adequate for evaluation.",
    "Low-grade dysplasia identified.",
    "High-grade dysplasia identified.",
    "Reactive cellular changes noted."
]

discrepancy_types = [
    "None",
    "Missing physician information",
    "Missing diagnosis text",
    "Duplicate specimen ID",
    "Delayed report",
    "Specimen/test mismatch",
    "Missing client facility",
    "Invalid date sequence"
]

resolution_statuses = [
    "No Issue",
    "Resolved",
    "Pending Review",
    "Escalated",
    "Awaiting Client Response"
]

# Valid specimen/test pairings for mismatch checks
valid_test_map = {
    "Tissue Biopsy": ["Histopathology", "Immunohistochemistry", "Molecular Testing"],
    "Blood": ["Molecular Testing", "Flow Cytometry", "Hematopathology"],
    "Cytology": ["Cytology", "Molecular Testing"],
    "Bone Marrow": ["Hematopathology", "Flow Cytometry", "Molecular Testing"],
    "Surgical Specimen": ["Histopathology", "Immunohistochemistry"],
    "Skin Shave": ["Histopathology"],
    "Fine Needle Aspirate": ["Cytology", "Molecular Testing"],
    "GI Biopsy": ["Histopathology", "Immunohistochemistry", "Molecular Testing"],
    "Breast Core Biopsy": ["Histopathology", "Immunohistochemistry", "Molecular Testing"],
    "Urine Cytology": ["Cytology", "Molecular Testing"]
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def random_patient_id():
    """Create fake masked patient ID. No real patient info."""
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PT-{code}"

def random_date(start_date, end_date):
    """Generate random date between two dates."""
    delta_days = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, delta_days))

def generate_specimen_id(i):
    """Create mostly unique specimen IDs."""
    return f"SP-{CURRENT_YEAR}-{i:06d}"

def choose_with_prob(options, probabilities):
    """Choose value based on probability distribution."""
    return np.random.choice(options, p=probabilities)

def calculate_tat_hours(start_date, end_date):
    """Calculate turnaround time in hours."""
    return int((end_date - start_date).total_seconds() / 3600)

# -----------------------------
# GENERATE RAW RECORDS
# -----------------------------

records = []

start_date = datetime(CURRENT_YEAR, 1, 1)
end_date = datetime(CURRENT_YEAR, 6, 30)

for i in range(1, NUM_RECORDS + 1):
    specimen_id = generate_specimen_id(i)

    patient_id_masked = random_patient_id()
    patient_age = random.randint(18, 90)
    patient_sex = choose_with_prob(["Female", "Male", "Other"], [0.51, 0.48, 0.01])

    client_facility = random.choice(client_facilities)
    physician_name = random.choice(physicians)

    specimen_type = random.choice(specimen_types)

    # 92% valid specimen/test pairing, 8% potential mismatch
    if random.random() < 0.92:
        test_type = random.choice(valid_test_map[specimen_type])
    else:
        test_type = random.choice(test_types)

    priority = choose_with_prob(priority_levels, [0.78, 0.17, 0.05])

    collection_date = random_date(start_date, end_date)

    # Most specimens received within 0-2 days
    received_date = collection_date + timedelta(days=random.choice([0, 0, 1, 1, 2]))

    # Accession usually same day or next day
    accession_date = received_date + timedelta(days=random.choice([0, 0, 0, 1]))

    # Report date depends on priority
    if priority == "STAT":
        report_delay_days = random.choice([0, 0, 1])
    elif priority == "Urgent":
        report_delay_days = random.choice([1, 1, 2, 3])
    else:
        report_delay_days = random.choice([2, 3, 4, 5, 6, 7])

    report_date = accession_date + timedelta(days=report_delay_days)

    report_status = choose_with_prob(
        report_statuses,
        [0.74, 0.14, 0.08, 0.04]
    )

    diagnosis_text = random.choice(diagnosis_texts)

    discrepancy_type = "None"
    resolution_status = "No Issue"

    # -----------------------------
    # INJECT REALISTIC DATA ISSUES
    # -----------------------------

    issue_roll = random.random()

    # 5% missing physician
    if issue_roll < 0.05:
        physician_name = ""
        discrepancy_type = "Missing physician information"
        resolution_status = random.choice(["Pending Review", "Awaiting Client Response"])

    # 4% missing diagnosis
    elif issue_roll < 0.09:
        diagnosis_text = ""
        discrepancy_type = "Missing diagnosis text"
        resolution_status = random.choice(["Pending Review", "Escalated"])

    # 3% delayed report
    elif issue_roll < 0.12:
        report_date = accession_date + timedelta(days=random.randint(8, 14))
        discrepancy_type = "Delayed report"
        resolution_status = random.choice(["Resolved", "Pending Review"])

    # 2% missing client facility
    elif issue_roll < 0.14:
        client_facility = ""
        discrepancy_type = "Missing client facility"
        resolution_status = random.choice(["Pending Review", "Awaiting Client Response"])

    # 1.5% invalid date sequence
    elif issue_roll < 0.155:
        received_date = collection_date - timedelta(days=random.randint(1, 3))
        discrepancy_type = "Invalid date sequence"
        resolution_status = random.choice(["Escalated", "Pending Review"])

    # 2.5% specimen/test mismatch
    elif issue_roll < 0.18:
        invalid_tests = [t for t in test_types if t not in valid_test_map[specimen_type]]
        if invalid_tests:
            test_type = random.choice(invalid_tests)
        discrepancy_type = "Specimen/test mismatch"
        resolution_status = random.choice(["Pending Review", "Resolved"])

    turnaround_time_hours = calculate_tat_hours(accession_date, report_date)

    # Create HIPAA-safe note
    if discrepancy_type == "None":
        hipaa_safe_notes = "Record passed initial quality review."
    else:
        hipaa_safe_notes = f"{discrepancy_type} identified during quality check. No direct patient identifiers stored."

    records.append({
        "specimen_id": specimen_id,
        "patient_id_masked": patient_id_masked,
        "patient_age": patient_age,
        "patient_sex": patient_sex,
        "client_facility": client_facility,
        "physician_name": physician_name,
        "specimen_type": specimen_type,
        "test_type": test_type,
        "priority": priority,
        "collection_date": collection_date.date(),
        "received_date": received_date.date(),
        "accession_date": accession_date.date(),
        "report_date": report_date.date(),
        "report_status": report_status,
        "diagnosis_text": diagnosis_text,
        "turnaround_time_hours": turnaround_time_hours,
        "discrepancy_type": discrepancy_type,
        "resolution_status": resolution_status,
        "hipaa_safe_notes": hipaa_safe_notes
    })

raw_df = pd.DataFrame(records)

# -----------------------------
# INJECT DUPLICATE SPECIMEN IDs
# -----------------------------

duplicate_count = int(NUM_RECORDS * 0.02)
duplicate_indices = np.random.choice(raw_df.index, duplicate_count, replace=False)

for idx in duplicate_indices:
    source_idx = random.randint(0, NUM_RECORDS - 1)
    raw_df.loc[idx, "specimen_id"] = raw_df.loc[source_idx, "specimen_id"]
    raw_df.loc[idx, "discrepancy_type"] = "Duplicate specimen ID"
    raw_df.loc[idx, "resolution_status"] = random.choice(["Pending Review", "Escalated"])
    raw_df.loc[idx, "hipaa_safe_notes"] = "Duplicate specimen ID identified during accessioning validation."

# -----------------------------
# VALIDATION / CLEANING RULES
# -----------------------------

clean_df = raw_df.copy()

# Convert date columns
date_cols = ["collection_date", "received_date", "accession_date", "report_date"]
for col in date_cols:
    clean_df[col] = pd.to_datetime(clean_df[col])

# Standardize text fields
text_cols = [
    "client_facility",
    "physician_name",
    "specimen_type",
    "test_type",
    "priority",
    "report_status",
    "diagnosis_text",
    "discrepancy_type",
    "resolution_status"
]

for col in text_cols:
    clean_df[col] = clean_df[col].astype(str).str.strip()

# Data quality flags
clean_df["duplicate_flag"] = clean_df.duplicated(subset=["specimen_id"], keep=False)

clean_df["missing_physician_flag"] = clean_df["physician_name"].eq("") | clean_df["physician_name"].eq("nan")

clean_df["missing_client_flag"] = clean_df["client_facility"].eq("") | clean_df["client_facility"].eq("nan")

clean_df["missing_diagnosis_flag"] = clean_df["diagnosis_text"].eq("") | clean_df["diagnosis_text"].eq("nan")

clean_df["invalid_date_flag"] = (
    (clean_df["received_date"] < clean_df["collection_date"]) |
    (clean_df["accession_date"] < clean_df["received_date"]) |
    (clean_df["report_date"] < clean_df["accession_date"])
)

clean_df["delayed_report_flag"] = clean_df["turnaround_time_hours"] > 168

def check_specimen_test_mismatch(row):
    valid_tests = valid_test_map.get(row["specimen_type"], [])
    return row["test_type"] not in valid_tests

clean_df["specimen_test_mismatch_flag"] = clean_df.apply(check_specimen_test_mismatch, axis=1)

clean_df["missing_info_flag"] = (
    clean_df["missing_physician_flag"] |
    clean_df["missing_client_flag"] |
    clean_df["missing_diagnosis_flag"]
)

clean_df["quality_issue_flag"] = (
    clean_df["duplicate_flag"] |
    clean_df["missing_info_flag"] |
    clean_df["invalid_date_flag"] |
    clean_df["delayed_report_flag"] |
    clean_df["specimen_test_mismatch_flag"]
)

# Quality score: starts at 100 and subtracts based on issues
clean_df["quality_score"] = 100

clean_df.loc[clean_df["duplicate_flag"], "quality_score"] -= 30
clean_df.loc[clean_df["missing_info_flag"], "quality_score"] -= 25
clean_df.loc[clean_df["invalid_date_flag"], "quality_score"] -= 25
clean_df.loc[clean_df["delayed_report_flag"], "quality_score"] -= 15
clean_df.loc[clean_df["specimen_test_mismatch_flag"], "quality_score"] -= 20

clean_df["quality_score"] = clean_df["quality_score"].clip(lower=0)

# Final issue category based on validation flags
def assign_final_issue(row):
    if row["duplicate_flag"]:
        return "Duplicate specimen ID"
    if row["missing_physician_flag"]:
        return "Missing physician information"
    if row["missing_client_flag"]:
        return "Missing client facility"
    if row["missing_diagnosis_flag"]:
        return "Missing diagnosis text"
    if row["invalid_date_flag"]:
        return "Invalid date sequence"
    if row["delayed_report_flag"]:
        return "Delayed report"
    if row["specimen_test_mismatch_flag"]:
        return "Specimen/test mismatch"
    return "None"

clean_df["final_issue_category"] = clean_df.apply(assign_final_issue, axis=1)

# Create flagged issues table
flagged_df = clean_df[clean_df["quality_issue_flag"]].copy()

flagged_df = flagged_df[
    [
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
        "hipaa_safe_notes"
    ]
]

# -----------------------------
# SUMMARY TABLE
# -----------------------------

summary_df = pd.DataFrame({
    "metric": [
        "total_records",
        "unique_specimen_ids",
        "duplicate_specimen_records",
        "records_with_quality_issues",
        "missing_physician_records",
        "missing_client_records",
        "missing_diagnosis_records",
        "invalid_date_records",
        "delayed_report_records",
        "specimen_test_mismatch_records",
        "average_turnaround_time_hours",
        "average_quality_score"
    ],
    "value": [
        len(clean_df),
        clean_df["specimen_id"].nunique(),
        int(clean_df["duplicate_flag"].sum()),
        int(clean_df["quality_issue_flag"].sum()),
        int(clean_df["missing_physician_flag"].sum()),
        int(clean_df["missing_client_flag"].sum()),
        int(clean_df["missing_diagnosis_flag"].sum()),
        int(clean_df["invalid_date_flag"].sum()),
        int(clean_df["delayed_report_flag"].sum()),
        int(clean_df["specimen_test_mismatch_flag"].sum()),
        round(clean_df["turnaround_time_hours"].mean(), 2),
        round(clean_df["quality_score"].mean(), 2)
    ]
})

# -----------------------------
# EXPORT FILES
# -----------------------------

raw_path = OUTPUT_DIR / "raw_specimen_records.csv"
clean_path = OUTPUT_DIR / "clean_specimen_records.csv"
flagged_path = OUTPUT_DIR / "flagged_quality_issues.csv"
summary_path = OUTPUT_DIR / "quality_summary_metrics.csv"

raw_df.to_csv(raw_path, index=False)
clean_df.to_csv(clean_path, index=False)
flagged_df.to_csv(flagged_path, index=False)
summary_df.to_csv(summary_path, index=False)

print("Dataset generation complete.")
print(f"Raw records saved to: {raw_path.resolve()}")
print(f"Clean records saved to: {clean_path.resolve()}")
print(f"Flagged issues saved to: {flagged_path.resolve()}")
print(f"Summary metrics saved to: {summary_path.resolve()}")

print("\nQuick Summary:")
print(summary_df)