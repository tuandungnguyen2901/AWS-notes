"""
Configuration - Configurable thresholds and feature flags
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class ExtractionConfig:
    """Configuration for knowledge extraction pipeline"""
    
    # Schema mode
    schema_mode: str = "strict"  # "strict" or "legacy"
    
    # Feature flags
    enable_normalization: bool = True
    enable_validation: bool = True
    enable_clustering: bool = True
    enable_incremental: bool = False
    
    # Thresholds
    similarity_threshold: float = 0.75
    min_chunk_tokens: int = 1000
    max_chunk_tokens: int = 3000
    
    # Model selection
    embedding_model: str = "all-MiniLM-L6-v2"
    kg_gen_model: str = "google/gemini-2.0-flash-001"
    kg_gen_temperature: float = 0.0
    
    # Clustering
    use_hdbscan: bool = True
    min_cluster_size: int = 2
    
    # Validation
    min_evidence_words: int = 3
    
    @classmethod
    def from_env(cls) -> "ExtractionConfig":
        """Create config from environment variables"""
        return cls(
            schema_mode=os.getenv("KG_SCHEMA_MODE", "strict"),
            enable_normalization=os.getenv("KG_ENABLE_NORMALIZATION", "true").lower() == "true",
            enable_validation=os.getenv("KG_ENABLE_VALIDATION", "true").lower() == "true",
            enable_clustering=os.getenv("KG_ENABLE_CLUSTERING", "true").lower() == "true",
            enable_incremental=os.getenv("KG_ENABLE_INCREMENTAL", "false").lower() == "true",
            similarity_threshold=float(os.getenv("KG_SIMILARITY_THRESHOLD", "0.75")),
            min_chunk_tokens=int(os.getenv("KG_MIN_CHUNK_TOKENS", "1000")),
            max_chunk_tokens=int(os.getenv("KG_MAX_CHUNK_TOKENS", "3000")),
            embedding_model=os.getenv("KG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            kg_gen_model=os.getenv("KG_GEN_MODEL", "google/gemini-2.0-flash-001"),
            kg_gen_temperature=float(os.getenv("KG_GEN_TEMPERATURE", "0.0")),
            use_hdbscan=os.getenv("KG_USE_HDBSCAN", "true").lower() == "true",
            min_cluster_size=int(os.getenv("KG_MIN_CLUSTER_SIZE", "2")),
            min_evidence_words=int(os.getenv("KG_MIN_EVIDENCE_WORDS", "3"))
        )
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            "schema_mode": self.schema_mode,
            "enable_normalization": self.enable_normalization,
            "enable_validation": self.enable_validation,
            "enable_clustering": self.enable_clustering,
            "enable_incremental": self.enable_incremental,
            "similarity_threshold": self.similarity_threshold,
            "min_chunk_tokens": self.min_chunk_tokens,
            "max_chunk_tokens": self.max_chunk_tokens,
            "embedding_model": self.embedding_model,
            "kg_gen_model": self.kg_gen_model,
            "kg_gen_temperature": self.kg_gen_temperature,
            "use_hdbscan": self.use_hdbscan,
            "min_cluster_size": self.min_cluster_size,
            "min_evidence_words": self.min_evidence_words
        }


# Global config instance
_config_instance: Optional[ExtractionConfig] = None


def get_config() -> ExtractionConfig:
    """Get the global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ExtractionConfig.from_env()
    return _config_instance


def set_config(config: ExtractionConfig):
    """Set the global config instance"""
    global _config_instance
    _config_instance = config
