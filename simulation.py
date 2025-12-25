import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time

# ================= CONFIGURATION =================

load_dotenv()

# ZOHO Config
ZOHO_CLIENT_ID=os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET=os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN=os.getenv("ZOHO_REFRESH_TOKEN")
ZOHO_ACCOUNT_ID=os.getenv("ZOHO_ACCOUNT_ID")
ZOHO_FROM_EMAIL=os.getenv("ZOHO_FROM_EMAIL")

ZOHO_ACCOUNT_URL = "https://accounts.zoho.in"
ZOHO_MAIL_URL = "https://mail.zoho.in"

# Google Gemini Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# Simulation Config
MAX_RETRIES = 3
STATE_FILE = "simulation_state.json"
LOG_FILE = "simulation_log.txt"

# ================= STATE MANAGEMENT =================
class SimulationState:
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.load_state()
        
    def load_state(self):
        """Load Simulation state from idle"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                self.users = data.get('users', {})
        else:
            self.users = {}

    def save_state(self):
        """Save Simulation state to idle"""
        with open(STATE_FILE, 'w') as f:
            json.dump({'users': self.users}, f, indent=2)
            
    def get_user(self, email: str) -> Optional[Dict]:
        """Get user state"""
        return self.users.get(email)
    
    def add_user(self, email: str, message_id: str, thread_id: str):
        """Initialize new user in Simulation"""
        self.users[email] = {
            'email': email,
            'initial_message_id': message_id,
            'thread_id': thread_id,
            'retry_count': 0,
            "intent": None,
            "status": "initial_sent",
            "history": [],
            "created_at": datetime.now().isoformat()
        }
        self.save_state()
        
    def update_user(self, email: str, **kwargs):
        """Update User Stats"""
        if email in self.users:
            self.users[email].update(kwargs)
            self.save_state()
            
    def add_history(self, email: str, event: str, details: Dict):
        """Add event to user history"""
        if email in self.users:
            self.users[email]['history'].append({
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'details': details
            })
            self.save_state()
            
    def increment_retry(self, email: str):
        """Increment retry count"""
        if email in self.users:
            self.users[email]['retry_count'] += 1
            self.save_state()
            
# =============== LOGGING ==================

class SimulationLogger:
    @staticmethod
    def log(event_type: str, data: Dict):
        """Log Simulation Event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
                
        logs.append(log_entry)
        
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"[{event_type}] {data}")
        
# ======================= ZOHO MAIL API =======================