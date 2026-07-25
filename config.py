import sys
import os
import yaml
from dotenv import load_dotenv

load_dotenv()


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)

    errors = []

    mistral_key = os.getenv("MISTRAL_API_KEY")
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

    if not mistral_key:
        errors.append("MISTRAL_API_KEY is not set in .env or environment")
    
    if "api" not in cfg:
        cfg["api"] = {}
    cfg["api"]["mistral_key"] = mistral_key

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
        
        if not github_token:
            print("Warning: GITHUB_PERSONAL_ACCESS_TOKEN is not set in .env or environment")
        
        if "env" not in github:
            github["env"] = {}
        github["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token

    if errors:
        print("Config validation failed:")
        for e in errors:
            print(f"  - {e}")
        print(f"\nCheck your .env and {path} files.")
        sys.exit(1)

    return cfg
