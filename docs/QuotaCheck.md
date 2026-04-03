## Check Quota Availability Before Deployment

Before deploying the Content Generation Solution Accelerator, **ensure sufficient quota availability** for the required models.

> **For Global Standard | GPT-5.1 - ensure capacity to at least 150 tokens post-deployment for optimal performance.**

> **For Global Standard | GPT-Image-1-mini - ensure capacity to at least 1 RPM (Requests Per Minute) for image generation.**


### Login if you have not done so already
```sh
az login
```


### 📌 Default Models & Capacities:
```
gpt-5.1:150,gpt-image-1-mini:1
```
**Note:** GPT-5.1 capacity is in tokens, GPT-Image-1-mini capacity is in RPM (Requests Per Minute).
### 📌 Default Regions:
```
australiaeast, centralus, eastasia, eastus, eastus2, japaneast, northeurope, southeastasia, swedencentral, uksouth, westus, westus3
```
### Usage Scenarios:
- No parameters passed → Default models and capacities will be checked in default regions.
- Only model(s) provided → The script will check for those models in the default regions.
- Only region(s) provided → The script will check default models in the specified regions.
- Both models and regions provided → The script will check those models in the specified regions.
- `--verbose` passed → Enables detailed logging output for debugging and traceability.

### **Input Formats**
> Use the --models, --regions, and --verbose options for parameter handling:

✔️ Run without parameters to check default models & regions without verbose logging:
   ```
  ./quota_check_params.sh
   ```
✔️ Enable verbose logging:
   ```
  ./quota_check_params.sh --verbose
   ```
✔️ Check specific model(s) in default regions:
  ```
  ./quota_check_params.sh --models gpt-5.1:150,gpt-image-1-mini:1
  ```
✔️ Check default models in specific region(s):
  ```
./quota_check_params.sh --regions eastus,swedencentral
  ```
✔️ Passing Both models and regions:
  ```
  ./quota_check_params.sh --models gpt-5.1:150,gpt-image-1-mini:1 --regions eastus,swedencentral
  ```
✔️ All parameters combined:
  ```
 ./quota_check_params.sh --models gpt-5.1:150,gpt-image-1-mini:1 --regions eastus,swedencentral --verbose
  ```

### **Sample Output**
The final table lists regions with available quota. You can select any of these regions for deployment.

![quota-check-output](images/quota-check-output.png)

---
### **If using Azure Portal and Cloud Shell**

1. Navigate to the [Azure Portal](https://portal.azure.com).
2. Click on **Azure Cloud Shell** in the top right navigation menu.
3. Run the appropriate command based on your requirement:

   **To check quota for the deployment**

    ```sh
    curl -L -o quota_check_params.sh "https://raw.githubusercontent.com/microsoft/content-generation-solution-accelerator/main/content-gen/infra/scripts/quota_check_params.sh"
    chmod +x quota_check_params.sh
    ./quota_check_params.sh
    ```
    - Refer to [Input Formats](#input-formats) for detailed commands.

### **If using VS Code or Codespaces**
1. Open the terminal in VS Code or Codespaces.
2. If you're using VS Code, click the dropdown on the right side of the terminal window, and select `Git Bash`.
   ![git_bash](images/git_bash.png)
3. Navigate to the `infra/scripts` folder where the script files are located and make the script as executable:
   ```sh
    cd infra/scripts
    chmod +x quota_check_params.sh
    ```
4. Run the appropriate script based on your requirement:

   **To check quota for the deployment**

    ```sh
    ./quota_check_params.sh
    ```
   - Refer to [Input Formats](#input-formats) for detailed commands.

5. If you see the error `_bash: az: command not found_`, install Azure CLI:

    ```sh
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
    az login
    ```
6. Rerun the script after installing Azure CLI.
