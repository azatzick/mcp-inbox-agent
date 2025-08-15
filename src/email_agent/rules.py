from typing import Dict, Any, List
import yaml

def load_rules(path: str = "config/rules.yaml") -> Dict[str, Any]:
    """Load YAML rules from a file."""
    with open(path, "r") as f:
        return yaml.safe_load(f) or {"rules": []}

def header_value(payload: dict, name: str) -> str | None:
    """Extract a header value from message payload."""
    if not payload:
        return None
    headers = payload.get("headers", [])
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None

def score_message(payload: dict, rule: Dict[str, Any]) -> bool:
    """Check if a message matches a given rule."""
    subject = (header_value(payload, "Subject") or "").lower()
    sender = (header_value(payload, "From") or "").lower()

    def any_contains(text: str, needles: List[str]) -> bool:
        return any(n.lower() in text for n in needles)

    if "any_subject_contains" in rule:
        if not any_contains(subject, rule["any_subject_contains"]):
            return False

    if "any_sender_contains" in rule:
        if not any_contains(sender, rule["any_sender_contains"]):
            return False

    return True

def apply_rules(message: dict, rules: Dict[str, Any]) -> List[str]:
    """Return the list of labels to assign based on rules."""
    payload = message.get("payload", {})
    for rule in rules.get("rules", []):
        if score_message(payload, rule):
            return rule.get("assign_labels", [])
    return []  # no match