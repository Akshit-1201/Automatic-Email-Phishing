import os
import json
import requests
import time
import re
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GOOGLE_FORM_URL = os.getenv("GOOGLE_FORM_URL")

class EmailGenerator:
    """LLM-powered email generator for phishing simulation follow-ups"""
    
    def __init__(self, template_service):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.template_service = template_service
    
    def generate_followup(self, template_id: str, user_response: str, intent: str) -> Dict[str, str]:
        """
        Generate personalized follow-up email based on user response
        
        Args:
            template_id: Original template ID
            user_response: User's response text
            intent: Classified intent ('worried_curious' or 'unbothered_dismissive')
        
        Returns:
            Dictionary with 'subject' and 'body_html'
        """
        # Get original template for context
        template = self.template_service.get_template(template_id)
        if not template:
            return self._get_fallback_followup(intent)
        
        # Build prompt
        prompt = self._build_followup_prompt(template, user_response, intent)
        
        # Call LLM with retry logic
        response = self._call_gemini_with_retry(prompt)
        
        if not response:
            return self._get_fallback_followup(intent)
        
        # Parse response
        email_data = self._parse_email_response(response)
        
        # Inject credential link if needed
        if intent == 'worried_curious' and GOOGLE_FORM_URL:
            email_data['body_html'] = self._inject_credential_link(email_data['body_html'])
        
        return email_data
    
    def generate_reminder(self, template_id: str, retry_count: int) -> Dict[str, str]:
        """
        Generate escalating reminder email
        
        Args:
            template_id: Original template ID
            retry_count: Current retry count (1, 2, or 3)
        
        Returns:
            Dictionary with 'subject' and 'body_html'
        """
        # Get original template for context
        template = self.template_service.get_template(template_id)
        if not template:
            return self._get_fallback_reminder(retry_count)
        
        # Build prompt
        prompt = self._build_reminder_prompt(template, retry_count)
        
        # Call LLM with retry logic
        response = self._call_gemini_with_retry(prompt)
        
        if not response:
            return self._get_fallback_reminder(retry_count)
        
        # Parse response
        email_data = self._parse_email_response(response)
        
        return email_data
    
    def _build_followup_prompt(self, template: Dict, user_response: str, intent: str) -> str:
        """Build prompt for follow-up email generation"""
        
        if intent == 'worried_curious':
            intent_description = "worried, anxious, curious, asking questions"
            requirements = """
- Acknowledge their response professionally and reassuringly
- Thank them for their prompt reply
- Continue the exact scenario from the original email (e.g., if it was about a prize, continue about prize claiming; if security, continue about security verification)
- Provide specific next steps they need to take
- Include the placeholder {CREDENTIAL_LINK} where a verification/claim button or link should appear
- Create moderate urgency with a deadline (e.g., "within 24 hours")
- Use professional, trustworthy tone
- Include visual elements like buttons, boxes, colored sections in HTML
"""
        else:  # dismissive
            intent_description = "unbothered, dismissive, brief, not concerned"
            requirements = """
- Create MAXIMUM URGENCY to grab their attention immediately
- Use warning colors (red backgrounds, bold text)
- Include consequences of inaction (account suspension, prize forfeiture, etc.)
- Continue the exact scenario from the original email with escalated stakes
- Use urgent subject line with emojis (🔴, ⚠️, ⏰)
- Emphasize time running out ("FINAL HOURS", "LAST CHANCE")
- Make them feel they're missing something critical
- Use HTML with warning boxes, countdown timers, urgent styling
"""
        
        # Get a snippet of the original email for better context
        original_preview = template.get('body_html', '')[:500]
        
        prompt = f"""You are a cybersecurity educator creating realistic, contextual phishing simulation follow-up emails.

ORIGINAL EMAIL CONTEXT:
Template Name: {template['name']}
Subject: {template['subject']}
Scenario: {template.get('description', 'General phishing scenario')}
Original Email Preview: {original_preview}...

USER'S RESPONSE:
"{user_response}"

USER'S EMOTIONAL STATE:
The user appears {intent_description}.

YOUR TASK:
Write a follow-up email that:
1. DIRECTLY responds to what the user said
2. CONTINUES the exact same scenario from the original email (not a new scenario)
3. Feels like a natural reply in an ongoing email conversation
4. Stays in character with the original email's tone and sender

REQUIREMENTS:
{requirements}

CRITICAL OUTPUT RULES:
- Return ONLY a valid JSON object
- NO markdown formatting, NO code blocks, NO backticks
- The JSON MUST be properly escaped
- Use double backslashes for quotes inside HTML: \\" instead of "
- Example: {{"subject": "Test", "body_html": "<div style=\\"color: red;\\">Hello</div>"}}

OUTPUT FORMAT (properly escaped JSON):
{{"subject": "Re: [original subject] - Your exact subject here", "body_html": "<html><body style=\\"font-family: Arial, sans-serif;\\">Your complete HTML email here with all quotes escaped as \\"</body></html>"}}

Generate the follow-up email now (valid JSON only):"""
        
        return prompt
    
    def _build_reminder_prompt(self, template: Dict, retry_count: int) -> str:
        """Build prompt for reminder email generation"""
        
        urgency_levels = {
            1: "GENTLE - First friendly reminder",
            2: "MODERATE - Second reminder with consequences mentioned",
            3: "CRITICAL - Final warning with severe consequences"
        }
        
        urgency_level = urgency_levels.get(retry_count, urgency_levels[3])
        
        # Get original email preview
        original_preview = template.get('body_html', '')[:500]
        
        prompt = f"""You are a cybersecurity educator creating realistic phishing simulation reminder emails.

ORIGINAL EMAIL CONTEXT:
Template Name: {template['name']}
Subject: {template['subject']}
Scenario: {template.get('description', 'General phishing scenario')}
Original Email Preview: {original_preview}...

SITUATION:
- User has NOT responded to the original email
- This is reminder #{retry_count} of 3
- Urgency Level: {urgency_level}

YOUR TASK:
Create an escalating reminder that:
1. References the original email scenario (continue the same story)
2. Increases urgency appropriate to reminder number
3. Mentions specific consequences of continued non-response
4. Uses visual urgency cues in HTML (colors, emojis, formatting)

REMINDER #{retry_count} REQUIREMENTS:
"""
        
        if retry_count == 1:
            prompt += """
- Friendly but firm tone
- Mention they may have missed the original email
- Provide deadline extension (e.g., "24 more hours")
- Use yellow/orange warning colors
- Subject: Add "REMINDER:" prefix
- Maintain professional appearance
"""
        elif retry_count == 2:
            prompt += """
- More urgent tone
- Explicitly state consequences (suspension, forfeiture, etc.)
- Shorter deadline (e.g., "12 hours remaining")
- Use orange/red warning colors
- Subject: Add "⚠️ REMINDER 2:" with warning emoji
- Include countdown or time pressure
"""
        else:  # retry_count == 3
            prompt += """
- CRITICAL urgency
- Severe consequences emphasized (FINAL CHANCE)
- Very short deadline (e.g., "6 hours" or "end of day")
- Dominant red colors, bold warnings
- Subject: Add "🔴 FINAL REMINDER:" with multiple urgency indicators
- Make it clear this is the absolute last notification
"""
        
        prompt += """
CRITICAL OUTPUT RULES:
- Return ONLY a valid JSON object
- NO markdown formatting, NO code blocks, NO backticks
- The JSON MUST be properly escaped
- Use double backslashes for quotes inside HTML: \\" instead of "
- Example: {{"subject": "Test", "body_html": "<div style=\\"color: red;\\">Hello</div>"}}

OUTPUT FORMAT (properly escaped JSON):
{{"subject": "Your urgent subject here", "body_html": "<html><body style=\\"font-family: Arial, sans-serif;\\">Your complete HTML email here with all quotes escaped as \\"</body></html>"}}

Generate the reminder email now (valid JSON only):"""
        
        return prompt
    
    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call Gemini API with retry logic"""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 3000,
                "topP": 0.8,
                "topK": 20
            }
        }
        
        for attempt in range(max_retries):
            try:
                print(f"🤖 Calling Gemini API (attempt {attempt + 1}/{max_retries})...")
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'candidates' not in data or not data['candidates']:
                    print(f"⚠️  No candidates in response")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None
                
                candidate = data['candidates'][0]
                
                if 'content' not in candidate or 'parts' not in candidate['content']:
                    print(f"⚠️  No content in response")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                
                text = candidate['content']['parts'][0]['text']
                print(f"✅ LLM response received ({len(text)} chars)")
                
                return text
                
            except requests.exceptions.RequestException as e:
                print(f"❌ API Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    def _parse_email_response(self, response_text: str) -> Dict[str, str]:
        """Parse LLM response and extract subject and body"""
        
        try:
            # Clean the response text
            cleaned = response_text.strip()
            
            # Remove markdown code blocks (multiple patterns)
            cleaned = re.sub(r'^```json\s*\n?', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'^```\s*\n?', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()
            
            print(f"🔍 Attempting to parse JSON...")
            
            # First, try standard JSON parsing
            try:
                data = json.loads(cleaned)
                
                # Validate required fields
                if 'subject' in data and 'body_html' in data:
                    subject = str(data['subject']).strip()
                    body_html = str(data['body_html']).strip()
                    
                    # Basic HTML validation
                    if not any(tag in body_html.lower() for tag in ['<html', '<body', '<div', '<p']):
                        print(f"⚠️  Invalid HTML, wrapping...")
                        body_html = f"<html><body style='font-family: Arial, sans-serif;'>{body_html}</body></html>"
                    
                    print(f"✅ Successfully parsed - Subject: {subject[:60]}...")
                    return {'subject': subject, 'body_html': body_html}
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Standard JSON parse failed: {str(e)[:100]}")
                print(f"⚠️  Attempting smart extraction...")
            
            # Smart manual extraction
            # Try to find subject
            subject = None
            subject_patterns = [
                r'"subject"\s*:\s*"([^"]+)"',
                r'"subject"\s*:\s*\'([^\']+)\'',
                r'subject:\s*"([^"]+)"'
            ]
            
            for pattern in subject_patterns:
                match = re.search(pattern, cleaned)
                if match:
                    subject = match.group(1)
                    break
            
            if not subject:
                subject = "Re: Account Verification Required"
            
            # Extract body_html - more robust approach
            # Find where body_html value starts
            body_patterns = [
                r'"body_html"\s*:\s*"(.+)"\s*\}',
                r'"body_html"\s*:\s*"(.+)"$',
                r'body_html:\s*"(.+)"\s*\}',
            ]
            
            body_html = None
            for pattern in body_patterns:
                match = re.search(pattern, cleaned, re.DOTALL)
                if match:
                    body_html = match.group(1)
                    break
            
            # If still not found, try to extract everything between body_html and the end
            if not body_html:
                body_start_marker = cleaned.find('"body_html"')
                if body_start_marker != -1:
                    # Find the opening quote after the colon
                    start_quote = cleaned.find('"', body_start_marker + len('"body_html"') + 1)
                    if start_quote != -1:
                        # The body goes until we find "}
                        remaining = cleaned[start_quote + 1:]
                        
                        # Find the last occurrence of "}
                        end_marker = remaining.rfind('"}')
                        if end_marker == -1:
                            end_marker = remaining.rfind('"')
                        
                        if end_marker != -1:
                            body_html = remaining[:end_marker]
            
            if body_html:
                # Clean up common escape sequences
                body_html = body_html.replace('\\"', '"')
                body_html = body_html.replace('\\n', '\n')
                body_html = body_html.replace('\\t', '\t')
                body_html = body_html.replace('\\/', '/')
                body_html = body_html.replace('\\\\', '\\')
                
                # Validate we have some HTML
                if not any(tag in body_html.lower() for tag in ['<html', '<body', '<div', '<p', '<h']):
                    print(f"⚠️  No HTML tags found, wrapping content...")
                    body_html = f"<html><body style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'><div style='padding: 20px;'>{body_html}</div></body></html>"
                
                print(f"✅ Manual extraction successful!")
                print(f"   Subject: {subject[:60]}...")
                print(f"   Body length: {len(body_html)} chars")
                
                return {
                    'subject': subject,
                    'body_html': body_html
                }
            
            raise ValueError("Could not extract email data from response")
            
        except Exception as e:
            print(f"❌ All parsing attempts failed: {e}")
            print(f"📄 Response preview: {response_text[:400]}...")
            print(f"⚠️  Using fallback template")
            return self._get_fallback_followup('worried_curious')
    
    def _inject_credential_link(self, body_html: str) -> str:
        """Inject credential capture link into email body"""
        
        if not GOOGLE_FORM_URL:
            return body_html
        
        # Look for placeholder
        if '{CREDENTIAL_LINK}' in body_html:
            return body_html.replace('{CREDENTIAL_LINK}', GOOGLE_FORM_URL)
        
        # If no placeholder, inject before closing body tag
        button_html = f'''
<div style="text-align: center; margin: 30px 0;">
    <a href="{GOOGLE_FORM_URL}" 
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
'''
        
        if '</body>' in body_html:
            return body_html.replace('</body>', f'{button_html}</body>')
        else:
            return body_html + button_html
    
    def _get_fallback_followup(self, intent: str) -> Dict[str, str]:
        """Return fallback email if LLM fails"""
        
        if intent == 'worried_curious':
            return {
                'subject': 'Re: Security Verification Required',
                'body_html': '''<html><body style="font-family: Arial, sans-serif;">
                <p>Dear User,</p>
                <p>Thank you for your prompt response. To resolve this security issue, please complete the verification process.</p>
                <p>Click the button below to verify your account:</p>
                <div style="text-align: center; margin: 20px;">
                    <a href="{CREDENTIAL_LINK}" style="background-color: #1a73e8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Verify Account</a>
                </div>
                <p>Best regards,<br>Security Team</p>
                </body></html>'''
            }
        else:
            return {
                'subject': '🔴 URGENT: Immediate Action Required',
                'body_html': '''<html><body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d32f2f;">⚠️ FINAL WARNING</h2>
                <p>Your account requires immediate attention. Failure to respond will result in account suspension.</p>
                <p><strong>Reply immediately to prevent account lockout.</strong></p>
                <p>Security Team</p>
                </body></html>'''
            }
    
    def _get_fallback_reminder(self, retry_count: int) -> Dict[str, str]:
        """Return fallback reminder if LLM fails"""
        
        urgency = "⚠️" * retry_count
        
        return {
            'subject': f'{urgency} REMINDER {retry_count}: Action Required',
            'body_html': f'''<html><body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d32f2f;">{urgency} Reminder #{retry_count} of 3</h2>
            <p>You have not responded to our previous messages.</p>
            <p><strong>Please reply immediately to avoid account suspension.</strong></p>
            <p>This is an automated reminder.</p>
            </body></html>'''
        }