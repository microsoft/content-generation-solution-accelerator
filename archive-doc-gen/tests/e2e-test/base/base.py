import json

from config.constants import URL
from dotenv import load_dotenv


class BasePage:
    def __init__(self, page=None):
        self.page = page

    def scroll_into_view(self, locator):
        reference_list = locator
        locator.nth(reference_list.count() - 1).scroll_into_view_if_needed()

    def is_visible(self, locator):
        locator.is_visible()

    def validate_response_status(self, question_api=""):
        load_dotenv()  # Ensure environment variables are loaded
        # URL of the API endpoint
        url = f"{URL}/conversation"

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # Payload (data) to be sent in the POST request
        payload = {
            "chat_type": "browse",
            "messages": [
                {
                    "role": "user",
                    "content": question_api,  # Use the passed question
                }
            ],
        }

        # Make the POST request
        response = self.page.request.post(
            url, headers=headers, data=json.dumps(payload), timeout=120000
        )
        assert response.status == 200, (
            "response code is " + str(response.status) + " " + str(response.json())
        )

    def validate_generate_response_status(self, question_api=""):
        load_dotenv()  # Ensure environment variables are loaded
        # URL of the API endpoint
        url = f"{URL}/history/generate"

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        # Payload (data) to be sent in the POST request
        payload = {
            "chat_type": "template",
            "messages": [
                {
                    "role": "user",
                    "content": question_api,  # Use the passed question
                }
            ],
        }

        # Make the POST request
        response = self.page.request.post(
            url, headers=headers, data=json.dumps(payload), timeout=120000
        )
        assert response.status == 200, (
            "response code is " + str(response.status) + " " + str(response.json())
        )
