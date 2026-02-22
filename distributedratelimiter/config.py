"""
Configuration management for distributed rate limiter.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class RateLimitAlgorithm(str, Enum):
    """Supported rate limiting algorithms."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW_LOG = "sliding_window_log"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    connection_pool_size: int = 10
    timeout: int = 5
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RedisConfig":
        """Create config from dictionary."""
        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 6379),
            db=data.get("db", 0),
            password=data.get("password"),
            ssl=data.get("ssl", False),
            connection_pool_size=data.get("connection_pool_size", 10),
            timeout=data.get("timeout", 5)
        )
    
    def to_url(self) -> str:
        """Convert to Redis URL."""
        if self.password:
            auth = f":{self.password}@"
        else:
            auth = ""
        
        protocol = "rediss" if self.ssl else "redis"
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class RateLimitRule:
    """Single rate limit rule."""
    path: str
    methods: List[str]
    limit: int
    window: float
    algorithm: str = "token_bucket"
    identifier: str = "client_ip"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RateLimitRule":
        """Create rule from dictionary."""
        return cls(
            path=data["path"],
            methods=data.get("methods", ["GET"]),
            limit=data["limit"],
            window=data["window"],
            algorithm=data.get("algorithm", "token_bucket"),
            identifier=data.get("identifier", "client_ip")
        )


@dataclass
class MiddlewareConfig:
    """Middleware configuration."""
    enabled: bool = True
    header_prefix: str = "X-RateLimit"
    include_stats_in_response: bool = True
    skip_paths: List[str] = field(default_factory=list)
    default_rule: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MiddlewareConfig":
        """Create config from dictionary."""
        default_rule = data.get("default_rule")
        if default_rule and isinstance(default_rule, dict):
            default_rule = RateLimitRule.from_dict(default_rule).__dict__
        
        return cls(
            enabled=data.get("enabled", True),
            header_prefix=data.get("header_prefix", "X-RateLimit"),
            include_stats_in_response=data.get("include_stats_in_response", True),
            skip_paths=data.get("skip_paths", []),
            default_rule=default_rule
        )


@dataclass
class FallbackConfig:
    """Fallback configuration."""
    enabled: bool = True
    algorithm: str = "token_bucket"
    max_requests: int = 100
    window: float = 60.0
    recovery_threshold: int = 10
    recovery_window: float = 30.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FallbackConfig":
        """Create config from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            algorithm=data.get("algorithm", "token_bucket"),
            max_requests=data.get("max_requests", 100),
            window=data.get("window", 60.0),
            recovery_threshold=data.get("recovery_threshold", 10),
            recovery_window=data.get("recovery_window", 30.0)
        )


@dataclass
class Config:
    """Main configuration."""
    redis: Optional[RedisConfig] = None
    rules: List[RateLimitRule] = field(default_factory=list)
    middleware: MiddlewareConfig = field(default_factory=MiddlewareConfig)
    fallback: FallbackConfig = field(default_factory=FallbackConfig)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        redis_data = data.get("redis")
        redis_config = RedisConfig.from_dict(redis_data) if redis_data else None
        
        rules_data = data.get("rules", [])
        rules = [RateLimitRule.from_dict(rule) for rule in rules_data]
        
        return cls(
            redis=redis_config,
            rules=rules,
            middleware=MiddlewareConfig.from_dict(data.get("middleware", {})),
            fallback=FallbackConfig.from_dict(data.get("fallback", {}))
        )
    
    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data or {})
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        data = {
            "redis": {
                "host": os.getenv("RATELIMIT_REDIS_HOST", "localhost"),
                "port": int(os.getenv("RATELIMIT_REDIS_PORT", "6379")),
                "db": int(os.getenv("RATELIMIT_REDIS_DB", "0")),
                "password": os.getenv("RATELIMIT_REDIS_PASSWORD"),
                "ssl": os.getenv("RATELIMIT_REDIS_SSL", "false").lower() == "true",
                "connection_pool_size": int(os.getenv("RATELIMIT_POOL_SIZE", "10")),
                "timeout": int(os.getenv("RATELIMIT_TIMEOUT", "5"))
            },
            "rules": [],
            "middleware": {
                "enabled": os.getenv("RATELIMIT_ENABLED", "true").lower() == "true",
                "header_prefix": os.getenv("RATELIMIT_HEADER_PREFIX", "X-RateLimit"),
                "include_stats_in_response": os.getenv("RATELIMIT_INCLUDE_STATS", "true").lower() == "true",
                "skip_paths": []
            },
            "fallback": {
                "enabled": os.getenv("RATELIMIT_FALLBACK_ENABLED", "true").lower() == "true",
                "algorithm": os.getenv("RATELIMIT_FALLBACK_ALGORITHM", "token_bucket"),
                "max_requests": int(os.getenv("RATELIMIT_FALLBACK_MAX", "100")),
                "window": float(os.getenv("RATELIMIT_FALLBACK_WINDOW", "60.0"))
            }
        }
        
        # Parse rules from environment (format: RULE_1_PATH=/api, RULE_1_LIMIT=100, etc.)
        rules = []
        rule_idx = 1
        while os.getenv(f"RULE_{rule_idx}_PATH"):
            rule = {
                "path": os.getenv(f"RULE_{rule_idx}_PATH"),
                "limit": int(os.getenv(f"RULE_{rule_idx}_LIMIT", "100")),
                "window": float(os.getenv(f"RULE_{rule_idx}_WINDOW", "60.0")),
                "methods": (os.getenv(f"RULE_{rule_idx}_METHODS", "GET").split(",") if os.getenv(f"RULE_{rule_idx}_METHODS") else ["GET"]),
                "algorithm": os.getenv(f"RULE_{rule_idx}_ALGORITHM", "token_bucket"),
                "identifier": os.getenv(f"RULE_{rule_idx}_IDENTIFIER", "client_ip")
            }
            rules.append(RateLimitRule.from_dict(rule))
            rule_idx += 1
        
        data["rules"] = rules
        data["middleware"]["skip_paths"] = (
            os.getenv("RATELIMIT_SKIP_PATHS", "").split(",")
            if os.getenv("RATELIMIT_SKIP_PATHS")
            else []
        )
        
        return cls.from_dict(data)


# Default configuration
DEFAULT_CONFIG = Config(
    redis=RedisConfig(),
    rules=[],
    middleware=MiddlewareConfig(),
    fallback=FallbackConfig()
)


def load_config(path: Optional[str] = None) -> Config:
    """
    Load configuration from file or environment.
    
    Args:
        path: Path to YAML config file. If None, uses environment variables.
        
    Returns:
        Config object
    """
    if path:
        return Config.from_yaml(path)
    return Config.from_env()


def get_config_for_path(config: Config, path: str, method: str) -> Optional[RateLimitRule]:
    """
    Get the rate limit rule for a specific path and method.
    
    Args:
        config: Configuration object
        path: Request path
        method: HTTP method
        
    Returns:
        RateLimitRule if matching rule exists, None otherwise
    """
    for rule in config.rules:
        # Check path match (exact or prefix match)
        if path == rule.path or path.startswith(rule.path):
            # Check method match
            if method.upper() in [m.upper() for m in rule.methods]:
                return rule
    
    return None
