"""Configuration management and settings for AgentLab.

This module defines the central Config dataclass and loader mechanism:
- Manages paths, execution limits, logging levels, and environment states.
- Loads settings from JSON configuration files with fallback to safe defaults.
- Enforces strict validation on types, ranges, environments, and log levels.
- Recursively scans JSON input to strictly forbid credentials/secrets in files.
- Reads API keys and secrets strictly from environment variables (AGENTLAB_API_KEY).
- Hides secrets from object representation and serialization.

Rule: core/ depends on nothing else in the project.
"""

from dataclasses import dataclass, field
import copy
import json
import math
import os
from pathlib import Path
import re
from typing import Any

# Allowed discrete choices
ALLOWED_ENVIRONMENTS: frozenset[str] = frozenset({"development", "testing", "production"})
ALLOWED_LOG_LEVELS: frozenset[str] = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

# Sensitive key patterns that indicate credentials or secrets in JSON configuration
# Regex patterns ensure word boundaries to avoid false positives (e.g. 'author' is allowed, 'apiKey' is rejected)
SENSITIVE_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^.*api[_-]?key.*$"),
    re.compile(r"^.*client[_-]?secret.*$"),
    re.compile(r"^.*access[_-]?token.*$"),
    re.compile(r"^.*refresh[_-]?token.*$"),
    re.compile(r"^.*auth[_-]?token.*$"),
    re.compile(r"^.*bearer[_-]?token.*$"),
    re.compile(r"^.*private[_-]?key.*$"),
    re.compile(r"^.*secret[_-]?key.*$"),
    re.compile(r"^.*ssh[_-]?key.*$"),
    re.compile(r"^.*signing[_-]?key.*$"),
    re.compile(r"^.*passw(or)?d.*$"),
    re.compile(r"^.*passphrase.*$"),
    re.compile(r"^.*credential(s)?(?!_path$).*"),
    re.compile(r"^.*aws[_-]?secret.*$"),
    re.compile(r"^.*authorization.*$"),
    re.compile(r"^.*jwt.*$"),
    re.compile(r"^.*cookie.*$"),
    re.compile(r"^.*(_secret)$"),
    re.compile(r"^.*(secret|token|bearer|apikey|auth)$"),
)

DEFAULT_CONFIG_FILENAME: str = "agentlab.json"


def is_sensitive_key(key_name: str) -> bool:
    """Checks whether a key name represents a credential or secret.

    Normalizes camelCase and kebab-case to snake_case before matching.
    Avoids false positives such as 'author' or 'authority'.
    """
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(key_name)).lower()
    normalized = normalized.replace("-", "_")
    # Avoid common false positives
    if normalized.endswith("_policy") or normalized.endswith("_path") or normalized == "max_token":
        return False
    return any(pattern.match(normalized) for pattern in SENSITIVE_KEY_PATTERNS)


def detect_secrets_recursively(data: Any, path: str = "", _depth: int = 0) -> None:
    """Recursively scans data structures for forbidden sensitive/secret keys.

    Args:
        data: The parsed JSON data structure (dict, list, or primitive).
        path: The object path string used for clear error messages.

    Raises:
        ValueError: If any forbidden sensitive key name is detected.
    """
    if _depth > 100:
        raise ValueError("Configuration structure is too deeply nested")
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else str(key)
            if is_sensitive_key(str(key)):
                raise ValueError(
                    f"Security error: Secrets must never be stored in configuration files. "
                    f"Found forbidden credential/secret key '{key}' at '{current_path}'. "
                    f"Use environment variables (e.g., AGENTLAB_API_KEY) instead."
                )
            try:
                detect_secrets_recursively(value, current_path, _depth + 1)
            except RecursionError as exc:
                raise ValueError("Configuration structure is too deeply nested") from exc
    elif isinstance(data, list):
        for index, item in enumerate(data):
            try:
                detect_secrets_recursively(item, f"{path}[{index}]", _depth + 1)
            except RecursionError as exc:
                raise ValueError("Configuration structure is too deeply nested") from exc


@dataclass(slots=True, kw_only=True)
class Config:
    """Central configuration parameters for AgentLab."""

    runs_dir: str = "runs"
    scenarios_dir: str = "scenarios"
    default_timeout_seconds: float = 30.0
    default_max_steps: int = 10
    max_timeout_seconds: float = 300.0
    max_steps_limit: int = 100
    log_level: str = "INFO"
    environment: str = "development"
    # Secrets: repr=False prevents printing in logs/debug, excluded from to_dict()
    api_key: str | None = field(default=None, repr=False)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates configuration parameters and boundaries."""
        object.__setattr__(self, "metadata", copy.deepcopy(self.metadata))
        self.validate()

    def validate(self) -> None:
        """Enforces type and range validations on all configuration fields."""
        if not isinstance(self.runs_dir, str) or not self.runs_dir.strip():
            raise ValueError("Config.runs_dir must be a non-empty string")
        if not isinstance(self.scenarios_dir, str) or not self.scenarios_dir.strip():
            raise ValueError("Config.scenarios_dir must be a non-empty string")

        # Step validation (reject booleans explicitly)
        if isinstance(self.default_max_steps, bool) or not isinstance(self.default_max_steps, int) or self.default_max_steps <= 0:
            raise ValueError("Config.default_max_steps must be a positive integer greater than zero (booleans not allowed)")
        if isinstance(self.max_steps_limit, bool) or not isinstance(self.max_steps_limit, int) or self.max_steps_limit <= 0:
            raise ValueError("Config.max_steps_limit must be a positive integer greater than zero (booleans not allowed)")
        if self.max_steps_limit < self.default_max_steps:
            raise ValueError(
                f"Config.max_steps_limit ({self.max_steps_limit}) cannot be less than "
                f"Config.default_max_steps ({self.default_max_steps})"
            )

        # Timeout validation (reject booleans, NaNs, infinities)
        if (
            isinstance(self.default_timeout_seconds, bool)
            or not isinstance(self.default_timeout_seconds, (int, float))
            or not math.isfinite(self.default_timeout_seconds)
            or self.default_timeout_seconds <= 0.0
        ):
            raise ValueError(
                "Config.default_timeout_seconds must be a finite positive number greater than zero"
            )
        if (
            isinstance(self.max_timeout_seconds, bool)
            or not isinstance(self.max_timeout_seconds, (int, float))
            or not math.isfinite(self.max_timeout_seconds)
            or self.max_timeout_seconds <= 0.0
        ):
            raise ValueError(
                "Config.max_timeout_seconds must be a finite positive number greater than zero"
            )
        if self.max_timeout_seconds < self.default_timeout_seconds:
            raise ValueError(
                f"Config.max_timeout_seconds ({self.max_timeout_seconds}) cannot be less than "
                f"Config.default_timeout_seconds ({self.default_timeout_seconds})"
            )

        # Environment & logging validation (strictly check str before membership)
        if not isinstance(self.environment, str):
            raise ValueError(
                f"Config.environment must be a string, got {type(self.environment).__name__}"
            )
        if self.environment not in ALLOWED_ENVIRONMENTS:
            raise ValueError(
                f"Config.environment '{self.environment}' is invalid. "
                f"Must be one of: {sorted(ALLOWED_ENVIRONMENTS)}"
            )

        if not isinstance(self.log_level, str):
            raise ValueError(
                f"Config.log_level must be a string, got {type(self.log_level).__name__}"
            )
        if self.log_level not in ALLOWED_LOG_LEVELS:
            raise ValueError(
                f"Config.log_level '{self.log_level}' is invalid. "
                f"Must be one of: {sorted(ALLOWED_LOG_LEVELS)}"
            )

        # Metadata validation (must be a dictionary)
        if not isinstance(self.metadata, dict):
            raise ValueError(
                f"Config.metadata must be a dictionary, got {type(self.metadata).__name__}"
            )

        # API key validation (must be str or None)
        if self.api_key is not None and not isinstance(self.api_key, str):
            raise ValueError(
                f"Config.api_key must be a string or None, got {type(self.api_key).__name__}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serializes non-sensitive configuration to a JSON-compatible dictionary.

        Security Note:
            api_key is strictly excluded from serialization to prevent leaking secrets.
        """
        result = {
            "runs_dir": self.runs_dir,
            "scenarios_dir": self.scenarios_dir,
            "default_timeout_seconds": float(self.default_timeout_seconds),
            "default_max_steps": self.default_max_steps,
            "max_timeout_seconds": float(self.max_timeout_seconds),
            "max_steps_limit": self.max_steps_limit,
            "log_level": self.log_level,
            "environment": self.environment,
            "metadata": copy.deepcopy(self.metadata),
        }
        try:
            json.dumps(result, allow_nan=False)
        except (ValueError, TypeError) as exc:
            raise ValueError("Configuration contains non-JSON-serializable values") from exc
        return result


def _read_and_parse_json(path: Path) -> dict[str, Any]:
    """Reads and parses a JSON file with clear, helpful error handling."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON syntax in configuration file '{path}': {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"Unable to read configuration file '{path}': {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read configuration file '{path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Configuration file '{path}' must contain a JSON object (dictionary)")
    return data


def load_config(config_path: str | os.PathLike[str] | None = None) -> Config:
    """Loads configuration with safe defaults, JSON file merging, and environment secrets.

    Behavior:
        - If config_path is explicitly provided and does not exist: raises FileNotFoundError.
        - If config_path is None and default 'agentlab.json' does not exist: uses safe defaults.
        - Scans JSON data recursively to reject any stored secrets/passwords/API keys.
        - Populates api_key strictly from the AGENTLAB_API_KEY environment variable.

    Args:
        config_path: Optional explicit path to a JSON configuration file.

    Returns:
        A validated Config instance.
    """
    file_data: dict[str, Any] = {}

    if config_path is not None:
        target_path = Path(config_path)
        if not target_path.is_file():
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        file_data = _read_and_parse_json(target_path)
    else:
        default_path = Path(DEFAULT_CONFIG_FILENAME)
        if default_path.is_file():
            file_data = _read_and_parse_json(default_path)

    # Security check: recursive scan for forbidden sensitive keys
    detect_secrets_recursively(file_data)

    # Read sensitive API key strictly from environment variable
    env_api_key = os.environ.get("AGENTLAB_API_KEY")
    if isinstance(env_api_key, str) and env_api_key.strip() == "":
        env_api_key = None

    # Build kwargs for Config, overriding defaults with JSON values
    kwargs: dict[str, Any] = {}
    allowed_fields = {
        "runs_dir",
        "scenarios_dir",
        "default_timeout_seconds",
        "default_max_steps",
        "max_timeout_seconds",
        "max_steps_limit",
        "log_level",
        "environment",
        "metadata",
    }

    for key, value in file_data.items():
        if key in allowed_fields:
            kwargs[key] = value

    kwargs["api_key"] = env_api_key

    return Config(**kwargs)
