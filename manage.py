"""
CLI for reviewing and closing out LinkedIn post drafts.

This is the human side of the approval loop: after scheduler.py emails
you a draft, you read it, and if you post it on LinkedIn yourself, run

    python manage.py mark-posted <post_id>

so the business database (app/memory/database.py) reflects reality.
This never talks to LinkedIn -- it only updates local records.

Usage:
    python manage.py list-pending        # show drafts awaiting review
    python manage.py show <post_id>      # print one draft's full text
    python manage.py mark-posted <id>    # record that you posted it
"""

import argparse
import sys
from datetime import datetime, timezone

from app.memory.database import Database

STATUS_PENDING_APPROVAL = "pending_approval"
STATUS_POSTED = "posted"


def cmd_list_pending(database: Database) -> int:
    """Print every draft currently awaiting review.

    Args:
        database: The business database to read from.

    Returns:
        Process exit code (always 0).
    """
    posts = database.list_posts(status=STATUS_PENDING_APPROVAL)
    if not posts:
        print("No drafts are currently pending approval.")
        return 0

    for post in posts:
        preview = post["content"].strip().splitlines()[0] if post["content"] else ""
        print(f"[{post['id']}] {post['topic']}")
        print(f"    created_at: {post['created_at']}")
        if preview:
            print(f"    preview:    {preview[:100]}")
        print()
    return 0


def cmd_show(database: Database, post_id: int) -> int:
    """Print a single post's full stored content.

    Args:
        database: The business database to read from.
        post_id: The id of the post to show.

    Returns:
        Process exit code: 0 if found, 1 if no such post exists.
    """
    post = database.get_post(post_id)
    if post is None:
        print(f"No post with id {post_id}.", file=sys.stderr)
        return 1

    print(f"Post {post['id']} -- {post['topic']} (status: {post['status']})")
    print("-" * 60)
    print(post["content"] or "(no content yet)")
    return 0


def cmd_mark_posted(database: Database, post_id: int) -> int:
    """Mark a post as manually posted to LinkedIn.

    Args:
        database: The business database to update.
        post_id: The id of the post that was posted.

    Returns:
        Process exit code: 0 if updated, 1 if no such post exists.
    """
    post = database.get_post(post_id)
    if post is None:
        print(f"No post with id {post_id}.", file=sys.stderr)
        return 1

    published_at = datetime.now(timezone.utc).isoformat()
    database.update_post_status(post_id, status=STATUS_POSTED, published_at=published_at)
    database.log_agent_action("manage.py", f"marked_posted:post:{post_id}")
    print(f"Post {post_id} marked as posted at {published_at}.")
    return 0


def main() -> int:
    """Parse CLI arguments and dispatch to the matching command.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-pending", help="List drafts awaiting approval.")

    show_parser = subparsers.add_parser("show", help="Print a draft's full text.")
    show_parser.add_argument("post_id", type=int)

    mark_parser = subparsers.add_parser(
        "mark-posted", help="Record that you posted a draft on LinkedIn."
    )
    mark_parser.add_argument("post_id", type=int)

    args = parser.parse_args()
    database = Database()

    if args.command == "list-pending":
        return cmd_list_pending(database)
    if args.command == "show":
        return cmd_show(database, args.post_id)
    if args.command == "mark-posted":
        return cmd_mark_posted(database, args.post_id)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
