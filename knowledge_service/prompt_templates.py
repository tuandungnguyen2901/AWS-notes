"""
Prompt Templates - Strict schema-driven prompt templates for kg-gen
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """Manage prompt templates for kg-gen extraction"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize prompt template manager
        
        Args:
            template_dir: Directory containing prompt templates (default: prompts/ in project root)
        """
        if template_dir is None:
            # Default to prompts/ directory in project root
            project_root = Path(__file__).parent.parent
            template_dir = str(project_root / "prompts")
        
        self.template_dir = Path(template_dir)
        self._templates: dict = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load prompt templates from files"""
        if not self.template_dir.exists():
            logger.warning(f"Template directory not found: {self.template_dir}")
            return
        
        # Load wa_prompt.txt (Well-Architected prompt)
        wa_prompt_path = self.template_dir / "wa_prompt.txt"
        if wa_prompt_path.exists():
            with open(wa_prompt_path, 'r', encoding='utf-8') as f:
                self._templates['well_architected'] = f.read()
            logger.info(f"Loaded prompt template: well_architected")
        else:
            logger.warning(f"Template file not found: {wa_prompt_path}")
            # Use default template
            self._templates['well_architected'] = self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Get default prompt template if file not found"""
        return """You are an extractor that outputs only JSON triples following this schema: (subject, subject_type, relation, object, object_type, evidence, inferred?, source).

Allowed subject/object types: Service, Component, Pattern, Pillar, BestPractice, Risk, Mitigation, Metric, Role.

Allowed relations: uses, implements, addresses, recommended_by, affects, depends_on, violates, example_of.

Rules:

1) Only output triples that comply with the allowed types for subject and object for the chosen relation.

2) Provide a short evidence text (one sentence) from the input text for each triple.

3) If the relation is not explicitly written, set inferred=true and add a one-sentence justification.

4) Do not invent new types or relation labels.

5) Canonicalize known AWS services (e.g., "S3" -> "Amazon S3", "EC2" -> "Amazon EC2").

6) Output a JSON array of triples.

Now extract triples from the following text:

"""
    
    def get_template(self, template_name: str = 'well_architected') -> str:
        """
        Get a prompt template
        
        Args:
            template_name: Name of the template (default: 'well_architected')
            
        Returns:
            Template string
        """
        return self._templates.get(template_name, self._get_default_template())
    
    def build_prompt(self, chunk_text: str, source_info: Optional[dict] = None, template_name: str = 'well_architected') -> str:
        """
        Build a complete prompt with context
        
        Args:
            chunk_text: Text chunk to extract from
            source_info: Optional source information (source, section, url, etc.)
            template_name: Template to use (default: 'well_architected')
            
        Returns:
            Complete prompt string
        """
        template = self.get_template(template_name)
        
        # Add source context if provided
        if source_info:
            context_lines = []
            if 'source' in source_info:
                context_lines.append(f"Source: {source_info['source']}")
            if 'section' in source_info:
                context_lines.append(f"Section: {source_info['section']}")
            if 'url' in source_info and source_info['url']:
                context_lines.append(f"URL: {source_info['url']}")
            
            if context_lines:
                context = "\n".join(context_lines) + "\n\n"
                template = template + context
        
        # Append chunk text
        prompt = template + chunk_text
        
        return prompt
    
    def add_template(self, name: str, template: str):
        """
        Add or update a template
        
        Args:
            name: Template name
            template: Template content
        """
        self._templates[name] = template
        logger.info(f"Added/updated template: {name}")


# Global template manager instance
_template_manager: Optional[PromptTemplateManager] = None


def get_template_manager() -> PromptTemplateManager:
    """Get the global prompt template manager instance"""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager()
    return _template_manager
