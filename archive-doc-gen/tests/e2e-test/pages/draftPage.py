import time
import os
from base.base import BasePage
from pytest_check import check
from playwright.sync_api import expect
import logging
logger = logging.getLogger(__name__)


class DraftPage(BasePage):
    Draft_Sections = "//textarea"
    Draft_headings = "//span[@class='fui-Text ___nl2uoq0 fk6fouc f4ybsrx f1i3iumi f16wzh4i fpgzoln f1w7gpdv f6juhto f1gl81tg f2jf649 fepr9ql febqm8h']"
    invalid_response = "The requested information is not available in the retrieved data. Please try another query or topic."
    invalid_response1 = "There was an issue fetching your data. Please try again."
    SECTION_CONTAINER = "div[role='region']"
    SECTION_GENERATE_BUTTON = "button.fui-Button:has-text('Generate')"

    def __init__(self, page):
        super().__init__(page)

    def validate_draft_sections_loaded(self):
        max_wait_time = 180  # seconds
        poll_interval = 2

        self.page.wait_for_timeout(25000)

        # All draft section containers
        section_blocks = self.page.locator("//div[@class='ms-Stack ___mit7380 f4zyqsv f6m9rw3 fwbpcpn folxr9a f1s274it css-103']")
        total_sections = section_blocks.count()

        logger.info(f"🔍 Total sections found: {total_sections}")

        for index in range(total_sections):
            section = section_blocks.nth(index)

            try:
                section.scroll_into_view_if_needed()
                self.page.wait_for_timeout(500)

                title_element = section.locator("//span[@class='fui-Text ___nl2uoq0 fk6fouc f4ybsrx f1i3iumi f16wzh4i fpgzoln f1w7gpdv f6juhto f1gl81tg f2jf649 fepr9ql febqm8h']")
                title_text = title_element.inner_text(timeout=5000).strip()
            except Exception as e:
                logger.error(f"❌ Could not read title for section #{index + 1}: {e}")
                continue

            logger.info(f"➡️ Validating section [{index + 1}/{total_sections}]: '{title_text}'")

            content_locator = section.locator("//textarea")
            generate_btn = section.locator("//span[@class='fui-Button__icon rywnvv2 ___963sj20 f1nizpg2']")
            spinner_locator = section.locator("//div[@id='section-card-spinner']")

            content_loaded = False

            # 🚨 If spinner is visible inside this section, click generate immediately
            try:
                if spinner_locator.is_visible(timeout=1000):
                    logger.warning(f"⏳ Spinner found in section '{title_text}'. Clicking Generate immediately.")
                    generate_btn.click()
                    self.page.wait_for_timeout(3000)
                    confirm_btn = self.page.locator("//button[@class='fui-Button r1alrhcs ___zqkcn80 fd1o0ie fjxutwb fwiml72 fj8njcf fzcpov4 f1d2rq10 f1mk8lai ff3glw6']")
                    if confirm_btn.is_visible(timeout=3000):
                        confirm_btn.click()
                        logger.info(f"🟢 Clicked Confirm button for section '{title_text}'")
                    else:
                        logger.warning(f"⚠️ Confirm button not visible for section '{title_text}'")
            except Exception as e:
                logger.error(f"❌ Error while clicking Confirm button for section '{title_text}': {e}")

            # ⏳ Retry short wait (15s) for content to load
            short_wait = 15
            short_start = time.time()
            while time.time() - short_start < short_wait:
                try:
                    content = content_locator.text_content(timeout=2000).strip()
                    if content:
                        logger.info(f"✅ Section '{title_text}' loaded after Generate + Confirm.")
                        content_loaded = True
                        break
                except Exception as e:
                    logger.info(f"⏳ Waiting for section '{title_text}' to load... {e}")
                time.sleep(1)

            if not content_loaded:
                logger.error(f"❌ Section '{title_text}' still empty after Generate + Confirm wait ({short_wait}s). Skipping.")

            # Step 1: Wait for content to load normally
            start = time.time()
            while time.time() - start < max_wait_time:
                try:
                    content = content_locator.text_content(timeout=2000).strip()
                    if content:
                        logger.info(f"✅ Section '{title_text}' loaded successfully.")
                        content_loaded = True
                        break
                except Exception as e:
                    logger.info(f"⏳ Waiting for section '{title_text}' to load... {e}")
                time.sleep(poll_interval)

            # Step 2: If still not loaded, click Generate and retry
            if not content_loaded:
                logger.warning(f"⚠️ Section '{title_text}' is empty. Attempting 'Generate'...")

                try:
                    generate_btn.click()
                    logger.info(f"🔄 Clicked 'Generate' for section '{title_text}'")
                except Exception as e:
                    logger.error(f"❌ Failed to click 'Generate' for section '{title_text}': {e}")
                    continue

                # Retry wait
                start = time.time()
                while time.time() - start < max_wait_time:
                    try:
                        content = content_locator.text_content(timeout=2000).strip()
                        if content:
                            logger.info(f"✅ Section '{title_text}' loaded after clicking Generate.")
                            content_loaded = True
                            break
                    except Exception as e:
                        logger.info(f"⏳ Waiting for section '{title_text}' to load after Generate... {e}")
                    time.sleep(poll_interval)

                if not content_loaded:
                    logger.error(f"❌ Section '{title_text}' still empty after retrying.")
                    # Note: Screenshots are only captured on test failures, not during normal page operations
                    continue

            try:
                content = content_locator.text_content(timeout=2000).strip()
                with check:
                    if content == self.invalid_response or content == self.invalid_response1:
                        logger.warning(f"❌ Invalid response found in '{title_text}'. Retrying Generate + Confirm...")

                        try:
                            generate_btn.click()
                            self.page.wait_for_timeout(3000)

                            confirm_btn = self.page.locator("//button[@class='fui-Button r1alrhcs ___zqkcn80 fd1o0ie fjxutwb fwiml72 fj8njcf fzcpov4 f1d2rq10 f1mk8lai ff3glw6']")
                            if confirm_btn.is_visible(timeout=3000):
                                confirm_btn.click()
                                logger.info(f"🟢 Retried Confirm for section '{title_text}'")
                            else:
                                logger.warning(f"⚠️ Confirm button not visible during retry for '{title_text}'")
                        except Exception as e:
                            logger.error(f"❌ Retry Generate/Confirm failed: {e}")

                        retry_start = time.time()
                        while time.time() - retry_start < short_wait:
                            try:
                                content = content_locator.text_content(timeout=2000).strip()
                                if content and content not in [self.invalid_response, self.invalid_response1]:
                                    logger.info(f"✅ Section '{title_text}' fixed after retry.")
                                    break
                            except Exception as e:
                                logger.info(f"⏳ Retrying section '{title_text}'... {e}")
                            time.sleep(1)

                        with check:
                            assert content != self.invalid_response, f"❌ '{title_text}' still has invalid response after retry"
                            assert content != self.invalid_response1, f"❌ '{title_text}' still has invalid response after retry"

                    else:
                        logger.info(f"🎯 Section '{title_text}' has valid content.")
            except Exception as e:
                logger.error(f"❌ Could not validate content for '{title_text}': {e}")
                logger.info(f"✔️ Completed section: '{title_text}'\n")

    def verify_all_section_generate_buttons(self, expected_count=11):
        """
        Verifies that each Draft section contains a visible 'Generate' button.
        Ensures no section is missing its Generate button.
        """
        buttons = self.page.locator('button:has-text("Generate")')
        found_count = buttons.count()

        # Logging (optional)
        logger.info(f"Found {found_count} Generate buttons, expected {expected_count}")

        # Assertion
        expect(buttons).to_have_count(expected_count)

        return found_count

    def click_section_generate_button(self, section_index):
        """
        Click the Generate button for a specific section on the Draft page.
        """

        logger.info(f"🔹 Clicking Generate button for section {section_index + 1}")

        # Corrected section locator (your old one was too rigid)
        section_blocks = self.page.locator(
            "//div[contains(@class,'ms-Stack') and contains(@class,'f1s274it')]"
        )

        section = section_blocks.nth(section_index)

        # Get section title (your previous locator was global → replaced with relative)
        try:
            title_element = section.locator(".fui-Text").first
            title = title_element.inner_text(timeout=3000).strip()
            logger.info(f"Section title: '{title}'")
        except Exception:
            title = f"Section {section_index + 1}"
            logger.warning(f"⚠️ Could not read section title, using default: {title}")

        # Scroll into view before clicking
        section.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)

        # Find Generate button inside section
        generate_button = section.locator("button:has-text('Generate')").first
        expect(generate_button).to_be_visible(timeout=5000)

        generate_button.click()
        logger.info(f"✅ Clicked Generate button for section: {title}")

        return title

    def verify_regenerate_popup_displayed(self):
        """
        Verify that the Regenerate popup is displayed with Generate button.
        """
        logger.info("🔹 Verifying Regenerate popup is displayed")

        # Wait for the popup to appear
        self.page.wait_for_timeout(1000)

        # Correct locator for the Popover
        popup = self.page.locator("div.fui-PopoverSurface").first

        try:
            expect(popup).to_be_visible(timeout=5000)
            logger.info("✅ Regenerate popup is displayed")
        except Exception as e:
            logger.error(f"❌ Regenerate popup not found: {e}")
            raise

        # Locate the Generate button inside the popup
        generate_button = popup.locator("button[data-testid='generate-btn-in-popover']")
        expect(generate_button).to_be_visible(timeout=3000)
        logger.info("✅ Generate button found in Regenerate popup")

        return popup

    def update_prompt_and_regenerate(self, additional_instruction):
        """
        Read the existing section-specific prompt from the popup, append additional instruction, and regenerate.
        
        Args:
            additional_instruction: Additional instruction to append to the existing prompt (e.g., "add max 150 words")
        """
        logger.info(f"🔹 Reading existing prompt from popup and appending: '{additional_instruction}'")
        
        # Find the popup using the correct locator
        popup = self.page.locator("div.fui-PopoverSurface").first
        
        # Find the textarea in the popup
        prompt_input = popup.locator("textarea").first
        
        try:
            # Read the existing section-specific prompt from the popup
            existing_prompt = prompt_input.input_value(timeout=3000)
            logger.info(f"📝 Existing prompt in popup: '{existing_prompt}'")
            
            # Append the additional instruction to the existing prompt
            updated_prompt = f"{existing_prompt} {additional_instruction}"
            
            # Clear and enter the updated prompt
            prompt_input.clear()
            prompt_input.fill(updated_prompt)
            logger.info(f"✅ Updated prompt: '{updated_prompt}'")
        except Exception as e:
            logger.error(f"❌ Failed to update prompt: {e}")
            raise
        
        # Click Generate button in popup using the correct data-testid
        generate_button = popup.locator("button[data-testid='generate-btn-in-popover']")
        
        try:
            expect(generate_button).to_be_visible(timeout=3000)
            generate_button.click()
            logger.info("✅ Clicked Generate button in popup")
        except Exception as e:
            logger.error(f"❌ Failed to click Generate button: {e}")
            raise
        
        # Wait for popup to close and regeneration to start
        self.page.wait_for_timeout(2000)

    def verify_section_content_updated(self, section_index, original_content):
        """
        Verify that the section content has been updated after regeneration.
        
        Args:
            section_index: Index of the section (0-based)
            original_content: Original content before regeneration
        
        Returns:
            new_content: The updated content
        """
        logger.info(f"🔹 Verifying section {section_index + 1} content is updated")
        
        # Wait for regeneration to complete
        max_wait = 60  # seconds
        start_time = time.time()
        
        # Use the same section locator as other methods for consistency
        section_blocks = self.page.locator(
            "//div[contains(@class,'ms-Stack') and contains(@class,'f1s274it')]"
        )
        section = section_blocks.nth(section_index)
        
        # Wait for spinner to disappear if present
        spinner_locator = section.locator("//div[@id='section-card-spinner']")
        try:
            if spinner_locator.is_visible(timeout=2000):
                logger.info("⏳ Waiting for regeneration to complete...")
                spinner_locator.wait_for(state="hidden", timeout=max_wait * 1000)
        except Exception:
            pass  # Spinner might not appear for fast responses
        
        # Get updated content
        content_locator = section.locator("//textarea")
        
        while time.time() - start_time < max_wait:
            try:
                new_content = content_locator.text_content(timeout=3000).strip()
                
                if new_content and new_content != original_content:
                    logger.info(f"✅ Section content updated successfully")
                    logger.info(f"Original length: {len(original_content)} chars")
                    logger.info(f"New length: {len(new_content)} chars")
                    return new_content
                    
            except Exception as e:
                logger.warning(f"⏳ Waiting for content update: {e}")
            
            time.sleep(2)
        
        # If we reach here, content didn't update
        logger.warning("⚠️ Section content may not have updated within timeout")
        new_content = content_locator.text_content(timeout=3000).strip()
        return new_content

    def regenerate_all_sections(self, additional_instruction="add max 150 words"):
        """
        Iterate through all sections, click Generate button, append instruction to existing popup prompt, and verify regeneration.
        
        Args:
            additional_instruction: Instruction to append to the existing section-specific prompt in the popup
        """
        logger.info("🔹 Starting regeneration of all sections")
        logger.info(f"Additional instruction to append: '{additional_instruction}'")
        
        # Get total section count
        section_blocks = self.page.locator(
        "//div[contains(@class,'ms-Stack') and contains(@class,'f1s274it')]"
        )
        total_sections = section_blocks.count()
        
        logger.info(f"Total sections to regenerate: {total_sections}")
        
        for i in range(total_sections):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing section {i + 1}/{total_sections}")
            logger.info(f"{'='*60}")
            
            # Get original content
            section = section_blocks.nth(i)
            content_locator = section.locator("//textarea")
            original_content = content_locator.text_content(timeout=3000).strip()
            
            # Step 1: Click Generate button for this section
            self.click_section_generate_button(i)
            
            # Step 2: Verify regenerate popup is displayed
            self.verify_regenerate_popup_displayed()
            
            # Step 3: Read existing prompt from popup and append additional instruction
            self.update_prompt_and_regenerate(additional_instruction)
            
            # Step 4: Verify content is updated
            new_content = self.verify_section_content_updated(i, original_content)
            
            with check:
                assert new_content != original_content, f"Section {i + 1} content did not update"
            
            logger.info(f"✅ Section {i + 1} regenerated successfully\n")
            
            # Small delay between sections
            self.page.wait_for_timeout(1000)
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ All sections regenerated successfully")
        logger.info(f"{'='*60}")

    def verify_character_count_labels(self, max_chars=2000):
        """
        Verify that each section shows a character count label and count is less than max_chars.
        
        Args:
            max_chars: Maximum allowed characters (default: 2000)
        """
        logger.info("🔹 Verifying character count labels in all sections")
        
        # Get all section containers
        section_blocks = self.page.locator(
            "//div[contains(@class,'ms-Stack') and contains(@class,'f1s274it')]"
        )
        total_sections = section_blocks.count()
        
        logger.info(f"Total sections to verify: {total_sections}")
        
        # Locator for character count label
        char_count_locator = "span.fui-Text.___1v8ne64.fk6fouc.f1ugzwwg.f1i3iumi.figsok6.fpgzoln.f1w7gpdv.f6juhto.f1gl81tg.f2jf649.fq02s40.f4aeiui.f1locze1"
        
        for i in range(total_sections):
            section = section_blocks.nth(i)
            
            # Get section title for logging
            try:
                title_element = section.locator(".fui-Text").first
                title = title_element.inner_text(timeout=3000).strip()
            except Exception:
                title = f"Section {i + 1}"
            
            logger.info(f"🔹 Verifying character count for: {title}")
            
            # Scroll section into view
            section.scroll_into_view_if_needed()
            self.page.wait_for_timeout(300)
            
            # Find character count label within this section
            char_label = section.locator(char_count_locator).first
            
            try:
                expect(char_label).to_be_visible(timeout=5000)
                label_text = char_label.inner_text(timeout=3000).strip()
                logger.info(f"📊 Character count label: '{label_text}'")
                
                # Extract the number from label text (e.g., "1551 characters remaining")
                import re
                match = re.search(r'(\d+)\s+characters remaining', label_text)
                
                if match:
                    remaining_chars = int(match.group(1))
                    logger.info(f"📈 Characters remaining: {remaining_chars}")
                    
                    # Verify remaining characters is less than or equal to max_chars
                    with check:
                        assert remaining_chars <= max_chars, f"{title}: Remaining chars {remaining_chars} should be <= {max_chars}"
                    
                    # Calculate used characters
                    used_chars = max_chars - remaining_chars
                    logger.info(f"✅ {title}: Used {used_chars} chars, Remaining {remaining_chars} chars")
                else:
                    logger.error(f"❌ Could not parse character count from label: '{label_text}'")
                    
            except Exception as e:
                logger.error(f"❌ Character count label not found for {title}: {e}")
                raise
        
        logger.info("✅ All sections have valid character count labels")

    def test_character_limit_restriction(self, section_index=0):
        """
        Test that a section restricts input to max 2000 characters.
        
        Args:
            section_index: Index of the section to test (default: 0 - first section)
        """
        logger.info(f"🔹 Testing character limit restriction for section {section_index + 1}")
        
        # Get section
        section_blocks = self.page.locator(
            "//div[contains(@class,'ms-Stack') and contains(@class,'f1s274it')]"
        )
        section = section_blocks.nth(section_index)
        
        # Get section title
        try:
            title_element = section.locator(".fui-Text").first
            title = title_element.inner_text(timeout=3000).strip()
            logger.info(f"Testing section: '{title}'")
        except Exception:
            logger.info(f"Testing section: 'Section {section_index + 1}'")
        
        # Scroll section into view
        section.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        
        # Find the textarea
        textarea = section.locator("//textarea").first
        
        # Create a string with more than 2000 characters (e.g., 2500 chars)
        test_text = "A" * 2500
        logger.info(f"Attempting to enter {len(test_text)} characters")
        
        # Clear existing text
        textarea.clear()
        
        # Try to fill with 2500 characters
        textarea.fill(test_text)
        self.page.wait_for_timeout(1000)
        
        # Get the actual text in textarea
        actual_text = textarea.input_value()
        actual_length = len(actual_text)
        
        logger.info(f"📊 Actual characters entered: {actual_length}")
        
        # Verify it's restricted to 2000 characters
        with check:
            assert actual_length == 2000, f"Text should be restricted to 2000 chars, but got {actual_length}"
        
        logger.info(f"✅ Character limit enforced: Only 2000 characters allowed")
        
        # Verify the character count label shows "0 characters remaining"
        char_count_locator = "span.fui-Text.___1v8ne64.fk6fouc.f1ugzwwg.f1i3iumi.figsok6.fpgzoln.f1w7gpdv.f6juhto.f1gl81tg.f2jf649.fq02s40.f4aeiui.f1locze1"
        char_label = section.locator(char_count_locator).first
        
        try:
            label_text = char_label.inner_text(timeout=3000).strip()
            logger.info(f"📊 Character count label after max input: '{label_text}'")
            
            with check:
                assert "0 characters remaining" in label_text, f"Expected '0 characters remaining', got '{label_text}'"
            
            logger.info("✅ Character count label correctly shows '0 characters remaining'")
        except Exception as e:
            logger.error(f"❌ Failed to verify character count label: {e}")
            raise
        
        return actual_length

    def enter_document_title(self, title):
        """
        Enter a title in the document title text box on the Draft page
        
        Args:
            title: The title to enter in the document title field
        """
        try:
            logger.info(f"🔹 Entering document title: '{title}'")
            
            # Primary locator: by placeholder text
            title_input = self.page.locator("input[placeholder='Enter title here']")
            
            # Check if input field is visible
            if not title_input.is_visible(timeout=5000):
                # Try alternative locator: by class name
                logger.warning("⚠️ Title input not found by placeholder, trying by class")
                title_input = self.page.locator("input.ms-TextField-field")
            
            # Wait for the input to be editable
            title_input.wait_for(state="visible", timeout=5000)
            
            # Scroll to the input field if needed
            title_input.scroll_into_view_if_needed()
            self.page.wait_for_timeout(500)
            
            # Clear any existing title
            title_input.clear()
            self.page.wait_for_timeout(300)
            
            # Enter new title
            title_input.fill(title)
            self.page.wait_for_timeout(500)
            
            # Verify the title was entered correctly
            entered_value = title_input.input_value()
            if entered_value == title:
                logger.info(f"✅ Successfully entered document title: '{title}'")
            else:
                logger.warning(f"⚠️ Title mismatch - Expected: '{title}', Got: '{entered_value}'")
            
        except Exception as e:
            logger.error(f"❌ Failed to enter document title: {e}")
            # Note: Screenshots are only captured on test failures, not during normal page operations
            raise

    def click_export_document_button(self):
        """
        Click the 'Export Document' button at the bottom of the Draft page.
        Waits for the button to be enabled before clicking to ensure document is ready.
        """
        try:
            # First, ensure no section generation is in progress
            # Check for any visible spinners indicating sections are still being generated
            spinner_locator = self.page.locator("//div[@id='section-card-spinner']")
            if spinner_locator.first.is_visible(timeout=2000):
                logger.warning("⚠️ Sections still generating, waiting for completion...")
                # Wait for all spinners to disappear (max 5 minutes for complex documents)
                try:
                    spinner_locator.first.wait_for(state="hidden", timeout=300000)
                    logger.info("✅ All sections finished generating")
                except Exception as e:
                    logger.warning(f"⚠️ Timeout waiting for spinners: {e}")
            
            # Locate the Export Document button using the class and text
            # Button structure: <button class="ms-Button ms-Button--commandBar _exportDocumentIcon_1x53n_11 root-239" aria-label="export document">
            export_button = self.page.locator("button[aria-label='export document']")
            
            if not export_button.is_visible(timeout=5000):
                # Try alternative locator by text
                export_button = self.page.locator("button:has-text('Export Document')")
            
            # Wait for button to be visible and enabled (critical for ensuring document is ready)
            expect(export_button).to_be_visible(timeout=15000)
            expect(export_button).to_be_enabled(timeout=60000)  # Wait up to 60s for document to be ready
            
            # Scroll to button if needed
            export_button.scroll_into_view_if_needed()
            self.page.wait_for_timeout(1000)
            
            # Click the button
            export_button.click()
            
            logger.info("✅ Clicked 'Export Document' button")
            
            # Wait for the export process to initiate (allows download event to trigger)
            self.page.wait_for_timeout(3000)
            
        except Exception as e:
            logger.error(f"❌ Failed to click Export Document button: {e}")
            raise