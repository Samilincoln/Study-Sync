from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WhatsApp Tutoring Reminder API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Scheduler for reminders
scheduler = AsyncIOScheduler()

# Pydantic models
class TutoringClass(BaseModel):
    id: Optional[str] = None
    parent_phone: str
    child_name: str
    subject: str
    day_of_week: str  # Monday, Tuesday, etc.
    class_time: str   # "14:30" format
    reminder_minutes: int = 30  # Minutes before class
    is_active: bool = True
    created_at: Optional[datetime] = None

class Parent(BaseModel):
    phone: str
    name: str
    children: List[str] = []
    timezone: str = "UTC"

class ReminderRequest(BaseModel):
    class_id: str
    custom_message: Optional[str] = None

class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    message_type: str = "text"

# In-memory storage (use database in production)
parents_db = {}
classes_db = {}
messages_db = []

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler stopped")

# WhatsApp webhook simulation
async def send_whatsapp_message(phone: str, message: str):
    """Simulate sending WhatsApp message"""
    whatsapp_msg = WhatsAppMessage(phone=phone, message=message)
    messages_db.append({
        "id": str(uuid.uuid4()),
        "phone": phone,
        "message": message,
        "timestamp": datetime.now(),
        "status": "sent"
    })
    logger.info(f"WhatsApp message sent to {phone}: {message}")
    return whatsapp_msg

# Reminder function
async def send_class_reminder(class_id: str):
    """Send reminder for a specific class"""
    if class_id not in classes_db:
        logger.error(f"Class {class_id} not found")
        return
    
    tutoring_class = classes_db[class_id]
    if not tutoring_class["is_active"]:
        return
    
    message = f"""
🔔 Class Reminder!

📚 Subject: {tutoring_class['subject']}
👶 Student: {tutoring_class['child_name']}
⏰ Time: {tutoring_class['class_time']}
📅 Today: {tutoring_class['day_of_week']}

Don't forget! Class starts in {tutoring_class['reminder_minutes']} minutes.
"""
    
    await send_whatsapp_message(tutoring_class["parent_phone"], message.strip())

# API Routes
@app.get("/")
async def root():
    return {"message": "WhatsApp Tutoring Reminder API"}

@app.post("/parents/", response_model=dict)
async def create_parent(parent: Parent):
    """Register a new parent"""
    if parent.phone in parents_db:
        raise HTTPException(status_code=400, detail="Parent already exists")
    
    parents_db[parent.phone] = parent.dict()
    return {"message": "Parent registered successfully", "phone": parent.phone}

@app.get("/parents/{phone}")
async def get_parent(phone: str):
    """Get parent information"""
    if phone not in parents_db:
        raise HTTPException(status_code=404, detail="Parent not found")
    return parents_db[phone]

@app.post("/classes/", response_model=dict)
async def create_class(tutoring_class: TutoringClass):
    """Create a new tutoring class"""
    class_id = str(uuid.uuid4())
    tutoring_class.id = class_id
    tutoring_class.created_at = datetime.now()
    
    classes_db[class_id] = tutoring_class.dict()
    
    # Schedule reminder
    await schedule_reminder(class_id, tutoring_class)
    
    return {"message": "Class created successfully", "class_id": class_id}

@app.get("/classes/", response_model=List[dict])
async def get_all_classes():
    """Get all tutoring classes"""
    return list(classes_db.values())

@app.get("/classes/parent/{phone}")
async def get_parent_classes(phone: str):
    """Get all classes for a specific parent"""
    parent_classes = [
        class_data for class_data in classes_db.values()
        if class_data["parent_phone"] == phone
    ]
    return parent_classes

@app.put("/classes/{class_id}")
async def update_class(class_id: str, updated_class: TutoringClass):
    """Update a tutoring class"""
    if class_id not in classes_db:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Remove old reminder
    try:
        scheduler.remove_job(f"reminder_{class_id}")
    except:
        pass
    
    # Update class
    updated_class.id = class_id
    classes_db[class_id] = updated_class.dict()
    
    # Schedule new reminder
    await schedule_reminder(class_id, updated_class)
    
    return {"message": "Class updated successfully"}

@app.delete("/classes/{class_id}")
async def delete_class(class_id: str):
    """Delete a tutoring class"""
    if class_id not in classes_db:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Remove reminder
    try:
        scheduler.remove_job(f"reminder_{class_id}")
    except:
        pass
    
    del classes_db[class_id]
    return {"message": "Class deleted successfully"}

@app.post("/reminders/send/{class_id}")
async def send_manual_reminder(class_id: str, request: ReminderRequest):
    """Send a manual reminder for a class"""
    if class_id not in classes_db:
        raise HTTPException(status_code=404, detail="Class not found")
    
    await send_class_reminder(class_id)
    return {"message": "Reminder sent successfully"}

@app.get("/messages/{phone}")
async def get_messages(phone: str):
    """Get all messages sent to a phone number"""
    phone_messages = [
        msg for msg in messages_db
        if msg["phone"] == phone
    ]
    return phone_messages

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(message: dict):
    """Handle incoming WhatsApp messages"""
    phone = message.get("phone")
    text = message.get("text", "").lower()
    
    response_message = "I'm your tutoring reminder assistant! Commands:\n"
    response_message += "• 'classes' - View your classes\n"
    response_message += "• 'today' - Today's classes\n"
    response_message += "• 'help' - Show commands"
    
    if "classes" in text:
        parent_classes = [
            class_data for class_data in classes_db.values()
            if class_data["parent_phone"] == phone
        ]
        if parent_classes:
            response_message = "Your scheduled classes:\n\n"
            for cls in parent_classes:
                response_message += f"📚 {cls['subject']} - {cls['child_name']}\n"
                response_message += f"📅 {cls['day_of_week']} at {cls['class_time']}\n"
                response_message += f"🔔 Reminder: {cls['reminder_minutes']} min before\n\n"
        else:
            response_message = "No classes scheduled yet."
    
    elif "today" in text:
        today = datetime.now().strftime("%A")
        today_classes = [
            cls for cls in classes_db.values()
            if cls["parent_phone"] == phone and cls["day_of_week"] == today
        ]
        if today_classes:
            response_message = f"Today's classes ({today}):\n\n"
            for cls in today_classes:
                response_message += f"📚 {cls['subject']} - {cls['child_name']}\n"
                response_message += f"⏰ {cls['class_time']}\n\n"
        else:
            response_message = f"No classes scheduled for today ({today})."
    
    await send_whatsapp_message(phone, response_message)
    return {"status": "processed"}

async def schedule_reminder(class_id: str, tutoring_class: TutoringClass):
    """Schedule a recurring reminder for a class"""
    day_mapping = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    
    if tutoring_class.day_of_week not in day_mapping:
        logger.error(f"Invalid day: {tutoring_class.day_of_week}")
        return
    
    # Parse class time
    try:
        hour, minute = map(int, tutoring_class.class_time.split(":"))
    except:
        logger.error(f"Invalid time format: {tutoring_class.class_time}")
        return
    
    # Calculate reminder time
    reminder_time = datetime.now().replace(
        hour=hour, minute=minute, second=0, microsecond=0
    ) - timedelta(minutes=tutoring_class.reminder_minutes)
    
    # Create cron trigger
    trigger = CronTrigger(
        day_of_week=day_mapping[tutoring_class.day_of_week],
        hour=reminder_time.hour,
        minute=reminder_time.minute
    )
    
    # Schedule the job
    scheduler.add_job(
        send_class_reminder,
        trigger=trigger,
        args=[class_id],
        id=f"reminder_{class_id}",
        replace_existing=True
    )
    
    logger.info(f"Scheduled reminder for class {class_id}")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "total_parents": len(parents_db),
        "total_classes": len(classes_db),
        "scheduled_jobs": len(scheduler.get_jobs())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)