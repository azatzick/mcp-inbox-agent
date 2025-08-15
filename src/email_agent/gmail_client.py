from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import pathlib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .settings import settings

@dataclass
class GmailMessage:
    id: str
    threadId: str
    snippet: Optional[str]
    internalDate: Optional[int]
    labelIds: Optional[List[str]]
    payload: Optional[dict]

class GmailClient:
    def __init__(self):
        self.client_secret_file = settings.gmail_client_secret_file
        self.token_file = settings.gmail_token_file
        self.scopes = settings.gmail_scopes
        self._service = None

    def _authorize(self) -> Credentials:
        creds = None
        token_path = pathlib.Path(self.token_file)
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json())
        return creds

    @property
    def service(self):
        if self._service is None:
            creds = self._authorize()
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    # --- Labels ---
    def list_labels(self) -> List[dict]:
        return self.service.users().labels().list(userId="me").execute().get("labels", [])

    def find_or_create_label(self, name: str) -> str:
        labels = self.list_labels()
        for l in labels:
            if l["name"] == name:
                return l["id"]
        body = {"name": name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        created = self.service.users().labels().create(userId="me", body=body).execute()
        return created["id"]

    # --- Messages ---
    def list_messages(self, label_ids: List[str] = None, q: str = None, max_results: int = 100) -> List[GmailMessage]:
        kwargs = {"userId": "me", "maxResults": max_results}
        if label_ids:
            kwargs["labelIds"] = label_ids
        if q:
            kwargs["q"] = q
        resp = self.service.users().messages().list(**kwargs).execute()
        messages = []
        for m in resp.get("messages", []):
            msg = self.service.users().messages().get(userId="me", id=m["id"], format="metadata").execute()
            messages.append(GmailMessage(
                id=msg["id"],
                threadId=msg.get("threadId"),
                snippet=msg.get("snippet"),
                internalDate=int(msg.get("internalDate", "0")) if msg.get("internalDate") else None,
                labelIds=msg.get("labelIds"),
                payload=msg.get("payload")
            ))
        return messages

    def modify_labels(self, msg_ids: List[str], add_label_ids: List[str] = None, remove_label_ids: List[str] = None) -> Dict:
        results = {"modified": [], "errors": []}
        add_label_ids = add_label_ids or []
        remove_label_ids = remove_label_ids or []
        for mid in msg_ids:
            try:
                self.service.users().messages().modify(
                    userId="me",
                    id=mid,
                    body={"addLabelIds": add_label_ids, "removeLabelIds": remove_label_ids}
                ).execute()
                results["modified"].append(mid)
            except HttpError as e:
                results["errors"].append(f"{mid}: {e}")
        return results

    def trash_messages(self, msg_ids: List[str]) -> Dict:
        results = {"trashed": [], "errors": []}
        for mid in msg_ids:
            try:
                self.service.users().messages().trash(userId="me", id=mid).execute()
                results["trashed"].append(mid)
            except HttpError as e:
                results["errors"].append(f"{mid}: {e}")
        return results

    def delete_messages(self, msg_ids: List[str]) -> Dict:
        results = {"deleted": [], "errors": []}
        for mid in msg_ids:
            try:
                self.service.users().messages().delete(userId="me", id=mid).execute()
                results["deleted"].append(mid)
            except HttpError as e:
                results["errors"].append(f"{mid}: {e}")
        return results