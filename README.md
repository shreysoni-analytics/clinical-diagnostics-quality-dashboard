# Clinical Diagnostics Data Quality & Specimen Tracking Analysis

This project generates synthetic pathology lab specimen records, runs quality checks, saves analysis outputs, and provides an optional Streamlit dashboard.

## Project Root

Use this folder in VS Code:

`C:\Users\shrey\OneDrive`

## Files

- `generate_clinical_diagnostics_data.py`
- `clinical_diagnostics_analysis.py`
- `app.py`
- `requirements.txt`
- `RUN_INSTRUCTIONS.txt`
- `data/`
- `outputs/`

## How to Run

Follow the commands in `RUN_INSTRUCTIONS.txt`.

## What the Project Does

- Generates synthetic pathology data with masked patient IDs.
- Validates specimen and report quality rules.
- Exports CSV outputs, a SQLite database, and chart images.
- Displays the results in a Streamlit dashboard.

## Validation Rules

- Duplicate specimen IDs
- Missing physician/client/diagnosis values
- Invalid date sequences
- Delayed reports beyond 168 hours
- Specimen/test mismatches

## Notes

The Streamlit app reads from the local `data/` and `outputs/` folders inside this project root.