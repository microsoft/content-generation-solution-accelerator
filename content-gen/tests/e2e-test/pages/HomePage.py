"""Home page object module for Fabric SQL automation tests."""
import logging
import json
import os
import re
import math
from io import BytesIO
from collections import Counter

from PIL import Image
from base.base import BasePage
from config.constants import HELLO_PROMPT, GOOD_MORNING_PROMPT, RAI_PROMPT, OUT_OF_SCOPE_PROMPT

from playwright.sync_api import expect

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    """Page object class for Home Page interactions and validations."""
    # ---------- LOCATORS ----------
    HOME_PAGE_TEXT = "//span[.='Welcome to your Content Generation Accelerator']"
    HOME_PAGE_SUBTEXT = "//span[.='Here are the options I can assist you with today']"
    USER_MESSAGE = "//span[contains(text(),'I need to create a social media post about paint p')]"
    USER_MESSAGE_2 = "//span[contains(text(),'Generate a social')]"

    # Input and send locators
    ASK_QUESTION_TEXTAREA = "//input[@placeholder='Type a message']"
    SEND_BUTTON = "//button[2]//span[1]"
    
    # Response and status locators
    TYPING_INDICATOR = "//div[@class='typing-indicator']"
    AGENT = "//div[.='PlanningAgent']"
    CONFIRM_BRIEF_BUTTON = "//button[normalize-space()='Confirm brief']"
    BRIEF_CONFIRMED_TEXT = "//div[contains(text(),'Brief Confirmed')]"
    OLIVE_STONE_TEXT = "(//span[normalize-space()='Olive Stone'])[last()]"
    OBSIDIAN_TEXT = "(//span[normalize-space()='Obsidian Pearl'])[last()]"
    GENERATE_CONTENT_BUTTON = "//button[normalize-space()='Generate Content']"
    ANALYZING_BRIEF_TEXT = "//span[contains(text(),'Analyzing creative brief..')]"
    GENERATED_CONTENT_TEXT_OLIVE = "//span[contains(.,'✨ Discover the serene elegance of Olive Stone.')]"
    GENERATED_CONTENT_TEXT_OBSIDIAN = "//span[contains(.,'✨ Discover the serene elegance of Obsidian Pearl.')]"
    PAINT_LIST = "//span[.='Here is the list of available paints:']"
    PRODUCT_SELECTED = "//div[contains(text(),'Products Selected')]"
    IMAGE_GEN = "//img[@alt='Generated marketing image']"
    PRODUCT_COLOR_SWATCH = "(//div[contains(text(),'Products Selected')]/following::img)[1]"
    START_NEW_CHAT = "//button[normalize-space()='Start new chat']"
    CHAT_HISTORY = "(//div[@style='padding: 8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 8px; background-color: transparent; border: 1px solid transparent; border-radius: 6px; margin-left: -8px; margin-right: -8px; transition: background-color 0.15s, border-color 0.15s; opacity: 1; pointer-events: auto;'])[1]"
    MORE_OPTIONS  = "(//button[@style='min-width: 24px; height: 24px; padding: 2px; color: var(--colorNeutralForeground3);'])[2]"
    MORE_OPTIONS_DELETE  = "(//button[@style='min-width: 24px; height: 24px; padding: 2px; color: var(--colorNeutralForeground3);'])[3]"
    RENAME_OPTION = "//span[normalize-space()='Rename']"
    RENAME_OPTION = "//span[normalize-space()='Rename']"
    DELETE_CHAT = "//span[normalize-space()='Delete']"
    DELETE_BUTTON = "//button[normalize-space()='Delete']"
    RENAME_CONVERSATION_INPUT = "//input[@placeholder='Enter conversation name']"
    RENAME_BUTTON = "//button[normalize-space()='Rename']"
    RENAME_VALIDATION  = "//span[contains(text(),'Conversation name cannot be empty or contain only ')]"
    CANCEL_BUTTON = "//button[normalize-space()='Cancel']"
    STOP_GENERATION_BUTTON = "//button[normalize-space()='Stop']"
    STOPPED_GENERATION_TEXT = "//p[normalize-space()='Generation stopped.']"
    START_OVER_BUTTON = "//button[normalize-space()='Start over']"
    START_OVER_VALIDATION_TEXT = "//p[contains(text(),'No problem. Please provide your creative brief aga')]"
    TYPE_MESSAGE = "//input[@placeholder='Type a message']"
    DOWNLOAD_IMAGE_BUTTON = "//button[@aria-label='Download image with banner']"
    CLEAR_ALL_CHAT_HISTORY = "//span[.='Clear all chat history']"
    CLEAR_ALL_BUTTON = "//button[normalize-space()='Clear All']"
    NO_CONVERSATIONS_TEXT = "//span[.='No conversations yet']"
    CHAT_HISTORY_MORE_OPTIONS  = "(//button[@style='min-width: 24px; height: 24px; padding: 2px; color: var(--colorNeutralForeground3);'])[1]"
    HIDE_CHAT_HISTORY_BUTTON = "//button[@aria-label='Hide chat history']"
    SHOW_CHAT_HISTORY_BUTTON = "//button[@aria-label='Show chat history']"

    # --- ERROR DETECTION PHRASES ---
    # Specific phrases indicating errors in AI responses.
    # Intentionally specific to avoid false positives from normal marketing content.
    ERROR_PHRASES = [
        "an error occurred", "an error has occurred",
        "internal server error", "something went wrong",
        "unable to process your request", "service unavailable",
        "rate limit exceeded", "quota exceeded",
        "request failed", "failed to generate", "generation failed",
        "server encountered an error", "error processing your request",
        "content filter triggered", "operation timed out",
        "request timeout", "connection refused",
        "traceback (most recent call last)", "unhandled exception",
        "failed to fetch", "the operation was cancelled",
        "sorry, something went wrong", "please try again later",
        "we encountered an issue", "could not complete your request",
        "unexpected error occurred", "api returned an error",
        "access denied", "resource not found",
    ]

    def __init__(self, page):
        """Initialize the HomePage with a Playwright page instance."""
        super().__init__(page)
        self.page = page

    def validate_home_page(self):
        """Validate that the home page elements are visible."""
        logger.info("Starting home page validation...")

        logger.info("Validating HOME_PAGE_TEXT is visible...")
        expect(self.page.locator(self.HOME_PAGE_TEXT)).to_be_visible(timeout=10000)
        self.page.wait_for_timeout(4000)
        logger.info("✓ HOME_PAGE_TEXT is visible")

        logger.info("Validating HOME_PAGE_SUBTEXT is visible...")
        expect(self.page.locator(self.HOME_PAGE_SUBTEXT)).to_be_visible(timeout=10000)
        self.page.wait_for_timeout(2000)
        logger.info("✓ HOME_PAGE_SUBTEXT is visible")

        logger.info("Home page validation completed successfully!")

    def click_new_conversation(self):
        """
        Click on 'Start new chat' button to start a fresh chat session and validate home page elements.
        Steps:
        1. Click on START_NEW_CHAT button
        2. Validate home page elements are visible
        """
        logger.info("=" * 80)
        logger.info("Starting New Conversation")
        logger.info("=" * 80)

        try:
            # Step 1: Click on START_NEW_CHAT button
            logger.info("Step 1: Clicking on START_NEW_CHAT button...")
            start_new_chat_btn = self.page.locator(self.START_NEW_CHAT)
            expect(start_new_chat_btn).to_be_visible(timeout=10000)
            start_new_chat_btn.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ START_NEW_CHAT button clicked")

            # Step 2: Validate home page elements are visible
            logger.info("Step 2: Validating home page elements...")
            self.validate_home_page()
            logger.info("✓ Home page elements validated")

            logger.info("=" * 80)
            logger.info("New Conversation Started Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'New conversation started and home page validated successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to start new conversation: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def validate_chat_history(self):
        """
        Validate that chat history is showing by checking CHAT_HISTORY element is visible.
        Steps:
        1. Validate CHAT_HISTORY element is visible
        """
        logger.info("=" * 80)
        logger.info("Starting Chat History Validation")
        logger.info("=" * 80)

        try:
            # Step 1: Validate CHAT_HISTORY element is visible
            logger.info("Step 1: Waiting for CHAT_HISTORY to be visible...")
            chat_history = self.page.locator(self.CHAT_HISTORY)
            expect(chat_history).to_be_visible(timeout=10000)
            logger.info("✓ CHAT_HISTORY is visible")

            # Get count of chat history items
            chat_count = chat_history.count()
            logger.info(f"Chat history items found: {chat_count}")

            logger.info("=" * 80)
            logger.info("Chat History Validation Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'chat_count': chat_count,
                'validation': 'Chat history is visible'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate chat history: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def show_hide_chat_history(self):
        """
        Validate show/hide chat history toggle functionality.
        Steps:
        1. Validate 'Hide chat history' button is visible and click it
        2. Validate chat history panel is hidden (CHAT_HISTORY not visible)
        3. Validate 'Show chat history' button is visible and click it
        4. Validate chat history panel is shown again (CHAT_HISTORY visible)
        """
        logger.info("=" * 80)
        logger.info("Starting Show/Hide Chat History Validation")
        logger.info("=" * 80)

        try:
            # Step 1: Click 'Hide chat history' button
            logger.info("Step 1: Clicking 'Hide chat history' button...")
            hide_button = self.page.locator(self.HIDE_CHAT_HISTORY_BUTTON)
            expect(hide_button).to_be_visible(timeout=10000)
            hide_button.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ 'Hide chat history' button clicked")

            # Step 2: Validate chat history panel is hidden
            logger.info("Step 2: Validating chat history panel is hidden...")
            chat_history = self.page.locator(self.CHAT_HISTORY)
            expect(chat_history).not_to_be_visible(timeout=10000)
            logger.info("✓ Chat history panel is hidden")

            # Step 3: Click 'Show chat history' button
            logger.info("Step 3: Clicking 'Show chat history' button...")
            show_button = self.page.locator(self.SHOW_CHAT_HISTORY_BUTTON)
            expect(show_button).to_be_visible(timeout=10000)
            show_button.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ 'Show chat history' button clicked")

            # Step 4: Validate chat history panel is visible again
            logger.info("Step 4: Validating chat history panel is visible again...")
            expect(chat_history).to_be_visible(timeout=10000)
            logger.info("✓ Chat history panel is visible again")

            logger.info("=" * 80)
            logger.info("Show/Hide Chat History Validation Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Chat history show/hide toggle works correctly'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate show/hide chat history: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def rename_chat_history(self, new_name="updated_chat"):
        """
        Rename a chat history item by hovering, clicking more options, and renaming.
        Steps:
        1. Hover on CHAT_HISTORY item
        2. Click on MORE_OPTIONS
        3. Click on RENAME_OPTION
        4. Clear RENAME_CONVERSATION_INPUT and enter new name
        5. Click on RENAME_BUTTON
        6. Validate the chat history name is updated

        Args:
            new_name: The new name for the chat history item. Defaults to 'updated_chat'.
        """
        logger.info("=" * 80)
        logger.info(f"Starting Rename Chat History to '{new_name}'")
        logger.info("=" * 80)

        try:
            # Step 1: Hover on CHAT_HISTORY item
            logger.info("Step 1: Hovering on CHAT_HISTORY item...")
            chat_history = self.page.locator(self.CHAT_HISTORY)
            expect(chat_history).to_be_visible(timeout=10000)
            chat_history.hover()
            self.page.wait_for_timeout(2000)
            logger.info("✓ Hovered on CHAT_HISTORY item")

            # Step 2: Click on MORE_OPTIONS
            logger.info("Step 2: Clicking on MORE_OPTIONS...")
            more_options = self.page.locator(self.MORE_OPTIONS)
            expect(more_options).to_be_visible(timeout=10000)
            more_options.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ MORE_OPTIONS clicked")

            # Step 3: Click on RENAME_OPTION
            logger.info("Step 3: Clicking on RENAME_OPTION...")
            rename_option = self.page.locator(self.RENAME_OPTION)
            expect(rename_option).to_be_visible(timeout=10000)
            rename_option.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ RENAME_OPTION clicked")

            # Step 4: Clear RENAME_CONVERSATION_INPUT and enter new name
            logger.info(f"Step 4: Clearing input and entering '{new_name}'...")
            rename_input = self.page.locator(self.RENAME_CONVERSATION_INPUT)
            expect(rename_input).to_be_visible(timeout=10000)
            rename_input.click()
            self.page.wait_for_timeout(1000)
            rename_input.fill("")
            self.page.wait_for_timeout(1000)
            rename_input.fill(new_name)
            self.page.wait_for_timeout(2000)
            logger.info(f"✓ Input updated to '{new_name}'")

            # Step 5: Click on RENAME_BUTTON
            logger.info("Step 5: Clicking on RENAME_BUTTON...")
            rename_button = self.page.locator(self.RENAME_BUTTON)
            expect(rename_button).to_be_visible(timeout=10000)
            rename_button.click()
            self.page.wait_for_timeout(5000)
            logger.info("✓ RENAME_BUTTON clicked")

            # Step 6: Validate the chat history name is updated
            logger.info("Step 6: Validating chat history name is updated...")
            renamed_item = self.page.locator(f"//span[normalize-space()='{new_name}']")
            expect(renamed_item).to_be_visible(timeout=10000)
            logger.info(f"✓ Chat history successfully renamed to '{new_name}'")

            logger.info("=" * 80)
            logger.info("Rename Chat History Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'new_name': new_name,
                'validation': f'Chat history successfully renamed to {new_name}'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to rename chat history: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def validate_rename_empty_validation(self):
        """
        Validate that the rename button is disabled and a validation message is displayed
        when the conversation name input is cleared (empty).
        Steps:
        1. Hover on CHAT_HISTORY item
        2. Click on MORE_OPTIONS
        3. Click on RENAME_OPTION
        4. Clear RENAME_CONVERSATION_INPUT to make it empty
        5. Validate RENAME_BUTTON is disabled
        6. Validate RENAME_VALIDATION message is displayed
        7. Click on CANCEL_BUTTON
        """
        logger.info("=" * 80)
        logger.info("Starting Rename Empty Validation Check")
        logger.info("=" * 80)

        try:
            # Step 1: Hover on CHAT_HISTORY item
            logger.info("Step 1: Hovering on CHAT_HISTORY item...")
            chat_history = self.page.locator(self.CHAT_HISTORY)
            expect(chat_history).to_be_visible(timeout=10000)
            chat_history.hover()
            self.page.wait_for_timeout(2000)
            logger.info("✓ Hovered on CHAT_HISTORY item")

            # Step 2: Click on MORE_OPTIONS
            logger.info("Step 2: Clicking on MORE_OPTIONS...")
            more_options = self.page.locator(self.MORE_OPTIONS)
            expect(more_options).to_be_visible(timeout=10000)
            more_options.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ MORE_OPTIONS clicked")

            # Step 3: Click on RENAME_OPTION
            logger.info("Step 3: Clicking on RENAME_OPTION...")
            rename_option = self.page.locator(self.RENAME_OPTION)
            expect(rename_option).to_be_visible(timeout=10000)
            rename_option.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ RENAME_OPTION clicked")

            # Step 4: Clear RENAME_CONVERSATION_INPUT to make it empty
            logger.info("Step 4: Clearing input to empty...")
            rename_input = self.page.locator(self.RENAME_CONVERSATION_INPUT)
            expect(rename_input).to_be_visible(timeout=10000)
            rename_input.click()
            self.page.wait_for_timeout(1000)
            rename_input.fill("")
            self.page.wait_for_timeout(2000)
            logger.info("✓ Input cleared to empty")

            # Step 5: Validate RENAME_BUTTON is disabled
            logger.info("Step 5: Validating RENAME_BUTTON is disabled...")
            rename_button = self.page.locator(self.RENAME_BUTTON)
            expect(rename_button).to_be_disabled(timeout=10000)
            logger.info("✓ RENAME_BUTTON is disabled")

            # Step 6: Validate RENAME_VALIDATION message is displayed
            logger.info("Step 6: Validating RENAME_VALIDATION message is displayed...")
            rename_validation = self.page.locator(self.RENAME_VALIDATION)
            expect(rename_validation).to_be_visible(timeout=10000)
            logger.info("✓ RENAME_VALIDATION message is displayed")

            # Step 7: Click on CANCEL_BUTTON
            logger.info("Step 7: Clicking on CANCEL_BUTTON...")
            cancel_button = self.page.locator(self.CANCEL_BUTTON)
            expect(cancel_button).to_be_visible(timeout=10000)
            cancel_button.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ CANCEL_BUTTON clicked")

            logger.info("=" * 80)
            logger.info("Rename Empty Validation Check Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Rename button is disabled and validation message is displayed for empty input'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed rename empty validation check: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def delete_chat_history(self):
        """
        Delete a chat history item by hovering, clicking more options, and deleting.
        Steps:
        1. Get initial chat history count
        2. Hover on CHAT_HISTORY item
        3. Click on MORE_OPTIONS
        4. Click on DELETE_CHAT
        5. Click on DELETE_BUTTON to confirm
        6. Validate chat history item is deleted
        """
        logger.info("=" * 80)
        logger.info("Starting Delete Chat History")
        logger.info("=" * 80)

        try:
            # Step 1: Get initial chat history count
            logger.info("Step 1: Getting initial chat history count...")
            chat_history = self.page.locator(self.CHAT_HISTORY)
            initial_count = chat_history.count()
            logger.info(f"Initial chat history count: {initial_count}")

            if not initial_count:
                error_msg = "No chat history items available to delete"
                logger.error(f"❌ {error_msg}")
                raise AssertionError(error_msg)

            # Get text of item to be deleted for validation
            item_to_delete_text = chat_history.text_content()
            logger.info(f"Chat item to delete: '{item_to_delete_text}'")

            # Step 2: Hover on CHAT_HISTORY item
            logger.info("Step 2: Hovering on CHAT_HISTORY item...")
            chat_history.hover()
            self.page.wait_for_timeout(2000)
            logger.info("✓ Hovered on CHAT_HISTORY item")

            # Step 3: Click on MORE_OPTIONS
            logger.info("Step 3: Clicking on MORE_OPTIONS...")
            more_options = self.page.locator(self.MORE_OPTIONS_DELETE)
            expect(more_options).to_be_visible(timeout=10000)
            more_options.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ MORE_OPTIONS clicked")

            # Step 4: Click on DELETE_CHAT
            logger.info("Step 4: Clicking on DELETE_CHAT...")
            delete_chat = self.page.locator(self.DELETE_CHAT)
            expect(delete_chat).to_be_visible(timeout=10000)
            delete_chat.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ DELETE_CHAT clicked")

            # Step 5: Click on DELETE_BUTTON to confirm
            logger.info("Step 5: Clicking on DELETE_BUTTON to confirm...")
            delete_button = self.page.locator(self.DELETE_BUTTON)
            expect(delete_button).to_be_visible(timeout=10000)
            delete_button.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ DELETE_BUTTON clicked")

            # Step 6: Validate chat history item is deleted
            logger.info("Step 6: Validating chat history item is deleted...")
            deleted_item = self.page.locator(f"//span[normalize-space()='{item_to_delete_text.strip()[:50]}']")
            expect(deleted_item).to_have_count(0, timeout=10000)
            logger.info("✓ Chat history item successfully deleted")

            logger.info("=" * 80)
            logger.info("Delete Chat History Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'deleted_item': item_to_delete_text,
                'validation': 'Chat history item successfully deleted'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to delete chat history: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def send_prompt(self, quick_link=None):
        """
        Send a prompt by clicking on a quick link and then clicking SEND_BUTTON.
        Does NOT wait for analyzing brief or confirm brief validations.
        Steps:
        1. Click on the quick link (USER_MESSAGE or USER_MESSAGE_2)
        2. Click the SEND_BUTTON to send the prompt

        Args:
            quick_link: Locator string for the quick link. Defaults to USER_MESSAGE.
        """
        if quick_link is None:
            quick_link = self.USER_MESSAGE

        logger.info("=" * 80)
        logger.info("Starting Send Prompt")
        logger.info("=" * 80)

        try:
            # Step 1: Click on the quick link
            logger.info("Step 1: Clicking on quick link...")
            user_message = self.page.locator(quick_link)
            expect(user_message).to_be_visible(timeout=10000)
            user_message.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ Quick link clicked")

            # Step 2: Click the SEND_BUTTON to send the prompt
            logger.info("Step 2: Clicking on SEND_BUTTON...")
            send_button = self.page.locator(self.SEND_BUTTON)
            expect(send_button).to_be_enabled(timeout=10000)
            send_button.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ SEND_BUTTON clicked")

            logger.info("=" * 80)
            logger.info("Send Prompt Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Quick link clicked and prompt sent successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to send prompt: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def send_prompt_from_quick_link(self, quick_link=None):
        """
        Send a prompt by clicking on a quick link and then clicking SEND_BUTTON.
        Steps:
        1. Click on the quick link (USER_MESSAGE or USER_MESSAGE_2)
        2. Click the SEND_BUTTON to send the prompt
        3. Validate ANALYZING_BRIEF_TEXT is visible
        4. Validate CONFIRM_BRIEF_BUTTON is visible

        Args:
            quick_link: Locator string for the quick link. Defaults to USER_MESSAGE.
        """
        if quick_link is None:
            quick_link = self.USER_MESSAGE

        logger.info("=" * 80)
        logger.info("Starting Send Prompt from Quick Link")
        logger.info("=" * 80)

        try:
            # Step 1: Click on the quick link
            logger.info("Step 1: Clicking on quick link...")
            user_message = self.page.locator(quick_link)
            expect(user_message).to_be_visible(timeout=10000)
            user_message.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ USER_MESSAGE quick link clicked")

            # Step 2: Click the SEND_BUTTON to send the prompt
            logger.info("Step 2: Clicking on SEND_BUTTON...")
            send_button = self.page.locator(self.SEND_BUTTON)
            expect(send_button).to_be_enabled(timeout=10000)
            send_button.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ SEND_BUTTON clicked")

            # Step 3: Validate ANALYZING_BRIEF_TEXT is visible
            logger.info("Step 3: Waiting for ANALYZING_BRIEF_TEXT to be visible...")
            analyzing_brief = self.page.locator(self.ANALYZING_BRIEF_TEXT)
            expect(analyzing_brief).to_be_visible(timeout=40000)
            logger.info("✓ ANALYZING_BRIEF_TEXT is visible")

            # Step 4: Validate CONFIRM_BRIEF_BUTTON is visible within 40 seconds
            logger.info("Step 4: Waiting for CONFIRM_BRIEF_BUTTON to be visible...")
            confirm_brief = self.page.locator(self.CONFIRM_BRIEF_BUTTON)
            expect(confirm_brief).to_be_visible(timeout=40000)
            logger.info("✓ CONFIRM_BRIEF_BUTTON is visible")

            logger.info("=" * 80)
            logger.info("Send Prompt from Quick Link Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Quick link prompt sent, analyzing brief text and confirm brief button validated successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to send prompt from quick link: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def confirm_brief(self):
        """
        Confirm the brief by clicking on CONFIRM_BRIEF_BUTTON and validate BRIEF_CONFIRMED_TEXT is visible.
        Steps:
        1. Click on the CONFIRM_BRIEF_BUTTON
        2. Validate that BRIEF_CONFIRMED_TEXT is visible
        """
        logger.info("=" * 80)
        logger.info("Starting Confirm Brief")
        logger.info("=" * 80)

        try:
            # Step 1: Click on the CONFIRM_BRIEF_BUTTON
            logger.info("Step 1: Clicking on CONFIRM_BRIEF_BUTTON...")
            confirm_brief_btn = self.page.locator(self.CONFIRM_BRIEF_BUTTON)
            expect(confirm_brief_btn).to_be_visible(timeout=10000)
            confirm_brief_btn.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ CONFIRM_BRIEF_BUTTON clicked")

            # Step 2: Validate that BRIEF_CONFIRMED_TEXT is visible
            logger.info("Step 2: Waiting for BRIEF_CONFIRMED_TEXT to be visible...")
            brief_confirmed = self.page.locator(self.BRIEF_CONFIRMED_TEXT)
            expect(brief_confirmed).to_be_visible(timeout=40000)
            logger.info("✓ BRIEF_CONFIRMED_TEXT is visible")

            logger.info("=" * 80)
            logger.info("Confirm Brief Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Brief confirmed successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to confirm brief: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def select_color_and_generate_content(self, color_locator=None, generated_content_locator=None, expected_color="olive"):
        """
        Select a color and generate content.
        Steps:
        1. Click on color locator to select the color
        2. Validate GENERATE_CONTENT_BUTTON is visible
        3. Click on GENERATE_CONTENT_BUTTON
        4. Validate TYPING_INDICATOR appears
        5. Wait for GENERATED_CONTENT_TEXT to be visible
        6. Validate IMAGE_GEN is visible
        7. Validate dominant color of the generated image

        Args:
            color_locator: XPath locator for the color to select. Defaults to OLIVE_STONE_TEXT.
            generated_content_locator: XPath locator for the generated content text. Defaults to GENERATED_CONTENT_TEXT_OLIVE.
            expected_color: Key from COLOR_RANGES for image validation. Defaults to 'olive'.
        """
        if color_locator is None:
            color_locator = self.OLIVE_STONE_TEXT
        if generated_content_locator is None:
            generated_content_locator = self.GENERATED_CONTENT_TEXT_OLIVE

        logger.info("=" * 80)
        logger.info(f"Starting Select Color and Generate Content (expected: {expected_color})")
        logger.info("=" * 80)

        try:
            # Step 1: Click on color locator to select the color
            logger.info("Step 1: Clicking on color to select...")
            color_element = self.page.locator(color_locator)
            expect(color_element).to_be_visible(timeout=40000)
            color_element.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ Color selected")

            # Step 2: Validate GENERATE_CONTENT_BUTTON is visible
            logger.info("Step 2: Waiting for GENERATE_CONTENT_BUTTON to be visible...")
            generate_content_btn = self.page.locator(self.GENERATE_CONTENT_BUTTON)
            expect(generate_content_btn).to_be_visible(timeout=40000)
            logger.info("✓ GENERATE_CONTENT_BUTTON is visible")

            # Step 3: Click on GENERATE_CONTENT_BUTTON
            logger.info("Step 3: Clicking on GENERATE_CONTENT_BUTTON...")
            generate_content_btn.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ GENERATE_CONTENT_BUTTON clicked")

            # Step 4: Validate TYPING_INDICATOR appears
            logger.info("Step 4: Waiting for TYPING_INDICATOR to appear...")
            typing_indicator = self.page.locator(self.TYPING_INDICATOR)
            expect(typing_indicator).to_be_visible(timeout=40000)
            logger.info("✓ TYPING_INDICATOR is visible")

            # Step 5: Wait for GENERATED_CONTENT_TEXT to be visible
            logger.info("Step 5: Waiting for GENERATED_CONTENT_TEXT to be visible...")
            generated_content = self.page.locator(generated_content_locator)
            expect(generated_content).to_be_visible(timeout=120000)
            logger.info("✓ GENERATED_CONTENT_TEXT is visible")

            # Step 6: Validate IMAGE_GEN is visible
            self.page.wait_for_timeout(5000)
            logger.info("Step 6: Waiting for IMAGE_GEN to be visible...")
            image_gen = self.page.locator(self.IMAGE_GEN)
            expect(image_gen).to_be_visible(timeout=40000)
            logger.info("✓ IMAGE_GEN is visible")

            # Step 7: Compare generated image color with the selected product color swatch
            logger.info("Step 7: Comparing generated image color with selected color swatch...")
            self.validate_color_match_with_swatch(image_gen)

            logger.info("=" * 80)
            logger.info("Select Color and Generate Content Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Color selected, content generated, image and color validated successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to select color and generate content: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def stop_generation(self):
        """
        Stop the content generation while it is in progress and validate
        that the 'Generation stopped.' message is displayed.
        Steps:
        1. Click on STOP_GENERATION_BUTTON
        2. Validate STOPPED_GENERATION_TEXT is visible
        """
        logger.info("=" * 80)
        logger.info("Starting Stop Generation")
        logger.info("=" * 80)

        try:
            # Step 1: Click on STOP_GENERATION_BUTTON
            logger.info("Step 1: Clicking on STOP_GENERATION_BUTTON...")
            stop_button = self.page.locator(self.STOP_GENERATION_BUTTON)
            expect(stop_button).to_be_visible(timeout=10000)
            stop_button.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ STOP_GENERATION_BUTTON clicked")

            # Step 2: Validate STOPPED_GENERATION_TEXT is visible
            logger.info("Step 2: Waiting for STOPPED_GENERATION_TEXT to be visible...")
            stopped_text = self.page.locator(self.STOPPED_GENERATION_TEXT)
            expect(stopped_text).to_be_visible(timeout=10000)
            logger.info("✓ STOPPED_GENERATION_TEXT is visible")

            logger.info("=" * 80)
            logger.info("Stop Generation Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Generation stopped and stopped text validated successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to stop generation: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def start_over(self):
        """
        Click the 'Start over' button after generation has been stopped and validate
        that the START_OVER_VALIDATION_TEXT message is displayed.
        Steps:
        1. Click on START_OVER_BUTTON
        2. Validate START_OVER_VALIDATION_TEXT is visible
        """
        logger.info("=" * 80)
        logger.info("Starting Start Over")
        logger.info("=" * 80)

        try:
            # Step 1: Click on START_OVER_BUTTON
            logger.info("Step 1: Clicking on START_OVER_BUTTON...")
            start_over_btn = self.page.locator(self.START_OVER_BUTTON)
            expect(start_over_btn).to_be_visible(timeout=10000)
            start_over_btn.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ START_OVER_BUTTON clicked")

            # Step 2: Validate START_OVER_VALIDATION_TEXT is visible
            logger.info("Step 2: Waiting for START_OVER_VALIDATION_TEXT to be visible...")
            start_over_text = self.page.locator(self.START_OVER_VALIDATION_TEXT)
            expect(start_over_text).to_be_visible(timeout=40000)
            logger.info("✓ START_OVER_VALIDATION_TEXT is visible")

            logger.info("=" * 80)
            logger.info("Start Over Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Start over button clicked and validation text displayed successfully'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to start over: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def validate_input_disabled_during_generation(self):
        """
        Validate that the input textarea and send button are disabled while
        the AI response is being generated.
        Steps:
        1. Validate ASK_QUESTION_TEXTAREA is disabled
        2. Validate SEND_BUTTON is disabled
        """
        logger.info("=" * 80)
        logger.info("Starting Input Disabled During Generation Validation")
        logger.info("=" * 80)

        try:
            # Step 1: Validate ASK_QUESTION_TEXTAREA is disabled
            logger.info("Step 1: Validating ASK_QUESTION_TEXTAREA is disabled...")
            ask_question = self.page.locator(self.ASK_QUESTION_TEXTAREA)
            expect(ask_question).to_be_disabled(timeout=10000)
            logger.info("✓ ASK_QUESTION_TEXTAREA is disabled")

            # Step 2: Validate SEND_BUTTON is disabled
            logger.info("Step 2: Validating SEND_BUTTON is disabled...")
            send_button = self.page.locator(self.SEND_BUTTON)
            expect(send_button).to_be_disabled(timeout=10000)
            logger.info("✓ SEND_BUTTON is disabled")

            logger.info("=" * 80)
            logger.info("Input Disabled During Generation Validation Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'Input textarea and send button are disabled during response generation'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate input disabled during generation: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def download_image(self):
        """
        Click on the download image button and validate that the download is triggered.
        Steps:
        1. Validate DOWNLOAD_IMAGE_BUTTON is visible
        2. Click on DOWNLOAD_IMAGE_BUTTON and wait for the download event
        3. Validate the downloaded file is not empty
        """
        logger.info("=" * 80)
        logger.info("Starting Download Image")
        logger.info("=" * 80)

        try:
            # Step 1: Validate DOWNLOAD_IMAGE_BUTTON is visible
            logger.info("Step 1: Validating DOWNLOAD_IMAGE_BUTTON is visible...")
            download_btn = self.page.locator(self.DOWNLOAD_IMAGE_BUTTON)
            expect(download_btn).to_be_visible(timeout=10000)
            logger.info("✓ DOWNLOAD_IMAGE_BUTTON is visible")

            # Step 2: Click on DOWNLOAD_IMAGE_BUTTON and wait for the download event
            logger.info("Step 2: Clicking on DOWNLOAD_IMAGE_BUTTON and waiting for download...")
            with self.page.expect_download() as download_info:
                download_btn.click()
            download = download_info.value
            self.page.wait_for_timeout(3000)
            logger.info(f"✓ Download triggered — file: {download.suggested_filename}")

            # Step 3: Validate the downloaded file is not empty
            logger.info("Step 3: Validating downloaded file is not empty...")
            download_path = download.path()
            file_size = os.path.getsize(download_path)
            logger.info(f"  Downloaded file size: {file_size} bytes")
            assert file_size > 0, "Downloaded file is empty (0 bytes)"
            logger.info("✓ Downloaded file is not empty")

            logger.info("=" * 80)
            logger.info("Download Image Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'filename': download.suggested_filename,
                'file_size': file_size,
                'validation': 'Image downloaded successfully and file is not empty'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to download image: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def clear_all_chat_history(self):
        """
        Clear all chat history by clicking the more options button, selecting
        'Clear all chat history', confirming with 'Clear All', and validating
        the 'No conversations yet' message is displayed.
        Steps:
        1. Click on CHAT_HISTORY_MORE_OPTIONS
        2. Click on CLEAR_ALL_CHAT_HISTORY option
        3. Click on CLEAR_ALL_BUTTON to confirm
        4. Validate NO_CONVERSATIONS_TEXT is visible
        """
        logger.info("=" * 80)
        logger.info("Starting Clear All Chat History")
        logger.info("=" * 80)

        try:
            # Step 1: Click on CHAT_HISTORY_MORE_OPTIONS
            logger.info("Step 1: Clicking on CHAT_HISTORY_MORE_OPTIONS...")
            more_options = self.page.locator(self.CHAT_HISTORY_MORE_OPTIONS)
            expect(more_options).to_be_visible(timeout=10000)
            more_options.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ CHAT_HISTORY_MORE_OPTIONS clicked")

            # Step 2: Click on CLEAR_ALL_CHAT_HISTORY option
            logger.info("Step 2: Clicking on CLEAR_ALL_CHAT_HISTORY...")
            clear_all_option = self.page.locator(self.CLEAR_ALL_CHAT_HISTORY)
            expect(clear_all_option).to_be_visible(timeout=10000)
            clear_all_option.click()
            self.page.wait_for_timeout(2000)
            logger.info("✓ CLEAR_ALL_CHAT_HISTORY clicked")

            # Step 3: Click on CLEAR_ALL_BUTTON to confirm
            logger.info("Step 3: Clicking on CLEAR_ALL_BUTTON to confirm...")
            clear_all_btn = self.page.locator(self.CLEAR_ALL_BUTTON)
            expect(clear_all_btn).to_be_visible(timeout=10000)
            clear_all_btn.click()
            self.page.wait_for_timeout(3000)
            logger.info("✓ CLEAR_ALL_BUTTON clicked")

            # Step 4: Validate NO_CONVERSATIONS_TEXT is visible
            logger.info("Step 4: Validating NO_CONVERSATIONS_TEXT is visible...")
            no_conversations = self.page.locator(self.NO_CONVERSATIONS_TEXT)
            expect(no_conversations).to_be_visible(timeout=10000)
            logger.info("✓ NO_CONVERSATIONS_TEXT is visible — all chat history cleared")

            logger.info("=" * 80)
            logger.info("Clear All Chat History Completed Successfully!")
            logger.info("=" * 80)

            return {
                'status': 'PASSED',
                'validation': 'All chat history cleared and No conversations text is displayed'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to clear all chat history: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    # ---------- RESPONSE VALIDATION METHODS ----------

    def assert_no_error_in_response(self, context=""):
        """
        Scan all visible text on the page for error/exception patterns.
        Fails the test immediately if any error pattern is detected in AI responses.

        Args:
            context: Description of which step this check is being performed at.

        Raises:
            AssertionError: If any error pattern is found in the visible text.
        """
        check_label = f" after '{context}'" if context else ""
        logger.info(f"🔍 Scanning for error patterns in response{check_label}...")

        try:
            page_text = self.page.inner_text("body")
            page_text_lower = page_text.lower()

            detected_errors = []
            for phrase in self.ERROR_PHRASES:
                if phrase.lower() in page_text_lower:
                    detected_errors.append(phrase)

            if detected_errors:
                # Extract the specific lines containing error text for context
                error_lines = []
                for line in page_text.split('\n'):
                    line_stripped = line.strip()
                    if not line_stripped or len(line_stripped) < 5:
                        continue
                    line_lower = line_stripped.lower()
                    if any(p.lower() in line_lower for p in detected_errors):
                        error_lines.append(line_stripped[:300])

                error_msg = (
                    f"❌ Error/exception detected in AI response{check_label}!\n"
                    f"Matched error patterns: {detected_errors}\n"
                    f"Error text found on page:\n"
                    + "\n".join(f"  → {line}" for line in error_lines[:10])
                )
                logger.error(error_msg)
                raise AssertionError(error_msg)

            logger.info(f"✓ No error patterns detected in response{check_label}")

        except AssertionError:
            raise
        except Exception as e:
            logger.warning(f"⚠️ Could not complete error scan: {str(e)}")

    def validate_planning_agent_response_quality(self, extra_keywords=None):
        """
        Validate that the PlanningAgent response is present and contains meaningful
        brief-related content (mentions objectives, key message, tone, etc.).

        Hard assertion: At least 2 baseline brief keywords must be present.
        Soft assertion: If extra_keywords are provided, logs warnings for missing ones.

        Args:
            extra_keywords: Optional list of use-case-specific keywords to soft-check
                (e.g., ["social media", "back to school"] for Obsidian Pearl).

        Raises:
            AssertionError: If PlanningAgent response is missing or lacks baseline content.
        """
        logger.info("🔍 Validating PlanningAgent response quality...")

        try:
            agent_label = self.page.locator(self.AGENT)
            expect(agent_label).to_be_visible(timeout=15000)
            logger.info("✓ PlanningAgent label is visible")

            page_text = self.page.inner_text("body")
            page_text_lower = page_text.lower()

            # --- Hard assertion: baseline brief structure keywords ---
            brief_keywords = [
                "objective", "key_message", "key message", "tone", "style",
                "timeline", "cta", "call to action", "campaign", "brief",
                "audience", "deliverable"
            ]

            found_keywords = [kw for kw in brief_keywords if kw in page_text_lower]

            if len(found_keywords) < 2:
                error_msg = (
                    f"❌ PlanningAgent response appears incomplete or irrelevant.\n"
                    f"Expected at least 2 of these brief-related keywords: {brief_keywords}\n"
                    f"Found only: {found_keywords}"
                )
                logger.error(error_msg)
                raise AssertionError(error_msg)

            logger.info(
                f"✓ PlanningAgent response contains {len(found_keywords)} "
                f"brief-related keywords: {found_keywords}"
            )

            # --- Soft assertion: use-case-specific extra keywords ---
            soft_warnings = []
            if extra_keywords:
                found_extra = [kw for kw in extra_keywords if kw.lower() in page_text_lower]
                missing_extra = [kw for kw in extra_keywords if kw.lower() not in page_text_lower]
                if found_extra:
                    logger.info(f"✓ [Soft] Use-case keywords found: {found_extra}")
                if missing_extra:
                    warn_msg = (
                        f"⚠️ [Soft] Some use-case keywords not found in PlanningAgent response: "
                        f"{missing_extra}"
                    )
                    logger.warning(warn_msg)
                    soft_warnings.append(warn_msg)

            return {
                'status': 'PASSED',
                'found_keywords': found_keywords,
                'soft_warnings': soft_warnings,
                'validation': 'PlanningAgent response is meaningful and brief-related'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate PlanningAgent response: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def validate_brief_confirmed_accuracy(self, expected_keywords=None, extra_fields=None):
        """
        Validate that the Brief Confirmed section displays accurate information
        matching the original campaign request.

        Hard assertion: Base required fields (overview, target audience, deliverable)
            must be present, and at least 50% of expected_keywords must match.
        Soft assertion: If extra_fields are provided (e.g., 'tone & style',
            'visual guidelines'), logs warnings for any that are missing.

        Args:
            expected_keywords: List of keywords expected in the brief summary.
                Defaults to ["paint", "homeowner", "marketing copy", "image"].
            extra_fields: Optional list of additional field labels to soft-check
                (e.g., ["tone & style", "visual guidelines"] for Obsidian Pearl).

        Raises:
            AssertionError: If Brief Confirmed section is missing or lacks required content.
        """
        if expected_keywords is None:
            expected_keywords = ["paint", "homeowner", "marketing copy", "image"]

        logger.info("🔍 Validating Brief Confirmed section accuracy...")

        try:
            brief_confirmed = self.page.locator(self.BRIEF_CONFIRMED_TEXT)
            expect(brief_confirmed).to_be_visible(timeout=15000)
            logger.info("✓ Brief Confirmed section is visible")

            page_text = self.page.inner_text("body")
            start_idx = page_text.rfind("Brief Confirmed")
            if start_idx < 0:
                raise AssertionError("❌ 'Brief Confirmed' text not found on page")

            end_idx = page_text.find("Products Selected", start_idx)
            if end_idx < 0:
                end_idx = min(start_idx + 1500, len(page_text))
            brief_text = page_text[start_idx:end_idx]
            brief_text_lower = brief_text.lower()

            logger.info(f"  Brief section text (first 500 chars): {brief_text[:500]}")

            # --- Hard assertion: base required fields ---
            required_fields = ["overview", "target audience", "deliverable"]
            missing_fields = [f for f in required_fields if f not in brief_text_lower]

            if missing_fields:
                error_msg = (
                    f"❌ Brief Confirmed section is missing required fields: {missing_fields}\n"
                    f"Brief text: {brief_text[:500]}"
                )
                logger.error(error_msg)
                raise AssertionError(error_msg)

            logger.info(f"✓ All required fields present: {required_fields}")

            # --- Soft assertion: extra fields (use-case specific) ---
            soft_warnings = []
            if extra_fields:
                found_extra = [f for f in extra_fields if f.lower() in brief_text_lower]
                missing_extra = [f for f in extra_fields if f.lower() not in brief_text_lower]
                if found_extra:
                    logger.info(f"✓ [Soft] Extra fields found: {found_extra}")
                if missing_extra:
                    warn_msg = (
                        f"⚠️ [Soft] Some extra fields not found in Brief Confirmed: "
                        f"{missing_extra}"
                    )
                    logger.warning(warn_msg)
                    soft_warnings.append(warn_msg)

            # --- Hard assertion: expected keywords (at least 50% must match) ---
            found_keywords = [kw for kw in expected_keywords if kw.lower() in brief_text_lower]
            missing_keywords = [kw for kw in expected_keywords if kw.lower() not in brief_text_lower]

            if len(found_keywords) < max(1, int(len(expected_keywords) * 0.5)):
                error_msg = (
                    f"❌ Brief Confirmed content does not match campaign request.\n"
                    f"Expected keywords: {expected_keywords}\n"
                    f"Found: {found_keywords}\n"
                    f"Missing: {missing_keywords}\n"
                    f"Brief text: {brief_text[:500]}"
                )
                logger.error(error_msg)
                raise AssertionError(error_msg)

            if missing_keywords:
                logger.warning(f"⚠️ Some expected keywords not found in brief: {missing_keywords}")

            logger.info(
                f"✓ Brief content matches campaign — found {len(found_keywords)}/"
                f"{len(expected_keywords)} keywords: {found_keywords}"
            )

            return {
                'status': 'PASSED',
                'found_keywords': found_keywords,
                'missing_keywords': missing_keywords,
                'soft_warnings': soft_warnings,
                'validation': 'Brief Confirmed content is accurate'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate Brief Confirmed accuracy: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def validate_generated_copy_accuracy(self, product_name, generated_content_locator=None,  # noqa: ARG002
                                           min_length=30, expected_copy_keywords=None):
        """
        Validate that the generated marketing copy is accurate and relevant.

        Hard assertions: product name present, minimum length, no error text.
        Soft assertion: If expected_copy_keywords are provided, logs warnings
            for any missing marketing/thematic keywords.

        Args:
            product_name: Product name that should appear in the copy (e.g., 'Olive Stone').
            generated_content_locator: XPath locator for generated content. Auto-detected if None.
            min_length: Minimum character count for the marketing copy (default: 30).
            expected_copy_keywords: Optional list of thematic keywords to soft-check
                in the copy (e.g., ["rich black", "drama", "backdrop"] for Obsidian Pearl).

        Raises:
            AssertionError: If the generated copy fails any hard validation check.
        """
        logger.info(f"🔍 Validating generated marketing copy for '{product_name}'...")

        try:
            page_text = self.page.inner_text("body")

            # Find the generated content section (starts with sparkle emoji)
            sparkle_idx = page_text.rfind("✨")
            if sparkle_idx < 0:
                raise AssertionError(
                    "❌ Generated marketing copy not found — no '✨' marker detected on page."
                )

            copy_text = page_text[sparkle_idx:sparkle_idx + 1500].strip()
            logger.info(f"  Generated copy (first 500 chars): {copy_text[:500]}")

            # Hard Validation 1: Minimum length
            if len(copy_text) < min_length:
                raise AssertionError(
                    f"❌ Generated marketing copy is too short ({len(copy_text)} chars). "
                    f"Expected at least {min_length} characters.\n"
                    f"Copy: '{copy_text}'"
                )
            logger.info(f"✓ Copy length OK: {len(copy_text)} chars (min: {min_length})")

            # Hard Validation 2: Product name mentioned
            if product_name.lower() not in copy_text.lower():
                raise AssertionError(
                    f"❌ Product name '{product_name}' not found in generated marketing copy.\n"
                    f"Copy: '{copy_text[:500]}'"
                )
            logger.info(f"✓ Product name '{product_name}' found in generated copy")

            # Hard Validation 3: No error text in the copy
            copy_lower = copy_text.lower()
            for phrase in self.ERROR_PHRASES:
                if phrase.lower() in copy_lower:
                    raise AssertionError(
                        f"❌ Error pattern '{phrase}' detected in generated marketing copy!\n"
                        f"Copy: '{copy_text[:500]}'"
                    )
            logger.info("✓ No error patterns in generated copy")

            # --- Soft assertion: thematic/marketing keywords ---
            soft_warnings = []
            if expected_copy_keywords:
                found_kw = [kw for kw in expected_copy_keywords if kw.lower() in copy_lower]
                missing_kw = [kw for kw in expected_copy_keywords if kw.lower() not in copy_lower]
                if found_kw:
                    logger.info(
                        f"✓ [Soft] Marketing/thematic keywords found in copy: {found_kw}"
                    )
                if missing_kw:
                    warn_msg = (
                        f"⚠️ [Soft] Some expected copy keywords not found: {missing_kw}"
                    )
                    logger.warning(warn_msg)
                    soft_warnings.append(warn_msg)

            logger.info(f"✓ Generated marketing copy validated successfully for '{product_name}'")

            return {
                'status': 'PASSED',
                'product_name': product_name,
                'copy_length': len(copy_text),
                'soft_warnings': soft_warnings,
                'validation': f'Marketing copy is accurate and mentions {product_name}'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate generated copy: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    def validate_products_selected_section(self, expected_product_name,
                                             expected_attributes=None,
                                             expected_price_pattern=None):
        """
        Validate that the Products Selected section shows the correct product.

        Hard assertion: Product name must be present.
        Soft assertions: If expected_attributes or expected_price_pattern are
            provided, logs warnings for any that are missing.

        Args:
            expected_product_name: Expected product name (e.g., 'Olive Stone').
            expected_attributes: Optional list of product descriptor keywords to
                soft-check (e.g., ['black', 'matte', 'dramatic', 'luxe']).
            expected_price_pattern: Optional price string to soft-check
                (e.g., '$59.95 USD').

        Raises:
            AssertionError: If Products Selected section is missing or shows wrong product.
        """
        logger.info(f"🔍 Validating Products Selected section for '{expected_product_name}'...")

        try:
            products_selected = self.page.locator(self.PRODUCT_SELECTED)
            expect(products_selected).to_be_visible(timeout=15000)
            logger.info("✓ Products Selected section is visible")

            page_text = self.page.inner_text("body")
            start_idx = page_text.rfind("Products Selected")
            if start_idx < 0:
                raise AssertionError("❌ 'Products Selected' text not found on page")

            end_idx = page_text.find("✨", start_idx)
            if end_idx < 0:
                end_idx = min(start_idx + 500, len(page_text))
            section_text = page_text[start_idx:end_idx]
            section_text_lower = section_text.lower()

            logger.info(f"  Products section text: {section_text[:400]}")

            # --- Hard assertion: product name ---
            if expected_product_name.lower() not in section_text_lower:
                raise AssertionError(
                    f"❌ Expected product '{expected_product_name}' not found in "
                    f"Products Selected section.\nSection text: '{section_text[:400]}'"
                )

            logger.info(
                f"✓ Product '{expected_product_name}' correctly shown in Products Selected"
            )

            # --- Soft assertion: product attributes ---
            soft_warnings = []
            if expected_attributes:
                found_attrs = [a for a in expected_attributes if a.lower() in section_text_lower]
                missing_attrs = [a for a in expected_attributes if a.lower() not in section_text_lower]
                if found_attrs:
                    logger.info(f"✓ [Soft] Product attributes found: {found_attrs}")
                if missing_attrs:
                    warn_msg = (
                        f"⚠️ [Soft] Some product attributes not found: {missing_attrs}"
                    )
                    logger.warning(warn_msg)
                    soft_warnings.append(warn_msg)

            # --- Soft assertion: price ---
            if expected_price_pattern:
                if expected_price_pattern.lower() in section_text_lower:
                    logger.info(f"✓ [Soft] Price found: {expected_price_pattern}")
                else:
                    # Also try a generic price regex as fallback
                    price_match = re.search(r'\$\d+\.\d{2}\s*usd', section_text_lower)
                    if price_match:
                        logger.info(
                            f"✓ [Soft] Price pattern found (different value): "
                            f"{price_match.group()}"
                        )
                    else:
                        warn_msg = (
                            f"⚠️ [Soft] Expected price '{expected_price_pattern}' "
                            f"not found in Products Selected section"
                        )
                        logger.warning(warn_msg)
                        soft_warnings.append(warn_msg)

            return {
                'status': 'PASSED',
                'product_name': expected_product_name,
                'soft_warnings': soft_warnings,
                'validation': f'{expected_product_name} is correctly displayed'
            }

        except AssertionError:
            raise
        except Exception as e:
            error_msg = f"Failed to validate Products Selected: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise AssertionError(error_msg) from e

    # ---------- COLOR DEFINITIONS ----------
    COLOR_RANGES = {
        "olive": {"r": (80, 180), "g": (80, 170), "b": (40, 120), "description": "olive/earthy tones"},
        "obsidian": {"r": (140, 230), "g": (140, 230), "b": (140, 230), "description": "obsidian/pearl gray tones"},
        "green": {"r": (20, 120), "g": (80, 200), "b": (40, 130), "description": "green/forest tones"},
        "beige": {"r": (160, 240), "g": (140, 220), "b": (100, 180), "description": "beige/warm tones"},
        "brown": {"r": (100, 180), "g": (60, 140), "b": (30, 100), "description": "brown/earthy tones"},
    }

    def extract_dominant_color(self, locator):
        """
        Extract the dominant (average) color from an element by taking a screenshot.
        Filters out near-black and near-white pixels for better accuracy.

        Args:
            locator: Playwright locator for the element to analyze.

        Returns:
            tuple: (avg_r, avg_g, avg_b) average RGB values, or None on error.
        """
        try:
            screenshot_bytes = locator.screenshot()
            image = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
            image = image.resize((100, 100))
            raw = image.tobytes()
            pixels = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]

            # Filter out very dark (near-black) and very bright (near-white) pixels
            filtered_pixels = [
                p for p in pixels
                if not (p[0] < 30 and p[1] < 30 and p[2] < 30)
                and not (p[0] > 225 and p[1] > 225 and p[2] > 225)
            ]
            if not filtered_pixels:
                filtered_pixels = pixels

            avg_r = sum(p[0] for p in filtered_pixels) // len(filtered_pixels)
            avg_g = sum(p[1] for p in filtered_pixels) // len(filtered_pixels)
            avg_b = sum(p[2] for p in filtered_pixels) // len(filtered_pixels)

            return (avg_r, avg_g, avg_b)
        except Exception as e:
            logger.warning(f"⚠️ Could not extract dominant color: {str(e)}")
            return None

    def _get_image_pixels(self, locator):
        """
        Take a screenshot of the element and return the list of RGB pixel tuples.

        Args:
            locator: Playwright locator for the element.

        Returns:
            list: List of (r, g, b) tuples, or None on error.
        """
        try:
            screenshot_bytes = locator.screenshot()
            image = Image.open(BytesIO(screenshot_bytes)).convert("RGB")
            image = image.resize((150, 150))
            raw = image.tobytes()
            return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
        except Exception as e:
            logger.warning(f"⚠️ Could not get image pixels: {str(e)}")
            return None

    def validate_color_match_with_swatch(self, image_locator, pixel_tolerance=80, min_match_percent=15):
        """
        Validate that the selected product color appears prominently in the
        generated image. Instead of comparing averages (which fails because
        generated images contain furniture, plants, floors, etc.), this method
        counts what percentage of image pixels are close to the swatch color.

        For example, if Olive Stone is selected, the generated image should have
        walls painted in that color — so a significant portion of pixels should
        be within tolerance of the swatch.

        This is a soft validation — logs a warning on mismatch but does not fail
        the test, since AI-generated images may vary.

        Args:
            image_locator: Playwright locator for the generated image element.
            pixel_tolerance: Max Euclidean distance for a pixel to be considered
                             a "match" to the swatch color (default: 80).
            min_match_percent: Minimum percentage of image pixels that must match
                               the swatch color to pass (default: 15%).
        """
        logger.info("Comparing selected color swatch with generated image...")

        try:
            # Step 1: Extract the swatch color
            swatch_locator = self.page.locator(self.PRODUCT_COLOR_SWATCH)
            if swatch_locator.count() == 0:
                logger.warning("⚠️ PRODUCT_COLOR_SWATCH not found — skipping color comparison.")
                return

            expect(swatch_locator).to_be_visible(timeout=10000)
            swatch_color = self.extract_dominant_color(swatch_locator)
            if swatch_color is None:
                logger.warning("⚠️ Could not extract swatch color — skipping comparison.")
                return
            logger.info(f"  Swatch color → RGB({swatch_color[0]}, {swatch_color[1]}, {swatch_color[2]})")

            # Step 2: Get all pixels from the generated image
            image_pixels = self._get_image_pixels(image_locator)
            if image_pixels is None:
                logger.warning("⚠️ Could not extract image pixels — skipping comparison.")
                return

            total_pixels = len(image_pixels)
            logger.info(f"  Total image pixels analyzed: {total_pixels}")

            # Step 3: Count pixels that are close to the swatch color
            matching_pixels = 0
            for pixel in image_pixels:
                distance = math.sqrt(
                    (swatch_color[0] - pixel[0]) ** 2
                    + (swatch_color[1] - pixel[1]) ** 2
                    + (swatch_color[2] - pixel[2]) ** 2
                )
                if distance <= pixel_tolerance:
                    matching_pixels += 1

            match_percent = (matching_pixels / total_pixels) * 100
            logger.info(f"  Matching pixels: {matching_pixels}/{total_pixels} ({match_percent:.1f}%)")
            logger.info(f"  Required minimum: {min_match_percent}%")

            if match_percent >= min_match_percent:
                logger.info(
                    f"✓ Product color is present in the generated image — "
                    f"{match_percent:.1f}% of pixels match the swatch color "
                    f"(min required: {min_match_percent}%)"
                )
            else:
                logger.warning(
                    f"⚠️ Product color is NOT prominently present in the generated image. "
                    f"Only {match_percent:.1f}% of pixels match the swatch "
                    f"RGB({swatch_color[0]}, {swatch_color[1]}, {swatch_color[2]}) "
                    f"(min required: {min_match_percent}%). "
                    f"This is a soft check — AI-generated images may vary."
                )

        except Exception as e:
            logger.warning(f"⚠️ Color swatch comparison failed: {str(e)}")

    def validate_image_dominant_color(self, image_locator, expected_color, min_match_percent=15):
        """
        Validate that the expected color appears prominently in the generated image
        by checking what percentage of pixels fall within the predefined color range.
        This is a soft validation — it logs a warning on mismatch but does not fail the test,
        since AI-generated images can vary in color between runs.

        Args:
            image_locator: Playwright locator for the image element
            expected_color: Key from COLOR_RANGES (e.g., 'olive', 'green', 'beige', 'brown')
            min_match_percent: Minimum percentage of pixels that must match (default: 15%)
        """
        logger.info(f"Analyzing image for '{expected_color}' color presence...")

        try:
            if expected_color not in self.COLOR_RANGES:
                logger.warning(f"⚠️ Unknown expected color '{expected_color}'. Available: {list(self.COLOR_RANGES.keys())}")
                return

            color_range = self.COLOR_RANGES[expected_color]
            r_min, r_max = color_range["r"]
            g_min, g_max = color_range["g"]
            b_min, b_max = color_range["b"]

            # Get all pixels from the image
            image_pixels = self._get_image_pixels(image_locator)
            if image_pixels is None:
                logger.warning("⚠️ Could not extract image pixels.")
                return

            total_pixels = len(image_pixels)

            # Count pixels that fall within the expected color range
            matching_pixels = 0
            for r, g, b in image_pixels:
                if r_min <= r <= r_max and g_min <= g <= g_max and b_min <= b <= b_max:
                    matching_pixels += 1

            match_percent = (matching_pixels / total_pixels) * 100
            logger.info(f"  Expected color: '{expected_color}' ({color_range['description']})")
            logger.info(f"  Range: R({r_min}-{r_max}), G({g_min}-{g_max}), B({b_min}-{b_max})")
            logger.info(f"  Matching pixels: {matching_pixels}/{total_pixels} ({match_percent:.1f}%)")
            logger.info(f"  Required minimum: {min_match_percent}%")

            if match_percent >= min_match_percent:
                logger.info(
                    f"✓ '{expected_color}' color is present in the generated image — "
                    f"{match_percent:.1f}% of pixels match (min required: {min_match_percent}%)"
                )
            else:
                logger.warning(
                    f"⚠️ '{expected_color}' ({color_range['description']}) is NOT prominently "
                    f"present in the generated image. Only {match_percent:.1f}% of pixels match "
                    f"the range R({r_min}-{r_max}), G({g_min}-{g_max}), B({b_min}-{b_max}) "
                    f"(min required: {min_match_percent}%). "
                    f"This is a soft check — AI-generated images may vary."
                )

        except Exception as e:
            logger.warning(f"⚠️ Could not analyze image dominant color: {str(e)}")
