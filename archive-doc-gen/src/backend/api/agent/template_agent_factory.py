from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from backend.helpers.azure_credential_utils import get_azure_credential_async
from backend.settings import app_settings
from event_utils import track_event_if_configured

from backend.api.agent.agent_factory_base import BaseAgentFactory


class TemplateAgentFactory(BaseAgentFactory):
    """Factory class for creating and managing template agent instances."""

    @classmethod
    async def create_or_get_agent(cls):
        """
        Create a new template agent instance.

        Returns:
            object: The created agent instance.
        """
        project_client = AIProjectClient(
            endpoint=app_settings.azure_ai.agent_endpoint,
            credential=await get_azure_credential_async(client_id=app_settings.base_settings.azure_client_id),
            api_version=app_settings.azure_ai.agent_api_version
        )

        agent_name = f"DG-TemplateAgent-{app_settings.base_settings.solution_name}"
        # 1. Check if the agent already exists
        async for agent in project_client.agents.list_agents():
            if agent.name == agent_name:
                track_event_if_configured("TemplateAgentExists", {"agent_name": agent_name})
                return {
                    "agent": agent,
                    "client": project_client
                }

        # 2. Create the agent if it does not exist
        track_event_if_configured("TemplateAgentCreating", {"agent_name": agent_name})
        index_name = f"project-index-{app_settings.datasource.connection_name}-{app_settings.datasource.index}"
        index_version = "1"
        field_mapping = {
            "contentFields": ["content"],
            "urlField": "sourceurl",
            "titleField": "sourceurl",
        }

        project_index = await project_client.indexes.create_or_update(
            name=index_name,
            version=index_version,
            index={
                "connectionName": app_settings.datasource.connection_name,
                "indexName": app_settings.datasource.index,
                "type": "AzureSearch",
                "fieldMapping": field_mapping
            }
        )
        print("Project index created or updated.")
        ai_search = AzureAISearchTool(
            index_asset_id=f"{project_index.name}/versions/{project_index.version}",
            index_connection_id=None,
            index_name=None,
            query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
            top_k=app_settings.datasource.top_k,
            filter="",
        )

        agent = await project_client.agents.create_agent(
            model=app_settings.azure_ai.agent_model_deployment_name,
            name=agent_name,
            instructions=app_settings.azure_openai.template_system_message,
            tools=ai_search.definitions,
            tool_resources=ai_search.resources,
        )

        return {
            "agent": agent,
            "client": project_client
        }

    @classmethod
    async def _delete_agent_instance(cls, agent_wrapper: dict):
        """
        Asynchronously deletes the specified agent instance from the Azure AI project.

        Args:
            agent_wrapper (dict): A dictionary containing the 'agent' and the corresponding 'client'.
        """
        await agent_wrapper["client"].agents.delete_agent(agent_wrapper["agent"].id)
