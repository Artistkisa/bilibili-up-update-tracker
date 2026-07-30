"""Configuration loading for YAML, environment variables and CLI overrides."""

import argparse
import copy
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config.yaml"
SUPPORTED_CHANNELS = ("email", "webhook", "gotify")

DEFAULTS = {
    "up_users": [],
    "data_file": str(PROJECT_ROOT / "data" / "monitor_data.json"),
    "schedule": {"cron": "0 10 * * *", "timezone": "Asia/Shanghai"},
    "notifications": {
        "email": {
            "enabled": False,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "recipients": [],
        },
        "webhook": {"enabled": False, "url": "", "headers": {}, "timeout": 10},
        "gotify": {
            "enabled": False,
            "url": "",
            "token": "",
            "priority": 5,
            "timeout": 10,
        },
    },
}

CONFIG_ENV_VARS = {
    "CONFIG_FILE", "DATA_FILE", "UP_USERS_JSON", "CHECK_CRON", "TZ",
    "NOTIFY_CHANNELS", "EMAIL_SMTP_HOST", "EMAIL_SMTP_PORT", "EMAIL_USER",
    "EMAIL_PASS", "EMAIL_TO", "WEBHOOK_URL", "WEBHOOK_HEADERS_JSON",
    "WEBHOOK_TIMEOUT", "GOTIFY_URL", "GOTIFY_TOKEN", "GOTIFY_PRIORITY",
    "GOTIFY_TIMEOUT",
}


class ConfigError(ValueError):
    """Raised when user-provided configuration is invalid."""


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bilibili UP update tracker")
    parser.add_argument("--config", type=Path, help="YAML configuration file")
    parser.add_argument("--data-file", type=Path, help="Monitor state file")
    parser.add_argument("--up", action="append", default=[], metavar="UID:NAME")
    parser.add_argument("--notify", action="append", choices=SUPPORTED_CHANNELS, default=[])
    return parser.parse_args(argv)


def parse_up(value):
    try:
        uid_text, name = value.split(":", 1)
        uid = int(uid_text)
    except (ValueError, TypeError) as exc:
        raise ConfigError(f"Invalid --up value {value!r}; expected UID:NAME") from exc
    if uid <= 0 or not name.strip():
        raise ConfigError(f"Invalid --up value {value!r}; UID and name are required")
    return {"uid": uid, "name": name.strip()}


def env_int(env, name):
    try:
        return int(env[name])
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def load_yaml(path):
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"Unable to read YAML config {path}: {exc}") from exc
    if not isinstance(content, dict):
        raise ConfigError(f"YAML config {path} must contain a mapping at the top level")
    return content


def load_legacy_config():
    try:
        import config as legacy
    except ImportError:
        return {}

    email = getattr(legacy, "EMAIL_CONFIG", {})
    username = email.get("smtp_user", "")
    password = email.get("smtp_pass", "")
    recipients = email.get("to", [])
    enabled = bool(
        username and password and recipients
        and username != "your_email@qq.com"
        and password != "your_auth_code"
        and recipients != ["recipient@example.com"]
    )
    return {
        "up_users": [
            {"uid": int(uid), "name": str(name)}
            for uid, name in getattr(legacy, "UP_LIST", {}).items()
        ],
        "data_file": str(getattr(legacy, "DATA_FILE", DEFAULTS["data_file"])),
        "notifications": {
            "email": {
                "enabled": enabled,
                "smtp_host": email.get("smtp_host", "smtp.qq.com"),
                "smtp_port": email.get("smtp_port", 587),
                "username": username,
                "password": password,
                "recipients": recipients,
            }
        },
    }


def environment_overrides(env):
    result = {}
    if env.get("DATA_FILE"):
        result["data_file"] = env["DATA_FILE"]
    if env.get("UP_USERS_JSON"):
        try:
            result["up_users"] = json.loads(env["UP_USERS_JSON"])
        except json.JSONDecodeError as exc:
            raise ConfigError(f"UP_USERS_JSON is not valid JSON: {exc}") from exc

    schedule = {}
    if env.get("CHECK_CRON"):
        schedule["cron"] = env["CHECK_CRON"]
    if env.get("TZ"):
        schedule["timezone"] = env["TZ"]
    if schedule:
        result["schedule"] = schedule

    notifications = {}
    email = {}
    email_map = {
        "EMAIL_SMTP_HOST": "smtp_host", "EMAIL_SMTP_PORT": "smtp_port",
        "EMAIL_USER": "username", "EMAIL_PASS": "password",
    }
    for env_name, key in email_map.items():
        if env.get(env_name):
            email[key] = env_int(env, env_name) if key == "smtp_port" else env[env_name]
    if env.get("EMAIL_TO"):
        email["recipients"] = [item.strip() for item in env["EMAIL_TO"].split(",") if item.strip()]
    if email:
        notifications["email"] = email

    webhook = {}
    if env.get("WEBHOOK_URL"):
        webhook["url"] = env["WEBHOOK_URL"]
    if env.get("WEBHOOK_TIMEOUT"):
        webhook["timeout"] = env_int(env, "WEBHOOK_TIMEOUT")
    if env.get("WEBHOOK_HEADERS_JSON"):
        try:
            webhook["headers"] = json.loads(env["WEBHOOK_HEADERS_JSON"])
        except json.JSONDecodeError as exc:
            raise ConfigError(f"WEBHOOK_HEADERS_JSON is not valid JSON: {exc}") from exc
    if webhook:
        notifications["webhook"] = webhook

    gotify = {}
    gotify_map = {
        "GOTIFY_URL": "url", "GOTIFY_TOKEN": "token",
        "GOTIFY_PRIORITY": "priority", "GOTIFY_TIMEOUT": "timeout",
    }
    for env_name, key in gotify_map.items():
        if env.get(env_name):
            gotify[key] = env_int(env, env_name) if key in {"priority", "timeout"} else env[env_name]
    if gotify:
        notifications["gotify"] = gotify

    if env.get("NOTIFY_CHANNELS"):
        selected = {item.strip().lower() for item in env["NOTIFY_CHANNELS"].split(",") if item.strip()}
        unknown = selected.difference(SUPPORTED_CHANNELS)
        if unknown:
            raise ConfigError(f"Unknown notification channels: {', '.join(sorted(unknown))}")
        for channel in SUPPORTED_CHANNELS:
            notifications.setdefault(channel, {})["enabled"] = channel in selected
    if notifications:
        result["notifications"] = notifications
    return result


def cli_overrides(args):
    result = {}
    if args.data_file:
        result["data_file"] = str(args.data_file)
    if args.up:
        result["up_users"] = [parse_up(value) for value in args.up]
    if args.notify:
        selected = set(args.notify)
        result["notifications"] = {
            channel: {"enabled": channel in selected} for channel in SUPPORTED_CHANNELS
        }
    return result


def validate(settings):
    users = settings.get("up_users")
    if not isinstance(users, list) or not users:
        raise ConfigError("up_users must contain at least one UP user")
    normalized_users = []
    seen = set()
    for item in users:
        if not isinstance(item, dict):
            raise ConfigError("Each up_users entry must be a mapping with uid and name")
        try:
            uid = int(item["uid"])
            name = str(item["name"]).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError("Each up_users entry requires a numeric uid and non-empty name") from exc
        if uid <= 0 or not name:
            raise ConfigError("Each up_users entry requires a positive uid and non-empty name")
        if uid not in seen:
            normalized_users.append({"uid": uid, "name": name})
            seen.add(uid)
    settings["up_users"] = normalized_users

    notifications = settings.get("notifications")
    if not isinstance(notifications, dict):
        raise ConfigError("notifications must be a mapping")
    for channel in SUPPORTED_CHANNELS:
        if not isinstance(notifications.get(channel), dict):
            raise ConfigError(f"notifications.{channel} must be a mapping")
    enabled = [name for name in SUPPORTED_CHANNELS if notifications[name].get("enabled")]
    if not enabled:
        raise ConfigError("At least one notification channel must be enabled")

    required = {
        "email": ("smtp_host", "smtp_port", "username", "password", "recipients"),
        "webhook": ("url",),
        "gotify": ("url", "token"),
    }
    for channel in enabled:
        missing = [key for key in required[channel] if not notifications[channel].get(key)]
        if missing:
            raise ConfigError(f"notifications.{channel} is enabled but missing: {', '.join(missing)}")
    if not isinstance(notifications["webhook"].get("headers"), dict):
        raise ConfigError("notifications.webhook.headers must be a mapping")
    for channel in ("webhook", "gotify"):
        url = notifications[channel].get("url")
        if notifications[channel].get("enabled"):
            parsed = urlsplit(str(url))
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ConfigError(
                    f"notifications.{channel}.url must be an absolute http:// or https:// URL"
                )
    for channel in ("webhook", "gotify"):
        if int(notifications[channel].get("timeout", 10)) <= 0:
            raise ConfigError(f"notifications.{channel}.timeout must be greater than zero")
    return settings


def load_settings(argv=None, env=None):
    env = os.environ if env is None else env
    args = parse_args(argv)
    config_path = args.config or Path(env.get("CONFIG_FILE") or DEFAULT_CONFIG_FILE)
    explicit_cli = bool(args.config or args.data_file or args.up or args.notify)
    explicit_env = any(env.get(name) for name in CONFIG_ENV_VARS)
    yaml_exists = config_path.is_file()

    settings = copy.deepcopy(DEFAULTS)
    if not yaml_exists and not explicit_env and not explicit_cli:
        legacy = load_legacy_config()
        if legacy:
            print(
                "Warning: src/config.py configuration is deprecated; migrate to config.yaml or environment variables before v1.2.",
                file=sys.stderr,
            )
            settings = deep_merge(settings, legacy)
    if args.config and not yaml_exists:
        raise ConfigError(f"Configuration file does not exist: {config_path}")
    if yaml_exists:
        settings = deep_merge(settings, load_yaml(config_path))
    settings = deep_merge(settings, environment_overrides(env))
    settings = deep_merge(settings, cli_overrides(args))

    data_path = Path(settings["data_file"])
    if not data_path.is_absolute():
        data_path = PROJECT_ROOT / data_path
    settings["data_file"] = data_path.resolve()
    return validate(settings)
