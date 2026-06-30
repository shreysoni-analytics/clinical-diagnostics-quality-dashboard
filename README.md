# Clinical Diagnostics Data Quality & Specimen Tracking Dashboard

## Project Overview

This project is an AI-assisted healthcare analytics and data quality system that simulates a pathology laboratory workflow for specimen accessioning, diagnostic reporting, discrepancy tracking, turnaround time monitoring, and manual-review prioritization.

The goal was to model how clinical diagnostics teams can identify operational and reporting risks before final report release. The project uses a fully synthetic dataset of 10,000 pathology specimen records. No real patient data, protected health information, or actual diagnostic records were used.

## Problem Statement

Clinical diagnostic laboratories process large volumes of specimen and reporting data. Even small data quality issues can create workflow delays or reporting risks. Common issues include duplicate specimen IDs, missing physician or client details, incomplete diagnosis fields, invalid date sequences, delayed reports, and specimen/test mismatches.

This project addresses the problem by building a simulated data quality pipeline that flags high-risk records, summarizes operational metrics, and visualizes records requiring manual review.

## What I Built

I created an end-to-end analytics workflow that includes:

* AI-assisted synthetic pathology data generation
* Masked patient identifiers for HIPAA-safe simulation
* Python-based data cleaning and validation checks
* SQL-based operational reporting
* Quality scoring and issue categorization
* Streamlit dashboard deployment
* Visual analysis of reporting status, turnaround time, specimen volume, and flagged records

## Key Results

* Total synthetic records analyzed: 10,000
* Records flagged for quality issues: 2,647
* Overall simulated issue rate: 26.47%
* Average turnaround time: 96.78 hours
* Reports Pending, On Hold, or In Review: 2,507
* Duplicate specimen ID records: 393
* Missing information records: 1,216
* Specimen/test mismatches: 747

## Live Dashboard

View the deployed dashboard here:

https://clinical-diagnostics-quality-dashboard-3gtzpffp33dybrbpazp8fs.streamlit.app/

## Tools Used

Python, Pandas, SQLite, Plotly, Streamlit, Matplotlib, GitHub, Streamlit Cloud
