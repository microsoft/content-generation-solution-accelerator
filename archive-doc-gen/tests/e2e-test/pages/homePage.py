from base.base import BasePage
from playwright.sync_api import expect
from config.constants import URL


class HomePage(BasePage):
    BROWSE_BUTTON = (
        "//p[contains(text(),'Let AI search through your files and provide answe')]"
    )
    HOME_TITLE = "//h2[normalize-space()='AI-powered document search and creation.']"
    BROWSE_TEXT = (
        "//p[contains(text(),'Let AI search through your files and provide answe')]"
    )
    GENERATE_TEXT = (
        "//p[normalize-space()='Have AI generate draft documents to save you time']"
    )

    def __init__(self, page):
        super().__init__(page)

    def click_browse_button(self):
        # click on BROWSE
        self.page.wait_for_timeout(3000)
        self.page.locator(self.BROWSE_BUTTON).click()
        self.page.wait_for_timeout(5000)

    def click_generate_button(self):
        # click on GENERATE
        self.page.wait_for_timeout(3000)
        self.page.locator(self.GENERATE_TEXT).click()
        self.page.wait_for_timeout(5000)
    
    def open_home_page(self):
        self.page.goto(URL)
        self.page.wait_for_timeout(3000)

    def validate_home_page(self):
        self.page.wait_for_timeout(5000)
        expect(self.page.locator(self.HOME_TITLE)).to_be_visible()
        expect(self.page.locator(self.BROWSE_TEXT)).to_be_visible()
        expect(self.page.locator(self.GENERATE_TEXT)).to_be_visible()