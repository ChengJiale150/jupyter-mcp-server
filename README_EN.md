<div align="center">

<!-- omit in toc -->

# 🪐 Jupyter MCP Server

<img title="cover" src="https://raw.githubusercontent.com/ChengJiale150/jupyter-mcp-server/main/assets/cover.png" alt="Jupyter MCP Server" data-align="center" width="700">

**An MCP service specifically developed for AI to connect and manage Jupyter Notebooks**

*Developed by [ChengJiale150](https://github.com/ChengJiale150)*

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/better-jupyter-mcp-server.svg)](https://pypi.org/project/better-jupyter-mcp-server/)
[![mcp-registry](https://img.shields.io/badge/mcp--registry-v1.1.0-blue)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.ChengJiale150/jupyter-mcp-server)

English | [中文](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/README.md)

</div>

## 📖 Table of Contents

- [Project Introduction](#-project-introduction)
- [Tools Overview](#-tools-overview)
- [Quick Start](#-quick-start)
- [Best Practices](#-best-practices)
- [Contribution Guidelines](#-contribution-guidelines)
- [Acknowledgements](#-acknowledgements)

## 🎯 Project Introduction

Jupyter MCP Server is a service based on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), providing the most advanced AI IDEs (like [Cursor](https://www.cursor.com/)) and CLI tools (like [Gemini CLI](https://github.com/google-gemini/gemini-cli)) with the ability to connect and manage Jupyter Notebooks. This enables AI to operate Notebooks for tasks such as data analysis, visualization, and machine learning.

### 🤔 Why Jupyter MCP Server?

Jupyter Notebook is one of the most common tools for data scientists, offering an interactive environment for exploratory tasks like data analysis, visualization, and machine learning. However, due to the format limitations of Notebooks, they are not as easily understood by AI as plain text files (like Markdown or Python files).

Existing tools or MCP services for operating Notebooks either only support reading and editing or can only manipulate a single Notebook, making it difficult to meet the complex demands of managing multiple Notebooks simultaneously. Furthermore, most tools do not support multimodal output, failing to fully leverage the powerful image and text understanding capabilities of advanced multimodal large models (like Gemini 2.5).

Jupyter MCP Server was developed to address this issue. Through the MCP protocol, it provides AI with tools to manage Jupyter Kernels and Notebooks, enabling it to handle **multiple Notebooks** for **interactive** task execution and output **multimodal** results, helping data scientists improve their analysis efficiency.

### ✨ Key Highlights

- 🔌 **MCP Compatible**: Can be used in any IDE or CLI tool that supports the MCP protocol.
- 📚 **Multi-Notebook Management**: Supports managing multiple Notebooks at the same time.
- 🔁 **Interactive Execution**: Can automatically adjust execution strategies based on cell output.
- 📊 **Multimodal Output**: Supports outputting multimodal results, such as text, images, tables, etc.

## 🔧 Tools Overview

### Notebook Management Module

| Name | Description | Notes |
|:---:|:---:|:---:|
| connect_notebook | Connect/create a Notebook at a specified path | Tool execution time is long (10s~30s) due to Kernel startup. |
| list_notebook | List all currently connected Notebooks | Used to view currently connected Notebooks for multi-Notebook tasks. |
| restart_notebook | Restart a specified Notebook | Clears all imported packages and variables. |
| read_notebook | Read the source content (without output) of a connected Notebook | Used to view the source content of the Notebook, only used when the user explicitly instructs to read the full content of the Notebook. |

### Basic Cell Function Module

| Name | Description | Notes |
|:---:|:---:|:---:|
| list_cell | List basic information of all cells in a specified Notebook | Used to locate cell index and purpose. |
| read_cell | Read the content of a specific cell in a specified Notebook | Supports various outputs like images, tables, text, etc. |
| delete_cell | Delete a specific cell in a specified Notebook | |
| insert_cell | Insert a cell above/below a specific index in a specified Notebook | |
| execute_cell | Execute a specific cell in a specified Notebook | Returns the output of the cell. |
| overwrite_cell | Overwrite the content of a specific cell in a specified Notebook | Used to modify cell content. |

### Advanced Integrated Cell Function Module

| Name | Description | Notes |
|:---:|:---:|:---:|
| append_execute_code_cell | Add and execute a code cell at the end of a Notebook | A combination of insert+execute for frequent operations, reducing tool calls. |
| execute_temporary_code | Execute a temporary code block (not saved to the Notebook) | Used for magic commands, code snippet debugging, viewing intermediate variables, etc. |

For more details on the tools, please see the [Tools Documentation](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/tools_EN.md).

## 🛠️ Quick Start

### Prerequisites

- Python 3.12+ (recommended to use [Anaconda](https://www.anaconda.com/))
- uv (for installation, see the [Installation Guide](https://docs.astral.sh/uv/getting-started/installation/))

### Installing Jupyter MCP Server

<details>
<summary>uvx Quick Installation (Recommended)</summary>

After installing uv, configure the MCP JSON format directly, as shown below:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uvx",
            "args": [
                "better-jupyter-mcp-server"
            ],
            "env": {
                "ALLOW_IMG": "true"
            },
            "transport": "stdio"
        }
    }
}
```

For specific client integration, please see the [Integration Documentation](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/integration_EN.md).

</details>

<details>
<summary>Source Code</summary>

1.  **Clone the project and install dependencies**

    ```bash
    git clone https://github.com/ChengJiale150/jupyter-mcp-server
    cd jupyter-mcp-server
    uv sync
    ```

2.  **(Optional) Configure config.toml**

    Go to the `src/config.toml` file and configure parameters as needed (e.g., whether to allow returning image data).

3.  **Start Jupyter MCP Server**

    ```bash
    uv run fastmcp run src/main.py
    ```

    If it starts successfully, you will see output similar to this:

    ```bash
    [09/14/25 20:14:59] INFO     Starting MCP server 'Jupyter-MCP-Server' with transport 'stdio'
    ```

4.  **Configure Standard JSON Format**

    ```json
    {
        "mcpServers":{
            "Jupyter-MCP-Server":{
                "command": "uv",
                "args": [
                    "run",
                    "--directory",
                    "your/path/to/jupyter-mcp-server",
                    "src/main.py"
                ],
                "env": {},
                "transport": "stdio"
            }
        }
    }
    ```

    For specific client integration, please see the [Integration Documentation](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/integration_EN.md).

</details>

### Using Jupyter MCP Server

<details>

<summary>Manually Start Jupyter Server Locally</summary>

Before formal use, you need to connect to a Jupyter Server. Here is how to start a Jupyter Server locally:

1. **Open a terminal and activate the environment**:

    Open your computer's terminal command line and activate the environment.

    For conda (Anaconda) users, you can use the following command to activate the environment:

    ```bash
    conda activate your_environment_name
    ```

    For convenience, you can use the `base` environment (`conda activate base`).

    Then switch to your current project directory for easier file operations.

    ```bash
    cd your/path/to/your/project
    ```

2. **Install necessary dependencies**:

    ```bash
    pip uninstall -y pycrdt datalayer_pycrdt
    pip install jupyter nbformat datalayer_pycrdt jupyter-collaboration
    ```

3. **Start Jupyter Server**:

    Use the following command to start the Jupyter Server.

    ```bash
    jupyter lab
    ```

    After a successful start, a browser window will pop up. You can check if the root path is your project directory.

4. **Get Authentication Token**:

    Use the following command to get the authentication token.

    ```bash
    jupyter server list
    ```

    The output will be similar to this:

    ```bash
    http://localhost:8888/?token=YOUR_TOKEN :: YOUR_PROJECT_PATH
    ```

    Where `YOUR_TOKEN` is the authentication token.

5. **Add Prompt and Rules**

    Before formal use, you **must** add the following prompt to your rules file to provide the necessary connection information for Jupyter MCP Server:

    ```
    Here are the Jupyter server connection parameters:
    URL = http://localhost:8888
    Token = YOUR_TOKEN
    ```

    Additionally, it is recommended to add key Notebook path information to the prompt to help the AI quickly locate the target Notebook and improve the execution efficiency of the `connect_notebook` tool. You can right-click the target Notebook file in Jupyter Lab and select `Copy Path` to get the relative path.

    After providing the above content, you can start using Jupyter MCP Server!

</details>

<details>

<summary>Use LLM to Manage Jupyter Server</summary>

1. **Install necessary dependencies**:

    ```bash
    pip uninstall -y pycrdt datalayer_pycrdt
    pip install jupyter nbformat datalayer_pycrdt jupyter-collaboration
    ```

2. **Provide prompt and rules documentation**:

```markdown
## Jupyter MCP Server Usage Guide

Before using Jupyter MCP Server, you **must** complete the following steps:

1. **Start Jupyter Server**:

    In the current project directory, use the following command to start the Jupyter Server in a way that does not block the current terminal, for example:

    - `Window`: `start jupyter lab`
    - `MacOS/Linux`: `nohup jupyter lab &`

2. **Get URL and Authentication Token**:

    Use `jupyter server list` to get the URL and authentication token.

    ONLY when completing the above steps, you can use Jupyter MCP Server.
```

</details>

## ✅ Best Practices

- Interact with a large model that supports multimodal input (like Gemini 2.5 Pro) to fully utilize advanced multimodal understanding capabilities.
- Use a client that supports returning image data via the MCP protocol and can parse it (like Cursor, Gemini CLI, etc.), as some clients may not support this feature.
- Break down complex tasks (like data science modeling) into multiple sub-tasks (like data cleaning, feature engineering, model training, model evaluation, etc.) and execute them step-by-step.
- Provide clearly structured prompts and rules. You can refer to the [Prompt and Rules Documentation](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/prompt_example_EN.md).
- Incorporate **expert experience and wisdom** (such as data cleaning and feature engineering techniques) into your prompts, as this is what AI lacks most and needs to be supplemented.
- Provide as much context as possible (such as field explanations for existing datasets, file paths, detailed task requirements, etc.).
- Provide Few Shot examples, provide Baseline or existing Workflow as a reference.

### Examples

- [Titanic Data Analysis](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/example/Titanic)

## 🤝 Contribution Guidelines

We welcome community contributions! If you would like to contribute to the Jupyter MCP Server project, please:

1.  Fork this repository
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

### Types of Contributions

- 🐛 Bug fixes
- 📝 Improvements to existing features
- ✨ New feature development
- 📚 Documentation improvements
- 🌍 Internationalization support

### Development Help Documentation

- You can refer to the [Project Architecture Document](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/src/README_EN.md) to help understand the project architecture and key communication flows.

## 🤗 Acknowledgements

This project has been helped by the following projects, and we would like to express our gratitude:

- [DataLayer](https://github.com/datalayer): Thanks to DataLayer for open-sourcing the [jupyter_nbmodel_client](https://github.com/datalayer/jupyter-nbmodel-client) and [jupyter_kernel_client](https://github.com/datalayer/jupyter-kernel-client) libraries, which greatly helped the rapid development of Jupyter MCP.
- [FastMCP](https://github.com/jlowin/fastmcp): Thanks to the developers of FastMCP. Without FastMCP, the rapid integration of Jupyter MCP would not have been possible.

In addition, this project also referenced the implementations of the following existing Jupyter MCP services, and we would like to thank them as well:

- [datalayer/jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)
- [jjsantos01/jupyter-notebook-mcp](https://github.com/jjsantos01/jupyter-notebook-mcp)
- [ihrpr/mcp-server-jupyter](https://github.com/ihrpr/mcp-server-jupyter)
- [itisaevalex/jupyter-mcp-extended](https://github.com/itisaevalex/jupyter-mcp-extended)

---

<div align="center">

**If this project is helpful to you, please give us a ⭐️**

Made with ❤️ by [ChengJiale150](https://github.com/ChengJiale150)

</div>
