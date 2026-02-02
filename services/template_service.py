import json
import os
from typing import Dict, Optional, List

TEMPLATES_FILE = "templates/email_templates.json"
CUSTOM_TEMPLATES_FILE = "templates/custom_templates.json"

class TemplateService:
    """Service for managing email templates"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.custom_templates = self._load_custom_templates()
    
    def _load_templates(self) -> Dict:
        """Load pre-defined templates from JSON file"""
        if not os.path.exists(TEMPLATES_FILE):
            print(f"⚠️  Warning: Templates file not found at {TEMPLATES_FILE}")
            return {}
        
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_custom_templates(self) -> Dict:
        """Load custom templates from JSON file"""
        if not os.path.exists(CUSTOM_TEMPLATES_FILE):
            return {}
        
        with open(CUSTOM_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_custom_templates(self):
        """Save custom templates to JSON file"""
        os.makedirs(os.path.dirname(CUSTOM_TEMPLATES_FILE), exist_ok=True)
        with open(CUSTOM_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.custom_templates, f, indent=2)
    
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
    
    def save_custom_template(self, name: str, subject: str, body_html: str) -> str:
        """
        Save a custom template
        
        Args:
            name: Template name
            subject: Email subject
            body_html: Email body HTML
        
        Returns:
            Template ID (e.g., 'custom_1')
        """
        # Generate custom template ID
        custom_count = len([t for t in self.custom_templates.keys() if t.startswith('custom_')])
        template_id = f"custom_{custom_count + 1}"
        
        # Create template
        self.custom_templates[template_id] = {
            'name': name,
            'category': 'custom',
            'description': f'Custom template: {name}',
            'subject': subject,
            'body_html': body_html
        }
        
        # Save to file
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