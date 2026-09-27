
# GovernAI — Corporate Governance Assessment & Risk Insight System

GovernAI is a Python-based application that analyzes corporate governance documents and identifies relevant evidence using keyword-based text analysis.

The application helps reviewers examine governance documentation across key areas, view preliminary documentation coverage indicators, record human review decisions, and export assessment reports.

> **Disclaimer:** GovernAI is a prototype documentation assessment tool. It does not provide legal advice, certify regulatory compliance, or determine whether governance controls are implemented or effective. All findings require human verification.

## Features

- **PDF Upload:** Upload corporate governance PDF documents for assessment.
- **Text Extraction:** Extract text from PDFs using PyPDF.
- **OCR Support:** Use Tesseract OCR and Poppler to process scanned PDF pages.
- **Governance Checklist:** Analyze documents across five governance areas.
- **Evidence Identification:** Identify matching keywords and supporting text with page references.
- **Risk Insight Dashboard:** View keyword coverage, documentation risk indicators, and assessment summaries.
- **Human Review Workflow:** Record reviewer status and comments for each governance area.
- **Review History:** Store and retrieve reviewer decisions using SQLite.
- **Report Export:** Export assessment results as CSV and PDF.

## Governance Areas

| Governance Area | Assessment Focus |
|---|---|
| Risk Management | Risk identification, assessment, mitigation, and monitoring |
| Whistleblower Mechanism | Reporting misconduct and confidential reporting channels |
| Data Protection | Protection of personal and sensitive information |
| Board Oversight | Board responsibilities and oversight |
| Internal Controls | Internal control procedures and monitoring |

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| Streamlit | Web application interface and dashboard |
| PyPDF | PDF text extraction |
| Tesseract OCR | Optical character recognition |
| Poppler | PDF-to-image conversion for OCR |
| Pandas | Data processing and assessment results |
| SQLite | Reviewer history storage |
| ReportLab | PDF report generation |

## How It Works

1. Upload a corporate governance PDF.
2. Extract document text using PDF text extraction.
3. Apply OCR to pages without extractable text.
4. Search extracted text for governance checklist keywords.
5. Display matching evidence, coverage indicators, and preliminary documentation risk levels.
6. Allow a reviewer to verify findings and enter comments.
7. Export the assessment as a CSV or PDF report.

## Risk Scoring

The prototype calculates keyword coverage as:

`Coverage (%) = Matched unique checklist keywords / Total checklist keywords × 100`

The documentation risk score is calculated as:

`Documentation Risk Score = 100 − Coverage (%)`

The application categorizes scores as:

- High: Score ≥ 70
- Medium: Score ≥ 40 and less than 70
- Low: Score less than 40

These scores are prototype keyword-coverage indicators, not validated risk measurements or legal compliance ratings. Keyword matches do not prove control effectiveness, and missing matches do not prove non-compliance.

## Installation and Setup

### Prerequisites

- Python 3.10 or a compatible Python version
- Git
- Tesseract OCR
- Poppler for Windows

Install Tesseract OCR and Poppler separately and configure their installation paths in `app.py` if necessary.

### 1. Clone the repository

```bash
git clone https://github.com/TrishaGanesha/GovernAI.git
cd GovernAI
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run the application using the virtual environment's Python executable directly.

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure OCR paths

Check the Tesseract and Poppler paths in `app.py`. Update them to match the local installation.

### 5. Run the application

```powershell
streamlit run app.py
```

The Streamlit application will open in your browser.

## Project Structure

```text
GovernAI/
├── app.py
├── README.md
├── requirements.txt
└── .gitignore
```

The SQLite database is created locally when the application runs and is not intended to be committed to the repository.

## Future Enhancements

- Semantic evidence retrieval using NLP.
- More detailed evidence validation and reviewer workflows.
- Configurable governance checklists and jurisdiction-specific references.
- Improved OCR handling for mixed text and scanned documents.
- Automated testing and deployment.

## Author

**Trisha G**

MCA — Artificial Intelligence & Data Science

GitHub: [TrishaGanesha](https://github.com/TrishaGanesha)

---

This project is developed for educational and prototype purposes.
