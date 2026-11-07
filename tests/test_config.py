"""Unit tests for AgentLab configuration management."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

# Ensure the 'src' directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.core.config import (
    ALLOWED_ENVIRONMENTS,
    ALLOWED_LOG_LEVELS,
    Config,
    load_config,
)


class TestConfigModel(unittest.TestCase):
    """Tests for the Config dataclass, validation, and representations."""

    def test_default_config_values(self) -> None:
        cfg = Config()
        self.assertEqual(cfg.runs_dir, "runs")
        self.assertEqual(cfg.scenarios_dir, "scenarios")
        self.assertEqual(cfg.default_timeout_seconds, 30.0)
        self.assertEqual(cfg.default_max_steps, 10)
        self.assertEqual(cfg.max_timeout_seconds, 300.0)
        self.assertEqual(cfg.max_steps_limit, 100)
        self.assertEqual(cfg.log_level, "INFO")
        self.assertEqual(cfg.environment, "development")
        self.assertIsNone(cfg.api_key)
        self.assertEqual(cfg.metadata, {})

    def test_api_key_hidden_from_repr(self) -> None:
        cfg = Config(api_key="super_secret_key_12345")
        representation = repr(cfg)
        self.assertNotIn("super_secret_key_12345", representation)
        self.assertNotIn("api_key", representation)

    def test_to_dict_never_includes_api_key(self) -> None:
        cfg = Config(api_key="super_secret_key_12345")
        data = cfg.to_dict()
        self.assertNotIn("api_key", data)
        self.assertNotIn("super_secret_key_12345", json.dumps(data))

    def test_environment_validation(self) -> None:
        for env in ALLOWED_ENVIRONMENTS:
            cfg = Config(environment=env)
            self.assertEqual(cfg.environment, env)

        invalid_environments = ["prod", "dev", "staging", "invalid", ""]
        for bad_env in invalid_environments:
            with self.assertRaises(ValueError, msg=f"Should reject environment: {bad_env}"):
                Config(environment=bad_env)

        # Non-string types must raise ValueError
        for bad_type in [123, True, False, ["development"], {"env": "development"}]:
            with self.assertRaises(ValueError, msg=f"Should reject non-string environment: {bad_type}"):
                Config(environment=bad_type)  # type: ignore[arg-type]

    def test_log_level_validation(self) -> None:
        for level in ALLOWED_LOG_LEVELS:
            cfg = Config(log_level=level)
            self.assertEqual(cfg.log_level, level)

        invalid_levels = ["info", "WARN", "VERBOSE", "TRACE", ""]
        for bad_level in invalid_levels:
            with self.assertRaises(ValueError, msg=f"Should reject log_level: {bad_level}"):
                Config(log_level=bad_level)

        # Non-string types must raise ValueError
        for bad_type in [10, True, False, ["INFO"], None]:
            with self.assertRaises(ValueError, msg=f"Should reject non-string log_level: {bad_type}"):
                Config(log_level=bad_type)  # type: ignore[arg-type]

    def test_metadata_type_validation(self) -> None:
        # Non-dict metadata must raise ValueError
        for bad_meta in ["string_meta", 123, True, [1, 2, 3]]:
            with self.assertRaises(ValueError, msg=f"Should reject non-dict metadata: {bad_meta}"):
                Config(metadata=bad_meta)  # type: ignore[arg-type]

    def test_api_key_type_validation(self) -> None:
        # Valid: string or None
        self.assertIsNone(Config(api_key=None).api_key)
        self.assertEqual(Config(api_key="valid_key").api_key, "valid_key")

        # Invalid: non-string (numbers, bools, lists) must raise ValueError
        for bad_key in [12345, True, False, ["key"], {"k": "v"}]:
            with self.assertRaises(ValueError, msg=f"Should reject non-string api_key: {bad_key}"):
                Config(api_key=bad_key)  # type: ignore[arg-type]

    def test_numeric_step_validation(self) -> None:
        # Zero or negative
        with self.assertRaises(ValueError):
            Config(default_max_steps=0)
        with self.assertRaises(ValueError):
            Config(default_max_steps=-5)

        # Booleans explicitly rejected
        with self.assertRaises(ValueError):
            Config(default_max_steps=True)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Config(default_max_steps=False)  # type: ignore[arg-type]

        # max_steps_limit < default_max_steps rejected
        with self.assertRaises(ValueError):
            Config(default_max_steps=20, max_steps_limit=15)

    def test_numeric_timeout_validation(self) -> None:
        # Zero or negative
        with self.assertRaises(ValueError):
            Config(default_timeout_seconds=0.0)
        with self.assertRaises(ValueError):
            Config(default_timeout_seconds=-1.0)

        # Non-finite values
        for bad_val in [float("nan"), float("inf"), float("-inf")]:
            with self.assertRaises(ValueError, msg=f"Should reject timeout value: {bad_val}"):
                Config(default_timeout_seconds=bad_val)

        # Booleans explicitly rejected
        with self.assertRaises(ValueError):
            Config(default_timeout_seconds=True)  # type: ignore[arg-type]

        # max_timeout_seconds < default_timeout_seconds rejected
        with self.assertRaises(ValueError):
            Config(default_timeout_seconds=50.0, max_timeout_seconds=40.0)

    def test_path_validation(self) -> None:
        with self.assertRaises(ValueError):
            Config(runs_dir="")
        with self.assertRaises(ValueError):
            Config(scenarios_dir="   ")


class TestConfigLoader(unittest.TestCase):
    """Tests for load_config, file handling, and security scanning."""

    def setUp(self) -> None:
        # Save and restore environment variables around tests
        self._orig_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._orig_env)

    def test_load_default_when_no_file_exists(self) -> None:
        # Calling load_config() when default agentlab.json does not exist
        # must succeed using safe defaults without raising FileNotFoundError.
        # Isolated in an empty temporary directory so no real agentlab.json interferes.
        orig_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as empty_dir:
            try:
                os.chdir(empty_dir)
                cfg = load_config(config_path=None)
                self.assertEqual(cfg.runs_dir, "runs")
                self.assertEqual(cfg.default_timeout_seconds, 30.0)
                self.assertEqual(cfg.default_max_steps, 10)
            finally:
                os.chdir(orig_cwd)

    def test_load_explicit_missing_file_raises_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_config(config_path="non_existent_config_file_12345.json")

    def test_load_valid_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "custom_agentlab.json"
            content = {
                "runs_dir": "custom_runs",
                "default_timeout_seconds": 45.0,
                "default_max_steps": 15,
                "environment": "testing",
                "log_level": "DEBUG",
                "metadata": {"project": "AgentLabDemo"},
            }
            config_file.write_text(json.dumps(content), encoding="utf-8")

            cfg = load_config(config_path=config_file)
            self.assertEqual(cfg.runs_dir, "custom_runs")
            self.assertEqual(cfg.default_timeout_seconds, 45.0)
            self.assertEqual(cfg.default_max_steps, 15)
            self.assertEqual(cfg.environment, "testing")
            self.assertEqual(cfg.log_level, "DEBUG")
            self.assertEqual(cfg.metadata["project"], "AgentLabDemo")
            # Unspecified fields retain defaults
            self.assertEqual(cfg.scenarios_dir, "scenarios")

    def test_load_malformed_json_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "bad.json"
            config_file.write_text("{ broken json content ...", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_config(config_path=config_file)
            self.assertIn("Invalid JSON syntax", str(ctx.exception))

    def test_load_json_array_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "array.json"
            config_file.write_text("[\"runs\", \"scenarios\"]", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_config(config_path=config_file)
            self.assertIn("must contain a JSON object", str(ctx.exception))

    def test_recursive_secret_detection_top_level(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "leaked_secret.json"
            content = {"runs_dir": "runs", "api_key": "my_secret_token"}
            config_file.write_text(json.dumps(content), encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path=config_file)
            self.assertIn("Security error", str(ctx.exception))
            self.assertIn("api_key", str(ctx.exception))

    def test_recursive_secret_detection_nested_dictionary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "nested_secret.json"
            content = {
                "runs_dir": "runs",
                "metadata": {
                    "database": {
                        "user": "admin",
                        "password": "plaintext_password_is_bad",
                    }
                },
            }
            config_file.write_text(json.dumps(content), encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path=config_file)
            self.assertIn("Security error", str(ctx.exception))
            self.assertIn("password", str(ctx.exception))

    def test_recursive_secret_detection_list_of_dictionaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "list_secret.json"
            content = {
                "runs_dir": "runs",
                "metadata": {
                    "integrations": [
                        {"name": "github", "token": "ghp_12345"},
                    ]
                },
            }
            config_file.write_text(json.dumps(content), encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path=config_file)
            self.assertIn("Security error", str(ctx.exception))
            self.assertIn("token", str(ctx.exception))

    def test_recursive_secret_detection_allows_benign_keys_such_as_author(self) -> None:
        # Ordinary keys containing 'auth' like 'author' or 'authority' must NOT be rejected
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "author_metadata.json"
            content = {
                "runs_dir": "runs",
                "metadata": {
                    "author": "Ahmad",
                    "authority": "high",
                    "author_email": "author@example.com",
                },
            }
            config_file.write_text(json.dumps(content), encoding="utf-8")

            cfg = load_config(config_path=config_file)
            self.assertEqual(cfg.metadata["author"], "Ahmad")
            self.assertEqual(cfg.metadata["authority"], "high")

    def test_recursive_secret_detection_various_credential_formats(self) -> None:
        # Sensitive credential keys in various forms (camelCase, snake_case, etc.) must be rejected
        sensitive_samples = [
            ("apiKey", "12345"),
            ("client_secret", "secret_val"),
            ("access_token", "token_val"),
            ("refresh_token", "refresh_val"),
            ("private_key", "key_val"),
            ("credentials", "creds_val"),
            ("db_password", "pass_val"),
        ]
        for key_name, val in sensitive_samples:
            with tempfile.TemporaryDirectory() as temp_dir:
                config_file = Path(temp_dir) / f"test_{key_name}.json"
                content = {
                    "runs_dir": "runs",
                    "metadata": {"nested": {key_name: val}},
                }
                config_file.write_text(json.dumps(content), encoding="utf-8")

                with self.assertRaises(ValueError, msg=f"Should detect sensitive key: {key_name}"):
                    load_config(config_path=config_file)

    def test_api_key_loaded_from_environment_only(self) -> None:
        os.environ["AGENTLAB_API_KEY"] = "sk-ant-test-from-env-1234"
        cfg = load_config(config_path=None)
        self.assertEqual(cfg.api_key, "sk-ant-test-from-env-1234")
        # Ensure it is not exposed in serialization or repr
        self.assertNotIn("sk-ant-test-from-env-1234", repr(cfg))
        self.assertNotIn("api_key", cfg.to_dict())

    def test_empty_api_key_env_becomes_none(self) -> None:
        os.environ["AGENTLAB_API_KEY"] = ""
        cfg = load_config(config_path=None)
        self.assertIsNone(cfg.api_key)
        os.environ["AGENTLAB_API_KEY"] = "   "
        cfg = load_config(config_path=None)
        self.assertIsNone(cfg.api_key)

    def test_config_metadata_defensive_copy(self) -> None:
        meta = {"nested": {"x": 1}}
        cfg = Config(metadata=meta)
        meta["nested"]["x"] = 999
        self.assertEqual(cfg.metadata["nested"]["x"], 1)
        cfg.metadata["nested"]["x"] = 123
        as_dict = cfg.to_dict()
        self.assertEqual(as_dict["metadata"]["nested"]["x"], 123)

    def test_load_invalid_encoding_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "bad_encoding.json"
            # Write invalid UTF-8 bytes
            config_file.write_bytes(b"{\xff\xfe runs_dir ")
            with self.assertRaises(ValueError):
                load_config(config_path=config_file)

    def test_deeply_nested_json_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "deep.json"
            # Create deeply nested structure
            deep = {"x": 1}
            current = deep
            for _ in range(200):
                current["nested"] = {"x": 1}
                current = current["nested"]
            config_file.write_text(json.dumps(deep), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(config_path=config_file)

    def test_to_dict_rejects_nan_infinity(self) -> None:
        # M2 JSON compatibility validation rejects non-finite numbers at validation time
        # (fail-fast), which preserves and strengthens the M1 safety intent.
        with self.assertRaises(ValueError):
            Config(metadata={"val": float("nan")})
        with self.assertRaises(ValueError):
            Config(metadata={"val": float("inf")})

    def test_secret_detection_aws_and_jwt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "aws.json"
            content = {"runs_dir": "runs", "metadata": {"aws_secret_access_key": "x"}}
            config_file.write_text(json.dumps(content), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(config_path=config_file)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "jwt.json"
            content = {"runs_dir": "runs", "metadata": {"jwt": "token"}}
            config_file.write_text(json.dumps(content), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(config_path=config_file)

    def test_secret_detection_false_positives(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "ok.json"
            content = {"runs_dir": "runs", "metadata": {"max_token": 1000, "password_policy": "strict", "credentials_path": "/tmp/x"}}
            config_file.write_text(json.dumps(content), encoding="utf-8")
            cfg = load_config(config_path=config_file)
            self.assertEqual(cfg.metadata["max_token"], 1000)


if __name__ == "__main__":
    unittest.main()
