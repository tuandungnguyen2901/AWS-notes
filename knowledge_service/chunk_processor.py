"""
Chunk Processor - Format chunks for kg-gen input with metadata headers
"""

from typing import List
from .markdown_parser import Chunk
import logging

logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Process and format chunks for kg-gen extraction"""
    
    def __init__(self):
        pass
    
    def format_chunk(self, chunk: Chunk) -> str:
        """
        Format a chunk with metadata headers for kg-gen processing
        
        Args:
            chunk: Chunk to format
            
        Returns:
            Formatted chunk string
        """
        # Build heading path string
        heading_path_str = " > ".join(chunk.heading_path) if chunk.heading_path else chunk.section
        
        # Build formatted chunk
        lines = [
            f"---SOURCE: {chunk.source}---",
            f"Section: {heading_path_str}",
        ]
        
        if chunk.url:
            lines.append(f"URL: {chunk.url}")
        
        if chunk.metadata:
            if 'created_at' in chunk.metadata:
                lines.append(f"Date: {chunk.metadata['created_at']}")
        
        lines.append("")
        lines.append("Text:")
        lines.append("")
        lines.append(chunk.text)
        lines.append("")
        lines.append("---")
        
        return "\n".join(lines)
    
    def format_chunks(self, chunks: List[Chunk]) -> List[str]:
        """
        Format multiple chunks
        
        Args:
            chunks: List of chunks to format
            
        Returns:
            List of formatted chunk strings
        """
        return [self.format_chunk(chunk) for chunk in chunks]
    
    def get_chunk_metadata(self, chunk: Chunk) -> dict:
        """
        Extract metadata from chunk for evidence attribution
        
        Args:
            chunk: Chunk to extract metadata from
            
        Returns:
            Metadata dictionary
        """
        return {
            'source': chunk.source,
            'section': chunk.section,
            'heading_path': chunk.heading_path,
            'url': chunk.url,
            'start_line': chunk.start_line,
            'end_line': chunk.end_line,
            'token_count': chunk.token_count,
            **(chunk.metadata or {})
        }
