from azure.keyvault.secrets import SecretClient
from azure.ai.inference import EmbeddingsClient
import re
import time
import pypdf
from io import BytesIO
from urllib.parse import urlparse
from azure.search.documents import SearchClient
from azure.storage.filedatalake import DataLakeServiceClient
from azure.search.documents.indexes import SearchIndexClient
from azure.identity import AzureCliCredential


key_vault_name = 'kv_to-be-replaced'
managed_identity_client_id = 'mici_to-be-replaced'
file_system_client_name = "data"
directory = 'pdf'
index_name = "pdf_index"


def get_secrets_from_kv(secret_name: str) -> str:
    """
    Retrieves a secret value from Azure Key Vault.
    Args:
        secret_name (str): Name of the secret.
        credential (AzureCliCredential): Credential with access to Key Vault.
    Returns:
        str: The secret value.
    """
    kv_credential = AzureCliCredential()
    secret_client = SecretClient(
        vault_url=f"https://{key_vault_name}.vault.azure.net/",
        credential=kv_credential
    )
    return secret_client.get_secret(secret_name).value


# Retrieve secrets from Key Vault
search_endpoint = get_secrets_from_kv("AZURE-SEARCH-ENDPOINT")
ai_project_endpoint = get_secrets_from_kv("AZURE-AI-AGENT-ENDPOINT")
account_name = get_secrets_from_kv("ADLS-ACCOUNT-NAME")
print("Secrets retrieved from Key Vault.")

# Azure Data Lake settings
account_url = f"https://{account_name}.dfs.core.windows.net"
credential = AzureCliCredential()
service_client = DataLakeServiceClient(account_url, credential=credential, api_version='2023-01-03')
file_system_client = service_client.get_file_system_client(file_system_client_name)
directory_name = directory
paths = file_system_client.get_paths(path=directory_name)
print("Azure DataLake setup complete.")

# Azure Search settings
search_client = SearchClient(search_endpoint, index_name, credential)
index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
print("Azure Search setup complete.")


# Function: Get Embeddings
def get_embeddings(text: str, ai_project_endpoint: str):
    embedding_model = "text-embedding-ada-002"
    # Construct inference endpoint with /models path
    inference_endpoint = f"https://{urlparse(ai_project_endpoint).netloc}/models"

    embeddings_client = EmbeddingsClient(
        endpoint=inference_endpoint,
        credential=credential,
        credential_scopes=["https://cognitiveservices.azure.com/.default"]
    )

    response = embeddings_client.embed(model=embedding_model, input=[text])
    embedding = response.data[0].embedding
    return embedding


# Function: Clean Spaces with Regex -
def clean_spaces_with_regex(text):
    # Use a regular expression to replace multiple spaces with a single space
    cleaned_text = re.sub(r'\s+', ' ', text)
    # Use a regular expression to replace consecutive dots with a single dot
    cleaned_text = re.sub(r'\.{2,}', '.', cleaned_text)
    return cleaned_text


# Function: Chunk Data
def chunk_data(text):
    tokens_per_chunk = 256  # 1024 # 500
    text = clean_spaces_with_regex(text)

    sentences = text.split('. ')  # Split text into sentences
    chunks = []
    current_chunk = ''
    current_chunk_token_count = 0

    # Iterate through each sentence
    for sentence in sentences:
        # Split sentence into tokens
        tokens = sentence.split()

        # Check if adding the current sentence exceeds tokens_per_chunk
        if current_chunk_token_count + len(tokens) <= tokens_per_chunk:
            # Add the sentence to the current chunk
            if current_chunk:
                current_chunk += '. ' + sentence
            else:
                current_chunk += sentence
            current_chunk_token_count += len(tokens)
        else:
            # Add current chunk to chunks list and start a new chunk
            chunks.append(current_chunk)
            current_chunk = sentence
            current_chunk_token_count = len(tokens)

    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# Function: Prepare Search Document
def prepare_search_doc(content, document_id):
    chunks = chunk_data(content)
    results = []
    for idx, chunk in enumerate(chunks, 1):
        chunk_id = f"{document_id}_{str(idx).zfill(2)}"

        try:
            v_contentVector = get_embeddings(str(chunk), ai_project_endpoint)
        except Exception as e:
            print(f"Error occurred: {e}. Retrying after 30 seconds...")
            time.sleep(30)
            try:
                v_contentVector = get_embeddings(str(chunk), ai_project_endpoint)
            except Exception as e:
                print(f"Retry failed: {e}. Setting v_contentVector to an empty list.")
                v_contentVector = []

        result = {
            "id": chunk_id,
            "chunk_id": chunk_id,
            "content": chunk,
            "sourceurl": path.name.split('/')[-1],
            "contentVector": v_contentVector
        }
        results.append(result)
    return results


# conversationIds = []
docs = []
counter = 0


for path in paths:
    file_client = file_system_client.get_file_client(path.name)
    pdf_file = file_client.download_file()

    stream = BytesIO()
    pdf_file.readinto(stream)
    pdf_reader = pypdf.PdfReader(stream)
    filename = path.name.split('/')[-1]
    document_id = filename.split('_')[1].replace('.pdf', '')

    text = ''
    num_pages = len(pdf_reader.pages)
    for page_num in range(num_pages):

        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    result = prepare_search_doc(text, document_id)
    docs.extend(result)

    counter += 1
    if docs != [] and counter % 10 == 0:
        result = search_client.upload_documents(documents=docs)
        docs = []

if docs != []:
    search_client.upload_documents(documents=docs)

print(f'{str(counter)} files processed.')
