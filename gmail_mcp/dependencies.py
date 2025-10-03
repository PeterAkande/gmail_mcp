"""Dependency injection functions for MCP tools."""

from typing import List, Optional
from fastapi import HTTPException, Depends
from mcp.server.fastmcp.server import Context
from starlette.requests import Request

from gmail_mcp.auth import TokenInfo

from .services import GmailService


def get_access_token(ctx: Context) -> str:
    """Extract access token from MCP context.

    Args:
        ctx: MCP context containing request information

    Returns:
        Access token string

    Raises:
        HTTPException: If no valid token is found
    """
    if not ctx or not ctx.request_context:
        raise HTTPException(status_code=401, detail="No request context available")

    request: Request = ctx.request_context.request
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid access token provided")

    return auth_header.replace("Bearer ", "")


def get_gmail_service(access_token: str = Depends(get_access_token)) -> GmailService:
    """Get GmailService instance with access token.

    Args:
        access_token: OAuth access token

    Returns:
        Configured GmailService instance
    """
    token_info = TokenInfo(
        access_token=access_token,
        email="",  # Email can be fetched if needed
        scope="",  # Scope can be fetched if needed
    )
    return GmailService(token_info=token_info)
    

def parse_comma_separated_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into a list of strings.
    
    Args:
        value: Comma-separated string or None
        
    Returns:
        List of strings or None
    """
    if value is None or value.strip() == "":
        return None
    # Split by comma and strip whitespace from each item
    return [item.strip() for item in value.split(',') if item.strip()]