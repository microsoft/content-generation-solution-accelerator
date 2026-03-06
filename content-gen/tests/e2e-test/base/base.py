"""Base page module for common page object functionality."""
from playwright.sync_api import Page


class BasePage:
    """Base class for all page objects with common methods."""
    
    def __init__(self, page: Page):
        """Initialize BasePage with Playwright page instance."""
        self.page = page

    def scroll_into_view(self, locator):
        """Scroll the specified locator into view if needed."""
        reference_list = locator
        locator.nth(reference_list.count() - 1).scroll_into_view_if_needed()

    def is_visible(self, locator):
        """Check if the specified locator is visible."""
        locator.is_visible()
    