import requests
import json

# MCP server URL (HTTP mode)
MCP_URL = "http://127.0.0.1:8765"

def plan_sort(limit=10):
    resp = requests.post(f"{MCP_URL}/plan_sort", json={"limit": limit})
    resp.raise_for_status()
    return resp.json()

def apply_sort(plan, dry_run=True):
    resp = requests.post(f"{MCP_URL}/apply_sort", json={"plan": plan, "dry_run": dry_run})
    resp.raise_for_status()
    return resp.json()

def purge_spam(limit=10, dry_run=True):
    resp = requests.post(f"{MCP_URL}/purge_spam", json={"limit": limit, "dry_run": dry_run})
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    # --- Plan sorting ---
    plan = plan_sort(limit=10)
    print("Planned sort:")
    print(json.dumps(plan, indent=2))

    # --- Apply sorting (dry-run) ---
    apply_result = apply_sort(plan, dry_run=True)
    print("\nApply result (dry-run):")
    print(json.dumps(apply_result, indent=2))

    # --- Preview spam purge (dry-run) ---
    spam_preview = purge_spam(limit=5, dry_run=True)
    print("\nSpam messages to remove (dry-run):")
    print(json.dumps(spam_preview, indent=2))