
import streamlit as st
from pypdf import PdfReader
from io import BytesIO
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_bytes
# OCR configuration for Windows
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from xml.sax.saxutils import escape
import hashlib

import sqlite3
from datetime import datetime
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

POPPLER_PATH = r"C:\poppler\Library\bin"
st.set_page_config(
    page_title="GovernAI",
    page_icon="📊",
    layout="wide"
)
# DATABASE SETUP

DB_NAME = "governai.db"


def init_database():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_history_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_hash TEXT NOT NULL,
        document_name TEXT NOT NULL,
        governance_area TEXT NOT NULL,
        reviewer_status TEXT NOT NULL,
        reviewer_comments TEXT,
        reviewed_at TEXT NOT NULL,
        UNIQUE(document_hash, governance_area)
            )
        """)

    conn.commit()
    conn.close()


def save_review(
    document_hash,
    document_name,
    governance_area,
    reviewer_status,
    reviewer_comments
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO review_history_v2 (
            document_hash,
            document_name,
            governance_area,
            reviewer_status,
            reviewer_comments,
            reviewed_at
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(document_hash, governance_area)
        DO UPDATE SET
            document_name = excluded.document_name,
            reviewer_status = excluded.reviewer_status,
            reviewer_comments = excluded.reviewer_comments,
            reviewed_at = excluded.reviewed_at
    """, (
        document_hash,
        document_name,
        governance_area,
        reviewer_status,
        reviewer_comments,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_review_history(document_hash):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            governance_area,
            reviewer_status,
            reviewer_comments,
            reviewed_at
        FROM review_history_v2
        WHERE document_hash = ?
        ORDER BY governance_area
    """, (document_hash,))

    rows = cursor.fetchall()
    conn.close()

    return rows

def get_all_reviews():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            document_name,
            document_hash,
            governance_area,
            reviewer_status,
            reviewer_comments,
            reviewed_at
        FROM review_history_v2
        ORDER BY reviewed_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows

init_database()
# Initialize reviewer status
if "review_status" not in st.session_state:
    st.session_state["review_status"] = {}

st.title("GovernAI")
st.subheader("Corporate Governance Assessment & Risk Insight System")

st.info(
    "This tool identifies governance-related evidence "
    "in uploaded documents. It does not certify legal compliance."
)

# Governance checklist


REVIEW_OPTIONS = [
    "Pending Review",
    "Verified",
    "Not Applicable",
    "Follow-up Required"]
checklist = {
    "Risk Management": {
        "keywords": [
            "risk management",
            "risk assessment",
            "risk mitigation",
            "risk monitoring"
        ],
        "source": "OECD corporate governance principles",
        "description": "Documented processes for identifying, assessing, and monitoring risks."
    },

    "Whistleblower Mechanism": {
        "keywords": [
            "whistleblower",
            "confidential reporting",
            "reporting misconduct",
            "vigil mechanism"
        ],
        "source": "Applicable governance and whistleblower guidelines",
        "description": "Documented channels and procedures for reporting misconduct."
    },

    "Data Protection": {
        "keywords": [
            "data protection",
            "personal data",
            "sensitive information",
            "authorized personnel"
        ],
        "source": "Applicable data protection requirements",
        "description": "Documented policies for protecting personal and sensitive information."
    },

    "Board Oversight": {
        "keywords": [
            "board oversees",
            "board responsibilities",
            "strategic decisions",
            "board oversight"
        ],
        "source": "OECD corporate governance principles",
        "description": "Documented board responsibilities and oversight."
    },

    "Internal Controls": {
        "keywords": [
            "internal controls",
            "control weaknesses",
            "corrective actions",
            "periodic reviews"
        ],
        "source": "COSO Internal Control Framework",
        "description": "Documented internal control procedures and monitoring."
    }
}



def assess_governance(page_texts):

    results = []

    for category, details in checklist.items():

        keywords = details["keywords"]
        evidence = []

        for page in page_texts:
            page_number = page["page"]
            text = page["text"]

            sentences = [
                sentence.strip()
                for sentence in text.replace("\n", " ").split(".")
                if sentence.strip()
            ]

            for sentence in sentences:
                sentence_lower = sentence.lower()
                matched_keywords = []

                for keyword in keywords:

                    # Normalize keyword and sentence
                    normalized_keyword = re.escape(
                        keyword.lower()
                    )

                    normalized_sentence = re.sub(
                        r"\s+",
                        " ",
                        sentence_lower
                    )

                    # Match keyword as a phrase
                    pattern = r"\b" + normalized_keyword + r"\b"

                    if re.search(pattern, normalized_sentence):
                        matched_keywords.append(keyword)

                if matched_keywords:
                    evidence.append({
                        "page": page_number,
                        "sentence": sentence,
                        "keywords": matched_keywords
                    })

            
        if not evidence:
            status = "No evidence found"
            evidence_text = (
                "No matching text identified. "
                "Manual review may be required."
            )

        else:
            status = "Manual review required"

            evidence_text = "\n\n".join(
                f"Page {item['page']}: {item['sentence']}"
                for item in evidence
            )

        # Calculate checklist keyword coverage

        matched_keywords = set()

        for item in evidence:
            for keyword in item["keywords"]:
                matched_keywords.add(keyword)

        total_keywords = len(keywords)
        matched_count = len(matched_keywords)

        coverage_percentage = (
            matched_count / total_keywords
        ) * 100

        # Preliminary documentation coverage score
        # Higher score means less keyword coverage.

        risk_score = round(
            100 - coverage_percentage
        )

        if risk_score >= 70:
            risk_level = "High"
        elif risk_score >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        matched_keywords_text = (
            ", ".join(sorted(matched_keywords))
            if matched_keywords
            else "No checklist keywords matched"
        )
                # Preliminary documentation risk scoring
        
        results.append({
            "Governance Area": category,
            "Description": details["description"],
            "Reference": details["source"],
            "Status": status,
            "Total Keywords": total_keywords,
            "Matched Keywords Count": matched_count,
            "Matched Keywords": matched_keywords_text,
            "Coverage (%)": round(coverage_percentage, 2),
            "Risk Score": risk_score,
            "Risk Level": risk_level,
            "Evidence": evidence_text
        })

    return results


def generate_pdf_report(results, document_name):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    # --------------------------------------------------
    # REPORT TITLE
    # --------------------------------------------------

    story.append(
        Paragraph(
            "GovernAI Assessment Report",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Document: " + escape(str(document_name)),
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Corporate Governance Assessment "
            "and Documentation Risk Analysis",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 12))

    # --------------------------------------------------
    # SUMMARY METRICS
    # --------------------------------------------------

    total_areas = len(results)

    high_risk = sum(
        result.get("Risk Level", "") == "High"
        for result in results
    )

    medium_risk = sum(
        result.get("Risk Level", "") == "Medium"
        for result in results
    )

    low_risk = sum(
        result.get("Risk Level", "") == "Low"
        for result in results
    )

    summary_data = [
        ["Metric", "Value"],
        ["Checklist Areas Assessed", str(total_areas)],
        ["High Documentation Risk", str(high_risk)],
        ["Medium Documentation Risk", str(medium_risk)],
        ["Low Documentation Risk", str(low_risk)]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[280, 150],
        repeatRows=1
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.darkblue
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            )
        ])
    )

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # --------------------------------------------------
    # DETAILED FINDINGS
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Detailed Governance Findings",
            styles["Heading1"]
        )
    )

    story.append(Spacer(1, 10))

    for result in results:

        # Governance area heading
        story.append(
            Paragraph(
                escape(str(
                    result.get("Governance Area", "N/A")
                )),
                styles["Heading2"]
            )
        )

        # Description
        story.append(
            Paragraph(
                "<b>Description:</b> "
                + escape(str(
                    result.get("Description", "N/A")
                )),
                styles["BodyText"]
            )
        )

        # Automated assessment status
        story.append(
            Paragraph(
                "<b>Automated Status:</b> "
                + escape(str(
                    result.get("Status", "N/A")
                )),
                styles["BodyText"]
            )
        )

        # Human reviewer status
        story.append(
            Paragraph(
                "<b>Reviewer Status:</b> "
                + escape(str(
                    result.get(
                        "Reviewer Status",
                        "Pending Review"
                    ) or "Pending Review"
                )),
                styles["BodyText"]
            )
        )

        # Human reviewer comments
        # IMPORTANT: This belongs inside the loop.
        story.append(
            Paragraph(
                "<b>Reviewer Comments:</b> "
                + escape(str(
                    result.get(
                        "Reviewer Comments", ""
                    ) or "No comments entered"
                )),
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 5))

        # Risk level
        story.append(
            Paragraph(
                "<b>Documentation Risk Level:</b> "
                + escape(str(
                    result.get("Risk Level", "N/A")
                )),
                styles["BodyText"]
            )
        )

        # Risk score
        story.append(
            Paragraph(
                "<b>Risk Score:</b> "
                + escape(str(
                    result.get("Risk Score", "N/A")
                )),
                styles["BodyText"]
            )
        )

        # Keyword coverage
        story.append(
            Paragraph(
                "<b>Keyword Coverage:</b> "
                + escape(str(
                    result.get("Coverage (%)", "N/A")
                ))
                + "%",
                styles["BodyText"]
            )
        )

        # Matched keywords
        story.append(
            Paragraph(
                "<b>Matched Keywords:</b> "
                + escape(str(
                    result.get(
                        "Matched Keywords", "None"
                    )
                )),
                styles["BodyText"]
            )
        )

        # Reference
        story.append(
            Paragraph(
                "<b>Reference:</b> "
                + escape(str(
                    result.get("Reference", "N/A")
                )),
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 6))

        # Supporting evidence
        story.append(
            Paragraph(
                "<b>Supporting Evidence:</b>",
                styles["BodyText"]
            )
        )

        evidence = str(
            result.get(
                "Evidence",
                "No matching evidence identified."
            )
        )

        evidence = escape(evidence).replace(
            "\n",
            "<br/>"
        )

        story.append(
            Paragraph(
                evidence,
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 18))

    # --------------------------------------------------
    # DISCLAIMER
    # IMPORTANT: Outside the results loop.
    # --------------------------------------------------

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Important Disclaimer",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            "This report is generated using a prototype "
            "keyword-based documentation assessment system. "
            "Risk scores represent checklist keyword coverage "
            "only. Matching text does not establish that a "
            "governance control is implemented or effective. "
            "Missing matching text does not establish "
            "non-compliance. Findings require human review "
            "and are not legal or regulatory certification.",
            styles["BodyText"]
        )
    )

    # --------------------------------------------------
    # GENERATE PDF
    # --------------------------------------------------

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()




# PDF upload
uploaded_file = st.file_uploader(
    "Upload a corporate governance PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    document_bytes = uploaded_file.getvalue()

    document_hash = hashlib.sha256(
            document_bytes
        ).hexdigest()

    document_name = uploaded_file.name

    
    pdf_bytes = uploaded_file.getvalue()

    reader = PdfReader(BytesIO(pdf_bytes))

    extracted_text = ""
    page_texts = []
    pages_without_text = 0

    # First, try extracting text directly
    for page_number, page in enumerate(
        reader.pages, start=1
    ):
        page_text = page.extract_text() or ""

        if not page_text.strip():
            pages_without_text += 1

        page_texts.append({
            "page": page_number,
            "text": page_text
        })

        extracted_text += f"\n{page_text}"

    # Run OCR if pages have no extractable text
    if pages_without_text > 0:

        st.info(
            "Some pages have no extractable text. "
            "Attempting OCR on the PDF..."
        )

        try:
            images = convert_from_bytes(
                pdf_bytes,
                dpi=200,
                poppler_path=POPPLER_PATH
            )

            for index, image in enumerate(images):

                ocr_text = pytesseract.image_to_string(
                    image,
                    lang="eng"
                )

                # Replace text for pages that had no text
                if index < len(page_texts):

                    if not page_texts[index]["text"].strip():

                        page_texts[index]["text"] = ocr_text

            # Rebuild extracted text from all pages
            extracted_text = "\n".join(
                page["text"]
                for page in page_texts
            )

            st.success("OCR processing completed.")

        except Exception as e:

            st.error(
                "OCR could not run. Check that "
                "Tesseract and Poppler are installed "
                "and their paths are correct."
            )

            st.exception(e)

    st.write("Number of pages:", len(reader.pages))

    st.success("PDF uploaded.")

    st.write("Number of pages:", len(reader.pages))

    if pages_without_text > 0:
        st.warning(
            f"{pages_without_text} page(s) have no "
            "extractable text. They may be scanned "
            "or image-based pages."
        )

    if not extracted_text.strip():
        st.error(
            "No text could be extracted. "
            "OCR is required for scanned documents."
        )

    st.success("PDF uploaded and text extracted.")

    st.write("Number of pages:", len(reader.pages))

    with st.expander("View extracted document text"):
        st.text_area(

            "Extracted text",
                extracted_text,
                height=250,
                key="extracted_text_display"        )

    # Run governance assessment
    if extracted_text.strip():

        st.header("Governance Assessment")

        results = assess_governance(page_texts)

        df = pd.DataFrame(results)

        # DASHBOARD METRICS

        st.subheader("Governance Assessment Dashboard")

        total_areas = len(results)

        matched_areas = sum(
            result["Status"] == "Manual review required"
            for result in results
        )

        no_evidence_areas = sum(
            result["Status"] == "No evidence found"
            for result in results
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Checklist Areas",
            total_areas
        )

        col2.metric(
            "Matching Text Found",
            matched_areas
        )

        col3.metric(
            "No Matching Text",
            no_evidence_areas
        )

        st.caption(
            "Matching text requires manual verification. "
            "No matching text does not prove that a control is absent."
        )

        # STATUS CHART

        st.subheader("Assessment Status Overview")

        status_counts = pd.DataFrame({
            "Status": [
                "Manual review required",
                "No evidence found"
            ],
            "Count": [
                matched_areas,
                no_evidence_areas
            ]
        })

        st.bar_chart(
            status_counts.set_index("Status")
        )

                # RISK LEVEL CHART
        st.subheader("How Risk Scores Are Calculated")

        st.write(
                "Coverage (%) = matched unique checklist keywords "
                "/ total checklist keywords × 100"
            )

        st.write(
                "Documentation Risk Score = 100 − Coverage (%)"
            )

        st.info(
                "These are prototype keyword-coverage indicators. "
                "A keyword match does not prove that a control exists "
                "or operates effectively. A missing keyword does not "
                "prove non-compliance.")

        st.subheader("Documentation Risk Overview")

        risk_counts = (
            df["Risk Level"]
            .value_counts()
            .reindex(
                ["High", "Medium", "Low"],
                fill_value=0
            )
        )

        risk_chart_df = risk_counts.rename(
            "Number of Areas"
        ).to_frame()

        st.bar_chart(risk_chart_df)

        st.caption(
            "Risk levels are preliminary documentation "
            "coverage indicators based on prototype rules. "
            "They are not legal compliance ratings."
        )

        # ASSESSMENT SUMMARY

        st.subheader("Assessment Summary")

        st.dataframe(
            df[
                [
                    "Governance Area",
                    "Status",
                    "Risk Score",
                    "Risk Level",
                    "Reference"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # CATEGORY FILTER

        st.subheader("Detailed Assessment Results")

        categories = ["All"] + df[
            "Governance Area"
        ].tolist()

        selected_category = st.selectbox(
            "Filter by governance category",
            categories
        )

        if selected_category == "All":
            filtered_df = df
        else:
            filtered_df = df[
                df["Governance Area"] == selected_category
            ]
        st.dataframe(
            filtered_df[
                [

            "Governance Area",
            "Description",
            "Reference",
            "Status",
            "Matched Keywords",
            "Coverage (%)",
            "Risk Score",
            "Risk Level"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )



                # HUMAN REVIEW WORKFLOW

        st.subheader("Human Review Workflow")

        st.write(
            "Review the evidence identified by GovernAI "
            "and record a reviewer decision for each area."
        )

        for area in df["Governance Area"]:

            if area not in st.session_state["review_status"]:
                st.session_state["review_status"][area] = (
                    "Pending Review"
                )

            selected_status = st.selectbox(
                f"Review status: {area}",
                REVIEW_OPTIONS,
                index=REVIEW_OPTIONS.index(
                    st.session_state["review_status"][area]
                ),
                key=f"review_{area}"
            )

            st.session_state["review_status"][area] = (
                selected_status
            )


            # REVIEW HISTORY

            st.subheader("Saved Review History")

            history = get_review_history(document_hash)

            if history:
                history_df = pd.DataFrame(
                    history,
                    columns=[
                        "Governance Area",
                        "Reviewer Status",
                        "Reviewer Comments",
                        "Reviewed At"
                    ]
                )

                st.dataframe(
                    history_df,
                    use_container_width=True
                )
            else:
                st.info("No saved reviews found.")

                        # Reviewer comments
            if "review_comments" not in st.session_state:
                st.session_state["review_comments"] = {}

            review_comment = st.text_area(
                f"Reviewer comments: {area}",
                value=st.session_state["review_comments"].get(
                    area, ""
                ),
                placeholder="Enter evidence checked, reason, or follow-up action...",
                key=f"comment_{area}"
            )

            st.session_state["review_comments"][area] = (
                review_comment
            )

            save_review(

                 document_hash,
                    document_name,
                    area,
                    selected_status,
                    review_comment
                )

            automated_status = df.loc[
                df["Governance Area"] == area,
                "Status"
            ].iloc[0]

            st.write(
                f"Automated finding: {automated_status}"
            )


        
        # EVIDENCE DETAILS

        st.subheader("Evidence Details")

        for _, result in filtered_df.iterrows():

            with st.expander(
                result["Governance Area"]
                + " — "
                + result["Status"]
            ):

                st.write(
                    "Assessment:",
                    result["Description"]
                )

                st.write(
                    "Reference:",
                    result["Reference"]
                )

                st.write("Evidence:")

                st.write(result["Evidence"])


        
        # DOWNLOAD REPORT

        st.subheader("Export Assessment Report")

        export_df = filtered_df.copy()

        # Add human reviewer status
        export_df["Reviewer Status"] = (
            export_df["Governance Area"].map(
                st.session_state["review_status"]
            ).fillna("Pending Review")
        )

        # Add reviewer comments
        review_comments = st.session_state.get(
            "review_comments", {}
        )

        export_df["Reviewer Comments"] = (
            export_df["Governance Area"].map(
                review_comments
            ).fillna("")
        )

        # CSV download
        csv_data = export_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download CSV Report",
            data=csv_data,
            file_name="GovernAI_Assessment.csv",
            mime="text/csv"
        )

        # PDF download
        try:

            pdf_data = generate_pdf_report(
                export_df.to_dict(orient="records"),
                uploaded_file.name
            )

            st.download_button(
                label="Download PDF Report",
                data=pdf_data,
                file_name="GovernAI_Assessment_Report.pdf",
                mime="application/pdf"
            )

        except Exception as e:

            st.error("Unable to generate PDF report.")

            st.exception(e)
        
# REVIEW HISTORY DASHBOARD

st.divider()

st.header("Review History Dashboard")

all_reviews = get_all_reviews()

if all_reviews:

    history_df = pd.DataFrame(
        all_reviews,
        columns=[
            "Document",
            "Document Hash",
            "Governance Area",
            "Reviewer Status",
            "Reviewer Comments",
            "Reviewed At"
        ]
    )

    # Summary metrics
    total_reviews = len(history_df)

    verified_count = (
        history_df["Reviewer Status"] == "Verified"
    ).sum()

    pending_count = (
        history_df["Reviewer Status"] == "Pending Review"
    ).sum()

    followup_count = (
        history_df["Reviewer Status"] == "Follow-up Required"
    ).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Reviews", total_reviews)
    col2.metric("Verified", int(verified_count))
    col3.metric("Pending", int(pending_count))
    col4.metric("Follow-up", int(followup_count))

    # Status filter
    selected_status = st.selectbox(
        "Filter by reviewer status",
        [
            "All",
            "Pending Review",
            "Verified",
            "Not Applicable",
            "Follow-up Required"
        ]
    )

    if selected_status != "All":

        filtered_history = history_df[
            history_df["Reviewer Status"]
            == selected_status
        ]

    else:
        filtered_history = history_df

    # Display review records
    st.subheader("Saved Reviews")

    st.dataframe(
        filtered_history.drop(
            columns=["Document Hash"]
        ),
        use_container_width=True,
        hide_index=True
    )

    # Document details
    document_list = history_df[
        "Document"
    ].unique().tolist()

    selected_document = st.selectbox(
        "View document review details",
        document_list
    )

    document_details = history_df[
        history_df["Document"] == selected_document
    ]

    st.subheader("Document Review Details")

    st.dataframe(
        document_details.drop(
            columns=["Document Hash"]
        ),
        use_container_width=True,
        hide_index=True
    )

else:
    st.info(
        "No saved reviews yet. Upload a PDF and "
        "record reviewer decisions to populate "
        "this dashboard."
    )