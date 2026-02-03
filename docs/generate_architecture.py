"""
Generate Solution Architecture Diagram for Content Generation Accelerator

Architecture based on main.bicep:
- AI Services: Azure AI Foundry with GPT-5.1 and GPT-Image-1 models
- AI Search: Azure AI Search with semantic search for product discovery
- Storage: Blob Storage with product-images, generated-images, data containers
- Cosmos DB: NoSQL database for conversations and products
- App Service: Node.js frontend with VNet integration
- Container Instance: Python/Quart backend API in private subnet
- VNet: Private networking with subnets for web, ACI, private endpoints
- Private DNS Zones: cognitiveservices, openai, blob, documents
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.azure.compute import ContainerInstances, AppServices, ContainerRegistries
from diagrams.azure.database import CosmosDb, BlobStorage
from diagrams.azure.ml import CognitiveServices
from diagrams.azure.network import VirtualNetworks, PrivateEndpoint, DNSZones
from diagrams.azure.analytics import AnalysisServices
from diagrams.onprem.client import User

# Graph attributes for dark theme - using TB (top-bottom) to avoid line crossings
graph_attr = {
    "bgcolor": "#1a2634",
    "fontcolor": "white",
    "fontsize": "14",
    "pad": "0.8",
    "splines": "ortho",  # Orthogonal lines for clean routing
    "nodesep": "0.8",
    "ranksep": "1.0",
    "compound": "true",  # Allow edges between clusters
}

node_attr = {
    "fontcolor": "white",
    "fontsize": "10",
}

edge_attr = {
    "color": "#4a9eff",
    "style": "bold",
    "penwidth": "1.5",
}

with Diagram(
    "Content Generation Solution Architecture",
    filename="/home/jahunte/content-generation-solution-accelerator/docs/images/readme/solution_architecture",
    outformat="png",
    show=False,
    direction="TB",  # Top-to-Bottom layout to avoid crossing lines
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    user = User("User")
    
    with Cluster("Azure Cloud", graph_attr={"bgcolor": "#243447", "fontcolor": "white"}):
        
        # Row 1: Frontend
        with Cluster("Frontend Tier", graph_attr={"bgcolor": "#2d4a5e"}):
            app_service = AppServices("App Service\n(Node.js Frontend)")
        
        # Row 2: Backend & Registry (side by side)
        with Cluster("Virtual Network (10.0.0.0/20)", graph_attr={"bgcolor": "#1e3a4c"}):
            
            with Cluster("ACI Subnet (10.0.4.0/24)", graph_attr={"bgcolor": "#2d4a5e"}):
                aci = ContainerInstances("Container Instance\n(Python/Quart API)")
            
            with Cluster("Private Endpoints", graph_attr={"bgcolor": "#2d4a5e"}):
                pep = PrivateEndpoint("Private\nEndpoints")
        
        with Cluster("Container Registry", graph_attr={"bgcolor": "#2d4a5e"}):
            acr = ContainerRegistries("Azure Container\nRegistry")
        
        # Row 3: AI Services (grouped together to avoid crossings)
        with Cluster("Azure AI Foundry", graph_attr={"bgcolor": "#2d4a5e"}):
            aoai_gpt = CognitiveServices("GPT-5.1\n(Content Gen)")
            aoai_image = CognitiveServices("GPT-Image-1\n(Image Gen)")
        
        with Cluster("Search", graph_attr={"bgcolor": "#2d4a5e"}):
            ai_search = AnalysisServices("Azure AI Search\n(Product Index)")
        
        # Row 4: Data Storage (side by side at bottom)
        with Cluster("Data Storage", graph_attr={"bgcolor": "#2d4a5e"}):
            blob = BlobStorage("Blob Storage\n(Images)")
            cosmos = CosmosDb("Cosmos DB\n(Products, Chats)")
    
    # Connections - ordered to minimize crossings
    # User to Frontend
    user >> Edge(label="HTTPS", color="#00cc66") >> app_service
    
    # Frontend to Backend (VNet integration)
    app_service >> Edge(label="VNet\nIntegration", color="#ffcc00") >> aci
    
    # ACR to ACI
    acr >> Edge(label="Pull\nImage", style="dashed", color="#999999") >> aci
    
    # Backend to AI (through private endpoints conceptually)
    aci >> Edge(label="Generate\nContent") >> aoai_gpt
    aci >> Edge(label="Generate\nImages") >> aoai_image
    aci >> Edge(label="Search\nProducts") >> ai_search
    
    # Backend to Data Storage
    aci >> Edge(label="CRUD") >> cosmos
    aci >> Edge(label="Store/Get\nImages") >> blob
    
    # Private endpoint connections (visual representation)
    pep >> Edge(style="dotted", color="#666666") >> aoai_gpt
    pep >> Edge(style="dotted", color="#666666") >> blob
    pep >> Edge(style="dotted", color="#666666") >> cosmos
