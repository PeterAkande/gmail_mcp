from typing import Optional, List
import json
import logging

from mcp.server import FastMCP
from fastapi import HTTPException
from mcp.server.fastmcp.server import Context

from ..services import GmailService
from ..models import ForwardEmailRequest, CreateDraftRequest, MessageFormat, ThreadListRequest
from ..dependencies import get_access_token, get_gmail_service, parse_comma_separated_list


logger = logging.getLogger(__name__)


def register_advanced_tools(mcp: FastMCP):
    """Register advanced Gmail tools with MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def gmail_forward_email(
        ctx: Context,
        message_id: str,
        to: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        additional_message: Optional[str] = None,
    ) -> str:
        """Forward an email to other recipients.

        Args:
            message_id: ID of email to forward
            to: Recipient email addresses (comma-separated string)
            cc: CC recipients (comma-separated string)
            bcc: BCC recipients (comma-separated string)
            additional_message: Additional message to include with forward
            ctx: MCP context for logging and progress

        Returns:
            JSON string with forward status and message ID
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Parse comma-separated strings into lists
            to_list = parse_comma_separated_list(to)
            cc_list = parse_comma_separated_list(cc)
            bcc_list = parse_comma_separated_list(bcc)

            # Forward the email using the Gmail service
            request = ForwardEmailRequest(
                to=to_list,
                cc=cc_list,
                bcc=bcc_list,
                additional_message=additional_message,
            )

            forwarded_message_id = await gmail_service.forward_message(message_id, request)

            result = {
                "success": True,
                "forwarded_message_id": forwarded_message_id,
                "original_message_id": message_id,
                "message": f"Email forwarded successfully to {', '.join(to_list) if to_list else 'recipients'}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in forward_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_move_to_folder(
        ctx: Context,
        message_id: str,
        folder_label_id: str,
        remove_inbox: bool = True,
    ) -> str:
        """Move an email to a specific folder/label.

        Args:
            message_id: Message ID to move
            folder_label_id: Target folder/label ID (e.g., 'TRASH', 'SPAM', or custom label ID)
            remove_inbox: Whether to remove from INBOX when moving
            ctx: MCP context for logging and progress

        Returns:
            JSON string with move status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:

            from ..models import ModifyLabelsRequest

            add_labels = [folder_label_id]
            remove_labels = []

            if remove_inbox and folder_label_id not in ["INBOX"]:
                remove_labels.append("INBOX")

            request = ModifyLabelsRequest(
                add_label_ids=add_labels,
                remove_label_ids=remove_labels if remove_labels else None,
            )

            updated_message = await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "moved_to": folder_label_id,
                "current_labels": updated_message.label_ids,
                "message": f"Email moved to {folder_label_id}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in move_to_folder: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_get_threads(
        ctx: Context,
        max_results: int = 10,
        label_ids: Optional[str] = None,
        query: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> str:
        """Get email threads/conversations.

        Args:
            max_results: Maximum number of threads to return (1-500)
            label_ids: Filter by label IDs (comma-separated string)
            query: Gmail search query
            include_spam_trash: Include spam and trash
            page_token: Token for pagination
            after: Show threads after this date (YYYY/MM/DD format)
            before: Show threads before this date (YYYY/MM/DD format)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with threads list
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # GmailService is injected via dependency injection
            
            # Parse comma-separated label_ids into list
            label_ids_list = parse_comma_separated_list(label_ids)

            request = ThreadListRequest(
                max_results=max_results,
                label_ids=label_ids_list,
                q=query,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
                after=after,
                before=before,
            )

            response = await gmail_service.list_threads(request)

            result = {
                "threads": [thread.model_dump() for thread in response.threads],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
                "count": len(response.threads),
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_threads: {e}")
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def gmail_get_thread_by_id(
        ctx: Context,
        thread_id: str,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> str:
        """Get a specific email thread by ID.

        Args:
            thread_id: Thread ID to retrieve
            format: Message format (minimal, full, metadata, raw)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with thread details
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            thread = await gmail_service.get_thread(thread_id, format)

            result = {
                "success": True,
                "thread": thread.model_dump(),
                "message_count": len(thread.messages),
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_thread_by_id: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_create_draft(
        ctx: Context,
        to: str,
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> str:
        """Create a draft email.

        Args:
            to: Recipient email addresses (comma-separated string)
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            cc: CC recipients (comma-separated string)
            bcc: BCC recipients (comma-separated string)
            thread_id: Thread ID for replies
            in_reply_to: Message ID being replied to
            ctx: MCP context for logging and progress

        Returns:
            JSON string with draft creation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            if not body_text and not body_html:
                return json.dumps({"error": "Either body_text or body_html must be provided"})

            # Parse comma-separated strings into lists
            to_list = parse_comma_separated_list(to)
            cc_list = parse_comma_separated_list(cc)
            bcc_list = parse_comma_separated_list(bcc)

            # GmailService is injected via dependency injection
            request = CreateDraftRequest(
                to=to_list,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc_list,
                bcc=bcc_list,
                thread_id=thread_id,
                in_reply_to=in_reply_to,
            )

            draft_id = await gmail_service.create_draft(request)

            result = {
                "success": True,
                "draft_id": draft_id,
                "message": f"Draft created successfully for {', '.join(to_list) if to_list else 'recipients'}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in create_draft: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_get_drafts(
        ctx: Context,
        max_results: int = 10,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
        query: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> str:
        """Get list of draft emails.

        Args:
            max_results: Maximum number of drafts to return
            page_token: Token for pagination
            format: Message format
            query: Search query (searches in subject and body)
            after: Show drafts after this date (YYYY/MM/DD format)
            before: Show drafts before this date (YYYY/MM/DD format)
            ctx: MCP context for logging and progress

        Returns:
            JSON string containing drafts list
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Import DraftListRequest
            from ..models import DraftListRequest

            request = DraftListRequest(
                max_results=max_results,
                page_token=page_token,
                message_format=format,
                q=query,
                after=after,
                before=before,
            )

            response = await gmail_service.list_drafts(request)

            result = {
                "drafts": [draft.model_dump() for draft in response.drafts],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
                "count": len(response.drafts),
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_drafts: {e}")
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def gmail_get_draft_by_id(
        ctx: Context,
        draft_id: str,
        format: MessageFormat = MessageFormat.FULL,
    ) -> str:
        """Get a specific draft by ID.

        Args:
            draft_id: Draft ID to retrieve
            format: Message format (minimal, full, metadata, raw)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with draft details
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            draft = await gmail_service.get_draft(draft_id, format)

            result = {
                "success": True,
                "draft": draft.model_dump(),
                "message": f"Draft {draft_id} retrieved successfully",
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_draft_by_id: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_send_draft(
        ctx: Context,
        draft_id: str,
    ) -> str:
        """Send an existing draft email.

        Args:
            draft_id: Draft ID to send
            ctx: MCP context for logging and progress

        Returns:
            JSON string with send status and message ID
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Send the draft email

            message_id = await gmail_service.send_draft(draft_id)

            result = {
                "success": True,
                "message_id": message_id,
                "draft_id": draft_id,
                "message": "Draft sent successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in send_draft: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_get_attachments(
        ctx: Context,
        message_id: str,
        attachment_id: Optional[str] = None,
    ) -> str:
        """Download email attachments.

        Args:
            message_id: Message ID containing attachments
            attachment_id: Specific attachment ID (if None, returns info about all attachments)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with attachment data or list of attachments
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # GmailService is injected via dependency injection

            if attachment_id:
                # Download specific attachment
                attachment = await gmail_service.get_attachment(message_id, attachment_id)

                result = {
                    "success": True,
                    "attachment": attachment.model_dump(),
                    "message": f"Attachment {attachment_id} downloaded successfully",
                }
            else:
                # Get message to list all attachments
                message = await gmail_service.get_message(message_id)

                result = {
                    "success": True,
                    "message_id": message_id,
                    "attachments": [att.model_dump() for att in message.attachments],
                    "count": len(message.attachments),
                    "message": f"Found {len(message.attachments)} attachments",
                }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in get_attachments: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
