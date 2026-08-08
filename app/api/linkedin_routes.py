"""API routes for LinkedIn post management."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.agent.linkedin_agent import LinkedInAgent
from app.memory.database import Database

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])


@router.get("/posts")
async def list_posts(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all posts or filter by status.
    
    Args:
        status: Optional status filter (e.g., "pending_approval", "approved", "published").
    
    Returns:
        A list of post dictionaries.
    """
    db = Database()
    return db.list_posts(status=status)


@router.get("/posts/{post_id}")
async def get_post(post_id: int) -> Dict[str, Any]:
    """Get a specific post by ID.
    
    Args:
        post_id: The ID of the post to retrieve.
    
    Returns:
        The post dictionary.
    
    Raises:
        HTTPException: If the post is not found.
    """
    db = Database()
    post = db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post("/generate/idea")
async def generate_idea() -> Dict[str, Any]:
    """Generate a new post idea (research + topic selection).
    
    This runs the Monday workflow step: researches trending topics
    and creates a new post idea with status "idea".
    
    Returns:
        A dict with post_id and the content brief.
    """
    agent = LinkedInAgent()
    result = agent.generate_post_idea()
    return {
        "message": "Post idea generated successfully",
        "post_id": result["post_id"],
        "topic": result["brief"]["topic"],
        "status": "idea"
    }


@router.post("/generate/draft")
async def generate_draft(post_id: Optional[int] = None) -> Dict[str, Any]:
    """Generate a draft post content.
    
    This runs the Wednesday workflow step: takes an existing idea
    (or generates a new topic) and creates a full draft with status
    "pending_approval".
    
    Args:
        post_id: Optional ID of an existing idea to draft. If not provided,
                 a new topic will be researched and drafted.
    
    Returns:
        A dict with post_id, topic, content, and status.
    
    Raises:
        HTTPException: If the post_id is provided but not found.
    """
    agent = LinkedInAgent()
    db = Database()
    
    # Validate post_id if provided
    if post_id is not None:
        existing_post = db.get_post(post_id)
        if not existing_post:
            raise HTTPException(status_code=404, detail="Post not found")
        if existing_post["status"] != "idea":
            raise HTTPException(
                status_code=400, 
                detail=f"Post must have status 'idea', current status: {existing_post['status']}"
            )
    
    result = agent.generate_post_draft(post_id=post_id)
    return {
        "message": "Post draft generated successfully - awaiting approval",
        "post_id": result["post_id"],
        "topic": result["topic"],
        "content": result["content"],
        "status": result["status"]
    }


@router.post("/posts/{post_id}/approve")
async def approve_post(post_id: int) -> Dict[str, Any]:
    """Approve a post for publishing.
    
    Changes the post status from "pending_approval" to "approved".
    After approval, the post can be published to LinkedIn.
    
    Args:
        post_id: The ID of the post to approve.
    
    Returns:
        A confirmation message.
    
    Raises:
        HTTPException: If the post is not found or not in pending_approval status.
    """
    db = Database()
    post = db.get_post(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["status"] != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Post must have status 'pending_approval' to approve, current status: {post['status']}"
        )
    
    db.update_post_status(post_id, "approved")
    
    return {
        "message": "Post approved successfully - ready for publishing",
        "post_id": post_id,
        "status": "approved"
    }


@router.post("/posts/{post_id}/publish")
async def publish_post(post_id: int) -> Dict[str, Any]:
    """Publish an approved post to LinkedIn.
    
    This endpoint will integrate with LinkedIn API to publish the post.
    Currently returns a mock response until LinkedIn API integration is complete.
    
    Args:
        post_id: The ID of the post to publish.
    
    Returns:
        A dict with publishing status and LinkedIn post URL (when available).
    
    Raises:
        HTTPException: If the post is not found or not approved.
    """
    db = Database()
    post = db.get_post(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Post must be approved before publishing, current status: {post['status']}"
        )
    
    # TODO: Integrate with LinkedIn API for actual publishing
    # For now, simulate successful publishing
    from datetime import datetime, timezone
    published_at = datetime.now(timezone.utc).isoformat()
    
    db.update_post_status(post_id, "published", published_at=published_at)
    
    return {
        "message": "Post published successfully to LinkedIn",
        "post_id": post_id,
        "status": "published",
        "published_at": published_at,
        "linkedin_url": f"https://www.linkedin.com/feed/update/urn:li:share:{post_id}",  # Mock URL
        "content": post["content"]
    }


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int) -> Dict[str, Any]:
    """Delete a post (only drafts or rejected posts).
    
    Args:
        post_id: The ID of the post to delete.
    
    Returns:
        A confirmation message.
    
    Raises:
        HTTPException: If the post is not found or cannot be deleted.
    """
    db = Database()
    post = db.get_post(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["status"] in ["published"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete published posts"
        )
    
    # Note: SQLite doesn't have foreign key constraints enabled by default,
    # so we can safely delete. In production, you might want to soft-delete.
    with db._connect() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    
    return {
        "message": "Post deleted successfully",
        "post_id": post_id
    }


@router.patch("/posts/{post_id}/edit")
async def edit_post(post_id: int, content: str) -> Dict[str, Any]:
    """Edit a draft or pending post.
    
    Allows manual editing of post content before approval or publishing.
    
    Args:
        post_id: The ID of the post to edit.
        content: The new content for the post.
    
    Returns:
        The updated post.
    
    Raises:
        HTTPException: If the post is not found or cannot be edited.
    """
    db = Database()
    post = db.get_post(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["status"] == "published":
        raise HTTPException(
            status_code=400,
            detail="Cannot edit published posts"
        )
    
    db.update_post_content(post_id, content)
    
    updated_post = db.get_post(post_id)
    return {
        "message": "Post updated successfully",
        "post": updated_post
    }
