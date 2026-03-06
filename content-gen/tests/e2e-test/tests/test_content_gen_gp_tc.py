"""Test module for Content Generation golden path test cases."""
import logging
import time

from pages.HomePage import HomePage
from config.constants import URL
from tests.test_utils import log_test_summary, log_test_failure

logger = logging.getLogger(__name__)


def test_validate_gp(login_logout, request):
    """
    Test case to validate content generation golden path flow for two quick links.
    Includes response accuracy validation and error/exception detection at every step.
    Steps:
    1. Validate home page elements are visible
    2. Quick Link 1: Send prompt → Validate PlanningAgent response → Confirm brief
       → Validate Brief accuracy → Select color & Generate content
       → Validate Products Selected, marketing copy accuracy, and error checks
    3. Start new conversation
    4. Quick Link 2: Same validations as Quick Link 1 with Obsidian Pearl
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Golden Path - Content Generation - test golden path works properly"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # --- Quick Link 1 (USER_MESSAGE) ---
        # Step 2: Send Prompt from Quick Link 1
        step2_start = time.time()
        home.send_prompt_from_quick_link(home.USER_MESSAGE)
        step2_end = time.time()
        home.assert_no_error_in_response("Quick Link 1 - Send Prompt")
        home.validate_planning_agent_response_quality()

        # Step 3: Confirm Brief
        step3_start = time.time()
        home.confirm_brief()
        step3_end = time.time()
        home.assert_no_error_in_response("Quick Link 1 - Confirm Brief")
        home.validate_brief_confirmed_accuracy(
            expected_keywords=["paint", "homeowner", "marketing copy", "image"]
        )

        # Step 4: Select Olive Stone Color and Generate Content
        step4_start = time.time()
        home.select_color_and_generate_content(
            color_locator=home.OLIVE_STONE_TEXT,
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OLIVE,
            expected_color="olive"
        )
        step4_end = time.time()
        home.assert_no_error_in_response("Quick Link 1 - Generate Content")
        home.validate_products_selected_section("Olive Stone")
        home.validate_generated_copy_accuracy(
            product_name="Olive Stone",
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OLIVE,
            min_length=30
        )

        # Step 5: Start New Conversation
        step5_start = time.time()
        home.click_new_conversation()
        step5_end = time.time()

        # --- Quick Link 2 (USER_MESSAGE_2) ---
        # Step 6: Send Prompt from Quick Link 2
        step6_start = time.time()
        home.send_prompt_from_quick_link(home.USER_MESSAGE_2)
        step6_end = time.time()
        home.assert_no_error_in_response("Quick Link 2 - Send Prompt")
        home.validate_planning_agent_response_quality(
            extra_keywords=["social media", "back to school", "school age children",
                           "playful", "humorous", "content creation"]
        )

        # Step 7: Confirm Brief
        step7_start = time.time()
        home.confirm_brief()
        step7_end = time.time()
        home.assert_no_error_in_response("Quick Link 2 - Confirm Brief")
        home.validate_brief_confirmed_accuracy(
            expected_keywords=["social media", "back to school", "ad copy", "image"],
            extra_fields=["tone & style", "visual guidelines"]
        )

        # Step 8: Select Obsidian Pearl Color and Generate Content
        step8_start = time.time()
        home.select_color_and_generate_content(
            color_locator=home.OBSIDIAN_TEXT,
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OBSIDIAN,
            expected_color="obsidian"
        )
        step8_end = time.time()
        home.assert_no_error_in_response("Quick Link 2 - Generate Content")
        home.validate_products_selected_section(
            "Obsidian Pearl",
            expected_attributes=["black", "matte", "dramatic", "luxe"],
            expected_price_pattern="$59.95 USD"
        )
        home.validate_generated_copy_accuracy(
            product_name="Obsidian Pearl",
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OBSIDIAN,
            min_length=30,
            expected_copy_keywords=["discover", "serene", "elegance", "rich black",
                                    "drama", "backdrop", "refresh", "space"]
        )

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Quick Link 1 - Send Prompt)", step2_end - step2_start),
            ("Step 3 (Quick Link 1 - Confirm Brief)", step3_end - step3_start),
            ("Step 4 (Quick Link 1 - Generate Content)", step4_end - step4_start),
            ("Step 5 (New Conversation)", step5_end - step5_start),
            ("Step 6 (Quick Link 2 - Send Prompt)", step6_end - step6_start),
            ("Step 7 (Quick Link 2 - Confirm Brief)", step7_end - step7_start),
            ("Step 8 (Quick Link 2 - Generate Content)", step8_end - step8_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Content Generation Golden Path Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_chat_history_panel(login_logout, request):
    """
    Test case to validate chat history panel is displayed.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link
    3. Confirm brief
    4. Select color and generate content
    5. Validate chat history panel is displayed
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Chat History Panel displayed"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt from Quick Link
        step2_start = time.time()
        home.send_prompt_from_quick_link(home.USER_MESSAGE)
        step2_end = time.time()

        # Step 3: Confirm Brief
        step3_start = time.time()
        home.confirm_brief()
        step3_end = time.time()

        # Step 4: Select Color and Generate Content
        step4_start = time.time()
        home.select_color_and_generate_content(
            color_locator=home.OLIVE_STONE_TEXT,
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OLIVE,
            expected_color="olive"
        )
        step4_end = time.time()

        # Step 5: Validate Chat History Panel is displayed
        step5_start = time.time()
        home.validate_chat_history()
        step5_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Confirm Brief)", step3_end - step3_start),
            ("Step 4 (Generate Content)", step4_end - step4_start),
            ("Step 5 (Chat History Panel Validation)", step5_end - step5_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Chat History Panel Displayed Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_rename_chat_history(login_logout, request):
    """
    Test case to validate renaming a chat history item.
    Steps:
    1. Validate home page elements are visible
    2. Rename chat history item
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Chat History - Rename the chat name"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Rename Chat History with dynamic name
        step2_start = time.time()
        dynamic_name = f"updated_chat_{int(time.time())}"
        home.rename_chat_history(dynamic_name)
        step2_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Rename Chat History)", step2_end - step2_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Rename Chat History Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_delete_chat_history(login_logout, request):
    """
    Test case to validate deleting a chat history item.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link
    3. Confirm brief
    4. Select color and generate content
    5. Delete chat history item
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Chat History - Delete the chat"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt from Quick Link
        step2_start = time.time()
        home.send_prompt_from_quick_link(home.USER_MESSAGE)
        step2_end = time.time()

        # Step 3: Confirm Brief
        step3_start = time.time()
        home.confirm_brief()
        step3_end = time.time()

        # Step 4: Select Color and Generate Content
        step4_start = time.time()
        home.select_color_and_generate_content(
            color_locator=home.OLIVE_STONE_TEXT,
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OLIVE,
            expected_color="olive"
        )
        step4_end = time.time()

        # Step 5: Delete Chat History
        step5_start = time.time()
        home.delete_chat_history()
        step5_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Confirm Brief)", step3_end - step3_start),
            ("Step 4 (Generate Content)", step4_end - step4_start),
            ("Step 5 (Delete Chat History)", step5_end - step5_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Delete Chat History Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_rename_empty_validation(login_logout, request):
    """
    Test case to validate that the rename button is disabled and a validation
    message is shown when the conversation name input is empty.
    Steps:
    1. Validate home page elements are visible
    2. Validate rename button disabled and validation message displayed, then cancel
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Chat History - User should get a validation or the rename button needs to be disabled"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Validate rename button disabled & validation message, then cancel
        step2_start = time.time()
        home.validate_rename_empty_validation()
        step2_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Rename Empty Validation)", step2_end - step2_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Rename Empty Validation Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_stop_generation(login_logout, request):
    """
    Test case to validate stop generation functionality.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link
    3. Confirm brief
    4. Stop generation while content is being generated and validate stopped text
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Response - Stop generation"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt
        step2_start = time.time()
        home.send_prompt(home.USER_MESSAGE)
        step2_end = time.time()

        # Step 3: Stop Generation
        step3_start = time.time()
        home.stop_generation()
        step3_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Stop Generation)", step3_end - step3_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Stop Generation Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_start_over(login_logout, request):
    """
    Test case to validate start over functionality after stopping generation.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link
    3. Confirm brief
    4. Stop generation while content is being generated
    5. Click Start over and validate start over text is displayed
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Response - Start over"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt
        step2_start = time.time()
        home.send_prompt(home.USER_MESSAGE)
        step2_end = time.time()


        # Step 3: Start Over
        step4_start = time.time()
        home.start_over()
        step4_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Start Over)", step4_end - step4_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Start Over Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_start_new_chat(login_logout, request):
    """
    Test case to validate start new chat functionality after content generation.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link
    3. Confirm brief
    4. Select color and generate content
    5. Click on new chat link
    6. Validate home page
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Response - Start new chat"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt from Quick Link
        step2_start = time.time()
        home.send_prompt_from_quick_link(home.USER_MESSAGE)
        step2_end = time.time()

        # Step 3: Confirm Brief
        step3_start = time.time()
        home.confirm_brief()
        step3_end = time.time()

        # Step 4: Select Color and Generate Content
        step4_start = time.time()
        home.select_color_and_generate_content(
            color_locator=home.OLIVE_STONE_TEXT,
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OLIVE,
            expected_color="olive"
        )
        step4_end = time.time()

        # Step 5: Click on New Chat link and validate home page
        step5_start = time.time()
        home.click_new_conversation()
        step5_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Confirm Brief)", step3_end - step3_start),
            ("Step 4 (Generate Content)", step4_end - step4_start),
            ("Step 5 (Start New Chat)", step5_end - step5_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Start New Chat Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_input_disabled_during_generation(login_logout, request):
    """
    Test case to validate that the input field and send button are disabled
    while the AI response is being generated.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link (lightweight)
    3. Validate input is disabled during response generation
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Response - Input disabled during response generation"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt
        step2_start = time.time()
        home.send_prompt(home.USER_MESSAGE)
        step2_end = time.time()

        # Step 3: Validate input is disabled during response generation
        step3_start = time.time()
        home.validate_input_disabled_during_generation()
        step3_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Input Disabled Validation)", step3_end - step3_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Input Disabled During Generation Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_download_image(login_logout, request):
    """
    Test case to validate download image functionality after content generation.
    Steps:
    1. Validate home page elements are visible
    2. Send prompt from quick link
    3. Confirm brief
    4. Select color and generate content
    5. Download the generated image and validate the file
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Response - Download image"
    start_time = time.time()

    try:
        # Step 1: Validate Home Page
        step1_start = time.time()
        home.validate_home_page()
        step1_end = time.time()

        # Step 2: Send Prompt from Quick Link
        step2_start = time.time()
        home.send_prompt_from_quick_link(home.USER_MESSAGE)
        step2_end = time.time()

        # Step 3: Confirm Brief
        step3_start = time.time()
        home.confirm_brief()
        step3_end = time.time()

        # Step 4: Select Color and Generate Content
        step4_start = time.time()
        home.select_color_and_generate_content(
            color_locator=home.OLIVE_STONE_TEXT,
            generated_content_locator=home.GENERATED_CONTENT_TEXT_OLIVE,
            expected_color="olive"
        )
        step4_end = time.time()

        # Step 5: Download the generated image
        step5_start = time.time()
        home.download_image()
        step5_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Home Page Validation)", step1_end - step1_start),
            ("Step 2 (Send Prompt)", step2_end - step2_start),
            ("Step 3 (Confirm Brief)", step3_end - step3_start),
            ("Step 4 (Generate Content)", step4_end - step4_start),
            ("Step 5 (Download Image)", step5_end - step5_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Download Image Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_show_hide_chat_history(login_logout, request):
    """
    Test case to validate show/hide chat history toggle functionality.
    Steps:
    1. Validate show/hide chat history toggle
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Validate show/hide chat history"
    start_time = time.time()

    try:
        # Step 1: Validate Show/Hide Chat History
        step1_start = time.time()
        home.show_hide_chat_history()
        step1_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Show/Hide Chat History)", step1_end - step1_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Show/Hide Chat History Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise


def test_validate_clear_all_chat_history(login_logout, request):
    """
    Test case to validate clear all chat history functionality.
    Steps:
    1. Clear all chat history and validate 'No conversations yet' text
    """
    page = login_logout
    page.goto(URL)
    page.wait_for_timeout(3000)
    home = HomePage(page)
    request.node._nodeid = "Content Generation - Validate clear all chat history"
    start_time = time.time()

    try:
        # Step 1: Clear all chat history
        step1_start = time.time()
        home.clear_all_chat_history()
        step1_end = time.time()

        # Log test summary
        step_times = [
            ("Step 1 (Clear All Chat History)", step1_end - step1_start)
        ]
        total_duration = log_test_summary(start_time, step_times, "Clear All Chat History Test")

        request.node._report_sections.append(
            ("call", "log", f"Total execution time: {total_duration:.2f}s")
        )
    except Exception as e:
        log_test_failure(start_time, e)
        raise

