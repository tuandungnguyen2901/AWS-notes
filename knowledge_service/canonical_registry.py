"""
Canonical Registry - Canonical entity names with descriptions and synonyms
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from .schema import EntityType
import logging

logger = logging.getLogger(__name__)


@dataclass
class CanonicalEntity:
    """Represents a canonical entity with its metadata"""
    name: str
    entity_type: EntityType
    description: Optional[str] = None
    synonyms: List[str] = None
    aliases: List[str] = None
    
    def __post_init__(self):
        if self.synonyms is None:
            self.synonyms = []
        if self.aliases is None:
            self.aliases = []
    
    def all_variants(self) -> Set[str]:
        """Get all name variants (name + synonyms + aliases)"""
        variants = {self.name.lower()}
        variants.update(s.lower() for s in self.synonyms)
        variants.update(a.lower() for a in self.aliases)
        return variants


class CanonicalRegistry:
    """Registry of canonical entities for normalization"""
    
    def __init__(self):
        self.services: Dict[str, CanonicalEntity] = {}
        self.components: Dict[str, CanonicalEntity] = {}
        self.patterns: Dict[str, CanonicalEntity] = {}
        self.pillars: Dict[str, CanonicalEntity] = {}
        self.best_practices: Dict[str, CanonicalEntity] = {}
        self.risks: Dict[str, CanonicalEntity] = {}
        self.mitigations: Dict[str, CanonicalEntity] = {}
        self.metrics: Dict[str, CanonicalEntity] = {}
        self.roles: Dict[str, CanonicalEntity] = {}
        
        # Reverse lookup: variant -> canonical name
        self.variant_to_canonical: Dict[str, str] = {}
        
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize the canonical registry with AWS services, patterns, pillars, etc."""
        
        # Well-Architected Pillars
        self.pillars["Operational Excellence"] = CanonicalEntity(
            name="Operational Excellence",
            entity_type=EntityType.PILLAR,
            description="The operational excellence pillar includes the ability to run and monitor systems to deliver business value and to continually improve supporting processes and procedures.",
            synonyms=["Ops Excellence", "Operational Excellence Pillar"]
        )
        
        self.pillars["Security"] = CanonicalEntity(
            name="Security",
            entity_type=EntityType.PILLAR,
            description="The security pillar includes the ability to protect information, systems, and assets while delivering business value through risk assessments and mitigation strategies.",
            synonyms=["Security Pillar"]
        )
        
        self.pillars["Reliability"] = CanonicalEntity(
            name="Reliability",
            entity_type=EntityType.PILLAR,
            description="The reliability pillar includes the ability of a workload to perform its intended function correctly and consistently when it's expected to.",
            synonyms=["Reliability Pillar"]
        )
        
        self.pillars["Performance Efficiency"] = CanonicalEntity(
            name="Performance Efficiency",
            entity_type=EntityType.PILLAR,
            description="The performance efficiency pillar includes the ability to use computing resources efficiently to meet system requirements, and to maintain that efficiency as demand changes and technologies evolve.",
            synonyms=["Performance Efficiency Pillar", "Performance"]
        )
        
        self.pillars["Cost Optimization"] = CanonicalEntity(
            name="Cost Optimization",
            entity_type=EntityType.PILLAR,
            description="The cost optimization pillar includes the ability to run systems to deliver business value at the lowest price point.",
            synonyms=["Cost Optimization Pillar", "Cost"]
        )
        
        # Common Patterns
        self.patterns["Multi-AZ Deployment"] = CanonicalEntity(
            name="Multi-AZ Deployment",
            entity_type=EntityType.PATTERN,
            description="Deploying resources across multiple Availability Zones for high availability",
            synonyms=["Multi-AZ", "Multi Availability Zone", "Multi-AZ Pattern"]
        )
        
        self.patterns["Blue-Green Deployment"] = CanonicalEntity(
            name="Blue-Green Deployment",
            entity_type=EntityType.PATTERN,
            description="Deployment pattern where two identical production environments are maintained",
            synonyms=["Blue Green", "Blue/Green"]
        )
        
        self.patterns["Canary Deployment"] = CanonicalEntity(
            name="Canary Deployment",
            entity_type=EntityType.PATTERN,
            description="Deployment pattern where new version is gradually rolled out to a subset of users",
            synonyms=["Canary"]
        )
        
        self.patterns["Hub and Spoke"] = CanonicalEntity(
            name="Hub and Spoke",
            entity_type=EntityType.PATTERN,
            description="Network topology where a central hub connects to multiple spoke networks",
            synonyms=["Hub-and-Spoke", "Hub & Spoke"]
        )
        
        self.patterns["Serverless"] = CanonicalEntity(
            name="Serverless",
            entity_type=EntityType.PATTERN,
            description="Architecture pattern using managed services that automatically scale",
            synonyms=["Serverless Architecture"]
        )
        
        # AWS Services (expanded from concept_extractor)
        aws_services_data = {
            "Amazon EC2": {
                "description": "Elastic Compute Cloud - resizable compute capacity in the cloud",
                "synonyms": ["EC2", "Elastic Compute Cloud", "EC2 instance", "AWS EC2"]
            },
            "Amazon S3": {
                "description": "Simple Storage Service - object storage service",
                "synonyms": ["S3", "Simple Storage Service", "S3 bucket", "AWS S3"]
            },
            "Amazon DynamoDB": {
                "description": "NoSQL database service",
                "synonyms": ["DynamoDB", "AWS DynamoDB"]
            },
            "Amazon RDS": {
                "description": "Relational Database Service - managed relational database",
                "synonyms": ["RDS", "Relational Database Service", "AWS RDS"]
            },
            "AWS Lambda": {
                "description": "Serverless compute service",
                "synonyms": ["Lambda", "Lambda function", "AWS Lambda"]
            },
            "Amazon VPC": {
                "description": "Virtual Private Cloud - isolated network environment",
                "synonyms": ["VPC", "Virtual Private Cloud", "AWS VPC"]
            },
            "AWS Transit Gateway": {
                "description": "Network transit hub for connecting VPCs",
                "synonyms": ["TGW", "Transit Gateway", "AWS Transit Gateway"]
            },
            "AWS Direct Connect": {
                "description": "Dedicated network connection to AWS",
                "synonyms": ["DX", "DirectConnect", "AWS Direct Connect"]
            },
            "AWS Site-to-Site VPN": {
                "description": "IPSec VPN connection between networks",
                "synonyms": ["VPN", "IPSec VPN", "Site-to-Site", "AWS VPN"]
            },
            "AWS Client VPN": {
                "description": "Managed client-based VPN service",
                "synonyms": ["Client VPN", "AWS Client VPN"]
            },
            "AWS IAM": {
                "description": "Identity and Access Management",
                "synonyms": ["IAM", "Identity and Access Management", "AWS IAM"]
            },
            "AWS CloudWatch": {
                "description": "Monitoring and observability service",
                "synonyms": ["CloudWatch", "AWS CloudWatch"]
            },
            "AWS CloudTrail": {
                "description": "Service for logging API calls",
                "synonyms": ["CloudTrail", "AWS CloudTrail"]
            },
            "Amazon Route 53": {
                "description": "DNS and domain name service",
                "synonyms": ["Route53", "Route 53", "R53", "AWS Route 53"]
            },
            "Elastic Load Balancing": {
                "description": "Load balancing service",
                "synonyms": ["ELB", "ALB", "NLB", "CLB", "Load Balancer", "AWS ELB"]
            },
            "AWS PrivateLink": {
                "description": "Private connectivity to AWS services",
                "synonyms": ["PrivateLink", "VPC Endpoint", "AWS PrivateLink"]
            },
            "Amazon CloudFront": {
                "description": "Content delivery network",
                "synonyms": ["CloudFront", "CDN", "AWS CloudFront"]
            },
            "AWS EKS": {
                "description": "Elastic Kubernetes Service",
                "synonyms": ["EKS", "Elastic Kubernetes Service", "AWS EKS"]
            },
            "Amazon SNS": {
                "description": "Simple Notification Service",
                "synonyms": ["SNS", "AWS SNS"]
            },
            "Amazon SQS": {
                "description": "Simple Queue Service",
                "synonyms": ["SQS", "AWS SQS"]
            },
            "Amazon Kinesis": {
                "description": "Streaming data service",
                "synonyms": ["Kinesis", "AWS Kinesis"]
            },
            "AWS KMS": {
                "description": "Key Management Service",
                "synonyms": ["KMS", "Key Management Service", "AWS KMS"]
            },
            "AWS Organizations": {
                "description": "Account management and governance",
                "synonyms": ["Organizations", "AWS Organizations"]
            },
            "AWS Control Tower": {
                "description": "Multi-account governance service",
                "synonyms": ["Control Tower", "AWS Control Tower"]
            },
            "AWS Backup": {
                "description": "Centralized backup service",
                "synonyms": ["Backup", "AWS Backup"]
            },
            "AWS Elastic Disaster Recovery": {
                "description": "Disaster recovery service",
                "synonyms": ["DRS", "Elastic Disaster Recovery", "AWS DRS"]
            },
            "Amazon GuardDuty": {
                "description": "Threat detection service",
                "synonyms": ["GuardDuty", "AWS GuardDuty"]
            },
            "AWS WAF": {
                "description": "Web Application Firewall",
                "synonyms": ["WAF", "Web Application Firewall", "AWS WAF"]
            },
            "AWS Shield": {
                "description": "DDoS protection service",
                "synonyms": ["Shield", "AWS Shield"]
            },
            "AWS Certificate Manager": {
                "description": "SSL/TLS certificate management",
                "synonyms": ["ACM", "Certificate Manager", "AWS ACM"]
            },
            "AWS IAM Identity Center": {
                "description": "Single sign-on and identity management",
                "synonyms": ["IAM Identity Center", "SSO", "AWS SSO"]
            },
            "Amazon Cognito": {
                "description": "User identity and access management",
                "synonyms": ["Cognito", "AWS Cognito"]
            }
        }
        
        for service_name, data in aws_services_data.items():
            self.services[service_name] = CanonicalEntity(
                name=service_name,
                entity_type=EntityType.SERVICE,
                description=data["description"],
                synonyms=data["synonyms"]
            )
        
        # Common Components
        components_data = {
            "EBS Volume": {
                "description": "Elastic Block Store volume",
                "synonyms": ["EBS", "Volume"]
            },
            "VPC Subnet": {
                "description": "Subnet within a VPC",
                "synonyms": ["Subnet", "VPC Subnet"]
            },
            "Security Group": {
                "description": "Virtual firewall for EC2 instances",
                "synonyms": ["SG", "Security Group"]
            },
            "Network ACL": {
                "description": "Network access control list",
                "synonyms": ["NACL", "Network ACL"]
            },
            "NAT Gateway": {
                "description": "Network Address Translation gateway",
                "synonyms": ["NAT", "NATGW"]
            },
            "Internet Gateway": {
                "description": "Gateway for internet access",
                "synonyms": ["IGW", "Internet Gateway"]
            },
            "Route Table": {
                "description": "Routing table for network traffic",
                "synonyms": ["Route Table"]
            },
            "Elastic IP": {
                "description": "Static IPv4 address",
                "synonyms": ["EIP", "Elastic IP"]
            },
            "VPC Endpoint": {
                "description": "Private connection to AWS services",
                "synonyms": ["Endpoint", "VPC Endpoint"]
            }
        }
        
        for component_name, data in components_data.items():
            self.components[component_name] = CanonicalEntity(
                name=component_name,
                entity_type=EntityType.COMPONENT,
                description=data["description"],
                synonyms=data["synonyms"]
            )
        
        # Build reverse lookup
        self._build_variant_lookup()
    
    def _build_variant_lookup(self):
        """Build reverse lookup from variants to canonical names"""
        registries = [
            (self.services, EntityType.SERVICE),
            (self.components, EntityType.COMPONENT),
            (self.patterns, EntityType.PATTERN),
            (self.pillars, EntityType.PILLAR),
            (self.best_practices, EntityType.BEST_PRACTICE),
            (self.risks, EntityType.RISK),
            (self.mitigations, EntityType.MITIGATION),
            (self.metrics, EntityType.METRIC),
            (self.roles, EntityType.ROLE)
        ]
        
        for registry, entity_type in registries:
            for canonical_name, entity in registry.items():
                for variant in entity.all_variants():
                    self.variant_to_canonical[variant] = canonical_name
    
    def find_canonical(self, name: str, entity_type: Optional[EntityType] = None) -> Optional[str]:
        """
        Find canonical name for a given variant
        
        Args:
            name: Variant name to look up
            entity_type: Optional entity type to filter by
            
        Returns:
            Canonical name if found, None otherwise
        """
        name_lower = name.lower().strip()
        
        # Direct lookup
        if name_lower in self.variant_to_canonical:
            canonical = self.variant_to_canonical[name_lower]
            
            # Filter by entity type if specified
            if entity_type:
                if entity_type == EntityType.SERVICE and canonical in self.services:
                    return canonical
                elif entity_type == EntityType.COMPONENT and canonical in self.components:
                    return canonical
                elif entity_type == EntityType.PATTERN and canonical in self.patterns:
                    return canonical
                elif entity_type == EntityType.PILLAR and canonical in self.pillars:
                    return canonical
                elif entity_type == EntityType.BEST_PRACTICE and canonical in self.best_practices:
                    return canonical
                elif entity_type == EntityType.RISK and canonical in self.risks:
                    return canonical
                elif entity_type == EntityType.MITIGATION and canonical in self.mitigations:
                    return canonical
                elif entity_type == EntityType.METRIC and canonical in self.metrics:
                    return canonical
                elif entity_type == EntityType.ROLE and canonical in self.roles:
                    return canonical
                return None
            
            return canonical
        
        return None
    
    def get_entity(self, canonical_name: str, entity_type: EntityType) -> Optional[CanonicalEntity]:
        """Get canonical entity by name and type"""
        registry_map = {
            EntityType.SERVICE: self.services,
            EntityType.COMPONENT: self.components,
            EntityType.PATTERN: self.patterns,
            EntityType.PILLAR: self.pillars,
            EntityType.BEST_PRACTICE: self.best_practices,
            EntityType.RISK: self.risks,
            EntityType.MITIGATION: self.mitigations,
            EntityType.METRIC: self.metrics,
            EntityType.ROLE: self.roles
        }
        
        registry = registry_map.get(entity_type)
        if registry:
            return registry.get(canonical_name)
        return None
    
    def add_entity(self, entity: CanonicalEntity):
        """Add a new canonical entity to the registry"""
        registry_map = {
            EntityType.SERVICE: self.services,
            EntityType.COMPONENT: self.components,
            EntityType.PATTERN: self.patterns,
            EntityType.PILLAR: self.pillars,
            EntityType.BEST_PRACTICE: self.best_practices,
            EntityType.RISK: self.risks,
            EntityType.MITIGATION: self.mitigations,
            EntityType.METRIC: self.metrics,
            EntityType.ROLE: self.roles
        }
        
        registry = registry_map.get(entity.entity_type)
        if registry:
            registry[entity.name] = entity
            # Rebuild variant lookup
            self._build_variant_lookup()


# Global registry instance
_registry_instance: Optional[CanonicalRegistry] = None


def get_registry() -> CanonicalRegistry:
    """Get the global canonical registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = CanonicalRegistry()
    return _registry_instance
