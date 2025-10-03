"""MCP tools for email sending and management operations."""

from typing import Optional, List, Union
import json
import logging

from mcp.server import FastMCP
from fastapi import HTTPException
from mcp.server.fastmcp.server import Context

from ..services import GmailService
from ..models import SendEmailRequest, ModifyLabelsRequest, CreateLabelRequest
from ..dependencies import get_access_token, get_gmail_service, parse_comma_separated_list


logger = logging.getLogger(__name__)


def register_management_tools(mcp: FastMCP):
    """Register email management tools with MCP server.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.tool()
    async def gmail_send_email(
        ctx: Context,
        to: str,
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[str] = None,
    ) -> str:
        """Send an email.

        Args:
            to: Recipient email addresses (comma-separated string)
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body
            cc: CC recipients (comma-separated string)
            bcc: BCC recipients (comma-separated string)
            attachments: File paths to attach (comma-separated string)
            ctx: MCP context for logging and progress
            gmail_service: GmailService instance (injected)

        Returns:
            JSON string with send status and message ID
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
            attachments_list = parse_comma_separated_list(attachments)

            # GmailService is configured with the access token

            request = SendEmailRequest(
                to=to_list,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc_list,
                bcc=bcc_list,
                attachments=attachments_list,
            )

            message_id = await gmail_service.send_message(request)

            result = {
                "success": True,
                "message_id": message_id,
                "message": f"Email sent successfully to {', '.join(to_list) if to_list else 'recipients'}",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    @mcp.tool()
    async def gmail_reply_to_email(
        ctx: Context,
        message_id: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        reply_all: bool = False,
    ) -> str:
        """Reply to an email.

        Args:
            message_id: ID of message to reply to
            body_text: Plain text reply body
            body_html: HTML reply body
            reply_all: Reply to all recipients
            ctx: MCP context for logging and progress

        Returns:
            JSON string with reply status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            if not body_text and not body_html:
                return json.dumps({"error": "Either body_text or body_html must be provided"})

            # GmailService is injected via dependency injection

            # Get original message to extract reply info
            original_message = await gmail_service.get_message(message_id)

            # Prepare reply
            to_addresses = [original_message.sender] if original_message.sender else []

            if reply_all and original_message.recipient:
                # Add other recipients for reply-all (simplified)
                # In production, you'd parse all To/CC recipients from headers
                pass

            subject = original_message.subject or ""
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"

            request = SendEmailRequest(
                to=to_addresses,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                thread_id=original_message.thread_id,
                in_reply_to=message_id,
            )

            reply_message_id = await gmail_service.send_message(request)

            result = {
                "success": True,
                "reply_message_id": reply_message_id,
                "original_message_id": message_id,
                "message": f"Reply sent successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in reply_to_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_mark_as_read(
        ctx: Context,
        message_id: str,
    ) -> str:
        """Mark an email as read.

        Args:
            message_id: Message ID to mark as read
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Mark message as read by removing UNREAD label

            request = ModifyLabelsRequest(remove_label_ids=["UNREAD"])
            await gmail_service.modify_message_labels(message_id, request)

            result = {"success": True, "message_id": message_id, "message": "Email marked as read"}

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in mark_as_read: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_mark_as_unread(
        ctx: Context,
        message_id: str,
    ) -> str:
        """Mark an email as unread.

        Args:
            message_id: Message ID to mark as unread
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Mark message as unread by adding UNREAD label

            request = ModifyLabelsRequest(add_label_ids=["UNREAD"])
            await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "message": "Email marked as unread",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in mark_as_unread: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_archive_email(
        ctx: Context,
        message_id: str,
    ) -> str:
        """Archive an email (remove from INBOX).

        Args:
            message_id: Message ID to archive
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Archive email by removing INBOX label

            request = ModifyLabelsRequest(remove_label_ids=["INBOX"])
            await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "message": "Email archived successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in archive_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_unarchive_email(
        ctx: Context,
        message_id: str,
    ) -> str:
        """Unarchive an email (add back to INBOX).

        Args:
            message_id: Message ID to unarchive
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Unarchive email by adding INBOX label

            request = ModifyLabelsRequest(add_label_ids=["INBOX"])
            await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "message": "Email unarchived successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in unarchive_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_delete_email(ctx: Context, message_id: str) -> str:
        """Delete an email permanently.

        Args:
            message_id: Message ID to delete
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            success = await gmail_service.delete_message(message_id)

            if success:
                result = {
                    "success": True,
                    "message_id": message_id,
                    "message": "Email deleted successfully",
                }
            else:
                result = {
                    "success": False,
                    "message_id": message_id,
                    "message": "Failed to delete email",
                }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in delete_email: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_add_label(ctx: Context, message_id: str, label_ids: str) -> str:
        """Add labels to an email.

        Args:
            message_id: Message ID
            label_ids: Label IDs to add (comma-separated string)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Parse comma-separated string into list
            label_ids_list = parse_comma_separated_list(label_ids)
            request = ModifyLabelsRequest(add_label_ids=label_ids_list)
            updated_message = await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "added_labels": label_ids_list,
                "current_labels": updated_message.label_ids,
                "message": f"Labels {', '.join(label_ids_list) if label_ids_list else 'none'} added successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in add_label: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_remove_label(ctx: Context, message_id: str, label_ids: str) -> str:
        """Remove labels from an email.

        Args:
            message_id: Message ID
            label_ids: Label IDs to remove (comma-separated string)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with operation status
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            # Parse comma-separated string into list
            label_ids_list = parse_comma_separated_list(label_ids)
            request = ModifyLabelsRequest(remove_label_ids=label_ids_list)
            updated_message = await gmail_service.modify_message_labels(message_id, request)

            result = {
                "success": True,
                "message_id": message_id,
                "removed_labels": label_ids_list,
                "current_labels": updated_message.label_ids,
                "message": f"Labels {', '.join(label_ids_list) if label_ids_list else 'none'} removed successfully",
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in remove_label: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)

    @mcp.tool()
    async def gmail_create_label(
        ctx: Context,
        name: str,
        message_list_visibility: str = "show",
        label_list_visibility: str = "labelShow",
    ) -> str:
        """Create a new Gmail label.

        Args:
            name: Label name
            message_list_visibility: Message list visibility (show/hide)
            label_list_visibility: Label list visibility (labelShow/labelHide)
            ctx: MCP context for logging and progress

        Returns:
            JSON string with created label information
        """
        access_token: str = get_access_token(ctx)
        gmail_service: GmailService = get_gmail_service(access_token=access_token)
        try:
            request = CreateLabelRequest(
                name=name,
                message_list_visibility=message_list_visibility,
                label_list_visibility=label_list_visibility,
            )

            label = await gmail_service.create_label(request)

            result = {
                "success": True,
                "label": label.model_dump(),
                "message": f"Label '{name}' created successfully",
            }

            return json.dumps(result, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error in create_label: {e}")
            return json.dumps({"error": str(e), "success": False}, indent=2)
