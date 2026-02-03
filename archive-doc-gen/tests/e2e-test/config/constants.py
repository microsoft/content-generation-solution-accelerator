import os
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("url")

if URL.endswith("/"):
    URL = URL[:-1]

# Get the absolute path to the repository root
repo_root = os.getenv("GITHUB_WORKSPACE", os.getcwd())

# browse input data
browse_question1 = "What are typical sections in a promissory note?"
browse_question2 = "List the details of two promissory notes governed by the laws of the state of California"
browse_question3 = "List all documents and their value"
browse_question4 = "list each promissory note, the borrower name, the lender name, the amount, and the interest rate in table format where the interest rate is not 5%"
browse_question5 = "list each promissory note, the borrower name, the lender name, the amount, and the interest rate in tabular format where the interest rate is not 5%"

# Generate input data
generate_question1 = "Generate promissory note for Washington State"
add_section = "Add Payment acceleration clause after the payment terms sections"

remove_section = "Remove Borrower Information Promissory note"

# Response Text Data
invalid_response = "I was unable to find content related to your query and could not generate a template. Please try again."
invalid_response1 = "An error occurred. Answers can't be saved at this time. If the problem persists, please contact the site administrator."


# Construct the absolute path to the JSON file
# Note: This section is commented out as prompts.json file doesn't exist
# All required constants are defined above
# json_file_path = os.path.join(repo_root, 'tests/e2e-test', 'testdata', 'prompts.json')
# with open(json_file_path, 'r') as file:
#     data = json.load(file)
#     questions = data['questions']
