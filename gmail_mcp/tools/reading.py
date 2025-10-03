"""MCP tools for email reading operations."""

from typing import Optional, List, Union
import json
import logging

from mcp.server import FastMCP
from fastapi import HTTPException
from mcp.server.fastmcp.server import Context

from ..services import GmailService
from ..models import EmailListRequest, SearchEmailsRequest, MessageFormat
from ..dependencies import get_access_token, get_gmail_service, parse_comma_separated_list


logger = logging.getLogger(__name__)


def register_reading_tools(mcp: FastMCP):
    """Register email reading tools with MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def gmail_get_emails(
        ctx: Context,
        max_results: int = 10,
        label_ids: Optional[str] = None,
        query: Optional[str] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        newer_than: Optional[str] = None,
        older_than: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Get list of emails from Gmail.

        Args:
            max_results: Maximum number of emails to return (1-500)
            label_ids: Filter by label IDs (comma-separated string, e.g., 'INBOX,UNREAD')
            query: Gmail search query (e.g., 'from:example@gmail.com')
            after_date: Get emails after this date (YYYY-MM-DD or YYYY/MM/DD)
            before_date: Get emails before this date (YYYY-MM-DD or YYYY/MM/DD)
            newer_than: Get emails newer than timeframe (e.g., '1d', '2w', '3m', '1y')
            older_than: Get emails older than timeframe (e.g., '1d', '2w', '3m', '1y')
            include_spam_trash: Include spam and trash emails
            page_token: Token for pagination
            format: Message format (MINIMAL, COMPACT, FULL, RAW, METADATA)

        Returns:
            JSON string with email list response

        Format Details:
            - MINIMAL: id, threadId, labelIds only
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Fetching {max_results} emails with format {format}")

            # GmailService is injected with the access token already configured

            # Parse comma-separated label_ids into list
            label_ids_list = parse_comma_separated_list(label_ids) or []

            # Create request object
            email_request = EmailListRequest(
                max_results=max_results,
                label_ids=label_ids_list,
                query=query,
                after_date=after_date,
                before_date=before_date,
                newer_than=newer_than,
                older_than=older_than,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            # Get emails with specified format
            response = await gmail_service.list_messages(email_request, format.value)

            logger.info(f"Retrieved {len(response.messages)} emails")

            return json.dumps(response.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get emails: {str(e)}")

    @mcp.tool()
    async def gmail_get_email_by_id(
        ctx: Context,
        email_id: str,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Get specific email by ID.

        Args:
            email_id: Gmail message ID
            format: Email format (MINIMAL, COMPACT, FULL, RAW, METADATA)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with email details

        Format Details:
            - MINIMAL: id, threadId, labelIds only (fastest)
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Fetching email {email_id} with format {format}")

            # GmailService is injected with the access token already configured
            message = await gmail_service.get_message(email_id, format.value)

            logger.info(f"Retrieved email: {message.subject}")

            return json.dumps(message.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting email {email_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get email: {str(e)}")

    @mcp.tool()
    async def gmail_search_emails(
        ctx: Context,
        query: str,
        max_results: int = 10,
        label_ids: Optional[str] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        newer_than: Optional[str] = None,
        older_than: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Search emails using Gmail search syntax.

        Args:
            query: Gmail search query (e.g., 'from:example@gmail.com subject:urgent')
            max_results: Maximum number of results (1-500)
            label_ids: Filter by label IDs (comma-separated string)
            after_date: Search emails after this date (YYYY-MM-DD or YYYY/MM/DD)
            before_date: Search emails before this date (YYYY-MM-DD or YYYY/MM/DD)
            newer_than: Search emails newer than timeframe (e.g., '1d', '2w', '3m', '1y')
            older_than: Search emails older than timeframe (e.g., '1d', '2w', '3m', '1y')
            include_spam_trash: Include spam and trash in search
            page_token: Token for pagination
            format: Message format (MINIMAL, COMPACT, FULL, RAW, METADATA)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with search results

        Format Details:
            - MINIMAL: id, threadId, labelIds only (fastest, but limited info)
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended for search)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Searching emails with query: {query}, format: {format}")

            # Parse comma-separated label_ids into list
            label_ids_list = parse_comma_separated_list(label_ids) or []

            search_request = SearchEmailsRequest(
                query=query,
                max_results=max_results,
                label_ids=label_ids_list,
                after_date=after_date,
                before_date=before_date,
                newer_than=newer_than,
                older_than=older_than,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            response = await gmail_service.search_messages(search_request, format.value)

            logger.info(f"Found {len(response.messages)} matching emails")

            return json.dumps(response.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to search emails: {str(e)}")

    @mcp.tool()
    async def gmail_get_labels(ctx: Context) -> str:
        """Get all Gmail labels.

        Args:
            ctx: MCP context for logging and progress

        Returns:
            JSON string with labels list
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info("Fetching Gmail labels")

            # GmailService is injected with the access token already configured
            labels = await gmail_service.list_labels()

            logger.info(f"Retrieved {len(labels)} labels")

            return json.dumps([label.model_dump() for label in labels.labels], default=str)

        except Exception as e:
            logger.error(f"Error getting labels: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get labels: {str(e)}")

    @mcp.tool()
    async def gmail_get_profile(ctx: Context) -> str:
        """Get Gmail profile information.

        Args:
            ctx: MCP context for logging and progress

        Returns:
            JSON string with profile information
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info("Fetching Gmail profile")

            profile = await gmail_service.get_profile()

            logger.info(f"Retrieved profile for {profile.email_address}")

            return json.dumps(profile.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

    @mcp.tool()
    async def gmail_get_my_sent_emails(
        ctx: Context,
        max_results: int = 10,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        newer_than: Optional[str] = None,
        older_than: Optional[str] = None,
        query: Optional[str] = None,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Get emails sent by the authenticated user.

        Args:
            max_results: Maximum number of sent emails to return (1-500)
            after_date: Get sent emails after this date (YYYY-MM-DD or YYYY/MM/DD)
            before_date: Get sent emails before this date (YYYY-MM-DD or YYYY/MM/DD)
            newer_than: Get sent emails newer than timeframe (e.g., '1d', '2w', '3m', '1y')
            older_than: Get sent emails older than timeframe (e.g., '1d', '2w', '3m', '1y')
            query: Additional Gmail search query to combine with sent filter
            page_token: Token for pagination
            format: Message format (MINIMAL, COMPACT, FULL, RAW, METADATA)

        Returns:
            JSON string with sent emails list response

        Format Details:
            - MINIMAL: id, threadId, labelIds only (fastest, but limited info)
            - COMPACT: MINIMAL + subject, sender, date, body_text (recommended)
            - FULL: Complete message including body, headers, attachments
            - RAW: Raw RFC2822 message
            - METADATA: Headers and labels only (no body)
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            logger.info(f"Fetching {max_results} sent emails with format {format}")

            # Create request object with SENT label filter
            email_request = EmailListRequest(
                max_results=max_results,
                label_ids=["SENT"],  # Always filter by SENT label
                query=query,
                after_date=after_date,
                before_date=before_date,
                newer_than=newer_than,
                older_than=older_than,
                include_spam_trash=False,  # Don't include spam/trash for sent emails
                page_token=page_token,
            )

            # Get emails with specified format
            response = await gmail_service.list_messages(email_request, format.value)

            logger.info(f"Retrieved {len(response.messages)} sent emails")

            return json.dumps(response.model_dump(), default=str)

        except Exception as e:
            logger.error(f"Error getting sent emails: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get sent emails: {str(e)}")
