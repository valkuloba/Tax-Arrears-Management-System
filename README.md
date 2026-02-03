# Tax-Arrears-Management-System
## Project Overview

The Tax Arrears Management System is a Python-based application designed to simulate how a tax authority (such as KRA) tracks, analyzes, and manages outstanding tax arrears.

The system records taxpayers, tax assessments, and payments, then calculates outstanding balances and categorizes arrears based on their age to support compliance monitoring and revenue recovery.

## Problem solved
Tax authorities face persistent challenges in effectively tracking, analyzing, and managing tax arrears due to high taxpayer volumes, different tax obligations, payment plans, and varying arrears ages. Reliance on manual systems often leads to inaccurate arrears balances, delayed identification of high-risk cases, and inefficient compliance monitoring. This project addresses these challenges by providing an automated Tax Arrears Management System that centralizes taxpayer records, calculates outstanding balances, categorizes arrears by age, and highlights high-risk arrears to support timely decision-making, improved revenue collection and an overall easier analysis.

## Features
**Taxpayer Management**
- Add and view taxpayer profiles
- Unique taxpayer identification (PIN)

**Tax Assessment & Payment Tracking**
- Record assessed tax amounts
- Support partial and full payments
- Automatic balance calculation

**Arrears Aging Analysis**
- Categorizes arrears based on assessment date
- Highlights long-outstanding arrears

**Risk Classification**
- Low Risk: 0–6 months
- Medium Risk: 6–12 months
- High Risk: Over 12 months

**Reporting**
- Total arrears value
- Arrears by aging category
- Identification of high-risk taxpayers

## Technologies used
- Python 3
- SQLite
- Streamlit (Web Interface & Dashboard)
- Pandas
- Datetime
- CSV / Excel

## Data Source
Manual creation.

## Project Success Criteria

The project will be considered successful if it accurately records taxpayer data, tax assessments, and payments; correctly calculates outstanding tax arrears; categorizes arrears by age; identifies high-risk arrears cases; and generates clear, reliable reports through a user-friendly interface. The system should operate without errors using manually created data and demonstrate effective application of Python programming, database management, and data analysis principles.

## Stretch goals
- User Authentication and Roles
- Automated Compliance Notifications
- Advanced Risk Scoring
- Deploy the Streamlit application locally or on a cloud platform
