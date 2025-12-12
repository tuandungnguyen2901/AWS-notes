"""
Diff Extractor - Extract differences for incremental updates
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .schema import Triple
from .triple_store import TripleStore, StoredTriple

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of diff extraction"""
    new_triples: List[Triple]
    updated_triples: List[Tuple[Triple, StoredTriple]]  # (new_triple, existing_stored)
    conflicts: List[Dict]
    unchanged_count: int


class DiffExtractor:
    """Extract differences between new and existing triples"""
    
    def __init__(self, triple_store: TripleStore):
        """
        Initialize DiffExtractor
        
        Args:
            triple_store: TripleStore containing existing triples
        """
        self.triple_store = triple_store
    
    def extract_diff(self, new_triples: List[Triple]) -> DiffResult:
        """
        Extract differences between new triples and existing store
        
        Args:
            new_triples: List of new triples to compare
            
        Returns:
            DiffResult with new, updated, and conflicting triples
        """
        logger.info(f"Extracting diff for {len(new_triples)} new triples...")
        
        new_triples_list = []
        updated_triples_list = []
        conflicts = []
        unchanged_count = 0
        
        for triple in new_triples:
            # Check if triple exists
            existing = self.triple_store.find_triple(
                triple.subject,
                triple.relation.value,
                triple.object
            )
            
            if existing:
                # Triple exists - check if it's an update or conflict
                # For now, we'll treat all matches as updates (evidence appended)
                updated_triples_list.append((triple, existing))
                unchanged_count += 1
            else:
                # New triple
                new_triples_list.append(triple)
        
        result = DiffResult(
            new_triples=new_triples_list,
            updated_triples=updated_triples_list,
            conflicts=conflicts,
            unchanged_count=unchanged_count
        )
        
        logger.info(f"Diff extraction complete:")
        logger.info(f"  New triples: {len(result.new_triples)}")
        logger.info(f"  Updated triples: {len(result.updated_triples)}")
        logger.info(f"  Conflicts: {len(result.conflicts)}")
        logger.info(f"  Unchanged: {result.unchanged_count}")
        
        return result
    
    def apply_diff(self, diff_result: DiffResult) -> Dict:
        """
        Apply diff result to triple store
        
        Args:
            diff_result: Diff result to apply
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'added': 0,
            'updated': 0,
            'conflicts': len(diff_result.conflicts)
        }
        
        # Add new triples
        for triple in diff_result.new_triples:
            is_new, _ = self.triple_store.add_triple(triple)
            if is_new:
                stats['added'] += 1
        
        # Update existing triples (evidence already appended in add_triple)
        for triple, existing in diff_result.updated_triples:
            self.triple_store.add_triple(triple)
            stats['updated'] += 1
        
        return stats
    
    def generate_diff_report(self, diff_result: DiffResult) -> str:
        """
        Generate human-readable diff report
        
        Args:
            diff_result: Diff result to report on
            
        Returns:
            Report string
        """
        lines = [
            "=" * 60,
            "Diff Extraction Report",
            "=" * 60,
            f"New triples: {len(diff_result.new_triples)}",
            f"Updated triples: {len(diff_result.updated_triples)}",
            f"Conflicts: {len(diff_result.conflicts)}",
            f"Unchanged: {diff_result.unchanged_count}",
            ""
        ]
        
        if diff_result.new_triples:
            lines.append("New Triples:")
            for i, triple in enumerate(diff_result.new_triples[:10], 1):
                lines.append(f"  {i}. {triple.subject} --[{triple.relation.value}]--> {triple.object}")
            if len(diff_result.new_triples) > 10:
                lines.append(f"  ... and {len(diff_result.new_triples) - 10} more")
            lines.append("")
        
        if diff_result.conflicts:
            lines.append("Conflicts:")
            for i, conflict in enumerate(diff_result.conflicts[:10], 1):
                lines.append(f"  {i}. {conflict}")
            if len(diff_result.conflicts) > 10:
                lines.append(f"  ... and {len(diff_result.conflicts) - 10} more")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
