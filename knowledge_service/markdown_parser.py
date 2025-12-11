"""
Markdown Parser - Parse markdown files and extract structured content
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Section:
    """Represents a section in a markdown document"""
    heading: str
    level: int
    content: str
    start_line: int
    end_line: int


@dataclass
class Document:
    """Represents a parsed markdown document"""
    title: str
    file_path: str
    content: str
    sections: List[Section]
    references: List[str]  # Links to other markdown files
    created_at: str


class MarkdownParser:
    """Parser for markdown files"""
    
    def __init__(self):
        self.markdown_link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def parse_file(self, file_path: str) -> Document:
        """
        Parse a markdown file
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Parsed Document object
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content, str(path))
    
    def parse_content(self, content: str, file_path: str) -> Document:
        """
        Parse markdown content
        
        Args:
            content: Markdown content string
            file_path: Path to the file (for reference)
            
        Returns:
            Parsed Document object
        """
        lines = content.split('\n')
        
        # Extract title (first H1 heading)
        title = self._extract_title(content)
        if not title:
            # Fallback to filename without extension
            title = Path(file_path).stem.replace('_', ' ').title()
        
        # Extract sections
        sections = self._extract_sections(content, lines)
        
        # Extract references (links to other markdown files)
        references = self._extract_references(content)
        
        # Get creation/modification time
        created_at = datetime.now().isoformat()
        
        return Document(
            title=title,
            file_path=file_path,
            content=content,
            sections=sections,
            references=references,
            created_at=created_at
        )
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from first H1 heading"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def _extract_sections(self, content: str, lines: List[str]) -> List[Section]:
        """Extract sections from markdown content"""
        sections = []
        current_section = None
        current_content = []
        current_start = 0
        
        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if heading_match:
                # Save previous section if exists
                if current_section:
                    sections.append(Section(
                        heading=current_section,
                        level=len(heading_match.group(1)),
                        content='\n'.join(current_content).strip(),
                        start_line=current_start,
                        end_line=i - 1
                    ))
                
                # Start new section
                current_section = heading_match.group(2).strip()
                current_content = []
                current_start = i
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append(Section(
                heading=current_section,
                level=1,  # Will be updated if we find the actual level
                content='\n'.join(current_content).strip(),
                start_line=current_start,
                end_line=len(lines) - 1
            ))
        
        # Fix section levels
        for i, section in enumerate(sections):
            if i > 0:
                # Find the heading level in the original content
                heading_line = lines[section.start_line]
                level_match = re.match(r'^(#{1,6})', heading_line)
                if level_match:
                    section.level = len(level_match.group(1))
        
        return sections
    
    def _extract_references(self, content: str) -> List[str]:
        """Extract references to other markdown files"""
        references = []
        matches = self.markdown_link_pattern.findall(content)
        
        for text, link in matches:
            # Check if it's a markdown file reference
            if link.endswith('.md') or link.startswith('./') or '/' in link:
                # Normalize the reference
                ref = link.replace('./', '').replace('.md', '')
                if ref not in references:
                    references.append(ref)
        
        return references
    
    def extract_first_line(self, content: str) -> Optional[str]:
        """
        Extract the first non-empty line of text (for kg-gen processing)
        
        Args:
            content: Markdown content string
            
        Returns:
            First non-empty line or None
        """
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            # Skip empty lines, markdown headers, and code blocks
            if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
                return stripped
        return None
