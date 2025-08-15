from typing import List
from .rules import load_rules, apply_rules
from .gmail_client import GmailMessage

SPAM_LABEL_ID = "SPAM"  # Gmail canonical spam label

def is_spam(msg: GmailMessage) -> bool:
    """Return True if the message is in Gmail's SPAM label."""
    return msg.labelIds is not None and SPAM_LABEL_ID in msg.labelIds

def categorize(msg: GmailMessage, rules_path: str = "config/rules.yaml") -> List[str]:
    """
    Return the list of labels to apply to a message based on rules.
    If no rules match, returns an empty list.
    """
    if msg.payload is None:
        return []
    rules = load_rules(rules_path)
    labels = apply_rules({"payload": msg.payload}, rules)
    return labels