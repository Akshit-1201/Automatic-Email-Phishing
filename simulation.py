import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time
import re
from html import unescape

# Import new services
from services.template_service import TemplateService
from services.email_generator import EmailGenerator

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
    
    def add_user(self, email: str, message_id: str, thread_id: str, template_id: str, template_name: str):
        """Initialize new user in Simulation"""
        self.users[email] = {
            'email': email,
            'template_id': template_id,
            'template_name': template_name,
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

# =================== SIMULATION ENGINE =====================
class PhishingSimulation:
    def __init__(self):
        self.state = SimulationState()
        self.logger = SimulationLogger()
        self.zoho = ZohoMailAPI()
        self.classifier = IntentClassifier()
        
        # NEW: Initialize template service and email generator
        self.template_service = TemplateService()
        self.email_generator = EmailGenerator(self.template_service)
        
    def start_simulation(self, target_emails: List[str], template_id: str = "security_incident"):
        """Start simulation by sending initial emails"""
        print(f"\n{'='*60}")
        print(f"🚀 STARTING SIMULATION")
        print(f"{'='*60}")
        print(f"Template: {template_id}")
        print(f"Targeting {len(target_emails)} user(s)\n")
        
        # Get template
        template = self.template_service.get_template(template_id)
        if not template:
            print_error(f"Template '{template_id}' not found!")
            return
        
        for email in target_emails:
            try:
                if self.state.get_user(email):
                    print_warning(f"{email} already in simulation, skipping")
                    continue
                
                # Use template from service
                subject = template['subject']
                body = template['body_html']
                
                response = self.zoho.send_email(email, subject, body)
                
                message_id = response.get('data', {}).get('messageId')
                thread_id = response.get('data', {}).get('threadId', message_id)
                
                self.state.add_user(email, message_id, thread_id, template_id, template['name'])
                
                self.logger.log('initial_email_sent', {
                    'email': email,
                    'template_id': template_id,
                    'template_name': template['name'],
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
                    
                    # Classify intent
                    intent = self.classifier.classify_intent(content)
                    
                    # Update State
                    self.state.update_user(sender, intent=intent, status='responded')
                    self.state.add_history(sender, 'user_replied', {
                        'content': content[:200],
                        'intent': intent
                    })
                    
                    # Generate follow-up using LLM
                    print_info(f"Generating personalized follow-up for {sender}...")
                    email_data_followup = self.email_generator.generate_followup(
                        template_id=user_state['template_id'],
                        user_response=content,
                        intent=intent
                    )
                    
                    subject = email_data_followup['subject']
                    body = email_data_followup['body_html']
                    
                    followup_type = "Worried/Curious" if intent == 'worried_curious' else "Dismissive"
                    
                    self.zoho.send_email(sender, subject, body, in_reply_to=thread_id)
                    
                    self.state.add_history(sender, 'followup_sent', {
                        'type': intent,
                        'subject': subject,
                        'generated_by': 'llm'
                    })
                    
                    self.zoho.mark_as_read(message_id)
                    
                    self.logger.log('response_processed', {
                        'email': sender,
                        'intent': intent,
                        'followup_type': intent,
                        'generated_by': 'llm'
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
                retry_count = user_data['retry_count'] + 1
                
                # Generate reminder using LLM
                print_info(f"Generating reminder {retry_count} for {email}...")
                email_data_reminder = self.email_generator.generate_reminder(
                    template_id=user_data['template_id'],
                    retry_count=retry_count
                )
                
                subject = email_data_reminder['subject']
                body = email_data_reminder['body_html']
                
                self.zoho.send_email(email, subject, body, in_reply_to=user_data['thread_id'])
                
                self.state.add_history(email, 'reminder_sent', {
                    'retry_count': retry_count,
                    'subject': subject,
                    'generated_by': 'llm'
                })
                
                self.logger.log('reminder_sent', {
                    'email': email,
                    'retry_count': retry_count,
                    'generated_by': 'llm'
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
    print("=" * 60)
    
    sim = PhishingSimulation()
    
    # List available templates
    templates = sim.template_service.list_templates()
    
    while True:
        print("\n" + "=" * 60)
        print("📋 MENU OPTIONS")
        print("=" * 60)
        print("1. 🚀 Start New Simulation (Send Initial Emails)")
        print("2. 📧 Process Responses")
        print("3. 🔔 Send Reminders to Non-Responders")
        print("4. 📊 View Simulation Report")
        print("5. 📄 List Available Templates")
        print("6. ✍️  Create Custom Template")
        print("7. 🚪 Exit")
        print("=" * 60)
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            print("\n" + "-" * 60)
            print("📧 AVAILABLE TEMPLATES:")
            print("-" * 60)
            for idx, template in enumerate(templates, 1):
                print(f"{idx}. {template['name']} ({template['category']})")
            print("-" * 60)
            
            template_choice = input(f"\nSelect template (1-{len(templates)}): ").strip()
            
            try:
                template_idx = int(template_choice) - 1
                if 0 <= template_idx < len(templates):
                    selected_template = templates[template_idx]
                    template_id = selected_template['id']
                    
                    print(f"\n✅ Selected: {selected_template['name']}")
                    
                    # Preview
                    preview = sim.template_service.get_template_preview(template_id)
                    print(f"\n📄 Preview: {preview}\n")
                    
                    emails_input = input("📧 Enter target emails (comma-separated): ").strip()
                    target_emails = [e.strip() for e in emails_input.split(',') if e.strip()]
                    
                    if target_emails:
                        sim.start_simulation(target_emails, template_id)
                    else:
                        print_error("No valid emails provided")
                else:
                    print_error("Invalid template selection")
            except ValueError:
                print_error("Invalid input")
        
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
            print("📄 AVAILABLE TEMPLATES")
            print("=" * 60)
            for idx, template in enumerate(templates, 1):
                custom_marker = "[CUSTOM]" if template['is_custom'] else ""
                print(f"{idx}. {template['name']} - {template['category']} {custom_marker}")
            print("=" * 60)
        
        elif choice == '6':
            print("\n" + "-" * 60)
            print("✍️  CREATE CUSTOM TEMPLATE")
            print("-" * 60)
            
            name = input("Template Name: ").strip()
            subject = input("Email Subject: ").strip()
            print("Credential Form — enter the .env variable name that holds")
            print("the Google Form URL (e.g. FORM_URL_MY_CUSTOM).")
            print("Leave blank to skip.")
            form_env_var = input("  .env variable name: ").strip()
            
            print("\nEnter email body HTML (type 'END' on a new line when done):")
            body_lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                body_lines.append(line)
            body_html = '\n'.join(body_lines)
            
            if name and subject and body_html:
                template_id = sim.template_service.save_custom_template(name, subject, body_html, form_env_var)
                print_success(f"Custom template created with ID: {template_id}")
                if form_env_var:
                    url_value = os.getenv(form_env_var, "")
                    if url_value:
                        print_success(f"Form URL resolved from {form_env_var}")
                    else:
                        print_warning(f"{form_env_var} is not set in .env — add it before running the simulation")
                
                # Refresh templates list
                templates = sim.template_service.list_templates()
            else:
                print_error("All fields are required")
        
        elif choice == '7':
            print("\n" + "=" * 60)
            print("👋 Exiting simulation system. Stay safe!")
            print("=" * 60 + "\n")
            break
        
        else:
            print_error("Invalid choice. Please select 1-7.")

if __name__ == "__main__":
    main()