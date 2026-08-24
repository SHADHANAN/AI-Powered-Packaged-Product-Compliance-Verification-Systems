import io
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.models.enums import AuditAction, ComplianceStatus, Severity
from app.models.verification import Verification
from app.schemas.report import ComplianceReportData
from app.services import audit_service, report_service
from app.utils.exceptions import NotFoundException
from app.utils.logging import get_logger

logger = get_logger("app.services.pdf_report")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page counts and footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 805, "Legal Metrology Packaged Product Compliance Verification Report")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 800, 559, 800)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 45, 559, 45)

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 32, page_str)
        self.drawString(36, 32, "CONFIDENTIAL & STATUTORY AUDIT DOCUMENT - FOR OFFICIAL USE ONLY")
        self.restoreState()


def _get_status_style(status_val: ComplianceStatus) -> tuple:
    """Return text color, background color, and badge text label for compliance status."""
    if status_val == ComplianceStatus.PASS:
        return colors.HexColor("#166534"), colors.HexColor("#DCFCE7"), "[ PASS ]"
    elif status_val == ComplianceStatus.FAIL:
        return colors.HexColor("#991B1B"), colors.HexColor("#FEE2E2"), "[ FAIL ]"
    elif status_val == ComplianceStatus.WARNING:
        return colors.HexColor("#9A3412"), colors.HexColor("#FFEDD5"), "[ WARN ]"
    else:
        return colors.HexColor("#374151"), colors.HexColor("#F3F4F6"), "[ N/A ]"


def generate_compliance_pdf(
    db: Session,
    verification_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> io.BytesIO:
    """Generate a publication-grade PDF compliance report for an evaluated verification."""
    verification = db.get(Verification, verification_id)
    if not verification:
        raise NotFoundException(f"Verification with id '{verification_id}' not found")

    # Fetch structured report data (raises NotFoundException if not generated yet)
    report_data: ComplianceReportData = report_service.get_latest_compliance_report(db, verification_id)

    # Fetch audit logs for audit summary section
    audit_logs = audit_service.get_verification_audit_logs(db, verification_id)

    buffer = io.BytesIO()

    # Document Template: A4 size, 36pt (0.5 inch) margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=48,
        bottomMargin=54,
    )

    # Typography & Styles
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=0,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "TableBody",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )

    body_bold = ParagraphStyle(
        "TableBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=base_styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#64748B"),
    )

    story = []

    # ------------------------------------------------------------------
    # A. REPORT HEADER
    # ------------------------------------------------------------------
    header_data = [
        [
            Paragraph("PACKAGED PRODUCT<br/>COMPLIANCE VERIFICATION REPORT", title_style),
            Paragraph(
                f"<b>Report ID:</b> {str(report_data.report_id or 'N/A')[:8]}...<br/>"
                f"<b>Verification ID:</b> {str(report_data.verification_id)[:8]}...<br/>"
                f"<b>Generated:</b> {report_data.generated_at.strftime('%Y-%m-%d %H:%M UTC')}<br/>"
                f"<b>Status:</b> {report_data.verification_status.value.upper()}",
                subtitle_style,
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[330, 193])
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

    # ------------------------------------------------------------------
    # B & C. PRODUCT & INSPECTOR INFORMATION (Side-by-Side)
    # ------------------------------------------------------------------
    prod = report_data.product
    insp = report_data.inspector

    prod_details = (
        f"<b>Product Name:</b> {prod.product_name or 'N/A' if prod else 'N/A'}<br/>"
        f"<b>Brand:</b> {prod.brand_name or 'N/A' if prod else 'N/A'}<br/>"
        f"<b>Manufacturer:</b> {prod.manufacturer or 'N/A' if prod else 'N/A'}<br/>"
        f"<b>Importer:</b> {prod.importer or 'N/A' if prod else 'N/A'}<br/>"
        f"<b>Origin:</b> {prod.country_of_origin or 'N/A' if prod else 'N/A'}"
    )

    insp_details = (
        f"<b>Inspector:</b> {insp.name if insp else 'System Automated'}<br/>"
        f"<b>Email:</b> {insp.email if insp else 'system@metrology.internal'}<br/>"
        f"<b>Role:</b> {insp.role.value.capitalize() if insp else 'Inspector'}<br/>"
        f"<b>User ID:</b> {str(insp.id)[:8] + '...' if insp else 'N/A'}"
    )

    info_data = [
        [
            Paragraph("<b>PRODUCT INFORMATION</b>", table_header_style),
            Paragraph("<b>INSPECTOR INFORMATION</b>", table_header_style),
        ],
        [
            Paragraph(prod_details, body_style),
            Paragraph(insp_details, body_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[260, 263])
    info_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # E. COMPLIANCE SUMMARY METRICS
    # ------------------------------------------------------------------
    score_val = report_data.overall_score if report_data.overall_score is not None else 0.0
    summary_data = [
        [
            Paragraph("<b>Overall Score</b>", table_header_style),
            Paragraph("<b>Evaluated Rules</b>", table_header_style),
            Paragraph("<b>Passed</b>", table_header_style),
            Paragraph("<b>Failed</b>", table_header_style),
            Paragraph("<b>Warning</b>", table_header_style),
            Paragraph("<b>Not Applicable</b>", table_header_style),
        ],
        [
            Paragraph(f"<b><font size=12 color='#0F172A'>{score_val:.1f}%</font></b>", body_style),
            Paragraph(str(report_data.summary.total_rules), body_style),
            Paragraph(f"<font color='#15803D'><b>{report_data.summary.passed_rules}</b></font>", body_style),
            Paragraph(f"<font color='#B91C1C'><b>{report_data.summary.failed_rules}</b></font>", body_style),
            Paragraph(f"<font color='#B45309'><b>{report_data.summary.warning_rules}</b></font>", body_style),
            Paragraph(str(report_data.summary.not_applicable_rules), body_style),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[90, 90, 85, 85, 85, 88])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(Paragraph("Compliance Summary", section_heading))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # D. EXTRACTED LABEL INFORMATION TABLE
    # ------------------------------------------------------------------
    story.append(Paragraph("Extracted Product Label Information", section_heading))
    if report_data.extracted_fields:
        fields_rows = [
            [
                Paragraph("<b>Field Name</b>", table_header_style),
                Paragraph("<b>Extracted Value</b>", table_header_style),
                Paragraph("<b>Confidence</b>", table_header_style),
                Paragraph("<b>Source Text</b>", table_header_style),
            ]
        ]
        for f in report_data.extracted_fields:
            conf_str = f"{int(f.confidence * 100)}%" if f.confidence is not None else "N/A"
            fields_rows.append([
                Paragraph(f.field_name.replace("_", " ").title(), body_bold),
                Paragraph(f.field_value or "<i>[Empty]</i>", body_style),
                Paragraph(conf_str, body_style),
                Paragraph(f.source_text or "—", body_style),
            ])
        fields_table = Table(fields_rows, colWidths=[120, 170, 65, 168], repeatRows=1)
        fields_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(fields_table)
    else:
        story.append(Paragraph("<i>No label fields extracted.</i>", body_style))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # F. RULE-BY-RULE RESULTS TABLE
    # ------------------------------------------------------------------
    story.append(Paragraph("Legal Metrology Compliance Rule Checks", section_heading))
    if report_data.checks:
        checks_rows = [
            [
                Paragraph("<b>Rule Code</b>", table_header_style),
                Paragraph("<b>Rule Name</b>", table_header_style),
                Paragraph("<b>Severity</b>", table_header_style),
                Paragraph("<b>Status</b>", table_header_style),
                Paragraph("<b>Actual / Detected</b>", table_header_style),
                Paragraph("<b>Expected Requirement</b>", table_header_style),
            ]
        ]
        for c in report_data.checks:
            _, _, badge_label = _get_status_style(c.status)
            checks_rows.append([
                Paragraph(c.rule_code, body_bold),
                Paragraph(c.rule_name, body_style),
                Paragraph(c.severity.value.upper(), body_style),
                Paragraph(f"<b>{badge_label}</b>", body_style),
                Paragraph(c.actual_value or "—", body_style),
                Paragraph(c.expected_value or "—", body_style),
            ])
        checks_table = Table(checks_rows, colWidths=[75, 128, 55, 65, 100, 100], repeatRows=1)
        checks_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(checks_table)
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # G. VIOLATIONS & NON-CONFORMITIES
    # ------------------------------------------------------------------
    story.append(Paragraph("Detected Non-Conformities & Violations", section_heading))
    if report_data.violations:
        viol_rows = [
            [
                Paragraph("<b>Rule</b>", table_header_style),
                Paragraph("<b>Severity</b>", table_header_style),
                Paragraph("<b>Non-Conformity Message</b>", table_header_style),
                Paragraph("<b>Actionable Recommendation</b>", table_header_style),
            ]
        ]
        for v in report_data.violations:
            viol_rows.append([
                Paragraph(f"<b>{v.rule_code}</b><br/>{v.rule_name}", body_style),
                Paragraph(f"<font color='#B91C1C'><b>{v.severity.value.upper()}</b></font>", body_style),
                Paragraph(f"<b>Detected:</b> {v.detected_value or 'Missing'}<br/><b>Required:</b> {v.expected_requirement or 'N/A'}", body_style),
                Paragraph(v.recommendation or "Review commodity label according to Legal Metrology Packaged Commodities Rules.", body_style),
            ])
        viol_table = Table(viol_rows, colWidths=[110, 60, 175, 178], repeatRows=1)
        viol_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FECACA")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(viol_table)
    else:
        story.append(Paragraph("<b>No compliance violations detected. Product meets all evaluated Legal Metrology rules.</b>", body_style))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # H. RECOMMENDATIONS
    # ------------------------------------------------------------------
    story.append(Paragraph("Corrective Action Recommendations", section_heading))
    if report_data.recommendations:
        for idx, rec in enumerate(report_data.recommendations, start=1):
            story.append(Paragraph(f"<b>{idx}.</b> {rec}", body_style))
            story.append(Spacer(1, 2))
    else:
        story.append(Paragraph("No corrective recommendations.", body_style))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------------
    # I. AUDIT TRAIL SUMMARY
    # ------------------------------------------------------------------
    story.append(Paragraph("Verification Audit Trail History", section_heading))
    if audit_logs:
        audit_rows = [
            [
                Paragraph("<b>Action</b>", table_header_style),
                Paragraph("<b>Timestamp (UTC)</b>", table_header_style),
                Paragraph("<b>Status</b>", table_header_style),
                Paragraph("<b>Details / Summary</b>", table_header_style),
            ]
        ]
        for a in audit_logs:
            audit_rows.append([
                Paragraph(a.action.value.replace("_", " ").title(), body_bold),
                Paragraph(a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "N/A", body_style),
                Paragraph(a.status, body_style),
                Paragraph(a.details or "—", body_style),
            ])
        audit_table = Table(audit_rows, colWidths=[130, 110, 65, 218], repeatRows=1)
        audit_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(audit_table)
    else:
        story.append(Paragraph("<i>No audit log records available.</i>", body_style))
    story.append(Spacer(1, 12))

    # ------------------------------------------------------------------
    # J. STATUTORY DISCLAIMER
    # ------------------------------------------------------------------
    disclaimer_text = (
        "<b>STATUTORY DISCLAIMER:</b> This report is an automated compliance verification aid "
        "based on extracted product-label information and configured Legal Metrology rules. "
        "It does not constitute legal advice or a final statutory determination. Human and legal review "
        "by an authorized Legal Metrology Officer may be required."
    )
    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=6),
        Paragraph(disclaimer_text, disclaimer_style),
    ]))

    try:
        # Build document into buffer
        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)

        # Record audit log event for PDF export
        audit_service.create_audit_log(
            db=db,
            verification_id=verification_id,
            user_id=user_id or verification.inspector_id,
            action=AuditAction.REPORT_PDF_EXPORTED,
            status="SUCCESS",
            details="Exported compliance report as PDF",
        )

        logger.info(f"Generated compliance PDF for verification '{verification_id}' ({buffer.getbuffer().nbytes} bytes)")
        return buffer

    except Exception as exc:
        logger.error(f"Failed to generate compliance PDF for verification '{verification_id}': {exc}", exc_info=True)
        raise
