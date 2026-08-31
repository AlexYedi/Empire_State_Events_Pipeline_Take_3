#!/usr/bin/env python3
"""
Print ready-to-paste `claude mcp add` commands for Confluent's managed MCP servers.

Reads the Global API key + secret (and region/cloud/org) from signal-stream/.env, Base64-encodes
`key:secret` for HTTP Basic auth, and emits the two commands with everything filled in — so you
don't fat-finger the encoding (the #1 setup failure after resource-scoped keys).

Usage:
    python3 signal-stream/scripts/encode_creds.py

Secrets are read from .env (never committed). The encoded credential is printed to YOUR terminal
only — it is not written to any file. Add the servers at local/user scope (the commands below),
NOT into .mcp.json.
"""
import base64, os, sys

ENV = os.path.join(os.path.dirname(__file__), "..", ".env")

def load_env():
    if not os.path.exists(ENV):
        sys.exit("signal-stream/.env not found — copy .env.example to .env and fill it in.")
    env = {}
    for line in open(ENV):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def main():
    e = load_env()
    key = e.get("CONFLUENT_CLOUD_API_KEY")
    secret = e.get("CONFLUENT_CLOUD_API_SECRET")
    missing = [k for k in ("CONFLUENT_CLOUD_API_KEY", "CONFLUENT_CLOUD_API_SECRET",
                           "CONFLUENT_REGION", "CONFLUENT_CLOUD", "CONFLUENT_ORG_ID") if not e.get(k)]
    if missing:
        sys.exit("Missing in .env: " + ", ".join(missing))

    encoded = base64.b64encode(f"{key}:{secret}".encode()).decode()
    region, cloud, org = e["CONFLUENT_REGION"], e["CONFLUENT_CLOUD"], e["CONFLUENT_ORG_ID"]

    print("# Run these two commands (local scope keeps the credential out of the repo):\n")
    print("claude mcp add --transport http confluent-mcp-global \\")
    print("  https://api.confluent.cloud/mcp/v1 \\")
    print(f'  --header "Authorization: Basic {encoded}"\n')
    print("claude mcp add --transport http confluent-mcp-regional \\")
    print(f"  https://mcp.{region}.{cloud}.confluent.cloud/mcp/v1/organizations/{org} \\")
    print(f'  --header "Authorization: Basic {encoded}"\n')
    print("# Then verify:  claude mcp list      (both should show connected)")
    print("# In session:   /mcp                 then ask: 'list my topics, read latest raw_signals, describe schema'")

if __name__ == "__main__":
    main()
