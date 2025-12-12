"""
Markdown Parser - Parse markdown files and extract structured content
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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


@dataclass
class Chunk:
    """Represents a chunk of text for processing"""
    text: str
    source: str  # Document file path
    section: str  # Section heading
    heading_path: List[str]  # Full path of headings (H1 -> H2 -> H3)
    url: Optional[str] = None
    metadata: Optional[Dict] = None
    start_line: int = 0
    end_line: int = 0
    token_count: int = 0


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
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters)
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        # This is a simple heuristic; for more accuracy, use tiktoken or similar
        return len(text) // 4
    
    def _remove_boilerplate(self, text: str) -> str:
        """
        Remove boilerplate content (headers, footers, navigation)
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []
        skip_patterns = [
            r'^---$',  # YAML frontmatter delimiters
            r'^\[.*\]\(.*\)$',  # Standalone markdown links
            r'^Table of Contents',  # TOC headers
            r'^Navigation',  # Navigation sections
        ]
        
        in_code_block = False
        for line in lines:
            stripped = line.strip()
            
            # Track code blocks
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Skip code blocks
            if in_code_block:
                continue
            
            # Skip empty lines at start/end
            if not stripped:
                if cleaned_lines:  # Keep internal empty lines
                    cleaned_lines.append('')
                continue
            
            # Skip boilerplate patterns
            skip = False
            for pattern in skip_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    skip = True
                    break
            
            if not skip:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def chunk_document(self, document: Document, min_tokens: int = 1000, max_tokens: int = 3000, url_base: Optional[str] = None) -> List[Chunk]:
        """
        Chunk a document into smaller pieces for processing
        
        Args:
            document: Document to chunk
            min_tokens: Minimum tokens per chunk (default: 1000)
            max_tokens: Maximum tokens per chunk (default: 3000)
            url_base: Base URL for generating section URLs (optional)
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        content = self._remove_boilerplate(document.content)
        lines = content.split('\n')
        
        # Build heading hierarchy as we process
        heading_stack: List[tuple[int, str]] = []  # (level, heading)
        
        current_chunk_lines = []
        current_chunk_start = 0
        current_heading_path: List[str] = []
        current_section = document.title
        
        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if heading_match:
                level = len(heading_match.group(1))
                heading = heading_match.group(2).strip()
                
                # Update heading stack
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading))
                
                # Build heading path
                current_heading_path = [h[1] for h in heading_stack]
                current_section = heading
                
                # Check if we should finalize current chunk
                if current_chunk_lines:
                    chunk_text = '\n'.join(current_chunk_lines).strip()
                    token_count = self._estimate_tokens(chunk_text)
                    
                    if token_count >= min_tokens:
                        # Create chunk
                        url = self._generate_section_url(document.file_path, current_heading_path, url_base)
                        chunk = Chunk(
                            text=chunk_text,
                            source=document.file_path,
                            section=current_section,
                            heading_path=current_heading_path.copy(),
                            url=url,
                            metadata={
                                'title': document.title,
                                'created_at': document.created_at,
                                'section_level': level
                            },
                            start_line=current_chunk_start,
                            end_line=i - 1,
                            token_count=token_count
                        )
                        chunks.append(chunk)
                        current_chunk_lines = []
                        current_chunk_start = i
                
                # Add heading to new chunk
                current_chunk_lines.append(line)
            else:
                current_chunk_lines.append(line)
                
                # Check if chunk exceeds max_tokens
                chunk_text = '\n'.join(current_chunk_lines).strip()
                token_count = self._estimate_tokens(chunk_text)
                
                if token_count > max_tokens:
                    # Split chunk at sentence boundary if possible
                    # For now, just finalize current chunk
                    if len(current_chunk_lines) > 1:
                        # Remove last line and create chunk
                        last_line = current_chunk_lines.pop()
                        chunk_text = '\n'.join(current_chunk_lines).strip()
                        token_count = self._estimate_tokens(chunk_text)
                        
                        if token_count >= min_tokens:
                            url = self._generate_section_url(document.file_path, current_heading_path, url_base)
                            chunk = Chunk(
                                text=chunk_text,
                                source=document.file_path,
                                section=current_section,
                                heading_path=current_heading_path.copy(),
                                url=url,
                                metadata={
                                    'title': document.title,
                                    'created_at': document.created_at
                                },
                                start_line=current_chunk_start,
                                end_line=i - 1,
                                token_count=token_count
                            )
                            chunks.append(chunk)
                            current_chunk_start = i
                            current_chunk_lines = [last_line]
        
        # Add final chunk
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines).strip()
            token_count = self._estimate_tokens(chunk_text)
            
            if token_count >= min_tokens or len(chunks) == 0:  # Always include last chunk if it's the only one
                url = self._generate_section_url(document.file_path, current_heading_path, url_base)
                chunk = Chunk(
                    text=chunk_text,
                    source=document.file_path,
                    section=current_section,
                    heading_path=current_heading_path.copy(),
                    url=url,
                    metadata={
                        'title': document.title,
                        'created_at': document.created_at
                    },
                    start_line=current_chunk_start,
                    end_line=len(lines) - 1,
                    token_count=token_count
                )
                chunks.append(chunk)
        
        logger.debug(f"Chunked document '{document.title}' into {len(chunks)} chunks")
        return chunks
    
    def _generate_section_url(self, file_path: str, heading_path: List[str], url_base: Optional[str] = None) -> Optional[str]:
        """
        Generate URL for a section
        
        Args:
            file_path: Document file path
            heading_path: List of headings (H1 -> H2 -> H3)
            url_base: Base URL (optional)
            
        Returns:
            URL string or None
        """
        if not url_base:
            return None
        
        # Create anchor from heading path
        anchor = '#'.join(h.lower().replace(' ', '-') for h in heading_path)
        file_name = Path(file_path).stem
        
        return f"{url_base}/{file_name}#{anchor}"
