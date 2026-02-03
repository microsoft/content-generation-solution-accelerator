# Content generation solution accelerator

This solution accelerator is an internal chatbot that interprets and understands context and direction from creative briefs to create multi-modal text and image content for marketing ad campaigns. Built on the Microsoft Agent Framework with HandoffBuilder orchestration, it uses specialized AI agents to parse briefs, research product data, generate content, and validate brand compliance.
<br/>

<div align="center">
  
[**SOLUTION OVERVIEW**](#solution-overview)  \| [**QUICK DEPLOY**](#quick-deploy)  \| [**BUSINESS SCENARIO**](#business-scenario)  \| [**SUPPORTING DOCUMENTATION**](#supporting-documentation)

</div>
<br/>

**Note:** With any AI solutions you create using these templates, you are responsible for assessing all associated risks and for complying with all applicable laws and safety standards. Learn more in the transparency documents for [Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/agents/transparency-note) and [Agent Framework](https://github.com/microsoft/agent-framework/blob/main/TRANSPARENCY_FAQ.md).
<br/>

<h2><img src="./docs/images/readme/solution_overview.png" width="48" />
Solution overview
</h2>

This solution leverages Microsoft Foundry, Azure AI Search, Azure Cosmos DB, and Azure Blob Storage to interpret creative briefs, retrieve product information, generate marketing content, and validate brand compliance.

The sample data includes synthetic product catalogs and brand guidelines. The data is intended for use as sample data only.

### Solution architecture
|![image](./docs/images/readme/solution_architecture.png)|
|---|


<br/>

### Additional resources

[Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/) 

[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)

[Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/)

[Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-studio/)


<br/>

### Key features
<details open>
  <summary>Click to learn more about the key features this solution enables</summary>

  - **Creative Brief Interpretation** <br/>
  Parse free-text creative briefs into structured fields (overview, objectives, target audience, key message, tone/style, deliverable, timelines, visual guidelines, CTA).

  - **Multimodal Content Generation** <br/>
  Generate marketing copy and images using GPT models and DALL-E 3 grounded in enterprise product data.

  - **Brand Compliance Validation** <br/>
  Validate all generated content against brand guidelines with severity-categorized feedback (Error, Warning, Info).

  - **Specialized Agent Orchestration** <br/>
  Uses Microsoft Agent Framework with HandoffBuilder to coordinate Triage, Planning, Research, Text Content, Image Content, and Compliance agents.
       
</details>

<br /><br />
<h2><img src="./docs/images/readme/quick_deploy.png" width="48" />
Quick deploy
</h2>

### How to install or deploy
Follow the quick deploy steps on the deployment guide to deploy this solution to your own Azure subscription.

> **Note:** This solution accelerator requires **Azure Developer CLI (azd) version 1.18.0 or higher**. Please ensure you have the latest version installed before proceeding with deployment. [Download azd here](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd).

[Click here to launch the deployment guide](./content-gen/docs/DEPLOYMENT.md)
<br/><br/>

| [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/content-generation-solution-accelerator) | [![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/content-generation-solution-accelerator) | [![Open in Visual Studio Code Web](https://img.shields.io/static/v1?style=for-the-badge&label=Visual%20Studio%20Code%20(Web)&message=Open&color=blue&logo=visualstudiocode&logoColor=white)](https://vscode.dev/azure/?vscode-azure-exp=foundry&agentPayload=eyJiYXNlVXJsIjogImh0dHBzOi8vcmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbS9taWNyb3NvZnQvY29udGVudC1nZW5lcmF0aW9uLXNvbHV0aW9uLWFjY2VsZXJhdG9yL3JlZnMvaGVhZHMvbWFpbi9jb250ZW50LWdlbi9pbmZyYS92c2NvZGVfd2ViIiwgImluZGV4VXJsIjogIi9pbmRleC5qc29uIiwgInZhcmlhYmxlcyI6IHsiYWdlbnRJZCI6ICIiLCAiY29ubmVjdGlvblN0cmluZyI6ICIiLCAidGhyZWFkSWQiOiAiIiwgInVzZXJNZXNzYWdlIjogIiIsICJwbGF5Z3JvdW5kTmFtZSI6ICIiLCAibG9jYXRpb24iOiAiIiwgInN1YnNjcmlwdGlvbklkIjogIiIsICJyZXNvdXJjZUlkIjogIiIsICJwcm9qZWN0UmVzb3VyY2VJZCI6ICIiLCAiZW5kcG9pbnQiOiAiIn0sICJjb2RlUm91dGUiOiBbImFpLXByb2plY3RzLXNkayIsICJweXRob24iLCAiZGVmYXVsdC1henVyZS1hdXRoIiwgImVuZHBvaW50Il19) |
|---|---|---|

<br/>

> ⚠️ **Important: Check Azure OpenAI Quota Availability**
 <br/>To ensure sufficient quota is available in your subscription, please follow [quota check instructions guide](./docs/QuotaCheck.md) before you deploy the solution.

<br/>

### Prerequisites and costs

To deploy this solution accelerator, ensure you have access to an [Azure subscription](https://azure.microsoft.com/free/) with the necessary permissions to create **resource groups, resources, app registrations, and assign roles at the resource group level**. This should include Contributor role at the subscription level and  Role Based Access Control role on the subscription and/or resource group level. Follow the steps in [Azure Account Set Up](./docs/AzureAccountSetUp.md).

Check the [Azure Products by Region](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/?products=all&regions=all) page and select a **region** where the following services are available.

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage. The majority of the Azure resources used in this infrastructure are on usage-based pricing tiers. However, Azure Container Registry has a fixed cost per registry per day.

Use the [Azure pricing calculator](https://azure.microsoft.com/en-us/pricing/calculator) to calculate the cost of this solution in your subscription. 

Review a [sample pricing sheet](https://azure.com/e/2402502429fc46429e395e0bb93d0711) in the event you want to customize and scale usage.

_Note: This is not meant to outline all costs as selected SKUs, scaled use, customizations, and integrations into your own tenant can affect the total consumption of this sample solution. The sample pricing sheet is meant to give you a starting point to customize the estimate for your specific needs._

<br/>

| Product | Description | Cost |
|---|---|---|
| [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/) | Free tier. Build generative AI applications on an enterprise-grade platform. | [Pricing](https://azure.microsoft.com/pricing/details/ai-studio/) |
| [Azure Storage Account](https://learn.microsoft.com/en-us/azure/storage/blobs/) | Standard tier, LRS. Pricing is based on storage and operations. Blob storage for product images and generated content. | [Pricing](https://azure.microsoft.com/pricing/details/storage/blobs/) |
| [Azure AI Services](https://learn.microsoft.com/en-us/azure/ai-services/) | S0 tier, defaults to gpt-5.1 (GPT) and gpt-image-1 (DALL-E 3) models. Pricing is based on token count. | [Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/) |
| [Azure Container Instance](https://learn.microsoft.com/en-us/azure/container-instances/) | Backend API hosting with private VNet integration. Pricing is based on resource allocation. | [Pricing](https://azure.microsoft.com/pricing/details/container-instances/) |
| [Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/) | B1 tier. Frontend hosting with Node.js proxy server. | [Pricing](https://azure.microsoft.com/pricing/details/app-service/) |
| [Azure Container Registry](https://learn.microsoft.com/en-us/azure/container-registry/) | Basic tier. Build, store, and manage container images and artifacts in a private registry for all types of container deployments | [Pricing](https://azure.microsoft.com/pricing/details/container-registry/) |
| [Log analytics](https://learn.microsoft.com/en-us/azure/azure-monitor/) | Pay-as-you-go tier. Costs based on data ingested. Collect and analyze on telemetry data generated by Azure. | [Pricing](https://azure.microsoft.com/pricing/details/monitor/) |
| [Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/) | Serverless tier. Product catalog and conversation history storage. | [Pricing](https://azure.microsoft.com/en-us/pricing/details/cosmos-db/autoscale-provisioned/) |



<br/>

>⚠️ **Important:** To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.

<br /><br />
<h2><img src="./docs/images/readme/business_scenario.png" width="48" />
Business Scenario
</h2>


|![image](./docs/images/readme/landing_page.png)|
|---|

<br/>

Accelerate your marketing content creation by leveraging AI to interpret creative briefs and generate on-brand, multimodal content. The solution helps marketing teams reduce time-to-market for campaigns by automating the creation of compliant marketing copy and images grounded in product data.

⚠️ The sample data used in this repository is synthetic and generated using Azure OpenAI Service. The data is intended for use as sample data only.


### Business value
<details>
  <summary>Click to learn more about what value this solution provides</summary>

  - **Interpret creative briefs** <br/>
  Parse unstructured creative briefs into structured fields automatically, ensuring all campaign requirements are captured.

  - **Generate multimodal content** <br/>
  Create marketing copy and images that align with your brand voice and product catalog using GPT and DALL-E 3.

  - **Ensure brand compliance** <br/>
  Validate all generated content against brand guidelines with severity-categorized feedback before publication.

  - **Ground in enterprise data** <br/>
  Leverage product information, images, and brand guidelines stored in Azure to ensure accurate, relevant content.

  - **Secure data and responsible AI** <br/>
  Maintain data security with managed identities and private networking while fostering responsible AI adoption.

     
</details>

<br /><br />

<h2><img src="./docs/images/readme/supporting_documentation.png" width="48" />
Supporting documentation
</h2>

### Security guidelines

This template uses [Managed Identity](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview) for authentication between Azure services.

The backend runs in Azure Container Instance within a private VNet subnet, accessible only through the App Service frontend proxy. Private networking can be enabled via the `enablePrivateNetworking` parameter.

To ensure continued best practices in your own repository, we recommend that anyone creating solutions based on our templates ensure that the [Github secret scanning](https://docs.github.com/code-security/secret-scanning/about-secret-scanning) setting is enabled.

You may want to consider additional security measures, such as:

* Enabling Microsoft Defender for Cloud to [secure your Azure resources](https://learn.microsoft.com/azure/defender-for-cloud).
* Protecting the Azure App Service with [authentication](https://learn.microsoft.com/azure/app-service/overview-authentication-authorization) and/or [Virtual Network integration](https://learn.microsoft.com/azure/app-service/overview-vnet-integration).

<br/>

### Cross references
Check out similar solution accelerators
 
| Solution Accelerator | Description |
|---|---|
| [Chat&nbsp;with&nbsp;your&nbsp;data](https://github.com/Azure-Samples/chat-with-your-data-solution-accelerator) | Chat with their own data by combining Azure Cognitive Search and Large Language Models (LLMs) to create a conversational search experience. It enables increased user efficiency by minimizing endpoints required to access internal company knowledgebases. |
| [Document&nbsp;knowledge&nbsp;mining](https://github.com/microsoft/Document-Knowledge-Mining-Solution-Accelerator) | Built on Azure OpenAI Service and Azure AI Document Intelligence to process and extract summaries, entities, and metadata from unstructured, multi-modal documents and enable searching and chatting over this data. |
| [Build&nbsp;your&nbsp;own&nbsp;copilot](https://github.com/microsoft/Build-your-own-copilot-Solution-Accelerator) | Helps client advisors to save time and prepare relevant discussion topics for scheduled meetings with overviews, client profile views, and chatting with structured data. |


<br/>   


## Provide feedback

Have questions, find a bug, or want to request a feature? [Submit a new issue](https://github.com/microsoft/content-generation-solution-accelerator/issues) on this repo and we'll connect.

<br/>

## Responsible AI Transparency FAQ 
Please refer to [Transparency FAQ](./content-gen/docs/TRANSPARENCY_FAQ.md) for responsible AI transparency details of this solution accelerator.

<br/>

## Disclaimers

This release is an artificial intelligence (AI) system that generates text based on user input. The text generated by this system may include ungrounded content, meaning that it is not verified by any reliable source or based on any factual data. The data included in this release is synthetic, meaning that it is artificially created by the system and may contain factual errors or inconsistencies. Users of this release are responsible for determining the accuracy, validity, and suitability of any content generated by the system for their intended purposes. Users should not rely on the system output as a source of truth or as a substitute for human judgment or expertise.

This release only supports English language input and output. Users should not attempt to use the system with any other language or format. The system output may not be compatible with any translation tools or services, and may lose its meaning or coherence if translated.

This release does not reflect the opinions, views, or values of Microsoft Corporation or any of its affiliates, subsidiaries, or partners. The system output is solely based on the system's own logic and algorithms, and does not represent any endorsement, recommendation, or advice from Microsoft or any other entity. Microsoft disclaims any liability or responsibility for any damages, losses, or harms arising from the use of this release or its output by any user or third party.

This release does not provide any financial advice, and is not designed to replace the role of qualified client advisors in appropriately advising clients. Users should not use the system output for any financial decisions or transactions, and should consult with a professional financial advisor before taking any action based on the system output. Microsoft is not a financial institution or a fiduciary, and does not offer any financial products or services through this release or its output.

This release is intended as a proof of concept only, and is not a finished or polished product. It is not intended for commercial use or distribution, and is subject to change or discontinuation without notice. Any planned deployment of this release or its output should include comprehensive testing and evaluation to ensure it is fit for purpose and meets the user's requirements and expectations. Microsoft does not guarantee the quality, performance, reliability, or availability of this release or its output, and does not provide any warranty or support for it.

This Software requires the use of third-party components which are governed by separate proprietary or open-source licenses as identified below, and you must comply with the terms of each applicable license in order to use the Software. You acknowledge and agree that this license does not grant you a license or other right to use any such third-party proprietary or open-source components.

To the extent that the Software includes components or code used in or derived from Microsoft products or services, including without limitation Microsoft Azure Services (collectively, “Microsoft Products and Services”), you must also comply with the Product Terms applicable to such Microsoft Products and Services. You acknowledge and agree that the license governing the Software does not grant you a license or other right to use Microsoft Products and Services. Nothing in the license or this ReadMe file will serve to supersede, amend, terminate or modify any terms in the Product Terms for any Microsoft Products and Services.

You must also comply with all domestic and international export laws and regulations that apply to the Software, which include restrictions on destinations, end users, and end use. For further information on export restrictions, visit https://aka.ms/exporting.

You acknowledge that the Software and Microsoft Products and Services (1) are not designed, intended or made available as a medical device(s), and (2) are not designed or intended to be a substitute for professional medical advice, diagnosis, treatment, or judgment and should not be used to replace or as a substitute for professional medical advice, diagnosis, treatment, or judgment. Customer is solely responsible for displaying and/or obtaining appropriate consents, warnings, disclaimers, and acknowledgements to end users of Customer’s implementation of the Online Services.

You acknowledge the Software is not subject to SOC 1 and SOC 2 compliance audits. No Microsoft technology, nor any of its component technologies, including the Software, is intended or made available as a substitute for the professional advice, opinion, or judgment of a certified financial services professional. Do not use the Software to replace, substitute, or provide professional financial advice or judgment.

BY ACCESSING OR USING THE SOFTWARE, YOU ACKNOWLEDGE THAT THE SOFTWARE IS NOT DESIGNED OR INTENDED TO SUPPORT ANY USE IN WHICH A SERVICE INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE OF THE SOFTWARE COULD RESULT IN THE DEATH OR SERIOUS BODILY INJURY OF ANY PERSON OR IN PHYSICAL OR ENVIRONMENTAL DAMAGE (COLLECTIVELY, “HIGH-RISK USE”), AND THAT YOU WILL ENSURE THAT, IN THE EVENT OF ANY INTERRUPTION, DEFECT, ERROR, OR OTHER FAILURE OF THE SOFTWARE, THE SAFETY OF PEOPLE, PROPERTY, AND THE ENVIRONMENT ARE NOT REDUCED BELOW A LEVEL THAT IS REASONABLY, APPROPRIATE, AND LEGAL, WHETHER IN GENERAL OR IN A SPECIFIC INDUSTRY. BY ACCESSING THE SOFTWARE, YOU FURTHER ACKNOWLEDGE THAT YOUR HIGH-RISK USE OF THE SOFTWARE IS AT YOUR OWN RISK.  
