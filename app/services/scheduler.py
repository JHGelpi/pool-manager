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