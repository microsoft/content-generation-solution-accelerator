import atexit
import io
import logging
import os
import pytest
from bs4 import BeautifulSoup
from config.constants import URL
from playwright.sync_api import sync_playwright
from datetime import datetime
from pytest_html import extras

# Create screenshots directory if it doesn't exist
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


@pytest.fixture(scope="session")
def login_logout():
    # perform login and browser close once in a session
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        context.set_default_timeout(120000)
        context.clear_cookies()
        page = context.new_page()
        # Navigate to the login URL
        page.goto(URL)
        # Wait for the login form to appear
        # page.wait_for_load_state('networkidle')
        # login to web url with username and password
        # login_page = LoginPage(page)
        # load_dotenv()
        # login_page.authenticate(os.getenv('user_name'),os.getenv('pass_word'))
        yield page
        # perform close the browser
        browser.close()


@pytest.hookimpl(tryfirst=True)
def pytest_html_report_title(report):
    report.title = "Test Automation DocGen"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Generate test report with logs, subtest details, and screenshots on failure"""
    outcome = yield
    report = outcome.get_result()

    # Capture screenshot on failure
    if report.when == "call" and report.failed:
        # Get the page fixture if it exists
        if "login_logout" in item.fixturenames:
            page = item.funcargs.get("login_logout")
            if page:
                try:
                    # Generate screenshot filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    test_name = item.name.replace(" ", "_").replace("/", "_")
                    screenshot_name = f"screenshot_{test_name}_{timestamp}.png"
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_name)
                    
                    # Take screenshot
                    page.screenshot(path=screenshot_path)
                    
                    # Add screenshot link to report
                    if not hasattr(report, 'extra'):
                        report.extra = []
                    
                    # Use relative path for screenshots to work in the Test-Report folder structure
                    relative_screenshot_path = f"../screenshots/{screenshot_name}"
                    
                    # pytest-html expects this format for extras
                    report.extra.append(extras.url(relative_screenshot_path, name='Screenshot'))
                    
                    logging.info("Screenshot saved: %s", screenshot_path)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logging.error("Failed to capture screenshot: %s", str(exc))

    handler, stream = log_streams.get(item.nodeid, (None, None))

    if handler and stream:
        # Make sure logs are flushed
        handler.flush()
        log_output = stream.getvalue()

        # Only remove the handler, don't close the stream yet
        logger = logging.getLogger()
        logger.removeHandler(handler)

        # Check if there are subtests
        subtests_html = ""
        if hasattr(item, 'user_properties'):
            item_subtests = [
                prop[1] for prop in item.user_properties if prop[0] == "subtest"
            ]
            if item_subtests:
                subtests_html = (
                    "<div style='margin-top: 10px;'>"
                    "<strong>Step-by-Step Details:</strong>"
                    "<ul style='list-style: none; padding-left: 0;'>"
                )
                for idx, subtest in enumerate(item_subtests, 1):
                    status = "✅ PASSED" if subtest.get('passed') else "❌ FAILED"
                    status_color = "green" if subtest.get('passed') else "red"
                    subtests_html += (
                        f"<li style='margin: 10px 0; padding: 10px; "
                        f"border-left: 3px solid {status_color}; "
                        f"background-color: #f9f9f9;'>"
                    )
                    subtests_html += (
                        f"<div style='font-weight: bold; color: {status_color};'>"
                        f"{status} - {subtest.get('msg', f'Step {idx}')}</div>"
                    )
                    if subtest.get('logs'):
                        subtests_html += (
                            f"<pre style='margin: 5px 0; padding: 5px; "
                            f"background-color: #fff; border: 1px solid #ddd; "
                            f"font-size: 11px;'>{subtest.get('logs').strip()}</pre>"
                        )
                    subtests_html += "</li>"
                subtests_html += "</ul></div>"

        # Combine main log output with subtests
        if subtests_html:
            report.description = f"<pre>{log_output.strip()}</pre>{subtests_html}"
        else:
            report.description = f"<pre>{log_output.strip()}</pre>"

        # Clean up references
        log_streams.pop(item.nodeid, None)
    else:
        report.description = ""


log_streams = {}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    # Prepare StringIO for capturing logs
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.addHandler(handler)

    # Save handler and stream
    log_streams[item.nodeid] = (handler, stream)


def pytest_collection_modifyitems(items):
    for item in items:
        if hasattr(item, "callspec"):
            prompt = item.callspec.params.get("prompt")
            if prompt:
                item._nodeid = (
                    prompt  # This controls how the test name appears in the report
                )


def rename_duration_column():
    report_path = os.path.abspath("report.html")  # or your report filename
    if not os.path.exists(report_path):
        print("Report file not found, skipping column rename.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find and rename the header
    headers = soup.select("table#results-table thead th")
    for th in headers:
        if th.text.strip() == "Duration":
            th.string = "Execution Time"
            # print("Renamed 'Duration' to 'Execution Time'")
            break
    else:
        print("'Duration' column not found in report.")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


# Register this function to run after everything is done
atexit.register(rename_duration_column)
