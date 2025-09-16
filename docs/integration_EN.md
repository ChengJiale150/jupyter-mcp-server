# Configure Necessary Paths

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

## Step 1: Confirm Your File Path

First, we need to confirm the path to the Jupyter MCP Server project to replace `"your/path/to/jupyter-mcp-server"` in the reference configuration above.

### File Explorer

<details>
<summary> Windows 11</summary>

In `File Explorer`, find the folder for the Jupyter MCP Server, and press the shortcut `ctrl+shift+C` to copy the file path. A reference path is as follows:

```bash
C:\Users\username\Desktop\MCP\jupyter-mcp-server
```

At this point, you need to replace the `\` in the path with `\\`. The final path will look like this:

```bash
C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server
```

Finally, replace the file path in the reference JSON format with the copied path. An example is as follows:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

<details>
<summary>MacOS</summary>

In `Finder`, find the folder for the Jupyter MCP Server, and press the shortcut `option+command+c` to copy the file path. A reference path is as follows:

```bash
/Users/username/Documents/mcp/jupyter-mcp-server
```

Finally, replace the file path in the reference JSON format with the copied path. An example is as follows:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "/Users/username/Documents/mcp/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

### Terminal

<details>
<summary> Windows CMD</summary>

In the terminal at the corresponding path, enter the following command:

```bash
echo %cd%
```

A reference output path is as follows:

```bash
C:\Users\username\Desktop\MCP\jupyter-mcp-server
```

At this point, you need to replace the `\` in the path with `\\`. The final path will look like this:

```bash
C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server
```

Finally, replace the file path in the reference JSON format with the copied path. An example is as follows:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

<details>
<summary> MacOS/Linux</summary>

In the terminal at the corresponding path, enter the following command:

```bash
pwd
```

A reference output path is as follows:

```bash
/Users/username/Documents/mcp/jupyter-mcp-server
```

Finally, replace the file path in the reference JSON format with the copied path. An example is as follows:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "/Users/username/Documents/mcp/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

## Step 2: Add the MCP Service in the Corresponding Client

Next, add the MCP service to the MCP configuration file in the corresponding client.

<details>

<summary> Cursor</summary>

In the upper right corner of Cursor, open `Cursor Settings` (⚙ icon), select `Tool & Integrations`, and click `New MCP Server` in `MCP Tools`. This will take you to the `mcp.json` file. An example result is as follows:

```json
{
  "mcpServers": {
    ...(existing MCPs, empty if none)
  }
}
```

Paste the completed JSON file after the existing MCPs. The final reference result is as follows:

```json
{
  "mcpServers": {
    ...(existing MCPs, empty if none),
    "Jupyter-MCP-Server" : {
        ...(the content from above)
    }
  }
}
```

Finally, save and close the `mcp.json` file. Go back and check if an MCP service named `Jupyter-MCP-Server` appears in `MCP Tools`. Wait a moment, and if the yellow light turns green, it means the MCP service has started successfully.

</details>

<details>

<summary> Trae</summary>

Open the AI function management button (⚙ icon) on the side of the application, select `MCP`, click `Import from JSON` under `Manual Add`, and enter the following content:

```json
{
  "mcpServers": {
    "Jupyter-MCP-Server" : {
        ...(the content from above)
    }
  }
}
```

Click confirm, open the corresponding MCP server, and check if the connection is successful.

</details>

<details>

<summary> Cline</summary>

At the bottom of the conversation, open `Manager MCP Servers`, click the settings button (⚙ icon), select `Installed`, and click `Configure MCP Servers`. This will take you to the `cline_mcp_settings.json` file. An example result is as follows:

```json
{
  "mcpServers": {
    ...(existing MCPs, empty if none)
  }
}
```

Add a `,` (comma) after the existing MCPs (if any), and then paste the completed JSON file. The final reference result is as follows:

```json
{
  "mcpServers": {
    ...(existing MCPs, empty if none),
    "Jupyter-MCP-Server" : {
        ...(the content from above)
    }
  }
}
```

Finally, save and close the `cline_mcp_settings.json` file. Go back and check if an MCP service named `Jupyter-MCP-Server` appears. Start it and wait a moment. If it turns green, it means the MCP service has started successfully.

</details>

<details>

<summary> Gemini CLI</summary>

You can also input the following command in the terminal:

```bash
gemini mcp add Jupyter-MCP-Server uv run --directory your/path/to/jupyter-mcp-server src/server.py
```

Or you can also add the following content to the `settings.json` file in the `.gemini` folder of your project:

```json
{
    ...(existing configurations, empty if none),
    "mcpServers":{
        ...(existing MCPs, empty if none),
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {}
        }
    }
}
```

</details>

<details>

<summary> Qwen Coder</summary>

You can also input the following command in the terminal:

```bash
qwen mcp add Jupyter-MCP-Server uv run --directory your/path/to/jupyter-mcp-server src/server.py
```

Or you can also add the following content to the `settings.json` file in the `.qwen` folder of your project:

```json
{
    ...(existing configurations, empty if none),
    "mcpServers":{
        ...(existing MCPs, empty if none),
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {}
        }
    }
}
```

</details>

<details>

<summary> Claude Code</summary>

You can also input the following command in the terminal:

```bash
claude mcp add Jupyter-MCP-Server uv run --directory your/path/to/jupyter-mcp-server src/server.py
```

</details>