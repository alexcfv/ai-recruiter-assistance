import sys
import yaml


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    errors = []

    api = cfg.get("api", {})
    val = api.get("mistral_key", "")
    if not val or "your-" in val:
        errors.append(f"api.mistral_key is not configured")

    for section in ("embedder", "explainer", "profile_builder", "reranker"):
        timeout = cfg.get(section, {}).get("timeout", 0)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append(f"{section}.timeout is missing or invalid")

    min_interval = cfg.get("rate_limiter", {}).get("min_interval", 0)
    if not isinstance(min_interval, (int, float)) or min_interval <= 0:
        errors.append("rate_limiter.min_interval is missing or invalid")

    github = cfg.get("github", {})
    if github:
        if not github.get("mcp_server_command"):
            errors.append("github.mcp_server_command is missing")
        env = github.get("env", {})
        if not env.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
            print("Warning: github.env.GITHUB_PERSONAL_ACCESS_TOKEN is not set")

    if errors:
        print("Config validation failed:")
        for e in errors:
            print(f"  - {e}")
        print(f"\nEdit {path} and try again.")
        sys.exit(1)

    return cfg
