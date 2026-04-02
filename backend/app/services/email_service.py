"""
Email service for transactional notifications using SMTP.
"""

from __future__ import annotations

import logging
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from app.config import settings

logger = logging.getLogger(__name__)


def _format_resolution_email(issue: Dict[str, Any], reopen_link: str) -> Dict[str, str]:
    hall = issue.get("hall_name") or "Hall"
    room = issue.get("room_number") or "N/A"
    category = issue.get("category_name") or "General"
    subject = f"Issue resolved – {hall} • Room {room}"
    student_name = issue.get('student_name') or 'Student'
    
    html_body = f"""
    <p>Dear {student_name},</p>
    <p>Your hostel repair request for <strong>{hall}</strong> (room <strong>{room}</strong>, category: {category})
    has been marked as <strong>Done</strong>.</p>
    <p>If no work was actually carried out and the issue persists, please click this button to reopen the ticket within the next 72 hours.</p>
    <p style="margin:16px 0;">
      <a href="{reopen_link}" style="background:#2563EB;color:#fff;padding:10px 18px;
         border-radius:6px;text-decoration:none;display:inline-block;">
        Reopen complaint
      </a>
    </p>
    <p>Thank you</p>
    """

    text_body = (
        f"Dear {student_name},\n\n"
        f"Your repair request for {hall} (room {room}, category: {category}) was marked as done.\n"
        f"If no work was actually carried out and the issue persists, reopen it within 72 hours: {reopen_link}\n\n"
        "Thank you"
    )

    return {"subject": subject, "html": html_body, "text": text_body}


def send_issue_resolved_email(issue: Dict[str, Any], reopen_link: str) -> None:
    """
    Send a completion email to the student with a reopen CTA.
    """
    issue_id = issue.get("id")
    recipient = issue.get("student_email")
    
    if not recipient:
        logger.warning(
            "Issue %s has no student_email field; skipping resolution email notification",
            issue_id
        )
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP_USER or SMTP_PASSWORD not configured in environment; skipping resolution email for issue %s",
            issue_id
        )
        return

    logger.info(
        "Attempting to send resolution email for issue %s to %s",
        issue_id,
        recipient[:3] + "***" if len(recipient) > 3 else "***"
    )

    template = _format_resolution_email(issue, reopen_link)

    try:
        _send_with_smtp(recipient, template)
        logger.info(
            "Resolution email sent successfully for issue %s to %s",
            issue_id,
            recipient[:3] + "***" if len(recipient) > 3 else "***"
        )
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "SMTP authentication error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except smtplib.SMTPConnectError as exc:
        logger.error(
            "SMTP connection error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except smtplib.SMTPException as exc:
        logger.error(
            "SMTP error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except socket.error as exc:
        logger.error(
            "Network error sending resolution email for issue %s: %s",
            issue_id,
            str(exc)
        )
    except Exception as exc:
        logger.error(
            "Unexpected error sending resolution email for issue %s: %s",
            issue_id,
            exc,
            exc_info=True
        )


def send_password_reset_email(recipient_email: str, reset_token: str, username: str) -> None:
    """
    Send password reset link email.

    Uses a one-time token and a short expiry window.
    """
    if not recipient_email:
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured; skipping password reset email to %s",
            recipient_email[:3] + "***",
        )
        return

    reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={reset_token}"
    subject = "Reset your Hostel Repairs password"
    expiry_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRY_MINUTES

    html_body = f"""
    <p>Hello {username},</p>
    <p>We received a request to reset your password.</p>
    <p style=\"margin:16px 0;\">
      <a href=\"{reset_link}\" style=\"background:#2563EB;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;display:inline-block;\">
        Reset Password
      </a>
    </p>
    <p>This link expires in {expiry_minutes} minutes and can be used only once.</p>
    <p>If you did not request this, you can ignore this email.</p>
    """

    text_body = (
        f"Hello {username},\n\n"
        f"We received a request to reset your password.\n"
        f"Reset link: {reset_link}\n\n"
        f"This link expires in {expiry_minutes} minutes and can be used only once.\n"
        "If you did not request this, you can ignore this email."
    )

    try:
        _send_with_smtp(
            recipient_email,
            {"subject": subject, "html": html_body, "text": text_body},
        )
        logger.info("Password reset email sent to %s", recipient_email[:3] + "***")
    except Exception as exc:
        logger.error(
            "Failed to send password reset email to %s: %s",
            recipient_email[:3] + "***",
            exc,
        )


def _send_with_smtp(recipient: str, template: Dict[str, str]) -> None:
    """
    Send email using SMTP.
    
    Creates a multipart email with both HTML and plain text versions.
    Connects to the configured SMTP server, authenticates, and sends the email.
    
    Raises:
        smtplib.SMTPAuthenticationError: If authentication fails
        smtplib.SMTPConnectError: If connection to SMTP server fails
        smtplib.SMTPException: For other SMTP-related errors
        socket.error: For network errors
    """
    logger.debug(
        "Sending email via SMTP to %s using server %s:%s",
        recipient[:3] + "***" if len(recipient) > 3 else "***",
        settings.SMTP_HOST,
        settings.SMTP_PORT
    )
    
    # Create multipart message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = template["subject"]
    msg['From'] = f"{settings.SYSTEM_EMAIL_NAME} <{settings.SYSTEM_EMAIL_FROM}>"
    msg['To'] = recipient
    
    # Add both plain text and HTML parts
    text_part = MIMEText(template["text"], 'plain', 'utf-8')
    html_part = MIMEText(template["html"], 'html', 'utf-8')
    
    msg.attach(text_part)
    msg.attach(html_part)
    
    # Connect to SMTP server and send
    try:
        # Use SSL for port 465, regular SMTP for other ports
        if settings.SMTP_PORT == 465:
            # Port 465 uses SSL from the start
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            # Port 587 uses STARTTLS
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        
        with server:
            # Enable debug output in development (level 1 = connection info)
            if settings.DEBUG:
                server.set_debuglevel(1)
            
            # Start TLS if enabled and not using SSL (port 465)
            if settings.SMTP_USE_TLS and settings.SMTP_PORT != 465:
                server.starttls()
            
            # Authenticate
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            # Send email
            server.send_message(msg)
            
            logger.debug("Email sent successfully via SMTP to %s", recipient[:3] + "***" if len(recipient) > 3 else "***")
    
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed for user %s", settings.SMTP_USER[:3] + "***" if len(settings.SMTP_USER) > 3 else "***")
        raise
    except smtplib.SMTPConnectError as e:
        logger.error("Failed to connect to SMTP server %s:%s: %s", settings.SMTP_HOST, settings.SMTP_PORT, str(e))
        raise
    except smtplib.SMTPException as e:
        logger.error("SMTP error occurred: %s", str(e))
        raise


# ===== Sync Failure Alert =====


def _format_sync_failure_alert(
    consecutive_failures: int, latest_errors: list
) -> Dict[str, str]:
    """Format sync failure alert email template."""
    error_list = ""
    for err in latest_errors[:5]:  # Show at most 5 recent errors
        error_list += f"<li>{err}</li>\n"

    subject = f"⚠️ Sync failure alert — {consecutive_failures} consecutive failures"

    html_body = f"""
    <p>The Google Sheets sync has failed <strong>{consecutive_failures} times in a row</strong>.</p>
    <p>This means new student complaints are <strong>not being imported</strong> into the system.</p>
    <h3>Recent Errors</h3>
    <ul>{error_list if error_list else "<li>No error details available</li>"}</ul>
    <p>Please check the server logs and Google Sheets API credentials.</p>
    <p style="color:#666;font-size:12px;">This is an automated alert from the Hostel Repair Management System.</p>
    """

    text_body = (
        f"The Google Sheets sync has failed {consecutive_failures} times in a row.\n"
        f"New student complaints are NOT being imported into the system.\n\n"
        f"Recent errors:\n"
        + "\n".join(f"- {e}" for e in latest_errors[:5])
        + "\n\nPlease check the server logs and Google Sheets API credentials."
    )

    return {"subject": subject, "html": html_body, "text": text_body}


def send_sync_failure_alert(
    recipient_email: str, consecutive_failures: int, latest_errors: list
) -> None:
    """
    Send sync failure alert email to an admin user.

    Called by the scheduler when N consecutive syncs have failed.

    Args:
        recipient_email: Admin email to send alert to
        consecutive_failures: Number of consecutive failures
        latest_errors: Recent error messages from sync logs

    Returns:
        None (logs errors instead of raising)
    """
    if not recipient_email:
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured; skipping sync failure alert to %s",
            recipient_email[:3] + "***",
        )
        return

    logger.info(
        "Sending sync failure alert (%d failures) to %s",
        consecutive_failures,
        recipient_email[:3] + "***",
    )

    template = _format_sync_failure_alert(consecutive_failures, latest_errors)

    try:
        _send_with_smtp(recipient_email, template)
        logger.info("Sync failure alert sent to %s", recipient_email[:3] + "***")
    except Exception as exc:
        logger.error(
            "Failed to send sync failure alert to %s: %s",
            recipient_email[:3] + "***",
            exc,
        )


# ===== New Issue Digest =====


def _format_new_issues_digest(
    hall_name: str, new_count: int, issue_summaries: list
) -> Dict[str, str]:
    """Format new issues digest email template."""
    rows = ""
    for iss in issue_summaries[:20]:  # Cap at 20 items in email
        desc = (iss.get("description") or "No description")[:80]
        rows += (
            f"<tr>"
            f"<td style='padding:4px 8px;border-bottom:1px solid #eee;'>{iss.get('room', 'N/A')}</td>"
            f"<td style='padding:4px 8px;border-bottom:1px solid #eee;'>{iss.get('category', 'N/A')}</td>"
            f"<td style='padding:4px 8px;border-bottom:1px solid #eee;'>{desc}</td>"
            f"</tr>\n"
        )

    subject = f"🔔 {new_count} new issue(s) reported in {hall_name}"

    html_body = f"""
    <p>Hello,</p>
    <p><strong>{new_count} new repair request(s)</strong> have been reported in <strong>{hall_name}</strong>.</p>
    <table style="border-collapse:collapse;width:100%;font-size:14px;">
      <thead>
        <tr style="background:#f5f5f5;">
          <th style="padding:6px 8px;text-align:left;">Room</th>
          <th style="padding:6px 8px;text-align:left;">Category</th>
          <th style="padding:6px 8px;text-align:left;">Description</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <p>Please log in to the dashboard to review and assign these issues.</p>
    <p style="color:#666;font-size:12px;">This is an automated notification from the Hostel Repair Management System.</p>
    """

    text_lines = [f"{new_count} new issue(s) reported in {hall_name}:\n"]
    for iss in issue_summaries[:20]:
        desc = (iss.get("description") or "No description")[:80]
        text_lines.append(
            f"  Room {iss.get('room', 'N/A')} | {iss.get('category', 'N/A')} | {desc}"
        )
    text_lines.append("\nPlease log in to the dashboard to review these issues.")

    return {"subject": subject, "html": html_body, "text": "\n".join(text_lines)}


def send_new_issues_digest(
    recipient_email: str, hall_name: str, new_count: int, issue_summaries: list
) -> None:
    """
    Send new issues digest email to a hall admin.

    Called at the end of a sync run when new issues were created for a hall.

    Args:
        recipient_email: Hall admin email
        hall_name: Name of the hall
        new_count: Number of new issues
        issue_summaries: List of dicts with room, category, description

    Returns:
        None (logs errors instead of raising)
    """
    if not recipient_email:
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured; skipping digest for %s to %s",
            hall_name,
            recipient_email[:3] + "***",
        )
        return

    logger.info(
        "Sending new issues digest (%d issues in %s) to %s",
        new_count,
        hall_name,
        recipient_email[:3] + "***",
    )

    template = _format_new_issues_digest(hall_name, new_count, issue_summaries)

    try:
        _send_with_smtp(recipient_email, template)
        logger.info("Issues digest sent to %s", recipient_email[:3] + "***")
    except Exception as exc:
        logger.error(
            "Failed to send issues digest to %s: %s",
            recipient_email[:3] + "***",
            exc,
        )
