## Content Generation Solution Accelerator: Responsible AI FAQ
- ### What is the Multi-Agent Content Generation?
    This solution accelerator is an open-source GitHub Repository to help create context-aware, multimodal campaign content (text + images) using a multiagent solution. This can be used by anyone looking for reusable architecture and code snippets to build a ready-to-use, extensible, multi-agent system that generates marketing content. The repository showcases a scenario of a user who wants to generate a marketing ad campaign for a social media post based on a sample set of data.

- ### What can the Multi-Agent Content Generation do? 
    This is a multimodal content generation solution for retail marketing campaigns. It uses Microsoft Agent Framework with Handoff Builder orchestration to interpret creative briefs and generate compliant marketing content (text + images) grounded in enterprise product data and brand guidelines.

    **Key Capabilities:**
    - Parse free-text creative briefs into structured fields
    - Generate marketing copy using GPT models
    - Generate marketing images using DALL-E 3
    - Validate content against brand guidelines with severity-categorized compliance checks
    - Ground content in product catalog data from Cosmos DB

- ### What is/are Content Generation Solution Accelerator's intended use(s)?  
    This repository is to be used only as a solution accelerator following the open-source license terms listed in the GitHub repository. The example scenario's intended purpose is to help users generate a marketing ad campaign for a social media post based on a sample set of data and help them perform their work more efficiently.

- ### How was Content Generation Solution Accelerator evaluated? What metrics are used to measure performance?
    We have used the Azure AI evaluation SDK to test for harmful content, groundedness and potential risks.
  
- ### What are the limitations of Content Generation Solution Accelerator? How can users minimize the impact of Content Generation Solution Accelerator's limitations when using the system?
    This solution accelerator can only be used as a sample to accelerate the creation of an AI assistant. The repository showcases a sample scenario of a user generating a marketing ad campaign. Users should review the system prompts provided and update them as per their organizational guidance. Users should run their own evaluation flow either using the guidance provided in the GitHub repository or their choice of evaluation methods. AI-generated content may be inaccurate and should be manually reviewed. Currently, the sample repo is available in English only.

- ### What operational factors and settings allow for effective and responsible use of Content Generation Solution Accelerator?
    Users can try different values for some parameters like system prompt, image models, etc. shared as configurable environment variables while running run evaluations for AI assistants. Please note that these parameters are only provided as guidance to start the configuration but not as a complete available list to adjust the system behavior. Please always refer to the latest product documentation for these details or reach out to your Microsoft account team if you need assistance.
