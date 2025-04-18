# Dify Plugin Helper - v0.0.2

This repository contains tools to assist with Dify plugin development. Currently, it features an assistant that automatically generates `README.md` and `PRIVACY.md` files for your Dify plugin projects. Future updates will introduce more helper functionalities.

## Features (v0.0.2)

* **Automatic Documentation Generation:** Analyzes your plugin's manifest (`plugin.yaml`) and code structure to generate initial `README.md` and `PRIVACY.md` files using Dify.AI.
* **Streaming API:** Utilizes Dify's streaming API for efficient handling of potentially long responses.
* **File Management:** Saves the generated markdown files and automatically copies them to your specified plugin source directory.

## Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/LogicOber/dify-plugin-automation.git
   cd dify-plugin-helper
   ```
2. **Install Dependencies:**
   Make sure you have Python 3 installed. Then, install the required packages:

   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment:**

   * Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   * Edit the `.env` file:
     * Set `DIFY_BASE_URL` to your Dify instance's API base URL (default is `https://api.dify.ai/v1`).
     * **Crucially, you need to set `DIFY_API_KEY`.** See the next step on how to obtain this.
4. **Import Dify Application & Get API Key:**

   * Go to your Dify instance.
   * Import the application definition file located at `dify-dsl/"Dify Plugin README & Privacy Generator.yml"` into your Dify workspace. This will create the necessary LLM application.
   * Navigate to the settings of the newly imported application within Dify.
   * Generate an API Key for this specific application.
   * Copy this API key and paste it into your `.env` file as the value for `DIFY_API_KEY`.

## Usage

1. **Run the Generator Script:**
   Open your terminal in the root directory of this project (`dify-plugin-helper`) and run:

   ```bash
   python assistant/readme_privacy_generator.py
   ```
2. **Enter Plugin Path:**
   The script will prompt you to enter the path to your Dify plugin's root directory.

    **Important:** Provide the path to your plugin's source code directory (the one containing `plugin.yaml`), *not* a packaged `.dify-pkg` file. Press Enter after typing the path.

3.  **Enter Optional Prompts (Optional):**
    The script will then ask for any additional instructions or prompts you want to give to the language model.

    If you have specific requirements for the README or Privacy Policy content, you can type them here. If not, simply press Enter to skip this step.

1. **Generation and Output:**
   The script will now communicate with the Dify API to generate the `README.md` and `PRIVACY.md` files. Upon completion, you'll see status messages, and the generated files will be automatically copied into the plugin directory path you provided in Step 2.

## Contributor

* **Lyson Ober**
  * X (Twitter): [https://x.com/lyson_ober](https://x.com/lyson_ober)

## Future Development

Stay tuned for more tools and features to streamline Dify.AI plugin development!
