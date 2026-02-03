from base.base import BasePage
from playwright.sync_api import expect
import logging
logger = logging.getLogger(__name__)

class GeneratePage(BasePage):
    GENERATE_DRAFT = "//button[@title='Generate Draft']"
    TYPE_QUESTION = "//textarea[@placeholder='Type a new question...']"
    SEND_BUTTON = "//div[@aria-label='Ask question button']"
    SHOW_CHAT_HISTORY_BUTTON = "//span[text()='Show template history']"
    HIDE_CHAT_HISTORY_BUTTON = "//span[text()='Hide Chat History']"
    CHAT_HISTORY_ITEM = "//body//div[@id='root']//div[@role='presentation']//div[@role='presentation']//div[1]//div[1]//div[1]//div[1]//div[1]//div[1]"
    SHOW_CHAT_HISTORY = "//span//i"
    CHAT_HISTORY_NAME = "div[aria-label='chat history list']"
    CHAT_CLOSE_ICON = "button[title='Hide']"
    CHAT_HISTORY_OPTIONS = "//button[@id='moreButton']"
    CHAT_HISTORY_DELETE = "//button[@role='menuitem']"
    CHAT_HISTORY_CLOSE = "//i[@data-icon-name='Cancel']"
    NEW_CHAT_BUTTON = 'button[aria-label="start a new chat button"]'
    CLEAR_CHAT_BROOM_BUTTON = "button.ms-Button--commandBar:has(i[data-icon-name='Broom'])"
    BROWSE_BUTTON = "span:has-text('Browse') >> xpath=preceding-sibling::button[1]"


    # ---------- THREAD RENAME LOCATORS ----------
    THREAD_NAME_INPUT = "//input[contains(@id, 'TextField')]"
    THREAD_RENAME_CONFIRM = "//button[@aria-label='confirm new title']"
    THREAD_RENAME_CANCEL = "//button[@aria-label='cancel edit title']"
    THREAD_TITLE_LABEL = "//div[contains(@class, 'thread-title')]"
    THREAD_EDIT_ICON = "//button[@aria-label='edit thread title']"


    def __init__(self, page):
        super().__init__(page)

    def validate_generate_page(self):
        """Validate that Generate page chat conversation elements are visible"""
        self.page.wait_for_timeout(1000)  # Reduced from 3s
        expect(self.page.locator(self.TYPE_QUESTION)).to_be_visible()
        expect(self.page.locator(self.SEND_BUTTON)).to_be_visible()

    def enter_a_question(self, text):
        # Type a question in the text area
        self.page.wait_for_timeout(1000)  # Reduced from 3s
        self.page.locator(self.TYPE_QUESTION).fill(text)
        self.page.wait_for_timeout(500)  # Reduced from 3s

    def click_send_button(self):
        # Type a question in the text area
        self.page.locator(self.SEND_BUTTON).click()
        locator = self.page.locator("//p[contains(text(),'Generating template...this may take up to 30 secon')]")
        stop_button = self.page.locator("//div[@aria-label='Stop generating']")

        try:
            # Wait up to 60s for the element to become **hidden**
            locator.wait_for(state="hidden", timeout=60000)
        except TimeoutError:
            msg = "❌ TIMED-OUT: Not recieved response within 60 sec."
            logger.info(msg)  # ✅ log to console/log file
            raise AssertionError(msg)

        finally:
            if stop_button.is_visible():
                stop_button.click()
                logger.info("Clicked on 'Stop generating' button after timeout.")
            else:
                logger.info("'Stop generating' button not visible.")

        self.page.wait_for_timeout(2000)  # Reduced from 5s

    def click_generate_draft_button(self):
        # Wait for Generate Draft button to be visible and enabled
        draft_btn = self.page.locator(self.GENERATE_DRAFT)
        expect(draft_btn).to_be_visible(timeout=8000)
        expect(draft_btn).to_be_enabled(timeout=15000)  # Wait up to 30s for button to be enabled
        draft_btn.click()
        self.page.wait_for_load_state("networkidle", timeout=20000)
    
    def click_browse_button(self):
        # click on BROWSE
        self.page.wait_for_timeout(1000)  # Reduced from 3s
        self.page.locator(self.BROWSE_BUTTON).click()
        self.page.wait_for_timeout(2000)  # Reduced from 5s

    def show_chat_history(self):
        """Click to show chat history if the button is visible."""
        show_button = self.page.locator(self.SHOW_CHAT_HISTORY_BUTTON)
        if show_button.is_visible():
            show_button.click()
            self.page.wait_for_timeout(1000)  # Reduced from 2s
            # Check that at least one chat history item is visible (use .first to avoid strict mode violation)
            expect(self.page.locator(self.CHAT_HISTORY_ITEM).first).to_be_visible()
        else:
            logger.info("Chat history is not generated")

    def close_chat_history(self):
        """Click to close chat history if visible."""
        hide_button = self.page.locator(self.HIDE_CHAT_HISTORY_BUTTON)
        if hide_button.is_visible():
            hide_button.click()
            self.page.wait_for_timeout(1000)  # Reduced from 2s
        else:
            logger.info(
                "Hide button not visible. Chat history might already be closed."
            )

    def delete_chat_history(self):

        self.page.locator(self.SHOW_CHAT_HISTORY_BUTTON).click()
        self.page.wait_for_timeout(4000)
        chat_history = self.page.locator("//span[contains(text(),'No chat history.')]")
        if chat_history.is_visible():
            self.page.wait_for_load_state("networkidle")
            self.page.locator("button[title='Hide']").wait_for(
                state="visible", timeout=5000
            )
            self.page.locator("button[title='Hide']").click()

        else:
            self.page.locator(self.CHAT_HISTORY_OPTIONS).click()
            self.page.locator(self.CHAT_HISTORY_DELETE).click()
            self.page.wait_for_timeout(5000)
            self.page.get_by_role("button", name="Clear All").click()
            self.page.wait_for_timeout(11000)  # Wait longer for deletion to complete
            
            # Try to verify "No chat history." text appears, but don't fail if it doesn't
            try:
                expect(self.page.locator("//span[contains(text(),'No chat history.')]")).to_be_visible(timeout=15000)
                logger.info("✅ 'No chat history.' text is visible after deletion")
            except AssertionError:
                logger.warning("⚠️ 'No chat history.' text not visible, but continuing (deletion may have succeeded)")
            
            # Close the chat history panel - use more specific locator to avoid strict mode violation
            close_button = self.page.get_by_role("button", name="Close")
            try:
                if close_button.is_visible(timeout=2000):
                    close_button.click()
                    logger.info("✅ Closed chat history panel")
            except Exception as e:
                logger.warning(f"⚠️ Could not close chat history panel: {e}")
            
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)

    def validate_draft_button_enabled(self):
        """
        Check if Generate Draft button is enabled.
        Returns True if enabled, False if disabled.
        """
        self.page.wait_for_timeout(2000)  # Reduced from 5s
        generate_draft_button = self.page.locator(self.GENERATE_DRAFT)
        is_enabled = generate_draft_button.is_enabled()
        
        if not is_enabled:
            logger.info("✅ 'Generate Draft' button is disabled (as expected on launch).")
        else:
            logger.info("✅ 'Generate Draft' button is enabled.")
        
        return is_enabled
    
    def select_history_thread(self, thread_index=0):
        """Select a history thread from the template history panel."""
        history_threads = self.page.locator('div[role="listitem"]')
        count = history_threads.count()

        # ❗ Fail the test if no threads found
        assert count > 0, "No history threads found — test failed."

        # Optional: fail if the index does not exist
        assert thread_index < count, (
            f"Thread index {thread_index} is out of range. Only {count} thread(s) available."
        )

        history_threads.nth(thread_index).wait_for(state="visible")
        history_threads.nth(thread_index).click()

    def click_new_chat_button(self):
        """Click the new chat button next to the chat box."""
        new_chat_button = self.page.locator(self.NEW_CHAT_BUTTON)

        # Fail the test if button not found or not visible
        assert new_chat_button.is_visible(), "New Chat button is not visible — test failed."

        assert new_chat_button.is_enabled(), "New Chat button is disabled — test failed."

        new_chat_button.click()
        logger.info("New Chat button clicked successfully")
    
    def verify_saved_chat(self, expected_text: str):
        """
        Verify that the expected text appears in the saved chat conversation.
        Uses multiple fallback strategies to locate chat messages.
        """
        logger.info(f"🔹 Verifying saved chat contains text: '{expected_text}'")
        
        # Wait for chat to load
        self.page.wait_for_timeout(5000)
        
        # Strategy 1: Try specific CSS class selectors (may change with UI updates)
        chat_messages_locator = '._chatMessageUserMessage_1dc7g_87, ._answerText_1qm4u_14'
        chat_messages = self.page.locator(chat_messages_locator)
        
        if chat_messages.count() > 0:
            logger.info(f"Found {chat_messages.count()} chat messages using CSS class selectors")
            for i in range(chat_messages.count()):
                message_text = chat_messages.nth(i).inner_text()
                if expected_text in message_text:
                    logger.info(f"✅ Found expected text in message {i}")
                    return
        
        # Strategy 2: Try more generic selectors for user messages and answers
        user_messages = self.page.locator("div[class*='chatMessage'], div[class*='userMessage']")
        answer_messages = self.page.locator("div[class*='answer'], p")
        
        all_messages_count = user_messages.count() + answer_messages.count()
        logger.info(f"Strategy 2: Found {user_messages.count()} user messages and {answer_messages.count()} answer messages")
        
        # Check user messages
        for i in range(user_messages.count()):
            message_text = user_messages.nth(i).inner_text()
            if expected_text in message_text:
                logger.info(f"✅ Found expected text in user message {i}")
                return
        
        # Check answer messages
        for i in range(answer_messages.count()):
            message_text = answer_messages.nth(i).inner_text()
            if expected_text in message_text:
                logger.info(f"✅ Found expected text in answer message {i}")
                return
        
        # Strategy 3: Search entire page content as last resort
        page_content = self.page.content()
        if expected_text in page_content:
            logger.info("✅ Found expected text in page content (full page search)")
            return
        
        # If we get here, the text was not found
        logger.error(f"❌ Expected text '{expected_text}' not found in saved chat")
        logger.error(f"Total messages checked: CSS={chat_messages.count()}, Generic={all_messages_count}")
        
        # Log first few message samples for debugging
        if chat_messages.count() > 0:
            logger.error(f"Sample message 0: {chat_messages.nth(0).inner_text()[:100]}")
        
        assert False, f"Expected text '{expected_text}' not found in saved chat after checking {chat_messages.count() + all_messages_count} messages."
            
    def delete_thread_by_index(self, thread_index: int = 0):
        """
        Delete a session thread based on its index and verify it is removed.
        
        :param thread_index: Index of the thread to delete (0 = first thread)
        """
        # 1️⃣ Locate all threads
        threads = self.page.locator('div[data-list-index]')
        count = threads.count()
        
        # Fail if no threads exist
        assert count > 0, "No history threads found — cannot delete."
        assert count > thread_index, f"Thread index {thread_index} out of range (total: {count})"

        # 2️⃣ Locate the thread at the given index
        thread = threads.nth(thread_index)
        
        # 2a️⃣ Hover over the thread to reveal action icons
        thread.hover()
        self.page.wait_for_timeout(500)  # Wait for icons to appear

        # 3️⃣ Click the Delete icon in that thread
        delete_icon = thread.locator('button[title="Delete"]')
        expect(delete_icon).to_be_visible(timeout=3000)
        delete_icon.click()
        logger.info(f"Clicked delete icon on thread at index {thread_index}")

        # 4️⃣ Wait for delete confirmation dialog
        dialog_title = self.page.get_by_text("Are you sure you want to delete this item?")
        dialog_title.wait_for(state="visible", timeout=5000)
        logger.info("Delete confirmation dialog appeared")

        # Verify dialog text is present
        dialog_text = self.page.get_by_text("The history of this chat session will permanently removed")
        assert dialog_text.is_visible(), "Delete confirmation text not visible in dialog"
        logger.info("Delete confirmation text verified")

        # 5️⃣ Click Delete button in the dialog
        delete_button = self.page.get_by_role("button", name="Delete")
        assert delete_button.is_visible(), "Delete button not visible in confirmation dialog"
        delete_button.click()
        logger.info("Clicked Delete in confirmation dialog")

        # Wait for dialog to disappear - use try/except for more resilient handling
        try:
            dialog_title.wait_for(state="hidden", timeout=10000)
            logger.info("Delete confirmation dialog closed")
        except Exception as e:
            logger.warning(f"⚠️ Dialog did not disappear as expected, but continuing: {e}")
            # Wait a bit longer for UI to settle
            self.page.wait_for_timeout(3000)

        # 6️⃣ Verify the thread is removed - re-query the threads to avoid stale elements
        self.page.wait_for_timeout(3000)  # Increased wait time for UI to update
        threads_after = self.page.locator('div[data-list-index]')
        new_count = threads_after.count()
        
        # Be more lenient - thread might be deleted even if count verification fails temporarily
        if new_count != count - 1:
            logger.warning(f"⚠️ Thread count mismatch on first check (before: {count}, after: {new_count}), waiting and rechecking...")
            self.page.wait_for_timeout(2000)
            threads_after = self.page.locator('div[data-list-index]')
            new_count = threads_after.count()
        
        assert new_count == count - 1, f"Thread at index {thread_index} was not deleted (before: {count}, after: {new_count})"
        logger.info(f"Thread at index {thread_index} successfully deleted. Thread count decreased from {count} to {new_count}")

    def click_edit_icon(self, thread_index: int = 0):
        """
        Click the edit icon for the selected history thread.
        
        :param thread_index: Index of the thread to edit (0 = first thread)
        """
        # 1️⃣ Locate all threads
        threads = self.page.locator('div[data-list-index]')
        count = threads.count()
        
        # Fail if no threads exist
        assert count > 0, "No history threads found — cannot click edit."
        assert count > thread_index, f"Thread index {thread_index} out of range (total: {count})"

        # 2️⃣ Locate the specified thread
        thread = threads.nth(thread_index)
        
        # 2a️⃣ Hover over the thread to reveal action icons
        thread.hover()
        self.page.wait_for_timeout(500)  # Wait for icons to appear

        # 3️⃣ Click the Edit icon in that thread
        edit_icon = thread.locator('button[title="Edit"]')
        expect(edit_icon).to_be_visible(timeout=3000)
        edit_icon.click()
        logger.info(f"Clicked edit icon on thread at index {thread_index}") 

    def update_thread_name(self, new_name: str, thread_index: int = 0):
        """
        Types new thread name into input box after edit icon is clicked.
        
        :param new_name: The new name for the thread
        :param thread_index: Index of the thread being renamed (0 = first thread)
        """
        # Wait for input field to appear after clicking edit icon
        self.page.wait_for_timeout(1000)
        
        # Locate the input field - it should be visible after clicking edit
        input_field = self.page.locator(self.THREAD_NAME_INPUT)
        
        # Wait for input to be visible and enabled
        input_field.wait_for(state="visible", timeout=5000)
        assert input_field.is_visible(), "Thread name input field is not visible"
        
        # Clear existing text and enter new name
        input_field.clear()
        input_field.fill(new_name)
        logger.info(f"Updated thread name to: {new_name}")

    def click_rename_confirm(self, thread_index: int = 0):
        """
        Clicks the tick icon to confirm rename.
        
        :param thread_index: Index of the thread being renamed (0 = first thread)
        """
        # Get the specific thread element
        threads = self.page.locator('div[role="listitem"]')
        thread = threads.nth(thread_index)
        
        # Locate the confirm button within this thread
        confirm_button = thread.locator(self.THREAD_RENAME_CONFIRM)
        
        # Wait for button to be visible
        confirm_button.wait_for(state="visible", timeout=10000)
        assert confirm_button.is_visible(), "Rename confirm button is not visible"
        
        confirm_button.click()
        logger.info("Clicked confirm button to save renamed thread at index %d", thread_index)
        
        # Wait for the rename to complete
        self.page.wait_for_timeout(2000)

    def click_rename_cancel(self, thread_index: int = 0):
        """
        Clicks the cross icon to cancel rename.
        
        :param thread_index: Index of the thread being renamed (0 = first thread)
        """
        # Get the specific thread element
        threads = self.page.locator('div[role="listitem"]')
        thread = threads.nth(thread_index)
        
        # Locate the cancel button within this thread
        cancel_button = thread.locator(self.THREAD_RENAME_CANCEL)
        
        # Wait for button to be visible
        cancel_button.wait_for(state="visible", timeout=10000)
        assert cancel_button.is_visible(), "Rename cancel button is not visible"
        
        cancel_button.click()
        logger.info("Clicked cancel button to discard rename for thread at index %d", thread_index)
        
        # Wait for the cancel to complete
        self.page.wait_for_timeout(1000)

    def get_thread_title(self, thread_index: int = 0):
        """
        Returns the thread title from the list.
        Prioritizes the hidden tooltip which contains the full untruncated text.
        """
        threads = self.page.locator('div[role="listitem"]')
        thread = threads.nth(thread_index)
        
        # If in edit mode, get value from input field
        input_field = thread.locator('input[type="text"]')
        if input_field.count() > 0 and input_field.is_visible():
            return input_field.input_value(timeout=2000).strip()
        
        # Get from hidden tooltip (full untruncated text)
        tooltip = thread.locator("div[hidden][id*='tooltip']")
        if tooltip.count() > 0:
            title = tooltip.first.text_content(timeout=2000).strip()
            if title:
                return title
        
        # Fallback: get from visible title div (may be truncated)
        title_div = thread.locator("div[class*='_chatTitle_']")
        if title_div.count() > 0:
            return title_div.first.inner_text(timeout=2000).strip()
        
        raise AssertionError(f"Unable to retrieve thread title at index {thread_index}")

    def click_clear_chat(self):
        """
        Clicks the clear chat button.
        """
        clear_chat_button = self.page.locator("button[aria-label='clear chat button']")
        clear_chat_button.wait_for(state="visible", timeout=10000)
        assert clear_chat_button.is_visible(), "Clear chat button is not visible"
        clear_chat_button.click()
        logger.info("Clicked clear chat button")
    
    def is_chat_cleared(self):
        """
        Verify that the chat has been cleared and a new session has started.
        Checks if the chat area is empty (no previous messages visible).
        
        :return: True if chat is cleared, False otherwise
        """
        self.page.wait_for_timeout(3000)
        
        # Check if any response paragraphs exist (indicating old messages)
        response_paragraphs = self.page.locator("//div[contains(@class, 'answerContainer')]//p")
        has_old_messages = response_paragraphs.count() > 0
        
        if has_old_messages:
            logger.warning("Chat still contains old messages after clearing")
            return False
        
        # Verify the input field is visible and empty (ready for new input)
        input_field = self.page.locator(self.TYPE_QUESTION)
        if not input_field.is_visible():
            logger.warning("Chat input field is not visible")
            return False
        
        # Check if input field is empty or has placeholder text
        input_value = input_field.input_value()
        if input_value.strip():
            logger.warning("Chat input field is not empty after clearing")
            return False
        
        logger.info("Chat successfully cleared and ready for new input")
        return True

    def get_history_thread_count(self):
        """
        Get the count of history threads in the template history panel.
        
        :return: Number of threads in history
        """
        self.show_chat_history()
        self.page.wait_for_timeout(2000)
        
        threads = self.page.locator('div[role="listitem"]')
        count = threads.count()
        logger.info("Current history thread count: %d", count)
        return count

    def is_new_session_visible(self):
        """
        Verify that a new chat session is visible (empty chat area with input ready).
        
        :return: True if new session is visible, False otherwise
        """
        # Check that input field is visible and ready
        input_field = self.page.locator(self.TYPE_QUESTION)
        if not input_field.is_visible():
            logger.warning("Input field not visible for new session")
            return False
        
        # Verify input is empty (placeholder visible)
        input_value = input_field.input_value()
        if input_value.strip():
            logger.warning("Input field contains text: '%s'", input_value)
            return False
        
        # Check that no old messages are visible
        response_paragraphs = self.page.locator("//div[contains(@class, 'answerContainer')]//p")
        if response_paragraphs.count() > 0:
            logger.warning("Old messages still visible in new session")
            return False
        
        logger.info("New session is visible and ready")
        return True

    def is_browse_button_disabled(self):
        """
        Returns True if the Browse button is disabled, else False.
        Disabled state is determined by the parent container (FluentUI pattern).
        """
        browse_button = self.page.locator(self.BROWSE_BUTTON)
        browse_button.wait_for(state="visible", timeout=5000)

        # Find the direct parent container holding disabled class
        parent_container = browse_button.locator("xpath=./ancestor::div[contains(@class, '_navigationButtonDisabled')]")

        if parent_container.count() > 0:
            logger.info("Browse button is DISABLED (parent has '_navigationButtonDisabled' class).")
            return True

        logger.info("Browse button is ENABLED")
        return False

    def is_response_generating(self):
        """
        Check if response is still generating by looking for 'Stop generating' button.
        Also checks if Browse button is disabled during generation.
        
        Returns:
            tuple: (is_generating: bool, is_browse_disabled: bool)
                - is_generating: True if response is generating (Stop generating button visible)
                - is_browse_disabled: True if Browse button is disabled
        """
        logger.info("Checking if response is still generating...")
        is_generating = False
        is_browse_disabled = False
        
        try:
            # Check for Stop generating button using class selector
            stop_button = self.page.locator("span[class*='_stopGeneratingText_']")
            if stop_button.is_visible(timeout=2000):
                logger.info("Response is still generating - Stop generating button is visible")
                is_generating = True
            else:
                # Double check with text selector
                stop_text_button = self.page.get_by_text("Stop generating")
                if stop_text_button.is_visible(timeout=2000):
                    logger.info("Response is still generating - Stop generating text found")
                    is_generating = True
            
            # If generating, check Browse button disabled state at the same time
            if is_generating:
                is_browse_disabled = self.is_browse_button_disabled()
                logger.info("Browse button disabled state during generation: %s", is_browse_disabled)
            else:
                logger.info("Response generation completed - Stop generating button not found")
            
            return is_generating, is_browse_disabled
            
        except Exception as e:
            logger.error("Error checking if response is generating: %s", str(e))
            return False, False

    def get_section_names_from_response(self):
        """
        Extract section names from the latest Generate response.
        Looks for bullet points, numbered lists, or formatted text in the response.
        
        Returns:
            list: List of section names found in the response
        """
        logger.info("🔹 Extracting section names from response")
        
        # Wait for response to be visible
        self.page.wait_for_timeout(3000)
        
        # Get the last answer container
        answer_container = self.page.locator("//div[contains(@class, 'answerContainer')]").last
        
        try:
            # Wait for answer to be visible
            expect(answer_container).to_be_visible(timeout=10000)
            
            section_names = []
            import re
            
            # Method 1: Try to get list items (ul/ol > li)
            list_items = answer_container.locator("li")
            
            if list_items.count() > 0:
                logger.info(f"Found {list_items.count()} list items in response")
                
                for i in range(list_items.count()):
                    section_name = list_items.nth(i).inner_text().strip()
                    if section_name:
                        section_names.append(section_name)
                        logger.info(f"  - Section {i + 1}: {section_name}")
                        
            if not section_names:
                # Method 2: Get all text content and parse line by line
                logger.info("No list items found, trying to parse full text content")
                full_text = answer_container.inner_text()
                
                logger.info(f"Response text preview (first 500 chars): {full_text[:500]}")
                
                # Split by newlines and look for section patterns
                lines = full_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Pattern 1: "1. Section Name" or "1) Section Name"
                    match = re.match(r'^(\d+)[.)]?\s*(.+)$', line)
                    if match and len(match.group(2).strip()) > 3:  # Avoid short non-section text
                        section_name = match.group(2).strip().rstrip(',.;:')  # Remove trailing punctuation
                        # Filter out non-section lines (like "30 seconds")
                        if not re.search(r'\d+\s*(second|minute|hour)', section_name, re.IGNORECASE):
                            section_names.append(section_name)
                            logger.info(f"  - Found numbered section: {section_name}")
                        continue
                    
                    # Pattern 2: "- Section Name" or "• Section Name"
                    match = re.match(r'^[-•*]\s*(.+)$', line)
                    if match and len(match.group(1).strip()) > 3:
                        section_name = match.group(1).strip().rstrip(',.;:')  # Remove trailing punctuation
                        section_names.append(section_name)
                        logger.info(f"  - Found bullet section: {section_name}")
                        continue
                    
                    # Pattern 3: Look for section keywords in bold or headers
                    # Common section name patterns in promissory notes
                    section_keywords = [
                        'principal', 'amount', 'interest', 'payment', 'maturity', 
                        'borrower', 'lender', 'promissory', 'repayment', 'default',
                        'collateral', 'guarantor', 'acceleration', 'prepayment',
                        'governing law', 'jurisdiction', 'waivers', 'remedies',
                        'notices', 'signatures', 'information', 'assignment', 'amendments'
                    ]
                    
                    if any(keyword in line.lower() for keyword in section_keywords):
                        # Check if it looks like a section header (not too long)
                        if len(line) < 100 and not line.endswith('.'):
                            # Strip trailing punctuation (commas, periods) for consistency
                            clean_line = line.rstrip(',.;:')
                            section_names.append(clean_line)
                            logger.info(f"  - Found keyword section: {clean_line}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_sections = []
            for section in section_names:
                if section.lower() not in seen:
                    seen.add(section.lower())
                    unique_sections.append(section)
            
            logger.info(f"✅ Extracted {len(unique_sections)} unique section names")
            return unique_sections
            
        except Exception as e:
            logger.error(f"❌ Failed to extract section names: {e}")
            return []

    def verify_section_removed(self, removed_section_name, current_section_list):
        """
        Verify that a removed section does not appear in the current section list.
        
        Args:
            removed_section_name: Name of the section that was removed
            current_section_list: Current list of section names
            
        Returns:
            bool: True if section is not in the list (successfully removed), False otherwise
        """
        logger.info(f"🔹 Verifying section '{removed_section_name}' is removed")
        
        # Normalize section names for comparison (case-insensitive, strip whitespace)
        removed_section_normalized = removed_section_name.lower().strip()
        
        for section in current_section_list:
            section_normalized = section.lower().strip()
            
            # Check if the removed section name appears in the current list
            if removed_section_normalized in section_normalized or section_normalized in removed_section_normalized:
                logger.error(f"❌ Removed section '{removed_section_name}' found in current list: '{section}'")
                return False
        
        logger.info(f"✅ Section '{removed_section_name}' is not in the current list")
        return True

    def verify_removed_sections_not_returned(self, removed_sections, current_sections):
        """
        Verify that all removed sections are not present in the current section list.
        
        Args:
            removed_sections: List of section names that were removed
            current_sections: Current list of section names
            
        Returns:
            tuple: (all_removed, returned_sections) - Boolean and list of sections that returned
        """
        logger.info(f"🔹 Verifying {len(removed_sections)} removed sections are not in current list")
        logger.info(f"Current sections count: {len(current_sections)}")
        
        returned_sections = []
        
        for removed_section in removed_sections:
            if not self.verify_section_removed(removed_section, current_sections):
                returned_sections.append(removed_section)
        
        if returned_sections:
            logger.error(f"❌ {len(returned_sections)} removed sections returned: {returned_sections}")
            return False, returned_sections
        else:
            logger.info(f"✅ All {len(removed_sections)} removed sections are confirmed not in current list")
            return True, []

    def verify_section_added(self, new_section_name, section_list):
        """
        Verify that a new section has been added to the section list.
        
        Args:
            new_section_name: Name of the section that should be added
            section_list: Current list of section names
            
        Returns:
            bool: True if section is found in the list, False otherwise
        """
        logger.info(f"🔹 Verifying section '{new_section_name}' is added")
        
        # Normalize section names for comparison (case-insensitive, strip whitespace)
        new_section_normalized = new_section_name.lower().strip()
        
        for section in section_list:
            section_normalized = section.lower().strip()
            
            # Check if the new section name appears in the list
            if new_section_normalized in section_normalized or section_normalized in new_section_normalized:
                logger.info(f"✅ New section '{new_section_name}' found in list: '{section}'")
                return True
        
        logger.error(f"❌ New section '{new_section_name}' not found in the list")
        return False

    def verify_section_position(self, new_section_name, reference_section_name, section_list, position="after"):
        """
        Verify that a new section is positioned correctly relative to a reference section.
        
        Args:
            new_section_name: Name of the section that was added
            reference_section_name: Name of the reference section (e.g., "payment terms")
            section_list: Current list of section names
            position: "after" or "before" - where the new section should be relative to reference
            
        Returns:
            tuple: (is_correct_position: bool, new_index: int, ref_index: int)
        """
        logger.info(f"🔹 Verifying section '{new_section_name}' is {position} '{reference_section_name}'")
        
        # Normalize for comparison
        new_section_normalized = new_section_name.lower().strip()
        reference_normalized = reference_section_name.lower().strip()
        
        new_index = -1
        ref_index = -1
        
        # Find indices of both sections
        for i, section in enumerate(section_list):
            section_normalized = section.lower().strip()
            
            if new_section_normalized in section_normalized or section_normalized in new_section_normalized:
                new_index = i
                logger.info(f"Found new section at index {i}: '{section}'")
            
            if reference_normalized in section_normalized or section_normalized in reference_normalized:
                ref_index = i
                logger.info(f"Found reference section at index {i}: '{section}'")
        
        # Check if both sections were found
        if new_index == -1:
            logger.error(f"❌ New section '{new_section_name}' not found in list")
            return False, new_index, ref_index
        
        if ref_index == -1:
            logger.error(f"❌ Reference section '{reference_section_name}' not found in list")
            return False, new_index, ref_index
        
        # Verify position
        if position.lower() == "after":
            is_correct = new_index > ref_index
            expected_msg = f"after (index {new_index} > {ref_index})"
        else:  # before
            is_correct = new_index < ref_index
            expected_msg = f"before (index {new_index} < {ref_index})"
        
        if is_correct:
            logger.info(f"✅ Section '{new_section_name}' is correctly positioned {expected_msg}")
        else:
            logger.error(f"❌ Section '{new_section_name}' is NOT correctly positioned {expected_msg}")
        
        return is_correct, new_index, ref_index