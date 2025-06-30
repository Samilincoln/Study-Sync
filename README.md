# Study-Sync

StudySync - WhatsApp AI Agent for Tutoring Reminders

Smart WhatsApp bot that helps parents never miss their children's tutoring classes. Features automated reminders, custom timing, multi-child support, and an intuitive web dashboard.

FastAPI backend • Streamlit frontend • WhatsApp integration • Smart scheduling

A complete backend and frontend solution for managing tutoring class reminders via WhatsApp.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend
```bash
# Save the FastAPI code as main.py
python main.py
# Or using uvicorn directly:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`
API Documentation (Swagger UI): `http://localhost:8000/docs`

### 3. Start the Streamlit Frontend
```bash
# In a new terminal, save the Streamlit code as app.py
streamlit run app.py
```

The web interface will open at: `http://localhost:8501`

## 📋 Features

### FastAPI Backend
- **Parent Management**: Register parents with phone numbers
- **Class Scheduling**: Create, update, delete tutoring classes  
- **Automatic Reminders**: Scheduled WhatsApp notifications
- **Custom Timing**: Set reminder minutes (5-120 minutes before class)
- **WhatsApp Webhook**: Handle incoming messages
- **Real-time Scheduling**: Uses APScheduler for reminder jobs

### Streamlit Frontend
- **User-Friendly Interface**: Easy parent registration and class management
- **Dashboard**: View today's classes and system status
- **Manual Reminders**: Send instant reminders for any class
- **Message History**: Track sent WhatsApp messages
- **Real-time Updates**: Auto-refresh capabilities

## 🔧 API Endpoints

### Parents
- `POST /parents/` - Register new parent
- `GET /parents/{phone}` - Get parent info

### Classes  
- `POST /classes/` - Create new class
- `GET /classes/` - Get all classes
- `GET /classes/parent/{phone}` - Get parent's classes
- `PUT /classes/{class_id}` - Update class
- `DELETE /classes/{class_id}` - Delete class

### Reminders
- `POST /reminders/send/{class_id}` - Send manual reminder
- `GET /messages/{phone}` - Get message history

### System
- `GET /health` - Health check
- `POST /webhook/whatsapp` - WhatsApp webhook

## 💬 WhatsApp Integration

### Webhook Messages
The system accepts WhatsApp webhook messages in this format:
```json
{
  "phone": "+1234567890",
  "text": "classes"
}
```

### Bot Commands
Parents can text these commands:
- `classes` - View all scheduled classes
- `today` - See today's classes  
- `help` - Show available commands

## 🔔 Reminder System

### Automatic Scheduling
- Reminders are automatically scheduled when classes are created
- Uses cron jobs to send recurring weekly reminders
- Customizable timing (5-120 minutes before class)

### Message Format
```
🔔 Class Reminder!

📚 Subject: Math
👶 Student: Emma  
⏰ Time: 4:00 PM
📅 Today: Monday

Don't forget! Class starts in 30 minutes.
```

## 🏗️ Production Setup

### Database Integration
Replace in-memory storage with a real database:
```python
# Example with SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/tutoring_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### WhatsApp API Integration
Integrate with WhatsApp Business API:
```python
import requests

async def send_whatsapp_message(phone: str, message: str):
    whatsapp_api_url = "https://graph.facebook.com/v17.0/YOUR_PHONE_ID/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone,
        "text": {"body": message}
    }
    response = requests.post(whatsapp_api_url, headers=headers, json=data)
    return response
```

### Environment Variables
```bash
export WHATSAPP_TOKEN="your_whatsapp_token"
export DATABASE_URL="your_database_connection_string"
export API_BASE_URL="https://your-api-domain.com"
```

## 📱 Usage Examples

### 1. Register Parent
```python
import requests

parent_data = {
    "phone": "+1234567890",
    "name": "John Doe",
    "children": ["Emma", "Jake"],
    "timezone": "UTC"
}

response = requests.post("http://localhost:8000/parents/", json=parent_data)
```

### 2. Schedule Class
```python
class_data = {
    "parent_phone": "+1234567890",
    "child_name": "Emma",
    "subject": "Math",
    "day_of_week": "Monday",
    "class_time": "16:00",
    "reminder_minutes": 30,
    "is_active": True
}

response = requests.post("http://localhost:8000/classes/", json=class_data)
```

### 3. Send Manual Reminder
```python
reminder_data = {"class_id": "class_uuid_here"}
response = requests.post(
    "http://localhost:8000/reminders/send/class_uuid_here", 
    json=reminder_data
)
```

##  Customization In View

### Adding New Features
- **SMS Support**: Add Twilio integration alongside WhatsApp
- **Email Reminders**: Send backup email notifications  
- **Calendar Integration**: Sync with Google Calendar
- **Payment Tracking**: Add tutoring session payment management
- **Reports**: Generate attendance and scheduling reports

### Scaling
- Use Redis for caching and session management
- Implement database connection pooling
- Add rate limiting for API endpoints
- Use message queues (Celery/Redis) for reminder processing
- Deploy with Docker and Kubernetes

## 🔒 Security Notes

- Add authentication and authorization
- Validate phone numbers and input data
- Use HTTPS in production
- Implement rate limiting
- Secure WhatsApp webhook endpoints
- Add logging and monitoring

## 📞 Support

For WhatsApp Business API setup and webhook configuration, refer to:
- [WhatsApp Business Platform Documentation](https://developers.facebook.com/docs/whatsapp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

Happy coding! 🎉