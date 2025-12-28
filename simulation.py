import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time
import re
from html import unescape

# ================= CONFIGURATION =================

load_dotenv()

# ZOHO Config
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ZOHO_ACCOUNT_ID = os.getenv("ZOHO_ACCOUNT_ID")
ZOHO_FROM_EMAIL = os.getenv("ZOHO_FROM_EMAIL")

ZOHO_ACCOUNT_URL = "https://accounts.zoho.in"
ZOHO_MAIL_URL = "https://mail.zoho.in"

# Google Gemini Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

# Simulation Config
MAX_RETRIES = 3
STATE_FILE = "simulation_state.json"
LOG_FILE = "simulation_log.json"
DEBUG_MODE = False  # Set to True for detailed debugging

# Google Form URL for verification
GOOGLE_FORM_URL = os.getenv("GOOGLE_FORM_URL")

# ================= HELPER FUNCTIONS =================

def print_info(message: str):
    """Print info message"""
    print(f"ℹ️ {message}")

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")

def print_debug(message: str):
    """Print debug message only if DEBUG_MODE is True"""
    if DEBUG_MODE:
        print(f"🔍 [DEBUG] {message}")

def strip_html(html_content: str) -> str:
    """Strip HTML tags and clean text content"""
    if not html_content:
        return ""
    
    # Unescape HTML entities
    text = unescape(html_content)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove email signatures and quoted text
    text = re.split(r'On.*wrote:|From:|Sent:|To:|Subject:', text)[0]
    
    return text.strip()

# ================= STATE MANAGEMENT =================
class SimulationState:
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.load_state()
        
    def load_state(self):
        """Load Simulation state from file"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                self.users = data.get('users', {})
        else:
            self.users = {}

    def save_state(self):
        """Save Simulation state to file"""
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
    def log(event_type: str, data: Dict, console_output: bool = False):
        """Log Simulation Event to file only"""
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
        
        if console_output or DEBUG_MODE:
            print(f"[LOG] {event_type}: {data}")
        
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

        try:
            r = requests.post(url, data=data, timeout=10)
            r.raise_for_status()
            self.access_token = r.json()["access_token"]
            print_debug(f"Access token refreshed successfully")
            return self.access_token
        except Exception as e:
            print_error(f"Failed to refresh access token: {e}")
            raise
    
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

        if in_reply_to:
            payload["inReplyTo"] = in_reply_to

        try:
            print_debug(f"Sending email to {to_email}")
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            print_error(f"HTTP Error sending email: {e}")
            print_debug(f"Response: {r.text}")
            raise
        except Exception as e:
            print_error(f"Unexpected error sending email: {e}")
            raise
    
    def get_unread_emails(self) -> List[Dict]:
        """Fetch unread Emails"""
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

        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception as e:
            print_error(f"Failed to fetch unread emails: {e}")
            raise
    
    def get_message_content(self, message_id: str) -> str:
        """Fetch full message content by message ID"""
        if not self.access_token:
            self.refresh_access_token()

        url = f"{ZOHO_MAIL_URL}/api/accounts/{ZOHO_ACCOUNT_ID}/messages/{message_id}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}"
        }

        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json().get("data", {})
            
            # Try to get plain text first, then HTML
            content = data.get('textContent', '')
            if not content or not content.strip():
                content = data.get('content', '')
            if not content or not content.strip():
                content = data.get('summary', '')
            
            # Strip HTML if present
            if '<' in content and '>' in content:
                content = strip_html(content)
            
            return content.strip()
        except Exception as e:
            print_error(f"Failed to fetch message content: {e}")
            return ""
    
    def mark_as_read(self, message_id: str):
        """Mark Email as read"""
        if not self.access_token:
            self.refresh_access_token()

        url = f"{ZOHO_MAIL_URL}/api/accounts/{ZOHO_ACCOUNT_ID}/messages/{message_id}/status"
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "status": "READ"
        }

        try:
            r = requests.put(url, headers=headers, json=data, timeout=10)
            r.raise_for_status()
            print_debug(f"Marked message {message_id} as read")
        except requests.exceptions.HTTPError as e:
            print_debug(f"Could not mark message as read (non-critical)")


# ================ GEMINI INTENT CLASSIFIER ======================
class IntentClassifier:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        
    def classify_intent(self, email_content: str, max_retries: int = 3) -> str:
        """Classify user intent using Google Gemini API with retry logic"""
        # Validate and clean input
        if not email_content or not email_content.strip():
            raise ValueError("Email content is empty - cannot classify intent")
        
        # Strip HTML if present
        if '<' in email_content and '>' in email_content:
            email_content = strip_html(email_content)
        
        # Final check after cleaning
        if not email_content or not email_content.strip():
            raise ValueError("Email content is empty after HTML stripping")
        
        print_debug(f"Email content to classify: {email_content[:300]}")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"""You are a cybersecurity expert analyzing email responses to phishing simulations.

Your task: Classify the user's emotional state based on their email response.

USER'S EMAIL:
"{email_content}"

CATEGORIES:

1. worried_curious
   - User shows CONCERN, WORRY, or asks QUESTIONS
   - Wants MORE DETAILS or VERIFICATION
   - Keywords: "what", "why", "how", "concerned", "worried", "details", "??", "didn't"
   
2. unbothered_dismissive  
   - Brief response (1-3 words) with NO questions
   - Shows NO concern
   - Keywords: "ok", "thanks", "noted", "fine"

EXAMPLES:
worried_curious: "What is happening?? I didn't do anything!"
unbothered_dismissive: "Ok thanks"

Output ONLY: worried_curious OR unbothered_dismissive"""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 500,
                "topP": 1.0,
                "topK": 1
            }
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                print_debug(f"Attempt {attempt + 1}/{max_retries}")
                
                r = requests.post(url, headers=headers, json=payload, timeout=30)
                r.raise_for_status()
                response = r.json()
                
                print_debug(f"API Response: {json.dumps(response, indent=2)}")
                
                if 'candidates' not in response or not response['candidates']:
                    raise ValueError("No candidates in API response")
                
                candidate = response['candidates'][0]
                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                
                if finish_reason == 'MAX_TOKENS':
                    raise ValueError("Response truncated")
                elif finish_reason == 'SAFETY':
                    raise ValueError("Content blocked by safety filters")
                
                if 'content' not in candidate:
                    raise ValueError(f"No content (reason: {finish_reason})")
                
                if 'parts' not in candidate['content'] or not candidate['content']['parts']:
                    raise ValueError("Empty response parts")
                
                intent = candidate['content']['parts'][0]['text'].strip().lower()
                intent = re.sub(r'[^a-z_]', '', intent)  # Keep only letters and underscore
                
                print_debug(f"Cleaned intent: '{intent}'")

                if 'worried' in intent or 'curious' in intent:
                    print_info(f"✓ Classified as: worried_curious")
                    return 'worried_curious'
                elif 'unbothered' in intent or 'dismissive' in intent:
                    print_info(f"✓ Classified as: unbothered_dismissive")
                    return 'unbothered_dismissive'
                else:
                    last_error = f"Invalid: '{intent}'"
                    print_warning(f"{last_error} - Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        raise ValueError(f"Invalid classification after {max_retries} attempts: '{intent}'")
                    
            except requests.exceptions.HTTPError as e:
                last_error = f"API Error: {e}"
                print_error(last_error)
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise
            except ValueError as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    print_warning(f"{last_error} - Retrying...")
                    time.sleep(1)
                    continue
                print_error(f"Failed after {max_retries} attempts")
                raise
            except Exception as e:
                last_error = f"Unexpected: {e}"
                print_error(last_error)
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise
        
        raise ValueError(f"Classification failed: {last_error}")
            
# =================== EMAIL TEMPLATES =======================
class EmailTemplates:
    @staticmethod
    def initial_email() -> tuple:
        """Initial phishing simulation email"""
        subject = "Important: Account Security Verification Required"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #1a73e8; margin-top: 0;">🔒 Security Alert</h2>
                
                <p>Dear User,</p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⚠️ Unusual Activity Detected</strong></p>
                    <p style="margin: 5px 0 0 0;">Our security team has detected unusual activity on your account from an unrecognized device.</p>
                </div>
                
                <p>As part of our routine security measures, we need to verify your account information to ensure your data remains protected.</p>
                
                <div style="background-color: #ffffff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px;"><strong>📍 Detection Details:</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Unrecognized login attempt</li>
                        <li>Unusual location access</li>
                        <li>Time: Within last 24 hours</li>
                    </ul>
                </div>
                
                <p><strong>Please reply to this email</strong> if you would like more information about this security alert or if you did not authorize this activity.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="background-color: #e8f5e9; color: #2e7d32; padding: 12px; border-radius: 5px; font-size: 14px;">
                        🛡️ Your account security is our top priority
                    </p>
                </div>
                
                <p style="font-size: 13px; color: #999; border-top: 1px solid #ddd; padding-top: 15px; margin-top: 30px;">
                    This is an automated security notification. If you believe this was sent in error, please contact support immediately.
                </p>
                
                <p style="margin-top: 20px;">
                    Thank you for your cooperation in keeping your account secure.<br><br>
                    Best regards,<br>
                    <strong>Security Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        return subject, body
    
    @staticmethod
    def reminder_email(retry_count: int) -> tuple:
        """Reminder email for non-responders"""
        urgency_colors = {
            1: {"bg": "#fff3cd", "border": "#ffc107", "text": "#856404"},
            2: {"bg": "#ffe5e5", "border": "#ff9800", "text": "#c62828"},
            3: {"bg": "#ffcdd2", "border": "#d32f2f", "text": "#b71c1c"}
        }
        
        colors = urgency_colors.get(retry_count, urgency_colors[3])
        
        subject = f"{'🔴 ' * retry_count}REMINDER {retry_count}: Action Required - Account Security"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #d32f2f; margin-top: 0;">⚠️ URGENT: Security Verification Overdue</h2>
                
                <div style="background-color: {colors['bg']}; padding: 20px; border-left: 5px solid {colors['border']}; margin: 20px 0;">
                    <p style="margin: 0; color: {colors['text']}; font-size: 16px; font-weight: bold;">
                        🔔 This is reminder #{retry_count} of {MAX_RETRIES}
                    </p>
                </div>
                
                <p>Dear User,</p>
                
                <p><strong>We still haven't received your response</strong> regarding the unusual activity detected on your account.</p>
                
                <div style="background-color: #ffffff; padding: 15px; border: 2px solid #d32f2f; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #d32f2f; font-weight: bold;">⏰ TIME-SENSITIVE ALERT</p>
                    <p style="margin: 10px 0 0 0;">Your account security is at risk. Failure to respond may result in:</p>
                    <ul style="margin: 10px 0; padding-left: 20px; color: #d32f2f;">
                        <li>Temporary account suspension</li>
                        <li>Limited access to services</li>
                        <li>Additional verification requirements</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <p style="font-size: 18px; font-weight: bold; color: #d32f2f; margin: 0;">
                        {"⚠️ " * retry_count}IMMEDIATE ACTION REQUIRED{"⚠️ " * retry_count}
                    </p>
                </div>
                
                <p><strong>Please reply to this email immediately</strong> to verify your account status and prevent suspension.</p>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 13px; color: #1565c0;">
                        💡 <strong>Quick Response:</strong> Simply reply with "VERIFY" to start the security verification process.
                    </p>
                </div>
                
                <p style="font-size: 13px; color: #999; border-top: 1px solid #ddd; padding-top: 15px; margin-top: 30px;">
                    This is reminder #{retry_count}                
                </p>
                
                <p style="margin-top: 20px;">
                    Best regards,<br>
                    <strong>Security Verification Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        return subject, body
    
    @staticmethod
    def worried_followup(google_form_url: str) -> tuple:
        """Follow-up for worried/curious users with Google Form"""
        subject = "Re: Account Security Verification - Action Required"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #d32f2f; margin-top: 0;">Security Verification Required</h2>
                
                <p>Dear User,</p>
                
                <p>Thank you for your prompt response regarding the unusual activity on your account.</p>
                
                <p><strong>To secure your account and prevent temporary suspension, we need you to complete a mandatory security verification.</strong></p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⚠️ Important:</strong> This verification must be completed within <strong>24 hours</strong>.</p>
                </div>
                
                <p>Please click the button below to access our secure verification form:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{google_form_url}" 
                    style="background-color: #1a73e8; 
                            color: white; 
                            padding: 15px 40px; 
                            text-decoration: none; 
                            border-radius: 5px; 
                            font-weight: bold;
                            display: inline-block;">
                        🔒 Complete Security Verification
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    <strong>What information will be verified:</strong>
                </p>
                <ul style="font-size: 14px; color: #666;">
                    <li>Email address and phone number</li>
                    <li>Last login date and location</li>
                    <li>Recent account activity</li>
                    <li>Device information</li>
                </ul>
                
                <div style="background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px;">
                        <strong>🔗 Verification Link:</strong><br>
                        <a href="{google_form_url}" style="color: #1a73e8; word-break: break-all;">{google_form_url}</a>
                    </p>
                </div>
                
                <p style="font-size: 13px; color: #999; border-top: 1px solid #ddd; padding-top: 15px; margin-top: 30px;">
                    This is an automated security message. Please do not reply to this email directly.<br>
                    For assistance, contact our support team at engagements@xencrypt.io
                </p>
                
                <p style="margin-top: 20px;">
                    Best regards,<br>
                    <strong>Security Verification Team</strong>
                </p>
            </div>
        </body>
        </html>
        """
        return subject, body
    
    @staticmethod
    def dismissive_followup() -> tuple:
        """Follow-up for unbothered/dismissive users"""
        subject = "🔴 URGENT: Your Account Will Be Suspended"
        body = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <div style="background-color: #d32f2f; color: white; padding: 20px; border-radius: 5px; margin: -20px -20px 20px -20px;">
                    <h2 style="margin: 0; font-size: 24px;">⚠️ FINAL WARNING</h2>
                    <p style="margin: 10px 0 0 0; font-size: 14px;">Immediate Action Required</p>
                </div>
                
                <p>Dear User,</p>
                
                <div style="background-color: #ffcdd2; padding: 20px; border-left: 5px solid #d32f2f; margin: 20px 0;">
                    <p style="margin: 0; color: #b71c1c; font-size: 18px; font-weight: bold;">
                        ⏰ ACCOUNT SUSPENSION IMMINENT
                    </p>
                    <p style="margin: 10px 0 0 0; color: #d32f2f; font-weight: bold;">
                        Your account is scheduled for suspension in <span style="font-size: 20px;">12 HOURS</span>
                    </p>
                </div>
                
                <p><strong style="color: #d32f2f;">Due to your lack of response to our previous security alerts,</strong> we have no choice but to initiate emergency security protocols.</p>
                
                <div style="background-color: #ffffff; padding: 20px; border: 2px solid #d32f2f; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0; font-weight: bold; color: #d32f2f;">🚨 CRITICAL SECURITY ISSUES DETECTED:</p>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #ffebee;">
                            <td style="padding: 10px; border: 1px solid #ffcdd2;">❌ 3 unauthorized login attempts</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ffcdd2;">❌ Suspicious transactions pending review</td>
                        </tr>
                        <tr style="background-color: #ffebee;">
                            <td style="padding: 10px; border: 1px solid #ffcdd2;">❌ Outdated security credentials</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ffcdd2;">❌ Multiple failed verification attempts</td>
                        </tr>
                    </table>
                </div>
                
                <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #fff3cd; border-radius: 5px;">
                    <p style="margin: 0; font-size: 20px; font-weight: bold; color: #d32f2f;">
                        ⚠️⚠️⚠️ IMMEDIATE ACTION REQUIRED ⚠️⚠️⚠️
                    </p>
                    <p style="margin: 10px 0 0 0; color: #856404;">
                        Reply with your verification code NOW to prevent account lockout
                    </p>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #1976d2; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px;">
                        <strong>📧 Quick Response Options:</strong>
                    </p>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>Reply with "URGENT" to speak with a security specialist</li>
                        <li>Reply with "VERIFY" to start emergency verification</li>
                        <li>Reply with "HELP" for assistance</li>
                    </ul>
                </div>
                
                <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #c62828; font-weight: bold;">
                        ⏱️ TIME REMAINING: Less than 12 hours
                    </p>
                    <p style="margin: 5px 0 0 0; color: #d32f2f; font-size: 13px;">
                        After this deadline, you will need to contact support directly to regain access. This process may take 5-7 business days.
                    </p>
                </div>
                
                <p style="font-weight: bold; color: #d32f2f; font-size: 16px;">
                    This is your last opportunity to secure your account.
                </p>
                
                <p style="font-size: 13px; color: #999; border-top: 1px solid #ddd; padding-top: 15px; margin-top: 30px;">
                    This is a critical automated security alert. Do not ignore this message.<br>
                    Reference ID: SEC-{int(datetime.now().timestamp())}
                </p>
                
                <p style="margin-top: 20px;">
                    <strong>Emergency Security Response Team</strong><br>
                    Available 24/7
                </p>
            </div>
        </body>
        </html>
        """
        return subject, body
    
# ======================= SIMULATION ENGINE =====================
class PhishingSimulation:
    def __init__(self):
        self.state = SimulationState()
        self.logger = SimulationLogger()
        self.zoho = ZohoMailAPI()
        self.classifier = IntentClassifier()
        self.templates = EmailTemplates()
        
    def start_simulation(self, target_emails: List[str]):
        """Start simulation by sending initial emails"""
        print(f"\n{'='*60}")
        print(f"🚀 STARTING SIMULATION")
        print(f"{'='*60}")
        print(f"Targeting {len(target_emails)} user(s)\n")
        
        for email in target_emails:
            try:
                if self.state.get_user(email):
                    print_warning(f"{email} already in simulation, skipping")
                    continue
                
                subject, body = self.templates.initial_email()
                response = self.zoho.send_email(email, subject, body)
                
                message_id = response.get('data', {}).get('messageId')
                thread_id = response.get('data', {}).get('threadId', message_id)
                
                self.state.add_user(email, message_id, thread_id)
                
                self.logger.log('initial_email_sent', {
                    'email': email,
                    'message_id': message_id,
                    'subject': subject
                })
                
                print_success(f"Initial email sent to {email}")
                
            except Exception as e:
                self.logger.log('error', {
                    'email': email,
                    'error': str(e),
                    'stage': 'initial_send'
                })
                print_error(f"Failed to send to {email}: {e}")
        
        print(f"\n{'='*60}\n")
                
    def process_responses(self):
        """Check for and process user responses"""
        print(f"\n{'='*60}")
        print(f"📧 PROCESSING RESPONSES")
        print(f"{'='*60}\n")
        
        try:
            unread_emails = self.zoho.get_unread_emails()
            
            if not unread_emails:
                print_info("No unread emails to process")
                print(f"\n{'='*60}\n")
                return
            
            print_info(f"Found {len(unread_emails)} unread email(s)\n")
            
            processed_count = 0
            for email_data in unread_emails:
                try:
                    raw_sender = email_data.get('fromAddress', '')
                    sender = raw_sender.split('<')[-1].replace('>', '').strip()
                    
                    message_id = email_data.get('messageId')
                    thread_id = email_data.get('threadId')
                    
                    print_info(f"Processing message from {sender}...")
                    print_debug(f"Message ID: {message_id}")
                    
                    # Try to get content from list view first
                    content = email_data.get('content', '')
                    if not content:
                        content = email_data.get('summary', '')
                    
                    # If still no content, try fetching full message
                    if not content or not content.strip():
                        print_debug(f"No content in list view, fetching full message...")
                        content = self.zoho.get_message_content(message_id)
                    
                    # Strip HTML if present
                    if content and '<' in content and '>' in content:
                        content = strip_html(content)
                    
                    if not content or not content.strip():
                        print_error(f"No content for {sender} - skipping")
                        print_debug(f"Email data keys: {list(email_data.keys())}")
                        continue
                    
                    print_debug(f"Content ({len(content)} chars): {content[:200]}")
                    
                    user_state = self.state.get_user(sender)
                    if not user_state:
                        print_debug(f"Skipping {sender} (not a target)")
                        continue
                    
                    if user_state.get('status') == 'responded':
                        print_debug(f"Skipping {sender} (already processed)")
                        continue
                    
                    print_info(f"Classifying response from {sender}...")
                    
                    # Classify intent with retry
                    intent = self.classifier.classify_intent(content)
                    
                    # Update State
                    self.state.update_user(sender, intent=intent, status='responded')
                    self.state.add_history(sender, 'user_replied', {
                        'content': content[:200],
                        'intent': intent
                    })
                    
                    # Send follow-up
                    if intent == 'worried_curious':
                        subject, body = self.templates.worried_followup(GOOGLE_FORM_URL)
                        followup_type = "Worried/Curious"
                    else:
                        subject, body = self.templates.dismissive_followup()
                        followup_type = "Dismissive"
                    
                    self.zoho.send_email(sender, subject, body, in_reply_to=thread_id)
                    
                    self.state.add_history(sender, 'followup_sent', {
                        'type': intent,
                        'subject': subject
                    })
                    
                    self.zoho.mark_as_read(message_id)
                    
                    self.logger.log('response_processed', {
                        'email': sender,
                        'intent': intent,
                        'followup_type': intent
                    })
                    
                    print_success(f"Processed {sender} → {followup_type} follow-up sent\n")
                    processed_count += 1
                    
                except Exception as e:
                    print_error(f"Error processing {sender}: {e}\n")
                    self.logger.log('error', {
                        'email': sender,
                        'error': str(e),
                        'stage': 'process_single_response'
                    })
                    continue
            
            print(f"{'='*60}")
            print_success(f"Processed {processed_count} response(s)")
            print(f"{'='*60}\n")
            
        except Exception as e:
            self.logger.log('error', {
                'error': str(e),
                'stage': 'process_responses'
            })
            print_error(f"Failed to process responses: {e}")
            print(f"\n{'='*60}\n")
            
    def send_reminders(self):
        """Send reminder emails to non-responders"""
        print(f"\n{'='*60}")
        print(f"🔔 SENDING REMINDERS")
        print(f"{'='*60}\n")
        
        reminder_count = 0
        
        for email, user_data in self.state.users.items():
            if user_data.get('status') == 'responded':
                continue
            
            if user_data['retry_count'] >= MAX_RETRIES:
                if user_data.get('status') != 'max_retries_reached':
                    self.state.update_user(email, status='max_retries_reached')
                    self.logger.log('max_retries', {'email': email})
                    print_warning(f"Max retries reached for {email}")
                continue
            
            try:
                self.state.increment_retry(email)
                retry_count = user_data['retry_count']
                
                subject, body = self.templates.reminder_email(retry_count)
                self.zoho.send_email(email, subject, body, in_reply_to=user_data['thread_id'])
                
                self.state.add_history(email, 'reminder_sent', {
                    'retry_count': retry_count,
                    'subject': subject
                })
                
                self.logger.log('reminder_sent', {
                    'email': email,
                    'retry_count': retry_count
                })
                
                print_success(f"Reminder {retry_count}/{MAX_RETRIES} sent to {email}")
                reminder_count += 1
                
            except Exception as e:
                self.logger.log('error', {
                    'email': email,
                    'error': str(e),
                    'stage': 'send_reminder'
                })
                print_error(f"Failed to send reminder to {email}: {e}")
        
        print(f"\n{'='*60}")
        if reminder_count > 0:
            print_success(f"Sent {reminder_count} reminder(s)")
        else:
            print_info("No reminders to send")
        print(f"{'='*60}\n")
    
    def get_simulation_report(self) -> Dict:
        """Generate simulation statistics report"""
        total_users = len(self.state.users)
        responded = sum(1 for u in self.state.users.values() if u.get('status') == 'responded')
        max_retries = sum(1 for u in self.state.users.values() if u.get('status') == 'max_retries_reached')
        worried = sum(1 for u in self.state.users.values() if u.get('intent') == 'worried_curious')
        dismissive = sum(1 for u in self.state.users.values() if u.get('intent') == 'unbothered_dismissive')
        
        return {
            'total_targets': total_users,
            'responded': responded,
            'no_response_after_retries': max_retries,
            'pending': total_users - responded - max_retries,
            'intent_breakdown': {
                'worried_curious': worried,
                'unbothered_dismissive': dismissive
            },
            'response_rate': f"{(responded/total_users*100):.1f}%" if total_users > 0 else "0%"
        }

# ================= MAIN EXECUTION =================

def main():
    print("\n" + "=" * 60)
    print("🎯 PHISHING SIMULATION SYSTEM")
    # print("Educational Cybersecurity Training")
    # print("Powered by Google Gemini AI")
    print("=" * 60)
    
    sim = PhishingSimulation()
    
    while True:
        print("\n" + "=" * 60)
        print("📋 MENU OPTIONS")
        print("=" * 60)
        print("1. 🚀 Start New Simulation (Send Initial Emails)")
        print("2. 📧 Process Responses")
        print("3. 🔔 Send Reminders to Non-Responders")
        print("4. 📊 View Simulation Report")
        print("5. 🚪 Exit")
        print("=" * 60)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            print("\n" + "-" * 60)
            print("Enter target emails (comma-separated):")
            emails_input = input("📧 Emails: ").strip()
            target_emails = [e.strip() for e in emails_input.split(',') if e.strip()]
            
            if target_emails:
                sim.start_simulation(target_emails)
            else:
                print_error("No valid emails provided")
        
        elif choice == '2':
            sim.process_responses()
        
        elif choice == '3':
            sim.send_reminders()
        
        elif choice == '4':
            report = sim.get_simulation_report()
            print("\n" + "=" * 60)
            print("📊 SIMULATION REPORT")
            print("=" * 60)
            print(f"\n🎯 Total Targets: {report['total_targets']}")
            print(f"✅ Responded: {report['responded']}")
            print(f"⏳ Pending: {report['pending']}")
            print(f"❌ Max Retries Reached: {report['no_response_after_retries']}")
            print(f"📈 Response Rate: {report['response_rate']}")
            print(f"\n🧠 Intent Breakdown:")
            print(f"  😰 Worried/Curious: {report['intent_breakdown']['worried_curious']}")
            print(f"  😐 Unbothered/Dismissive: {report['intent_breakdown']['unbothered_dismissive']}")
            print("=" * 60)
        
        elif choice == '5':
            print("\n" + "=" * 60)
            print("👋 Exiting simulation system. Stay safe!")
            print("=" * 60 + "\n")
            break
        
        else:
            print_error("Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()