import json
import os
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

TEMPLATES_FILE = "templates/email_templates.json"
CUSTOM_TEMPLATES_FILE = "templates/custom_templates.json"

# Maps each template ID to its .env variable name
FORM_URL_ENV_MAP = {
    "security_incident": "FORM_URL_SECURITY",
    "social_media":      "FORM_URL_SOCIAL_MEDIA",
    "prize_reward":      "FORM_URL_PRIZE_REWARD",
    "it_upgrade":        "FORM_URL_IT_UPGRADE",
    "package_delivery":  "FORM_URL_PACKAGE_DELIVERY",
}

class TemplateService:
    """Service for managing email templates"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.custom_templates = self._load_custom_templates()
    
    def _load_templates(self) -> Dict:
        """Load pre-defined templates from JSON file and attach form URLs from .env"""
        if not os.path.exists(TEMPLATES_FILE):
            print(f"⚠️  Warning: Templates file not found at {TEMPLATES_FILE}")
            return {}
        
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        # Attach credential_form_url from .env to each template
        for template_id, template_data in templates.items():
            env_var = FORM_URL_ENV_MAP.get(template_id)
            if env_var:
                url = os.getenv(env_var, "")
                template_data["credential_form_url"] = url
                if not url:
                    print(f"⚠️  Warning: {env_var} is not set in .env (template: {template_data['name']})")
        
        return templates
    
    def _load_custom_templates(self) -> Dict:
        """Load custom templates from JSON file and resolve form URLs from .env"""
        if not os.path.exists(CUSTOM_TEMPLATES_FILE):
            return {}
        
        with open(CUSTOM_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        # Resolve credential_form_url from .env for every custom template
        for template_id, template_data in templates.items():
            env_var = template_data.get('form_url_env_var', '')
            if env_var:
                url = os.getenv(env_var, "")
                template_data["credential_form_url"] = url
                if not url:
                    print(f"⚠️  Warning: {env_var} is not set in .env (custom template: {template_data['name']})")
            else:
                template_data.setdefault("credential_form_url", "")
        
        return templates
    
    def _save_custom_templates(self):
        """Save custom templates to JSON file (only env var names, not resolved URLs)"""
        os.makedirs(os.path.dirname(CUSTOM_TEMPLATES_FILE), exist_ok=True)
        
        # Build a copy that excludes the runtime-resolved credential_form_url
        to_persist = {}
        for tid, tdata in self.custom_templates.items():
            to_persist[tid] = {k: v for k, v in tdata.items() if k != 'credential_form_url'}
        
        with open(CUSTOM_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(to_persist, f, indent=2)
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """
        Get template by ID
        
        Args:
            template_id: Template identifier (e.g., 'security_incident', 'custom_123')
        
        Returns:
            Template dictionary with name, subject, body_html, etc.
        """
        # Check pre-defined templates first
        if template_id in self.templates:
            return self.templates[template_id]
        
        # Check custom templates
        if template_id in self.custom_templates:
            return self.custom_templates[template_id]
        
        return None
    
    def list_templates(self) -> List[Dict]:
        """
        List all available templates
        
        Returns:
            List of template dictionaries with id, name, category
        """
        result = []
        
        # Add pre-defined templates
        for template_id, template_data in self.templates.items():
            result.append({
                'id': template_id,
                'name': template_data['name'],
                'category': template_data.get('category', 'general'),
                'is_custom': False
            })
        
        # Add custom templates
        for template_id, template_data in self.custom_templates.items():
            result.append({
                'id': template_id,
                'name': template_data['name'],
                'category': 'custom',
                'is_custom': True
            })
        
        return result
    
    def save_custom_template(self, name: str, subject: str, body_html: str, form_url_env_var: str = '') -> str:
        """
        Save a custom template
        
        Args:
            name: Template name
            subject: Email subject
            body_html: Email body HTML
            form_url_env_var: .env variable name holding the Google Form URL (e.g. FORM_URL_MY_CUSTOM)
        
        Returns:
            Template ID (e.g., 'custom_1')
        """
        # Generate custom template ID
        custom_count = len([t for t in self.custom_templates.keys() if t.startswith('custom_')])
        template_id = f"custom_{custom_count + 1}"
        
        # Resolve the URL right now so it's available immediately this session
        credential_form_url = os.getenv(form_url_env_var, '') if form_url_env_var else ''
        
        # Persist to disk: store env var name (not the URL)
        self.custom_templates[template_id] = {
            'name': name,
            'category': 'custom',
            'description': f'Custom template: {name}',
            'subject': subject,
            'body_html': body_html,
            'form_url_env_var': form_url_env_var,
            'credential_form_url': credential_form_url   # live value for this session
        }
        
        # Save to file (only form_url_env_var persists; credential_form_url is re-resolved on next load)
        self._save_custom_templates()
        
        return template_id
    
    def validate_template(self, template_data: Dict) -> bool:
        """
        Validate template structure
        
        Args:
            template_data: Template dictionary
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'subject', 'body_html']
        return all(field in template_data for field in required_fields)
    
    def get_template_preview(self, template_id: str, max_length: int = 200) -> str:
        """
        Get a preview of template content
        
        Args:
            template_id: Template identifier
            max_length: Maximum preview length
        
        Returns:
            Preview text
        """
        template = self.get_template(template_id)
        if not template:
            return "Template not found"
        
        # Extract text from HTML (simple version)
        import re
        text = re.sub(r'<[^>]+>', '', template['body_html'])
        text = ' '.join(text.split())  # Clean whitespace
        
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text