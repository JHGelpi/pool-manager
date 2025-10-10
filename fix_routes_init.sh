#!/bin/bash
set -e

echo "📝 Creating app/api/routes/__init__.py..."

cat > app/api/routes/__init__.py << 'EOF'
from app.api.routes.health import router as health_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.readings import router as readings_router

__all__ = [
    "health_router",
    "inventory_router",
    "tasks_router",
    "alerts_router",
    "readings_router",
]
EOF

echo "✅ app/api/routes/__init__.py created!"

# Also check if app/services/__init__.py exists
if [ ! -f app/services/__init__.py ]; then
    echo "Creating app/services/__init__.py..."
    touch app/services/__init__.py
fi

# Check if service files exist, create if missing
if [ ! -s app/services/email.py ]; then
    echo "Creating app/services/email.py..."
    cat > app/services/email.py << 'EOF'
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
EOF
fi

if [ ! -s app/services/scheduler.py ]; then
    echo "Creating app/services/scheduler.py..."
    cat > app/services/scheduler.py << 'EOF'
from datetime import datetime, timezone, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Alert, ChemicalInventory, MaintenanceTask, User
from app.services.email import send_email, create_alert_email


async def check_alerts():
    """Check all alerts and send emails if conditions are met"""
    print(f"⏰ Running alert check at {datetime.now()}")
    
    async with AsyncSessionLocal() as db:
        # Get all alerts
        result = await db.execute(select(Alert))
        alerts = result.scalars().all()
        
        for alert in alerts:
            # Get user for email
            user_result = await db.execute(
                select(User).where(User.id == alert.user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                continue
            
            now = datetime.now(timezone.utc)
            should_send = False
            
            # Check if it's time to send based on cadence
            if alert.cadence == "daily":
                if not alert.last_sent or alert.last_sent.date() < now.date():
                    should_send = True
            
            elif alert.cadence == "weekly":
                weekday = now.isoweekday() % 7  # Convert to 0=Sunday
                if weekday in alert.days_of_week:
                    if not alert.last_sent or alert.last_sent.date() < now.date():
                        should_send = True
            
            if should_send:
                # Check inventory
                low_inventory = []
                if alert.alert_on_low_inventory:
                    inv_result = await db.execute(
                        select(ChemicalInventory)
                        .where(ChemicalInventory.user_id == alert.user_id)
                    )
                    for item in inv_result.scalars():
                        if item.quantity_on_hand <= item.reorder_threshold:
                            low_inventory.append(item)
                
                # Check tasks
                due_tasks = []
                if alert.alert_on_due_tasks:
                    today = date.today()
                    tasks_result = await db.execute(
                        select(MaintenanceTask)
                        .where(MaintenanceTask.user_id == alert.user_id)
                        .where(MaintenanceTask.next_due_date <= today)
                    )
                    due_tasks = tasks_result.scalars().all()
                
                # Send email if there's something to report
                if low_inventory or due_tasks:
                    email_body = create_alert_email(low_inventory, due_tasks)
                    await send_email(
                        recipient=user.email,
                        subject=f"Pool Alert: {alert.name}",
                        body=email_body
                    )
                    
                    # Update last_sent
                    alert.last_sent = now
                    await db.commit()
                else:
                    print(f"  No items to report for alert '{alert.name}'")


# Create scheduler
scheduler = AsyncIOScheduler()

# Run alert check every 5 minutes
scheduler.add_job(check_alerts, 'interval', minutes=5, id='check_alerts')
EOF
fi

echo "✅ All missing files created!"
echo ""
echo "Now restart the API:"
echo "  docker-compose restart api"
echo "  docker-compose logs -f api"

