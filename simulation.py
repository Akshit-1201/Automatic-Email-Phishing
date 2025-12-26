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

class ZohoMailAPI:
    def __init__(self):
        self.access_token = None
    
    def refresh_access_token(self) -> str:
        """Get fresh access token using refresh token"""
        url = f"{ZOHO_ACCOUNT_URL}/oauth/v2/token"
        data = {
            "refresh_token": ZOHO_REFRESH_TOKEN,
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token"
        }

        r = requests.post(url, data=data, timeout=10)
        r.raise_for_status()
        self.access_token = r.json()["access_token"]
        return self.access_token
    
    def send_email(self, to_email: str, subject: str, body: str, in_reply_to: Optional[str] = None) -> Dict:
        """Send Email via Zoho Mail API"""
        if not self.access_token:
            self.refresh_access_token()

        url = f"{ZOHO_MAIL_URL}/api/accounts/{ZOHO_ACCOUNT_ID}/messages"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "fromAddress": ZOHO_FROM_EMAIL,
            "toAddress": to_email,
            "subject": subject,
            "content": body,
            "mailFormat": "html"
        }

        # Add Threading support fro replies
        if in_reply_to:
            payload["inReplyTo"] = in_reply_to

        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        return r.json()
    
    def get_unread_emails(self) -> List[Dict]:
        """Fetch inread Emails"""
        if not self.access_token:
            self.refresh_access_token()

        url = f"{ZOHO_MAIL_URL}/api/accounts/{ZOHO_ACCOUNT_ID}/messages/view"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}"
        }
        params = {
            "status": "unread",
            "limit": 50
        }

        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r,json().get("data", [])
    
    def mark_as_read(self, message_id: str):
        """Mark Email as read"""
        if not self.access_token:
            self.refresh_access_token()

        url = f"{ZOHO_MAIL_URL}/api/accounts/{ZOHO_ACCOUNT_ID}/messages/{message_id}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}"
        }
        data = {
            "status": "read"
        }

        r = requests.put(url, headers=headers, json=data, timeout=10)
        r.raise_for_status()


# ================ GEMINI INTENT CLASSIFIER ======================
class IntentClassifier:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL

    def classify_intent(self, email_content: str) -> str:
        """Classify user intent using Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"""
                    You are analyzing a response to a phishing simulation email for educational purposes.
                    Email Response: {email_content}
                    
                    Classify the user's intent/emotional state into ONE of these categories:
                        - "worried_curious": User seems concerned, asking questions, wants more information
                        - "unbothered_dismissive": User seems unconcerned, brief response, or ignoring the urgency
                    Respond with ONLY the category name, nothing else. Do not include any explanation.
                """
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                        "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 200,
                "topP": 0.95,
                "topK": 40
            }
        }

        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()

        response = r.json()

        # Extract text from gemini response
        intent = response['candidates'][0]['content']['parts'][0]['text'].strip().lower()

        # Normalize to expected Values
        if 'worried' in intent or 'curious' in intent:
            return 'worried_curious'
        else:
            return 'unbothered_dismissive'
        

# =================== EMAIL TEMPLATES =======================
class EmailTemplates:
    @staticmethod
    def initial_email() -> tuple:
        """Initial phishing simulation email"""
        subject = "Important: Account Security Verification Required"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear User,</p>
            
            <p>Our security team has detected unusual activity on your account from an unrecognized device.</p>
            
            <p>As part of our routine security measures, we need to verify your account information to ensure your data remains protected.</p>
            
            <p><strong>Please reply to this email</strong> if you would like more information about this security alert.</p>
            
            <p>Thank you for your cooperation in keeping your account secure.</p>
            
            <p>Best regards,<br>
            Security Team</p>
        </body>
        </html>
        """
        return subject, body
    
    @staticmethod
    def reminder_email(retry_count: int) -> tuple:
        """Reminder email for non-responders"""
        subject = f"REMINDER {retry_count}: Action Required - Account Security"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear User,</p>
            
            <p><strong style="color: red;">This is reminder #{retry_count}</strong></p>
            
            <p>We still haven't received your response regarding the unusual activity detected on your account.</p>
            
            <p>Your account security is at risk. Please reply immediately to verify your account status.</p>
            
            <p>Failure to respond may result in temporary account suspension.</p>
            
            <p>Best regards,<br>
            Security Team</p>
        </body>
        </html>
        """
        return subject, body
    
    @staticmethod
    def worried_followup() -> tuple:
        """Follow-up for worried/curious users"""
        subject = "Re: Account Security Verification - Next Steps"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Thank you for your prompt response.</p>
            
            <p>To complete the verification process, we need you to confirm the following:</p>
            
            <ul>
                <li>Your last login location</li>
                <li>Recent transaction history</li>
                <li>Current contact information</li>
            </ul>
            
            <p>Please reply with "VERIFIED" if this information is correct, or contact us immediately if you notice any discrepancies.</p>
            
            <p><strong>Time-sensitive:</strong> Please respond within 24 hours to avoid account restrictions.</p>
            
            <p>Best regards,<br>
            Security Team</p>
        </body>
        </html>
        """
        return subject, body
    
    @staticmethod
    def dismissive_followup() -> tuple:
        """Follow-up for unbothered/dismissive users"""
        subject = "URGENT: Your Account Will Be Suspended"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p><strong style="color: red; font-size: 16px;">FINAL WARNING</strong></p>
            
            <p>Due to lack of response, your account is scheduled for suspension in <strong>12 hours</strong>.</p>
            
            <p>This is a mandatory security protocol. We have detected:</p>
            
            <ul style="color: red;">
                <li>3 unauthorized login attempts</li>
                <li>Suspicious transactions pending</li>
                <li>Outdated security credentials</li>
            </ul>
            
            <p><strong>IMMEDIATE ACTION REQUIRED:</strong> Reply with your verification code to prevent account lockout.</p>
            
            <p>This is your last opportunity to secure your account.</p>
            
            <p>Security Team</p>
        </body>
        </html>
        """
        return subject, body
    
# ======================= SIMULATION ENGINE =====================
