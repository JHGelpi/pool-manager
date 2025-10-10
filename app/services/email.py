import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


async def send_email(
    recipient: str,
    subject: str,
    body: str
):
    """Send an email using configured SMTP settings"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"⚠ Email not configured. Would send to {recipient}: {subject}")
        return
    
    message = MIMEMultipart()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_TLS,
        )
        print(f"✓ Email sent to {recipient}")
    except Exception as e:
        print(f"✗ Failed to send email to {recipient}: {e}")


def create_alert_email(low_inventory_items: list, due_tasks: list) -> str:
    """Create HTML email body for pool alerts"""
    html = "<html><body><h1>🏊 Pool Maintenance Alert</h1>"
    
    if low_inventory_items:
        html += "<h2>⚠️ Low Chemical Inventory</h2><ul>"
        for item in low_inventory_items:
            html += f"<li><strong>{item.name}:</strong> {item.quantity_on_hand} {item.unit} "
            html += f"(reorder at {item.reorder_threshold})</li>"
        html += "</ul>"
    
    if due_tasks:
        html += "<h2>📋 Tasks Due Soon</h2><ul>"
        for task in due_tasks:
            html += f"<li><strong>{task.name}:</strong> Due {task.next_due_date}</li>"
        html += "</ul>"
    
    if not low_inventory_items and not due_tasks:
        html += "<p>✓ All systems normal. No urgent actions required.</p>"
    
    html += "</body></html>"
    return html