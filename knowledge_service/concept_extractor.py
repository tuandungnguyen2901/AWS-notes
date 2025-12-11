"""
Improved AWS Concept Extractor — extracts AWS services, technologies,
network concepts, and relationships into graph-friendly structures.
"""

import re
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class Concept:
    name: str
    type: str  # service, technology, concept, aws_feature, network
    description: Optional[str] = None
    canonical: Optional[str] = None


class ConceptExtractor:
    def __init__(self):
        # =====================================================================
        # 1. Canonical AWS Service Dictionary (major services + abbreviations)
        # =====================================================================
        self.aws_services = {
            "Amazon EC2": ["EC2", "Elastic Compute Cloud", "EC2 instance"],
            "Amazon S3": ["S3", "Simple Storage Service", "S3 bucket"],
            "Amazon DynamoDB": ["DynamoDB"],
            "Amazon RDS": ["RDS", "Relational Database Service"],
            "AWS Lambda": ["Lambda", "Lambda function"],
            "Amazon VPC": ["VPC", "Virtual Private Cloud"],
            "AWS Transit Gateway": ["TGW", "Transit Gateway"],
            "AWS Direct Connect": ["DX", "DirectConnect"],
            "AWS Site-to-Site VPN": ["VPN", "IPSec VPN", "Site-to-Site"],
            "AWS Client VPN": ["Client VPN"],
            "AWS IAM": ["IAM", "Identity and Access Management"],
            "AWS CloudWatch": ["CloudWatch"],
            "AWS CloudTrail": ["CloudTrail"],
            "Amazon Route 53": ["Route53", "Route 53", "R53"],
            "Elastic Load Balancing": ["ELB", "ALB", "NLB", "CLB"],
            "AWS PrivateLink": ["PrivateLink", "VPC Endpoint"],
            "Amazon CloudFront": ["CloudFront", "CDN"],
            "AWS EKS": ["EKS", "Elastic Kubernetes Service"],
            "Amazon SNS": ["SNS"],
            "Amazon SQS": ["SQS"],
            "Amazon Kinesis": ["Kinesis"],
        }
        # Flatten synonyms → canonical mapping
        self.syn_map = {}
        for canonical, synonyms in self.aws_services.items():
            for s in synonyms:
                self.syn_map[s.lower()] = canonical.lower()

        # =====================================================================
        # 2. Technology / Networking Keywords
        # =====================================================================
        self.tech_keywords = {
            "ENI": "Elastic Network Interface",
            "CIDR": "CIDR Block",
            "NAT Gateway": "NAT Gateway",
            "Internet Gateway": "Internet Gateway",
            "IGW": "Internet Gateway",
            "NATGW": "NAT Gateway",
            "Subnets": "Subnet",
            "Availability Zone": "AZ",
            "AZ": "Availability Zone",
            "VPC Peering": "VPC Peering",
            "BGP": "Border Gateway Protocol",
            "IPSec": "IPSec",
            "TCP": "TCP",
            "UDP": "UDP",
            "DNS": "DNS",
            "Egress-only Internet Gateway": "Egress-only IGW",
        }

        # =====================================================================
        # 3. AWS architecture concepts (not services)
        # =====================================================================
        self.architecture_terms = [
            r"Route Table",
            r"Security Group",
            r"Network ACL",
            r"Subnet",
            r"Public Subnet",
            r"Private Subnet",
            r"Elastic IP",
            r"VPC Endpoint",
            r"Gateway Endpoint",
            r"Interface Endpoint",
            r"Peering Connection",
            r"Transit Gateway Attachment",
            r"VPN Tunnel",
        ]

        # =====================================================================
        # 4. Relationship Patterns
        # =====================================================================
        self.relationship_patterns = [
            (r"(\b[\w\s]+\b)\s+connects to\s+(\b[\w\s]+\b)", "CONNECTS_TO"),
            (r"(\b[\w\s]+\b)\s+attaches to\s+(\b[\w\s]+\b)", "ATTACHES_TO"),
            (r"(\b[\w\s]+\b)\s+uses\s+(\b[\w\s]+\b)", "USES"),
            (r"(\b[\w\s]+\b)\s+is used for\s+(\b[\w\s]+\b)", "USED_FOR"),
            (r"(\b[\w\s]+\b)\s+peers with\s+(\b[\w\s]+\b)", "PEERS_WITH"),
            (r"(\b[\w\s]+\b)\s+routes traffic to\s+(\b[\w\s]+\b)", "ROUTES_TO"),
            (r"(\b[\w\s]+\b)\s+communicates with\s+(\b[\w\s]+\b)", "COMMUNICATES_WITH"),
        ]

    # =====================================================================
    #                MAIN EXTRACTION FLOW
    # =====================================================================
    def extract_concepts(self, text: str) -> List[Concept]:
        results: List[Concept] = []
        seen = set()

        # 1. Extract AWS services + synonyms
        for concept in self._extract_aws_services(text):
            if concept.canonical not in seen:
                results.append(concept)
                seen.add(concept.canonical)

        # 2. Extract technologies
        for concept in self._extract_technologies(text):
            if concept.name.lower() not in seen:
                results.append(concept)
                seen.add(concept.name.lower())

        # 3. Extract architecture terms
        for concept in self._extract_architecture_terms(text):
            if concept.name.lower() not in seen:
                results.append(concept)
                seen.add(concept.name.lower())
        return results

    # =====================================================================
    #                      AWS SERVICE EXTRACTION
    # =====================================================================
    def _extract_aws_services(self, text: str) -> List[Concept]:
        found = []
        for canonical, synonyms in self.aws_services.items():
            for synonym in synonyms + [canonical]:
                if re.search(rf"\b{re.escape(synonym)}\b", text, re.IGNORECASE):
                    found.append(
                        Concept(
                            name=canonical,
                            canonical=canonical.lower(),
                            type="service",
                            description=self._extract_context(text, synonym)
                        )
                    )
        return found

    # =====================================================================
    #                     TECHNOLOGY EXTRACTION
    # =====================================================================
    def _extract_technologies(self, text: str) -> List[Concept]:
        found = []
        for keyword, canonical in self.tech_keywords.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
                found.append(
                    Concept(
                        name=canonical,
                        type="technology",
                        canonical=canonical.lower(),
                        description=self._extract_context(text, keyword)
                    )
                )
        return found

    # =====================================================================
    #                     ARCHITECTURE TERMS
    # =====================================================================
    def _extract_architecture_terms(self, text: str) -> List[Concept]:
        found = []
        for pattern in self.architecture_terms:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                term = m.group(0)
                found.append(
                    Concept(
                        name=term,
                        canonical=term.lower(),
                        type="concept",
                        description=self._extract_context(text, term)
                    )
                )
        return found

    # =====================================================================
    #                     RELATIONSHIP EXTRACTION
    # =====================================================================
    def extract_relationships(self, text: str, concepts: List[Concept]) -> List[Tuple[str, str, str]]:
        relationships = []
        concept_names = {c.name.lower(): c.name for c in concepts}
        for pattern, rel_type in self.relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                a = m.group(1).strip()
                b = m.group(2).strip()
                a_norm = concept_names.get(a.lower())
                b_norm = concept_names.get(b.lower())

                if a_norm and b_norm and a_norm != b_norm:
                    relationships.append((a_norm, rel_type, b_norm))
        return relationships

    # =====================================================================
    #                     CONTEXT EXTRACTION
    # =====================================================================
    def _extract_context(self, text: str, term: str, window=120) -> Optional[str]:
        match = re.search(re.escape(term), text, re.IGNORECASE)
        if not match:
            return None
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        return re.sub(r"\s+", " ", text[start:end]).strip()
