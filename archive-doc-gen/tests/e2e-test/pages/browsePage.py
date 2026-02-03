from base.base import BasePage
from playwright.sync_api import expect
import logging
logger = logging.getLogger(__name__)


class BrowsePage(BasePage):
    TYPE_QUESTION = "//textarea[@placeholder='Type a new question...']"
    SEND_BUTTON = "//div[@aria-label='Ask question button']"
    GENERATE_BUTTON = "//div[contains(@class, 'ms-Stack')]//span[normalize-space()='Generate']"
    DRAFT_TAB_BUTTON = "//span[normalize-space()='Draft']"
    DRAFT_TAB_CONTAINER = "//div[contains(@class, '_navigationButtonDisabled')]"
    RESPONSE_REFERENCE_EXPAND_ICON = "//span[@aria-label='Open references']"
    REFERENCE_LINKS_IN_RESPONSE = "//span[@class='_citationContainer_1qm4u_72']"
    REFERENCE_POPUP_PANEL = "//div[@role='dialog']"
    REFERENCE_POPUP_CONTENT = "//div[@role='dialog']//div[contains(@class, 'fui-DialogSurface')]"
    CLOSE_BUTTON = "//button[.='Close']"
    CLEAR_CHAT_BROOM_BUTTON = "button[aria-label='clear chat button']"

    def __init__(self, page):
        super().__init__(page)

    def validate_browse_page(self):
        """Validate that Browse page chat conversation elements are visible"""
        self.page.wait_for_timeout(3000)
        expect(self.page.locator(self.TYPE_QUESTION)).to_be_visible()
        expect(self.page.locator(self.SEND_BUTTON)).to_be_visible()

    def enter_a_question(self, text):
        # Type a question in the text area
        self.page.locator(self.TYPE_QUESTION).fill(text)
        self.page.wait_for_timeout(2000)

    def click_send_button(self):
        # Type a question in the text area
        self.page.locator(self.SEND_BUTTON).click()
        self.page.wait_for_timeout(10000)

    def click_generate_button(self):
        # Type a question in the text area
        self.page.locator(self.GENERATE_BUTTON).click()
        self.page.wait_for_timeout(5000)

    def click_reference_link_in_response(self):
        # Click on reference link response
        BasePage.scroll_into_view(
            self, self.page.locator(self.REFERENCE_LINKS_IN_RESPONSE)
        )
        self.page.wait_for_timeout(2000)
        reference_links = self.page.locator(self.REFERENCE_LINKS_IN_RESPONSE)
        reference_links.nth(reference_links.count() - 1).click()
        # self.page.locator(self.REFERENCE_LINKS_IN_RESPONSE).click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def click_expand_reference_in_response(self):
        # Click on expand in response reference area
        self.page.wait_for_timeout(5000)
        expand_icon = self.page.locator(self.RESPONSE_REFERENCE_EXPAND_ICON)
        expand_icon.nth(expand_icon.count() - 1).click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def close_citation(self):
        self.page.wait_for_timeout(3000)
        self.page.locator(self.CLOSE_BUTTON).click()
        self.page.wait_for_timeout(2000)

    def click_draft_tab_button(self):
        """Click on Draft tab button"""
        self.page.wait_for_timeout(2000)
        self.page.locator(self.DRAFT_TAB_BUTTON).click()
        self.page.wait_for_timeout(3000)

    def is_draft_tab_enabled(self):
        """Check if Draft tab is enabled (clickable)"""
        self.page.wait_for_timeout(2000)
        draft_button = self.page.locator(self.DRAFT_TAB_BUTTON)
        
        if draft_button.count() > 0:
            # Check if the container has the disabled class
            draft_container = self.page.locator(self.DRAFT_TAB_CONTAINER)
            has_disabled_class = draft_container.count() > 0
            
            # Check if cursor is not-allowed (disabled state)
            cursor_style = draft_container.get_attribute("style") if has_disabled_class else ""
            is_disabled = "cursor: not-allowed" in cursor_style or has_disabled_class
            
            return not is_disabled
        return False

    def is_draft_tab_disabled(self):
        """Check if Draft tab is disabled (not clickable)"""
        self.page.wait_for_timeout(2000)
        draft_button = self.page.locator(self.DRAFT_TAB_BUTTON)
        
        if draft_button.count() > 0:
            # Check if the container has the disabled class
            draft_container = self.page.locator(self.DRAFT_TAB_CONTAINER)
            has_disabled_class = draft_container.count() > 0
            
            # Check if cursor is not-allowed (disabled state)
            if has_disabled_class:
                cursor_style = draft_container.get_attribute("style") or ""
                is_disabled = "cursor: not-allowed" in cursor_style
                return is_disabled
            return False
        return True  # If not visible, consider it disabled

    def click_broom_icon(self):
        broom = self.page.locator(self.CLEAR_CHAT_BROOM_BUTTON)
        assert broom.is_visible(), "Broom (clear chat) icon is not visible"
        broom.click()
        logger.info("Clicked broom icon to clear the chat")

    def is_chat_cleared(self):
        """
        Verify that the chat has been cleared and a new session has started.
        Checks if the chat area is empty (no previous messages visible).
        
        :return: True if chat is cleared, False otherwise
        """
        self.page.wait_for_timeout(1000)
        
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
            logger.warning("Chat input field still contains text: '%s'", input_value)
            return False
        
        logger.info("Chat cleared successfully - no old messages, input field is empty")
        return True

    def get_citation_count(self):
        """
        Get the number of citations/references in the last response.
        
        Returns:
            int: Number of citation links found
        """
        logger.info("🔹 Counting citations in response")
        
        self.page.wait_for_timeout(2000)
        
        # Get citation links in the last response
        citation_links = self.page.locator(self.REFERENCE_LINKS_IN_RESPONSE)
        count = citation_links.count()
        
        logger.info(f"Found {count} citations in response")
        return count

    def get_citations_and_documents(self):
        """
        Get all citations and their corresponding document names from the last response.
        Expands the references section and extracts document information.
        
        Returns:
            tuple: (citation_count, document_list)
        """
        logger.info("🔹 Extracting citations and documents from response")
        
        self.page.wait_for_timeout(3000)
        
        # Count citations first
        citation_count = self.get_citation_count()
        
        if citation_count == 0:
            logger.warning("No citations found in response")
            return 0, []
        
        # Click to expand references
        try:
            expand_icon = self.page.locator(self.RESPONSE_REFERENCE_EXPAND_ICON)
            if expand_icon.count() > 0:
                expand_icon.nth(expand_icon.count() - 1).click()
                logger.info("Expanded references section")
                self.page.wait_for_timeout(2000)
            else:
                logger.warning("References expand icon not found")
                return citation_count, []
        except Exception as e:
            logger.error(f"Failed to expand references: {e}")
            return citation_count, []
        
        # Extract document names from expanded references
        documents = []
        
        try:
            # Look for reference items in the expanded section
            # This selector may need adjustment based on actual DOM structure
            reference_items = self.page.locator("//div[contains(@class, 'citationPanel')]//div[contains(@class, 'citationItem')]")
            
            if reference_items.count() == 0:
                # Try alternative selector
                reference_items = self.page.locator("//div[@role='complementary']//div[contains(@class, 'citation')]")
            
            ref_count = reference_items.count()
            logger.info(f"Found {ref_count} reference items in expanded section")
            
            for i in range(ref_count):
                try:
                    ref_text = reference_items.nth(i).inner_text()
                    documents.append(ref_text.strip())
                    logger.info(f"  Reference {i + 1}: {ref_text[:100]}...")
                except Exception as e:
                    logger.warning(f"Could not extract reference {i + 1}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to extract reference documents: {e}")
        
        logger.info(f"✅ Extracted {len(documents)} document references")
        return citation_count, documents

    def verify_response_has_citations(self, min_citations=1):
        """
        Verify that the response has at least the minimum number of citations.
        
        Args:
            min_citations: Minimum expected number of citations (default: 1)
            
        Returns:
            bool: True if citation count >= min_citations
        """
        logger.info(f"🔹 Verifying response has at least {min_citations} citation(s)")
        
        citation_count = self.get_citation_count()
        
        if citation_count >= min_citations:
            logger.info(f"✅ Response has {citation_count} citations (>= {min_citations})")
            return True
        else:
            logger.error(f"❌ Response has only {citation_count} citations (expected >= {min_citations})")
            return False

    def verify_response_generated_with_citations(self, timeout=60000):
        """
        Verify that a response is generated with citations/references.
        
        Args:
            timeout: Maximum wait time in milliseconds
            
        Returns:
            tuple: (response_text, citation_count)
        """
        logger.info("🔹 Verifying response generated with citations")
        
        # Wait for response container
        self.page.wait_for_timeout(5000)
        
        answer_container = self.page.locator("//div[contains(@class, 'answerContainer')]").last
        
        try:
            # Wait for answer to be visible
            expect(answer_container).to_be_visible(timeout=timeout)
            
            # Get response text
            response_text = answer_container.inner_text()
            logger.info(f"Response length: {len(response_text)} characters")
            
            # Verify response is not empty
            assert response_text.strip(), "Response text is empty"
            
            # Count citations
            citation_count = self.get_citation_count()
            logger.info(f"Response has {citation_count} citations")
            
            logger.info("✅ Response generated successfully with citations")
            return response_text, citation_count
            
        except Exception as e:
            logger.error(f"❌ Failed to verify response with citations: {e}")
            raise

