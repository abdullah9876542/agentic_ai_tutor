"""
services/notification_service.py — Email Notification Service (Phase 8)

Sends a comprehensive student performance report to the registered email.
Uses Python's built-in smtplib — no third-party email library needed.

Supports: Gmail (default), Outlook, Yahoo, any SMTP provider.
Gmail requires an App Password — see .env.example for setup instructions.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SMTP_HOST    = os.getenv("SMTP_HOST",      "smtp.gmail.com")
SMTP_PORT    = int(os.getenv("SMTP_PORT",  "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER",   "")
EMAIL_PASS   = os.getenv("EMAIL_PASSWORD", "")
FROM_NAME    = os.getenv("EMAIL_FROM_NAME","AI Tutor System")


# ─────────────────────────────────────────────────────────────────
# HTML Email Template
# ─────────────────────────────────────────────────────────────────

def _build_email_html(report: Dict[str, Any]) -> str:
    """Build the full HTML email body from the report dict."""

    student_name    = report.get("student_name", "Student")
    perf_level      = report.get("performance_level", "N/A")
    summary         = report.get("summary", "")
    weak_subjects   = report.get("weak_subjects", [])
    avg_subjects    = report.get("average_subjects", [])
    strong_subjects = report.get("strong_subjects", [])
    subject_grades  = report.get("subject_grades", [])
    quiz_history    = report.get("quiz_history", [])
    tutor_sessions  = report.get("tutor_sessions", 0)
    total_quizzes   = report.get("total_quizzes", 0)
    avg_quiz_score  = report.get("avg_quiz_score", 0)
    recommendations = report.get("study_recommendations", {})
    top_career      = report.get("top_career", "")
    immediate_actions = report.get("immediate_actions", [])
    motivational_note = report.get("motivational_note", "")
    generated_at    = datetime.now().strftime("%d %B %Y at %I:%M %p")

    perf_color = {
        "Excellent": "#22c55e", "Good": "#84cc16", "Average": "#f59e0b",
        "Needs Improvement": "#f97316", "Critical": "#ef4444"
    }.get(perf_level, "#6366f1")

    # ── Subject grades table rows ─────────────────────────────────
    grade_rows = ""
    for g in subject_grades:
        score     = g.get("score")
        max_score = g.get("max_score", 100)
        pct       = round((score / max_score) * 100, 1) if score is not None and max_score else None
        pct_str   = f"{pct}%" if pct is not None else "N/A"
        row_color = "#22c55e" if pct and pct >= 70 else ("#f59e0b" if pct and pct >= 50 else "#ef4444") if pct else "#94a3b8"
        grade_rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#e2e8f0;">{g.get('subject','')}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#e2e8f0;text-align:center;">{score if score is not None else 'N/A'} / {int(max_score) if max_score else 100}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;text-align:center;">
                <span style="color:{row_color};font-weight:700;">{pct_str}</span>
            </td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;text-align:center;">{g.get('grade','') or ''}</td>
        </tr>"""

    # ── Weak subjects list ────────────────────────────────────────
    weak_html = "".join(
        f'<li style="color:#fca5a5;margin:4px 0;">{s}</li>' for s in weak_subjects
    ) if weak_subjects else '<li style="color:#94a3b8;">None — great job!</li>'

    # ── Strong subjects list ──────────────────────────────────────
    strong_html = "".join(
        f'<li style="color:#86efac;margin:4px 0;">{s}</li>' for s in strong_subjects
    ) if strong_subjects else '<li style="color:#94a3b8;">Keep working — you\'ll get there!</li>'

    # ── Average subjects list ─────────────────────────────────────
    avg_html = "".join(
        f'<li style="color:#fde68a;margin:4px 0;">{s}</li>' for s in avg_subjects
    ) if avg_subjects else '<li style="color:#94a3b8;">None</li>'

    # ── Recommendations ───────────────────────────────────────────
    rec_html = ""
    for subject, rec in list(recommendations.items())[:5]:
        rec_html += f"""
        <div style="background:#1e293b;border-left:3px solid #6366f1;padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;">
            <div style="color:#f1f5f9;font-weight:700;margin-bottom:4px;">{subject}</div>
            <div style="color:#94a3b8;font-size:14px;">{rec}</div>
        </div>"""

    # ── Quiz history ──────────────────────────────────────────────
    quiz_rows = ""
    for q in quiz_history[:5]:
        pct = q.get("percentage", 0)
        q_color = "#22c55e" if pct >= 70 else ("#f59e0b" if pct >= 50 else "#ef4444")
        quiz_rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#e2e8f0;">{q.get('subject','')}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;text-align:center;color:{q_color};font-weight:700;">{q.get('score',0)}/{q.get('total',5)} ({pct}%)</td>
            <td style="padding:8px 12px;border-bottom:1px solid #334155;color:#94a3b8;text-align:center;">{q.get('attempted_at','')[:10]}</td>
        </tr>"""

    # ── Immediate actions ─────────────────────────────────────────
    actions_html = "".join(
        f'<li style="color:#e2e8f0;margin:6px 0;padding-left:4px;">{a}</li>'
        for a in immediate_actions[:3]
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Student Performance Report — {student_name}</title>
</head>
<body style="margin:0;padding:0;background:#0f172a;font-family:'Segoe UI',Arial,sans-serif;color:#e2e8f0;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;">
<tr><td align="center" style="padding:30px 20px;">

<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

    <!-- Header -->
    <tr><td style="background:linear-gradient(135deg,#1e293b,#0f172a);border-radius:12px 12px 0 0;padding:32px;border-bottom:3px solid {perf_color};">
        <table width="100%"><tr>
            <td>
                <div style="color:{perf_color};font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;">AI Tutor System</div>
                <div style="color:#f1f5f9;font-size:26px;font-weight:700;">Student Performance Report</div>
                <div style="color:#94a3b8;font-size:14px;margin-top:4px;">Generated on {generated_at}</div>
            </td>
            <td align="right">
                <div style="background:{perf_color};color:white;padding:10px 18px;border-radius:8px;font-weight:700;font-size:15px;white-space:nowrap;">{perf_level}</div>
            </td>
        </tr></table>
    </td></tr>

    <!-- Student info -->
    <tr><td style="background:#1e293b;padding:20px 32px;border-bottom:1px solid #334155;">
        <div style="color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Student</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700;">{student_name}</div>
    </td></tr>

    <!-- Summary -->
    <tr><td style="background:#162032;padding:24px 32px;border-bottom:1px solid #334155;">
        <div style="color:{perf_color};font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">📋 Overall Summary</div>
        <div style="color:#cbd5e1;font-size:15px;line-height:1.7;">{summary}</div>
    </td></tr>

    <!-- Stats row -->
    <tr><td style="background:#1e293b;padding:20px 32px;border-bottom:1px solid #334155;">
        <table width="100%"><tr>
            <td align="center" style="padding:10px;">
                <div style="color:#6366f1;font-size:24px;font-weight:700;">{total_quizzes}</div>
                <div style="color:#94a3b8;font-size:12px;">Quizzes Taken</div>
            </td>
            <td align="center" style="padding:10px;border-left:1px solid #334155;">
                <div style="color:#6366f1;font-size:24px;font-weight:700;">{avg_quiz_score}%</div>
                <div style="color:#94a3b8;font-size:12px;">Avg Quiz Score</div>
            </td>
            <td align="center" style="padding:10px;border-left:1px solid #334155;">
                <div style="color:#6366f1;font-size:24px;font-weight:700;">{tutor_sessions}</div>
                <div style="color:#94a3b8;font-size:12px;">Tutor Sessions</div>
            </td>
            <td align="center" style="padding:10px;border-left:1px solid #334155;">
                <div style="color:{perf_color};font-size:24px;font-weight:700;">{len(strong_subjects)}/{len(weak_subjects) + len(avg_subjects) + len(strong_subjects)}</div>
                <div style="color:#94a3b8;font-size:12px;">Strong Subjects</div>
            </td>
        </tr></table>
    </td></tr>

    <!-- Subject grades table -->
    <tr><td style="background:#162032;padding:24px 32px;border-bottom:1px solid #334155;">
        <div style="color:#f1f5f9;font-size:16px;font-weight:700;margin-bottom:14px;">📊 Subject-wise Performance</div>
        <table width="100%" style="border-collapse:collapse;border:1px solid #334155;border-radius:8px;overflow:hidden;">
            <tr style="background:#1e293b;">
                <th style="padding:10px 12px;text-align:left;color:#94a3b8;font-size:12px;text-transform:uppercase;">Subject</th>
                <th style="padding:10px 12px;text-align:center;color:#94a3b8;font-size:12px;text-transform:uppercase;">Score</th>
                <th style="padding:10px 12px;text-align:center;color:#94a3b8;font-size:12px;text-transform:uppercase;">Percentage</th>
                <th style="padding:10px 12px;text-align:center;color:#94a3b8;font-size:12px;text-transform:uppercase;">Grade</th>
            </tr>
            {grade_rows}
        </table>
    </td></tr>

    <!-- Weak / Average / Strong -->
    <tr><td style="background:#1e293b;padding:24px 32px;border-bottom:1px solid #334155;">
        <table width="100%"><tr>
            <td width="33%" style="vertical-align:top;padding-right:12px;">
                <div style="color:#ef4444;font-size:13px;font-weight:700;text-transform:uppercase;margin-bottom:8px;">🔴 Needs Improvement</div>
                <ul style="margin:0;padding-left:18px;">{weak_html}</ul>
            </td>
            <td width="33%" style="vertical-align:top;padding:0 6px;border-left:1px solid #334155;padding-left:12px;">
                <div style="color:#f59e0b;font-size:13px;font-weight:700;text-transform:uppercase;margin-bottom:8px;">🟡 Average</div>
                <ul style="margin:0;padding-left:18px;">{avg_html}</ul>
            </td>
            <td width="33%" style="vertical-align:top;padding-left:12px;border-left:1px solid #334155;">
                <div style="color:#22c55e;font-size:13px;font-weight:700;text-transform:uppercase;margin-bottom:8px;">🟢 Strong</div>
                <ul style="margin:0;padding-left:18px;">{strong_html}</ul>
            </td>
        </tr></table>
    </td></tr>

    <!-- Study recommendations -->
    {"" if not rec_html else f'''
    <tr><td style="background:#162032;padding:24px 32px;border-bottom:1px solid #334155;">
        <div style="color:#f1f5f9;font-size:16px;font-weight:700;margin-bottom:14px;">📚 Study Recommendations</div>
        {rec_html}
    </td></tr>
    '''}

    <!-- Quiz history -->
    {"" if not quiz_rows else f'''
    <tr><td style="background:#1e293b;padding:24px 32px;border-bottom:1px solid #334155;">
        <div style="color:#f1f5f9;font-size:16px;font-weight:700;margin-bottom:14px;">🎯 Recent Quiz Results</div>
        <table width="100%" style="border-collapse:collapse;border:1px solid #334155;">
            <tr style="background:#162032;">
                <th style="padding:8px 12px;text-align:left;color:#94a3b8;font-size:12px;text-transform:uppercase;">Subject</th>
                <th style="padding:8px 12px;text-align:center;color:#94a3b8;font-size:12px;text-transform:uppercase;">Score</th>
                <th style="padding:8px 12px;text-align:center;color:#94a3b8;font-size:12px;text-transform:uppercase;">Date</th>
            </tr>
            {quiz_rows}
        </table>
    </td></tr>
    '''}

    <!-- Career + Actions -->
    <tr><td style="background:#162032;padding:24px 32px;border-bottom:1px solid #334155;">
        <table width="100%"><tr>
            <td width="48%" style="vertical-align:top;padding-right:12px;">
                <div style="color:#f1f5f9;font-size:15px;font-weight:700;margin-bottom:10px;">🧭 Recommended Career Path</div>
                <div style="background:#1e3a5f;border:1px solid #1e40af;padding:12px 16px;border-radius:8px;color:#93c5fd;font-weight:600;">{top_career or 'Run Career Analysis to see recommendations'}</div>
            </td>
            <td width="4%"></td>
            <td width="48%" style="vertical-align:top;">
                <div style="color:#f1f5f9;font-size:15px;font-weight:700;margin-bottom:10px;">⚡ Immediate Actions</div>
                <ul style="margin:0;padding-left:18px;">{actions_html or '<li style="color:#94a3b8;">Run Career Analysis to get action items</li>'}</ul>
            </td>
        </tr></table>
    </td></tr>

    <!-- Motivational note -->
    {"" if not motivational_note else f'''
    <tr><td style="background:#14532d;padding:20px 32px;border-bottom:1px solid #166534;">
        <div style="color:#86efac;font-size:14px;font-style:italic;text-align:center;">
            💬 "{motivational_note}"
        </div>
    </td></tr>
    '''}

    <!-- Footer -->
    <tr><td style="background:#0f172a;padding:20px 32px;border-radius:0 0 12px 12px;text-align:center;">
        <div style="color:#475569;font-size:12px;">
            This report was generated automatically by the AI Tutor System.<br>
            For questions or support, log in to the AI Tutor platform.
        </div>
    </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def _build_plain_text(report: Dict[str, Any]) -> str:
    """Plain text fallback for email clients that don't render HTML."""
    student_name   = report.get("student_name", "Student")
    perf_level     = report.get("performance_level", "N/A")
    summary        = report.get("summary", "")
    weak_subjects  = report.get("weak_subjects", [])
    strong_subjects= report.get("strong_subjects", [])
    total_quizzes  = report.get("total_quizzes", 0)
    avg_quiz_score = report.get("avg_quiz_score", 0)
    top_career     = report.get("top_career", "")
    generated_at   = datetime.now().strftime("%d %B %Y at %I:%M %p")

    weak_list   = "\n".join(f"  - {s}" for s in weak_subjects) or "  None"
    strong_list = "\n".join(f"  - {s}" for s in strong_subjects) or "  None"

    return f"""
AI TUTOR SYSTEM — STUDENT PERFORMANCE REPORT
Generated: {generated_at}
{'='*50}

Student:     {student_name}
Performance: {perf_level}

SUMMARY
{summary}

PERFORMANCE BREAKDOWN
Quizzes Taken:     {total_quizzes}
Avg Quiz Score:    {avg_quiz_score}%
Recommended Career: {top_career or 'Run Career Analysis to see'}

SUBJECTS NEEDING IMPROVEMENT
{weak_list}

STRONG SUBJECTS
{strong_list}

---
This report was generated automatically by the AI Tutor System.
"""


# ─────────────────────────────────────────────────────────────────
# Send email function
# ─────────────────────────────────────────────────────────────────

def send_report_email(to_email: str, student_name: str, report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a performance report email.

    Args:
        to_email:     Recipient email (student's registered email)
        student_name: Student's display name
        report:       Full report dict from build_report()

    Returns:
        {"success": True} or {"success": False, "error": "message"}
    """
    if not EMAIL_SENDER or not EMAIL_PASS:
        return {
            "success": False,
            "error":   (
                "Email not configured. Add EMAIL_SENDER and EMAIL_PASSWORD "
                "to your .env file. See .env.example for setup instructions."
            ),
        }

    if not to_email:
        return {"success": False, "error": "No recipient email address."}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 Performance Report — {student_name} | AI Tutor"
        msg["From"]    = f"{FROM_NAME} <{EMAIL_SENDER}>"
        msg["To"]      = to_email

        # Attach plain text fallback first, then HTML
        plain = _build_plain_text(report)
        html  = _build_email_html(report)

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html,  "html",  "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())

        logger.info(f"[email] Report sent to {to_email} for {student_name}")
        return {"success": True}

    except smtplib.SMTPAuthenticationError:
        logger.error("[email] Authentication failed")
        return {
            "success": False,
            "error": (
                "Email authentication failed. "
                "Check your EMAIL_SENDER and EMAIL_PASSWORD in .env. "
                "Gmail users: use an App Password, not your regular password."
            ),
        }
    except smtplib.SMTPException as e:
        logger.error(f"[email] SMTP error: {e}")
        return {"success": False, "error": f"Email sending failed: {str(e)}"}
    except Exception as e:
        logger.error(f"[email] Unexpected error: {e}", exc_info=True)
        return {"success": False, "error": f"Could not send email: {str(e)}"}
