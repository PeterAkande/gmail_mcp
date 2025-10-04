#!/usr/bin/env python3
"""
Gmail Service Test Script

A standalone script to test Gmail functions directly with an access token.
No MCP server required - just supply your access token and test away!

Usage:
    python mail_test_main.py

Requirements:
    - Valid Gmail OAuth access token
    - Gmail API access enabled
"""

import asyncio
import json
import logging
from typing import Optional, List
from gmail_mcp.services import GmailService
from gmail_mcp.models import (
    EmailListRequest,
    SearchEmailsRequest,
    SendEmailRequest,
    ModifyLabelsRequest,
    CreateLabelRequest,
    ForwardEmailRequest,
    CreateDraftRequest,
    ThreadListRequest,
    MessageFormat,
)
from gmail_mcp.auth import TokenInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GmailTester:
    """Direct Gmail API tester without MCP."""

    def __init__(self, access_token: str):
        """Initialize with access token."""
        self.token_info = TokenInfo(
            access_token=access_token,
            email="",  # Email can be empty for testing
            scope="",  # Scope can be empty for testing
        )
        self.service = GmailService(self.token_info)
        logger.info("✅ Gmail service initialized")

    # === READING FUNCTIONS ===

    async def get_emails(
        self,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        newer_than: Optional[str] = None,
        older_than: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> dict:
        """Get list of emails from Gmail."""
        try:
            logger.info(f"📬 Getting {max_results} emails with format {format}")

            request = EmailListRequest(
                max_results=max_results,
                label_ids=label_ids or [],
                query=query,
                after_date=after_date,
                before_date=before_date,
                newer_than=newer_than,
                older_than=older_than,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            response = await self.service.list_messages(request, format.value)
            logger.info(f"✅ Retrieved {len(response.messages)} emails")

            return {
                "success": True,
                "count": len(response.messages),
                "messages": [msg.model_dump() for msg in response.messages],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
            }

        except Exception as e:
            logger.error(f"❌ Error getting emails: {e}")
            return {"success": False, "error": str(e)}

    async def get_my_sent_emails(
        self,
        max_results: int = 10,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        newer_than: Optional[str] = None,
        older_than: Optional[str] = None,
        query: Optional[str] = None,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> dict:
        """Get emails sent by the authenticated user."""
        try:
            logger.info(f"📤 Getting {max_results} sent emails with format {format}")

            # Use the regular get_emails method but with SENT label filter
            request = EmailListRequest(
                max_results=max_results,
                label_ids=["SENT"],
                query=query,
                after_date=after_date,
                before_date=before_date,
                newer_than=newer_than,
                older_than=older_than,
                include_spam_trash=False,
                page_token=page_token,
            )

            response = await self.service.list_messages(request, format.value)
            logger.info(f"✅ Retrieved {len(response.messages)} sent emails")

            return {
                "success": True,
                "count": len(response.messages),
                "messages": [msg.model_dump() for msg in response.messages],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
            }

        except Exception as e:
            logger.error(f"❌ Error getting sent emails: {e}")
            return {"success": False, "error": str(e)}

    async def get_email_by_id(
        self,
        email_id: str,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> dict:
        """Get specific email by ID."""
        try:
            logger.info(f"📧 Getting email {email_id} with format {format}")

            message = await self.service.get_message(email_id, format.value)
            logger.info(f"✅ Retrieved email: {message.subject or 'No Subject'}")

            return {"success": True, "message": message.model_dump()}

        except Exception as e:
            logger.error(f"❌ Error getting email {email_id}: {e}")
            return {"success": False, "error": str(e)}

    async def search_emails(
        self,
        query: str,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        newer_than: Optional[str] = None,
        older_than: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> dict:
        """Search emails using Gmail search syntax."""
        try:
            logger.info(f"🔍 Searching emails: '{query}' with format {format}")

            request = SearchEmailsRequest(
                query=query,
                max_results=max_results,
                label_ids=label_ids or [],
                after_date=after_date,
                before_date=before_date,
                newer_than=newer_than,
                older_than=older_than,
                include_spam_trash=include_spam_trash,
                page_token=page_token,
            )

            response = await self.service.search_messages(request, format.value)
            logger.info(f"✅ Found {len(response.messages)} matching emails")

            return {
                "success": True,
                "count": len(response.messages),
                "messages": [msg.model_dump() for msg in response.messages],
                "next_page_token": response.next_page_token,
                "result_size_estimate": response.result_size_estimate,
            }

        except Exception as e:
            logger.error(f"❌ Error searching emails: {e}")
            return {"success": False, "error": str(e)}

    async def get_labels(self) -> dict:
        """Get all Gmail labels."""
        try:
            logger.info("🏷️  Getting Gmail labels")

            labels = await self.service.list_labels()
            logger.info(f"✅ Retrieved {len(labels.labels)} labels")

            return {
                "success": True,
                "count": len(labels.labels),
                "labels": [label.model_dump() for label in labels.labels],
            }

        except Exception as e:
            logger.error(f"❌ Error getting labels: {e}")
            return {"success": False, "error": str(e)}

    async def get_profile(self) -> dict:
        """Get Gmail profile information."""
        try:
            logger.info("👤 Getting Gmail profile")

            profile = await self.service.get_profile()
            logger.info(f"✅ Retrieved profile for {profile.email_address}")

            return {"success": True, "profile": profile.model_dump()}

        except Exception as e:
            logger.error(f"❌ Error getting profile: {e}")
            return {"success": False, "error": str(e)}

    # === MANAGEMENT FUNCTIONS ===

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
    ) -> dict:
        """Send an email."""
        try:
            if not body_text and not body_html:
                return {"success": False, "error": "Either body_text or body_html is required"}

            logger.info(f"📤 Sending email to {', '.join(to)}: '{subject}'")

            request = SendEmailRequest(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
            )

            message_id = await self.service.send_message(request)
            logger.info(f"✅ Email sent successfully: {message_id}")

            return {
                "success": True,
                "message_id": message_id,
                "message": f"Email sent successfully to {', '.join(to)}",
            }

        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return {"success": False, "error": str(e)}

    async def mark_as_read(self, message_id: str) -> dict:
        """Mark an email as read."""
        try:
            logger.info(f"👁️  Marking email {message_id} as read")

            request = ModifyLabelsRequest(remove_label_ids=["UNREAD"])
            await self.service.modify_message_labels(message_id, request)

            return {"success": True, "message_id": message_id, "message": "Email marked as read"}

        except Exception as e:
            logger.error(f"❌ Error marking as read: {e}")
            return {"success": False, "error": str(e)}

    async def mark_as_unread(self, message_id: str) -> dict:
        """Mark an email as unread."""
        try:
            logger.info(f"✉️  Marking email {message_id} as unread")

            request = ModifyLabelsRequest(add_label_ids=["UNREAD"])
            await self.service.modify_message_labels(message_id, request)

            return {"success": True, "message_id": message_id, "message": "Email marked as unread"}

        except Exception as e:
            logger.error(f"❌ Error marking as unread: {e}")
            return {"success": False, "error": str(e)}

    async def archive_email(self, message_id: str) -> dict:
        """Archive an email (remove from INBOX)."""
        try:
            logger.info(f"📦 Archiving email {message_id}")

            request = ModifyLabelsRequest(remove_label_ids=["INBOX"])
            await self.service.modify_message_labels(message_id, request)

            return {
                "success": True,
                "message_id": message_id,
                "message": "Email archived successfully",
            }

        except Exception as e:
            logger.error(f"❌ Error archiving email: {e}")
            return {"success": False, "error": str(e)}

    async def unarchive_email(self, message_id: str) -> dict:
        """Unarchive an email (add back to INBOX)."""
        try:
            logger.info(f"📥 Unarchiving email {message_id}")

            # Import ModifyLabelsRequest
            from gmail_mcp.models import ModifyLabelsRequest

            request = ModifyLabelsRequest(add_label_ids=["INBOX"])
            await self.service.modify_message_labels(message_id, request)

            return {
                "success": True,
                "message_id": message_id,
                "message": "Email unarchived successfully",
            }

        except Exception as e:
            logger.error(f"❌ Error unarchiving email: {e}")
            return {"success": False, "error": str(e)}

    async def delete_email(self, message_id: str) -> dict:
        """Delete an email permanently."""
        try:
            logger.info(f"🗑️  Deleting email {message_id}")

            success = await self.service.delete_message(message_id)

            if success:
                return {
                    "success": True,
                    "message_id": message_id,
                    "message": "Email deleted successfully",
                }
            else:
                return {
                    "success": False,
                    "message_id": message_id,
                    "message": "Failed to delete email",
                }

        except Exception as e:
            logger.error(f"❌ Error deleting email: {e}")
            return {"success": False, "error": str(e)}

    # === ADVANCED FUNCTIONS ===

    async def create_draft(
        self,
        to: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> dict:
        """Create a draft email."""
        try:
            if not body_text and not body_html:
                return {"success": False, "error": "Either body_text or body_html is required"}

            logger.info(f"📝 Creating draft to {', '.join(to)}: '{subject}'")

            request = CreateDraftRequest(
                to=to,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                thread_id=thread_id,
                in_reply_to=in_reply_to,
            )

            draft_id = await self.service.create_draft(request)
            logger.info(f"✅ Draft created successfully: {draft_id}")

            return {
                "success": True,
                "draft_id": draft_id,
                "message": f"Draft created successfully for {', '.join(to)}",
            }

        except Exception as e:
            logger.error(f"❌ Error creating draft: {e}")
            return {"success": False, "error": str(e)}

    async def get_drafts(
        self,
        max_results: int = 10,
        page_token: Optional[str] = None,
        query: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> dict:
        """Get list of draft emails."""
        try:
            logger.info(f"📝 Getting {max_results} drafts")

            # Import DraftListRequest
            from gmail_mcp.models import DraftListRequest

            request = DraftListRequest(
                max_results=max_results,
                page_token=page_token,
                q=query,
                after=after,
                before=before,
            )

            response = await self.service.list_drafts(request)
            logger.info(f"✅ Retrieved {len(response.drafts)} drafts")

            return {
                "success": True,
                "count": len(response.drafts),
                "drafts": [draft.model_dump() for draft in response.drafts],
                "next_page_token": response.next_page_token,
            }

        except Exception as e:
            logger.error(f"❌ Error getting drafts: {e}")
            return {"success": False, "error": str(e)}

    async def get_draft_by_id(self, draft_id: str, format: str = "full") -> dict:
        """Get a specific draft by ID."""
        try:
            logger.info(f"📝 Getting draft by ID: {draft_id}")

            draft = await self.service.get_draft(draft_id, format)
            logger.info(f"✅ Retrieved draft")

            return {
                "success": True,
                "draft": draft.model_dump(),
                "message": f"Draft {draft_id} retrieved successfully",
            }

        except Exception as e:
            logger.error(f"❌ Error getting draft by ID: {e}")
            return {"success": False, "error": str(e)}

    async def reply_to_email(
        self,
        message_id: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        reply_all: bool = False,
    ) -> dict:
        """Reply to an email."""
        try:
            logger.info(f"📧 Replying to email: {message_id}")

            if not body_text and not body_html:
                return {"success": False, "error": "Either body_text or body_html must be provided"}

            # Get original message to extract reply info
            original_message = await self.service.get_message(message_id)

            # Prepare reply
            to_addresses = [original_message.sender] if original_message.sender else []

            if reply_all and original_message.recipient:
                # Add other recipients for reply-all (simplified)
                # In production, you'd parse all To/CC recipients from headers
                pass

            subject = original_message.subject or ""
            if not subject.startswith("Re:"):
                subject = f"Re: {subject}"

            # Import SendEmailRequest
            from gmail_mcp.models import SendEmailRequest

            request = SendEmailRequest(
                to=to_addresses,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                thread_id=original_message.thread_id,
                in_reply_to=message_id,
            )

            reply_message_id = await self.service.send_message(request)
            logger.info(f"✅ Reply sent with ID: {reply_message_id}")

            return {
                "success": True,
                "reply_message_id": reply_message_id,
                "original_message_id": message_id,
                "message": "Reply sent successfully",
            }

        except Exception as e:
            logger.error(f"❌ Error replying to email: {e}")
            return {"success": False, "error": str(e)}

    async def forward_email(
        self,
        message_id: str,
        to: List[str],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        additional_message: Optional[str] = None,
    ) -> dict:
        """Forward an email."""
        try:
            logger.info(f"📧 Forwarding email: {message_id}")

            forward_email_request = ForwardEmailRequest(
                to=to,
                cc=cc,
                bcc=bcc,
                additional_message=additional_message,
            )

            response = await self.service.forward_message(message_id, forward_email_request)
            logger.info(f"✅ Email forwarded with ID: {response}")

            return {
                "success": True,
                "message_id": response,
            }

        except Exception as e:
            logger.error(f"❌ Error forwarding email: {e}")
            return {"success": False, "error": str(e)}

    async def move_to_folder(
        self, message_id: str, folder_label_id: str, remove_inbox: bool = True
    ) -> dict:
        """Move email to folder/label."""
        try:
            logger.info(f"📁 Moving email {message_id} to folder {folder_label_id}")

            # Import ModifyLabelsRequest
            from gmail_mcp.models import ModifyLabelsRequest

            add_labels = [folder_label_id]
            remove_labels = []

            if remove_inbox and folder_label_id not in ["INBOX"]:
                remove_labels.append("INBOX")

            request = ModifyLabelsRequest(
                add_label_ids=add_labels,
                remove_label_ids=remove_labels if remove_labels else None,
            )

            updated_message = await self.service.modify_message_labels(message_id, request)
            logger.info(f"✅ Email moved successfully")

            return {
                "success": True,
                "message_id": message_id,
                "moved_to": folder_label_id,
                "current_labels": updated_message.label_ids,
                "message": f"Email moved to {folder_label_id}",
            }

        except Exception as e:
            logger.error(f"❌ Error moving email: {e}")
            return {"success": False, "error": str(e)}

    async def get_threads(
        self,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        page_token: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> dict:
        """Get threads."""
        try:
            logger.info(f"🧵 Getting {max_results} threads")

            # Import ThreadListRequest
            from gmail_mcp.models import ThreadListRequest

            list_threads_request = ThreadListRequest(
                max_results=max_results,
                label_ids=label_ids or [],
                q=query,
                page_token=page_token,
                include_spam_trash=False,
                after=after,
                before=before,
            )

            response = await self.service.list_threads(list_threads_request)
            logger.info(f"✅ Retrieved {len(response.threads)} threads")

            return {
                "success": True,
                "count": len(response.threads),
                "threads": [thread.model_dump() for thread in response.threads],
                "next_page_token": response.next_page_token,
            }

        except Exception as e:
            logger.error(f"❌ Error getting threads: {e}")
            return {"success": False, "error": str(e)}

    async def get_thread_by_id(
        self,
        thread_id: str,
        format: MessageFormat = MessageFormat.COMPACT,
    ) -> dict:
        """Get a specific thread by ID."""
        try:
            logger.info(f"🧵 Getting thread by ID: {thread_id}")

            thread = await self.service.get_thread(thread_id, format)
            logger.info(f"✅ Retrieved thread with {len(thread.messages)} messages")

            return {
                "success": True,
                "thread": thread.model_dump(),
                "message_count": len(thread.messages),
            }

        except Exception as e:
            logger.error(f"❌ Error getting thread by ID: {e}")
            return {"success": False, "error": str(e)}

    async def send_draft(self, draft_id: str) -> dict:
        """Send a draft email."""
        try:
            logger.info(f"📧 Sending draft: {draft_id}")

            response = await self.service.send_draft(draft_id)
            logger.info(f"✅ Draft sent with ID: {response}")

            return {
                "success": True,
                "message_id": response,
            }

        except Exception as e:
            logger.error(f"❌ Error sending draft: {e}")
            return {"success": False, "error": str(e)}

    async def get_attachments(self, message_id: str) -> dict:
        """Get attachments from an email."""
        try:
            logger.info(f"📎 Getting attachments from email: {message_id}")

            # Get message to list all attachments
            message = await self.service.get_message(message_id)
            logger.info(f"✅ Retrieved {len(message.attachments)} attachments")

            return {
                "success": True,
                "message_id": message_id,
                "count": len(message.attachments),
                "attachments": [att.model_dump() for att in message.attachments],
            }

        except Exception as e:
            logger.error(f"❌ Error getting attachments: {e}")
            return {"success": False, "error": str(e)}

    async def add_label(self, message_id: str, label_ids: List[str]) -> dict:
        """Add labels to an email."""
        try:
            logger.info(f"🏷️ Adding labels to email: {message_id}")

            # Import ModifyLabelsRequest
            from gmail_mcp.models import ModifyLabelsRequest

            request = ModifyLabelsRequest(add_label_ids=label_ids)
            updated_message = await self.service.modify_message_labels(message_id, request)
            logger.info(f"✅ Labels added successfully")

            return {
                "success": True,
                "message_id": message_id,
                "added_labels": label_ids,
                "current_labels": updated_message.label_ids,
                "message": f"Labels {', '.join(label_ids)} added successfully",
            }

        except Exception as e:
            logger.error(f"❌ Error adding labels: {e}")
            return {"success": False, "error": str(e)}

    async def remove_label(self, message_id: str, label_ids: List[str]) -> dict:
        """Remove labels from an email."""
        try:
            logger.info(f"🏷️ Removing labels from email: {message_id}")

            request = ModifyLabelsRequest(remove_label_ids=label_ids)

            response = await self.service.modify_message_labels(message_id, request)
            logger.info(f"✅ Labels removed successfully")

            return {"success": True, "message": response}

        except Exception as e:
            logger.error(f"❌ Error removing labels: {e}")
            return {"success": False, "error": str(e)}

    async def create_label(
        self,
        name: str,
        label_list_visibility: str = "labelShow",
        message_list_visibility: str = "show",
    ) -> dict:
        """Create a new label."""
        try:
            logger.info(f"🏷️ Creating label: {name}")

            request = CreateLabelRequest(
                name=name,
                label_list_visibility=label_list_visibility,
                message_list_visibility=message_list_visibility,
            )

            response = await self.service.create_label(request)
            logger.info(f"✅ Label created with ID: {response.id}")

            return {
                "success": True,
                "label_id": response.id,
                "label_name": response.name,
            }

        except Exception as e:
            logger.error(f"❌ Error creating label: {e}")
            return {"success": False, "error": str(e)}


# === INTERACTIVE TEST FUNCTIONS ===


async def run_tests():
    """Interactive test runner."""
    print("🔑 Gmail MCP Tester")
    print("==================")

    # Get access token
    access_token = input("Enter your Gmail OAuth access token: ").strip()
    if not access_token:
        print("❌ Access token is required!")
        return


    # Initialize tester
    try:
        tester = GmailTester(access_token)
    except Exception as e:
        print(f"❌ Failed to initialize Gmail service: {e}")
        return

    while True:
        print("\n📋 Available Tests:")
        print("===================")
        print("Reading Functions:")
        print("  1. Get emails (list)")
        print("  2. Get my sent emails")
        print("  3. Get email by ID")
        print("  4. Search emails")
        print("  5. Get labels")
        print("  6. Get profile")
        print("\nManagement Functions:")
        print("  7. Send email")
        print("  8. Reply to email")
        print("  9. Mark as read")
        print(" 10. Mark as unread")
        print(" 11. Archive email")
        print(" 12. Unarchive email")
        print(" 13. Delete email")
        print("\nLabel Management:")
        print(" 14. Add label to email")
        print(" 15. Remove label from email")
        print(" 16. Create new label")
        print("\nAdvanced Functions:")
        print(" 17. Forward email")
        print(" 18. Move to folder")
        print(" 19. Get threads")
        print(" 20. Get thread by ID")
        print(" 21. Create draft")
        print(" 22. Get drafts")
        print(" 23. Get draft by ID")
        print(" 24. Send draft")
        print(" 25. Get attachments")
        print("\nOther:")
        print("  0. Exit")

        choice = input("\nSelect a test (0-25): ").strip()

        try:
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                await test_get_emails(tester)
            elif choice == "2":
                await test_get_my_sent_emails(tester)
            elif choice == "3":
                await test_get_email_by_id(tester)
            elif choice == "4":
                await test_search_emails(tester)
            elif choice == "5":
                await test_get_labels(tester)
            elif choice == "6":
                await test_get_profile(tester)
            elif choice == "7":
                await test_send_email(tester)
            elif choice == "8":
                await test_reply_to_email(tester)
            elif choice == "9":
                await test_mark_as_read(tester)
            elif choice == "10":
                await test_mark_as_unread(tester)
            elif choice == "11":
                await test_archive_email(tester)
            elif choice == "12":
                await test_unarchive_email(tester)
            elif choice == "13":
                await test_delete_email(tester)
            elif choice == "14":
                await test_add_label(tester)
            elif choice == "15":
                await test_remove_label(tester)
            elif choice == "16":
                await test_create_label(tester)
            elif choice == "17":
                await test_forward_email(tester)
            elif choice == "18":
                await test_move_to_folder(tester)
            elif choice == "19":
                await test_get_threads(tester)
            elif choice == "20":
                await test_get_thread_by_id(tester)
            elif choice == "21":
                await test_create_draft(tester)
            elif choice == "22":
                await test_get_drafts(tester)
            elif choice == "23":
                await test_get_draft_by_id(tester)
            elif choice == "24":
                await test_send_draft(tester)
            elif choice == "25":
                await test_get_attachments(tester)
            else:
                print("❌ Invalid choice!")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


# === INDIVIDUAL TEST FUNCTIONS ===


async def test_get_emails(tester):
    """Test get_emails function."""
    print("\n📬 Testing: Get Emails")
    max_results = int(input("Max results (default 5): ") or "5")
    format_str = input("Format (MINIMAL/COMPACT/FULL, default COMPACT): ") or "COMPACT"
    query = input("Search query (optional): ").strip() or None
    after_date = input("After date (YYYY-MM-DD, optional): ").strip() or None
    before_date = input("Before date (YYYY-MM-DD, optional): ").strip() or None
    newer_than = input("Newer than (e.g., '1d', '2w', optional): ").strip() or None

    try:
        format_enum = MessageFormat(format_str.lower())
        result = await tester.get_emails(
            max_results=max_results,
            query=query,
            after_date=after_date,
            before_date=before_date,
            newer_than=newer_than,
            format=format_enum,
        )
        print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
    except ValueError:
        print(f"❌ Invalid format: {format_str}")


async def test_get_my_sent_emails(tester):
    """Test get_my_sent_emails function."""
    print("\n📤 Testing: Get My Sent Emails")
    max_results = int(input("Max results (default 5): ") or "5")
    format_str = input("Format (MINIMAL/COMPACT/FULL, default COMPACT): ") or "COMPACT"
    query = input("Additional search query (optional): ").strip() or None
    after_date = input("After date (YYYY-MM-DD, optional): ").strip() or None
    before_date = input("Before date (YYYY-MM-DD, optional): ").strip() or None
    newer_than = input("Newer than (e.g., '1d', '2w', optional): ").strip() or None

    try:
        format_enum = MessageFormat(format_str.lower())
        result = await tester.get_my_sent_emails(
            max_results=max_results,
            query=query,
            after_date=after_date,
            before_date=before_date,
            newer_than=newer_than,
            format=format_enum,
        )
        print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
    except ValueError:
        print(f"❌ Invalid format: {format_str}")


async def test_get_email_by_id(tester):
    """Test get_email_by_id function."""
    print("\n📧 Testing: Get Email by ID")
    email_id = input("Email ID: ").strip()
    format_str = input("Format (MINIMAL/COMPACT/FULL, default COMPACT): ") or "COMPACT"

    if not email_id:
        print("❌ Email ID is required!")
        return

    try:
        format_enum = MessageFormat(format_str.lower())
        result = await tester.get_email_by_id(email_id, format=format_enum)
        print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
    except ValueError:
        print(f"❌ Invalid format: {format_str}")


async def test_search_emails(tester):
    """Test search_emails function."""
    print("\n🔍 Testing: Search Emails")
    query = input("Search query (e.g., 'from:example@gmail.com'): ").strip()
    max_results = int(input("Max results (default 5): ") or "5")
    format_str = input("Format (MINIMAL/COMPACT/FULL, default COMPACT): ") or "COMPACT"
    after_date = input("After date (YYYY-MM-DD, optional): ").strip() or None
    before_date = input("Before date (YYYY-MM-DD, optional): ").strip() or None
    newer_than = input("Newer than (e.g., '1d', '2w', optional): ").strip() or None

    if not query:
        print("❌ Search query is required!")
        return

    try:
        format_enum = MessageFormat(format_str.lower())
        result = await tester.search_emails(
            query,
            max_results=max_results,
            after_date=after_date,
            before_date=before_date,
            newer_than=newer_than,
            format=format_enum,
        )
        print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")
    except ValueError:
        print(f"❌ Invalid format: {format_str}")


async def test_get_labels(tester):
    """Test get_labels function."""
    print("\n🏷️  Testing: Get Labels")
    result = await tester.get_labels()
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_get_profile(tester):
    """Test get_profile function."""
    print("\n👤 Testing: Get Profile")
    result = await tester.get_profile()
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_send_email(tester):
    """Test send_email function."""
    print("\n📤 Testing: Send Email")
    to = input("To (email address): ").strip()
    subject = input("Subject: ").strip()
    body_text = input("Body text: ").strip()

    if not to or not subject:
        print("❌ To and Subject are required!")
        return

    result = await tester.send_email([to], subject, body_text=body_text or None)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_mark_as_read(tester):
    """Test mark_as_read function."""
    print("\n👁️  Testing: Mark as Read")
    message_id = input("Message ID: ").strip()

    if not message_id:
        print("❌ Message ID is required!")
        return

    result = await tester.mark_as_read(message_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_mark_as_unread(tester):
    """Test mark_as_unread function."""
    print("\n✉️  Testing: Mark as Unread")
    message_id = input("Message ID: ").strip()

    if not message_id:
        print("❌ Message ID is required!")
        return

    result = await tester.mark_as_unread(message_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_archive_email(tester):
    """Test archive_email function."""
    print("\n📦 Testing: Archive Email")
    message_id = input("Message ID: ").strip()

    if not message_id:
        print("❌ Message ID is required!")
        return

    result = await tester.archive_email(message_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_unarchive_email(tester):
    """Test unarchive_email function."""
    print("\n📥 Testing: Unarchive Email")
    message_id = input("Message ID: ").strip()

    if not message_id:
        print("❌ Message ID is required!")
        return

    result = await tester.unarchive_email(message_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_delete_email(tester):
    """Test delete_email function."""
    print("\n🗑️  Testing: Delete Email")
    message_id = input("Message ID: ").strip()
    confirm = input("Are you sure? This is permanent! (yes/no): ").strip().lower()

    if not message_id:
        print("❌ Message ID is required!")
        return

    if confirm != "yes":
        print("❌ Deletion cancelled!")
        return

    result = await tester.delete_email(message_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_create_draft(tester):
    """Test create_draft function."""
    print("\n📝 Testing: Create Draft")
    to = input("To (email address): ").strip()
    subject = input("Subject: ").strip()
    body_text = input("Body text: ").strip()

    if not to or not subject:
        print("❌ To and Subject are required!")
        return

    result = await tester.create_draft([to], subject, body_text=body_text or None)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_get_drafts(tester):
    """Test get_drafts function."""
    print("\n📝 Testing: Get Drafts")
    max_results = int(input("Max results (default 5): ") or "5")
    
    # Optional date filtering
    print("Optional date filtering (leave empty to skip):")
    after = input("After date (YYYY/MM/DD): ").strip() or None
    before = input("Before date (YYYY/MM/DD): ").strip() or None
    q = input("Search query: ").strip() or None

    result = await tester.get_drafts(max_results=max_results, after=after, before=before, query=q)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_get_draft_by_id(tester):
    """Test get_draft_by_id function."""
    print("\n📝 Testing: Get Draft by ID")
    draft_id = input("Draft ID: ").strip()
    
    result = await tester.get_draft_by_id(draft_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_reply_to_email(tester):
    """Test reply_to_email function."""
    print("\n↩️ Testing: Reply to Email")
    message_id = input("Message ID to reply to: ").strip()
    reply_text = input("Reply message (text): ").strip()
    reply_html = input("Reply message (HTML, optional): ").strip() or None
    reply_all = input("Reply all? (y/N): ").strip().lower() == "y"

    if not message_id or not reply_text:
        print("❌ Message ID and reply text are required!")
        return

    result = await tester.reply_to_email(
        message_id, body_text=reply_text, body_html=reply_html, reply_all=reply_all
    )
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_forward_email(tester):
    """Test forward_email function."""
    print("\n📤 Testing: Forward Email")
    message_id = input("Message ID to forward: ").strip()
    to = input("Forward to (email address): ").strip()
    additional_message = input("Additional message (optional): ").strip()

    if not message_id or not to:
        print("❌ Message ID and recipient are required!")
        return

    result = await tester.forward_email(
        message_id, [to], additional_message=additional_message or None
    )
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_move_to_folder(tester):
    """Test move_to_folder function."""
    print("\n📁 Testing: Move to Folder")
    message_id = input("Message ID: ").strip()
    folder_label_id = input("Folder/Label ID: ").strip()

    if not message_id or not folder_label_id:
        print("❌ Message ID and folder label ID are required!")
        return

    result = await tester.move_to_folder(message_id, folder_label_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_get_threads(tester):
    """Test get_threads function."""
    print("\n🧵 Testing: Get Threads")
    max_results = int(input("Max results (default 5): ") or "5")
    query = input("Search query (optional): ").strip() or None
    after = input("After date (YYYY/MM/DD, optional): ").strip() or None
    before = input("Before date (YYYY/MM/DD, optional): ").strip() or None

    result = await tester.get_threads(
        max_results=max_results, query=query, after=after, before=before
    )
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_get_thread_by_id(tester):
    """Test get_thread_by_id function."""
    print("\n🧵 Testing: Get Thread by ID")
    thread_id = input("Thread ID: ").strip()
    format_choice = input("Format (minimal/full/metadata/raw, default 'full'): ").strip() or "full"

    if not thread_id:
        print("❌ Thread ID is required!")
        return

    result = await tester.get_thread_by_id(thread_id, format_choice)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_send_draft(tester):
    """Test send_draft function."""
    print("\n📧 Testing: Send Draft")
    draft_id = input("Draft ID to send: ").strip()

    if not draft_id:
        print("❌ Draft ID is required!")
        return

    result = await tester.send_draft(draft_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_get_attachments(tester):
    """Test get_attachments function."""
    print("\n📎 Testing: Get Attachments")
    message_id = input("Message ID: ").strip()

    if not message_id:
        print("❌ Message ID is required!")
        return

    result = await tester.get_attachments(message_id)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_add_label(tester):
    """Test add_label function."""
    print("\n🏷️ Testing: Add Label")
    message_id = input("Message ID: ").strip()
    label_ids = input("Label IDs (comma-separated): ").strip()

    if not message_id or not label_ids:
        print("❌ Message ID and label IDs are required!")
        return

    label_list = [label.strip() for label in label_ids.split(",")]
    result = await tester.add_label(message_id, label_list)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_remove_label(tester):
    """Test remove_label function."""
    print("\n🏷️ Testing: Remove Label")
    message_id = input("Message ID: ").strip()
    label_ids = input("Label IDs to remove (comma-separated): ").strip()

    if not message_id or not label_ids:
        print("❌ Message ID and label IDs are required!")
        return

    label_list = [label.strip() for label in label_ids.split(",")]
    result = await tester.remove_label(message_id, label_list)
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


async def test_create_label(tester):
    """Test create_label function."""
    print("\n🏷️ Testing: Create Label")
    name = input("Label name: ").strip()
    visibility = input("Visibility (labelShow/labelHide, default labelShow): ").strip()

    if not name:
        print("❌ Label name is required!")
        return

    result = await tester.create_label(name, label_list_visibility=visibility or "labelShow")
    print(f"\n📊 Result: {json.dumps(result, indent=2, default=str)}")


if __name__ == "__main__":
    """Run the interactive test script."""
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
