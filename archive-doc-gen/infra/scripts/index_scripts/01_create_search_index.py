from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchIndex
)

# === Configuration ===
key_vault_name = 'kv_to-be-replaced'
managed_identity_client_id = 'mici_to-be-replaced'
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


def create_search_index():
    """Create an Azure Search index."""

    # Shared credential
    credential = AzureCliCredential()

    # Retrieve secrets from Key Vault
    search_endpoint = get_secrets_from_kv("AZURE-SEARCH-ENDPOINT")
    openai_resource_url = get_secrets_from_kv("AZURE-OPENAI-ENDPOINT")
    embedding_model = get_secrets_from_kv("AZURE-OPENAI-EMBEDDING-MODEL")

    index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

    # Define index schema
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="chunk_id", type=SearchFieldDataType.String),
        SearchField(name="content", type=SearchFieldDataType.String),
        SearchField(name="sourceurl", type=SearchFieldDataType.String),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile",
        ),
    ]

    # Define vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="myHnsw")
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                vectorizer_name="myOpenAI"
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="myOpenAI",
                kind="azureOpenAI",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_resource_url,
                    deployment_name=embedding_model,
                    model_name=embedding_model
                )
            )
        ]
    )

    # Define semantic search configuration
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            keywords_fields=[SemanticField(field_name="chunk_id")],
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )
    result = index_client.create_or_update_index(index)
    print(f"Search index '{result.name}' created or updated successfully.")


create_search_index()
