"""
Concept Extractor - Extract AWS services, concepts, and entities from text
"""

import re
from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Concept:
    """Represents an extracted concept"""
    name: str
    type: str  # 'service', 'feature', 'technology', 'concept'
    description: Optional[str] = None


class ConceptExtractor:
    """Extract concepts and entities from text"""
    
    def __init__(self):
        # AWS service patterns
        self.aws_service_patterns = [
            r'AWS\s+([A-Z][a-zA-Z\s]+?)(?:\s+\([^)]+\))?(?:\s+service)?',
            r'Amazon\s+([A-Z][a-zA-Z\s]+?)(?:\s+\([^)]+\))?(?:\s+service)?',
            r'([A-Z][a-zA-Z\s]+?)\s+\(AWS\)',
        ]
        
        # Common AWS services (for better matching)
        self.aws_services = {
            'AWS Client VPN', 'AWS Site-to-Site VPN', 'AWS Direct Connect',
            'AWS Transit Gateway', 'AWS Cloud WAN', 'AWS PrivateLink',
            'Amazon VPC', 'Amazon CloudFront', 'AWS Wavelength',
            'AWS Outposts', 'AWS Local Zones', 'Amazon Route 53',
            'AWS Elastic Disaster Recovery', 'AWS DRS', 'AWS Network Manager',
            'Amazon S3', 'Amazon DynamoDB', 'AWS IAM', 'Amazon EC2',
            'AWS CloudWatch', 'Amazon CloudFront', 'AWS Lambda',
            'Amazon EBS', 'AWS Elastic Load Balancing'
        }
        
        # Technology/feature patterns
        self.technology_patterns = [
            r'IPSec',
            r'VPN',
            r'VPC',
            r'VIF',
            r'ENI',
            r'CDN',
            r'SD-WAN',
            r'IPv4',
            r'IPv6',
            r'TCP',
            r'OpenVPN',
            r'DNS',
            r'PoP',
            r'CNE',
            r'TGW',
            r'DX',
        ]
    
    def extract_concepts(self, text: str) -> List[Concept]:
        """
        Extract concepts from text
        
        Args:
            text: Text to extract concepts from
            
        Returns:
            List of Concept objects
        """
        concepts = []
        seen = set()
        
        # Extract AWS services
        aws_concepts = self._extract_aws_services(text)
        for concept in aws_concepts:
            if concept.name.lower() not in seen:
                concepts.append(concept)
                seen.add(concept.name.lower())
        
        # Extract technologies/features
        tech_concepts = self._extract_technologies(text)
        for concept in tech_concepts:
            if concept.name.lower() not in seen:
                concepts.append(concept)
                seen.add(concept.name.lower())
        
        # Extract key terms
        term_concepts = self._extract_key_terms(text)
        for concept in term_concepts:
            if concept.name.lower() not in seen:
                concepts.append(concept)
                seen.add(concept.name.lower())
        
        return concepts
    
    def _extract_aws_services(self, text: str) -> List[Concept]:
        """Extract AWS service names"""
        concepts = []
        
        # Check for known AWS services
        for service in self.aws_services:
            pattern = re.escape(service)
            if re.search(pattern, text, re.IGNORECASE):
                concepts.append(Concept(
                    name=service,
                    type='service',
                    description=self._extract_context(text, service)
                ))
        
        # Extract using patterns
        for pattern in self.aws_service_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                service_name = match.group(1).strip()
                # Clean up common suffixes
                service_name = re.sub(r'\s+service$', '', service_name, flags=re.IGNORECASE)
                if len(service_name) > 2 and service_name not in [c.name for c in concepts]:
                    concepts.append(Concept(
                        name=service_name,
                        type='service',
                        description=self._extract_context(text, service_name)
                    ))
        
        return concepts
    
    def _extract_technologies(self, text: str) -> List[Concept]:
        """Extract technology and feature names"""
        concepts = []
        
        for tech in self.technology_patterns:
            if re.search(r'\b' + tech + r'\b', text, re.IGNORECASE):
                full_name = self._get_full_name(tech)
                concepts.append(Concept(
                    name=full_name,
                    type='technology',
                    description=self._extract_context(text, tech)
                ))
        
        return concepts
    
    def _extract_key_terms(self, text: str) -> List[Concept]:
        """Extract key technical terms"""
        concepts = []
        
        # Patterns for important terms
        key_term_patterns = [
            r'Availability Zone[s]?',
            r'Region[s]?',
            r'Virtual Private Cloud',
            r'Customer Gateway',
            r'Virtual Private Gateway',
            r'Route Table',
            r'Elastic Network Interface',
            r'Core Network Edge',
            r'Transit Virtual Interface',
            r'Private Virtual Interface',
            r'Public Virtual Interface',
        ]
        
        for pattern in key_term_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                term = match.group(0)
                if term.lower() not in [c.name.lower() for c in concepts]:
                    concepts.append(Concept(
                        name=term,
                        type='concept',
                        description=self._extract_context(text, term)
                    ))
        
        return concepts
    
    def _extract_context(self, text: str, term: str, context_length: int = 100) -> Optional[str]:
        """Extract context around a term"""
        pattern = re.escape(term)
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - context_length)
            end = min(len(text), match.end() + context_length)
            context = text[start:end].strip()
            # Clean up context
            context = re.sub(r'\s+', ' ', context)
            return context
        return None
    
    def _get_full_name(self, abbreviation: str) -> str:
        """Get full name for abbreviations"""
        abbreviations = {
            'IPSec': 'IPSec',
            'VPN': 'Virtual Private Network',
            'VPC': 'Virtual Private Cloud',
            'VIF': 'Virtual Interface',
            'ENI': 'Elastic Network Interface',
            'CDN': 'Content Delivery Network',
            'SD-WAN': 'Software-Defined Wide Area Network',
            'IPv4': 'Internet Protocol version 4',
            'IPv6': 'Internet Protocol version 6',
            'TCP': 'Transmission Control Protocol',
            'OpenVPN': 'OpenVPN',
            'DNS': 'Domain Name System',
            'PoP': 'Point of Presence',
            'CNE': 'Core Network Edge',
            'TGW': 'Transit Gateway',
            'DX': 'Direct Connect',
        }
        return abbreviations.get(abbreviation, abbreviation)
    
    def extract_relationships(self, text: str, concepts: List[Concept]) -> List[Tuple[str, str, str]]:
        """
        Extract relationships between concepts
        
        Args:
            text: Text to analyze
            concepts: List of extracted concepts
            
        Returns:
            List of (source, relationship_type, target) tuples
        """
        relationships = []
        
        # Relationship patterns
        relationship_patterns = [
            (r'(\w+)\s+uses\s+(\w+)', 'USES'),
            (r'(\w+)\s+connects\s+to\s+(\w+)', 'CONNECTS_TO'),
            (r'(\w+)\s+enables\s+(\w+)', 'ENABLES'),
            (r'(\w+)\s+with\s+(\w+)', 'WORKS_WITH'),
            (r'(\w+)\s+via\s+(\w+)', 'VIA'),
        ]
        
        concept_names = {c.name.lower(): c.name for c in concepts}
        
        for pattern, rel_type in relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source = match.group(1)
                target = match.group(2)
                
                # Check if both are concepts
                source_name = concept_names.get(source.lower())
                target_name = concept_names.get(target.lower())
                
                if source_name and target_name and source_name != target_name:
                    relationships.append((source_name, rel_type, target_name))
        
        return relationships
