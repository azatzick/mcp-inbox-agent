from __future__ import annotations
import typer
from rich import print, box
from rich.table import Table

from .settings import settings
from .gmail_client import GmailClient
from .classifier import is_spam, categorize

app = typer.Typer(help="Inbox agent CLI (Gmail + MCP)")

@app.command()
def auth():
    """Run OAuth flow and cache token."""
    client = GmailClient()
    _ = client.service  # triggers auth
    print("[green]OAuth complete. Token cached at[/]", settings.gmail_token_file)

@app.command()
def labels(action: str = typer.Argument(..., help="list|ensure")):
    """List existing labels or ensure default labels exist."""
    client = GmailClient()
    if action == "list":
        labels = client.list_labels()
        table = Table(title="Labels", box=box.SIMPLE)
        table.add_column("ID")
        table.add_column("Name")
        for l in labels:
            table.add_row(l["id"], l["name"])
        print(table)
    elif action == "ensure":
        for name in settings.default_labels:
            lid = client.find_or_create_label(name)
            print(f"Ensured label '{name}' -> {lid}")
    else:
        raise typer.BadParameter("Unknown action: use 'list' or 'ensure'")

@app.command()
def spam(
    action: str = typer.Argument(..., help="purge"),
    mode: str = typer.Option("trash", help="trash|delete"),
    dry_run: bool = typer.Option(True, help="Show what would happen without changing anything"),
    i_understand_this_is_permanent: bool = typer.Option(False, help="Required for --mode delete"),
    limit: int = typer.Option(100, help="Max messages to act on")
):
    """Purge messages in Gmail's SPAM label."""
    if action != "purge":
        raise typer.BadParameter("Only 'purge' supported for now.")

    client = GmailClient()
    spam_msgs = client.list_messages(label_ids=["SPAM"], max_results=limit)
    print(f"Found {len(spam_msgs)} spam messages.")

    if dry_run:
        print("[yellow]Dry run:[/] would remove these ids:")
        for m in spam_msgs:
            print(m.id)
        raise typer.Exit(code=0)

    ids = [m.id for m in spam_msgs]
    if mode == "trash":
        res = client.trash_messages(ids)
        print(res)
    elif mode == "delete":
        if not i_understand_this_is_permanent:
            print("[red]Refusing to permanently delete without explicit confirmation flag.[/]")
            raise typer.Exit(code=1)
        res = client.delete_messages(ids)
        print(res)
    else:
        raise typer.BadParameter("mode must be 'trash' or 'delete'")

@app.command()
def sort(
    action: str = typer.Argument(..., help="plan|apply"),
    label: str = typer.Option(None, help="Only consider messages with this Gmail label id (optional)"),
    limit: int = typer.Option(100, help="Max messages to fetch"),
    dry_run: bool = typer.Option(True, help="For 'apply', perform a dry run first"),
):
    """Plan or apply sorting rules to messages."""
    client = GmailClient()
    msgs = client.list_messages(label_ids=[label] if label else None, max_results=limit)

    if action == "plan":
        table = Table(title="Planned Label Assignments", box=box.SIMPLE)
        table.add_column("Message ID")
        table.add_column("Existing Labels")
        table.add_column("Proposed Labels")
        for m in msgs:
            if is_spam(m):
                continue  # spam handled separately
            proposed = categorize(m)
            if proposed:
                table.add_row(m.id, ",".join(m.labelIds or []), ",".join(proposed))
        print(table)

    elif action == "apply":
        by_name, _ = client.get_label_map()
        ensure_needed = set()
        ops = []
        for m in msgs:
            if is_spam(m):
                continue
            proposed = categorize(m)
            if not proposed:
                continue
            ops.append((m.id, proposed))
            for name in proposed:
                if name not in by_name:
                    ensure_needed.add(name)

        for name in ensure_needed:
            lid = client.find_or_create_label(name)
            print(f"Created label '{name}' -> {lid}")

        by_name, _ = client.get_label_map()
        changed = 0
        for mid, names in ops:
            add_ids = [by_name[n] for n in names if n in by_name]
            if dry_run:
                print(f"[dry-run] would add {names} to {mid}")
            else:
                res = client.modify_labels([mid], add_label_ids=add_ids)
                if res.get("modified"):
                    changed += 1
        print(f"Applied to {changed} messages.")
    else:
        raise typer.BadParameter("action must be 'plan' or 'apply'")

if __name__ == "__main__":
    app()