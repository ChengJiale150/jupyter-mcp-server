# 🛠️ Tool Usage Guide

This document provides a detailed introduction to all the tools offered by the Jupyter MCP Server, aiming to help users understand and use these tools to interact with Jupyter Notebooks.

## Notebook Management Module

### `connect_notebook`

- **Function**: Connects to or creates a Notebook at a specified path.
- **Output**: Upon successful connection or creation, it returns basic information about the Notebook's cells (e.g., cell index, type, first line of content).
- **Important Notes**:
    - You must provide the Jupyter service connection parameters (URL and Token) in the prompt; otherwise, the tool will not work correctly.
    - `notebook_name` is a unique identifier for different Notebooks and must be unique.
    - This tool may take a long time to execute (10-30 seconds) as it needs to start a Jupyter Kernel.
    - If using `connect` mode, the Notebook path must exist.
    - If using `create` mode, the Notebook path must not exist.
    - If using `reconnect` mode, the Notebook path must be the same as the previously connected Notebook path.
    - Connection information can be saved, but connected Notebooks will be lost after the MCP server restarts and will need to be reconnected.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `server_url` | `str` | The URL where the Jupyter service is running. | |
| `token` | `str` | The token for Jupyter service authentication. | |
| `notebook_name` | `str` | A unique name to identify the Notebook. | |
| `notebook_path` | `str` | The relative path to the Notebook. | |
| `mode` | `Literal["connect", "create", "reconnect"]` | The connection mode. `connect` is for existing Notebooks, `create` is for new ones, `reconnect` is for reconnecting to an existing Notebook. | `"connect"` |

---

### `list_notebook`

- **Function**: Lists all currently connected Notebooks.
- **Output**: Returns a table with the names, Jupyter URL addresses, and paths of all connected Notebooks.
- **Important Notes**: Used to view connected Notebooks, making it easier for the AI to switch and operate between multiple Notebooks.
- **Parameters**: None.

---

### `restart_notebook`

- **Function**: Restarts the kernel of a specified Notebook, which clears all imported packages and defined variables.
- **Output**: Returns a message indicating the result of the restart.
- **Important Notes**: Use this when the kernel is unresponsive or when you need to reset the environment.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook to restart. | |

---

### `read_notebook`

- **Function**: Reads the source content (without output) of a connected Notebook.
- **Output**: Returns the source content of the Notebook (including index, type, execution count, and full source code).
- **Important Notes**: Only used when the user explicitly instructs to read the full content of the Notebook.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook to read. | |

## Basic Cell Function Module

### `list_cell`

- **Function**: Lists basic information for all cells in a specified Notebook.
- **Output**: Basic information about the Notebook's cells (e.g., cell index, type, execution count, first line of content).
- **Important Notes**:
    - Used for a quick overview of the Notebook's structure and status, and to locate the index and content type of specific cells.
    - To save on token consumption, only the first line of content is returned. It is recommended to include enough information in the first line (e.g., the purpose of the cell) to help the AI locate specific cells.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |

---

### `read_cell`

- **Function**: Reads the content of a cell at a specified index in a Notebook.
- **Output**: Returns the cell's source code, execution count, and multimodal output (e.g., text, images) as a list.
- **Important Notes**:
    - Supports reading all content of a cell block and can be used with the `list_cell` tool to help the AI understand the detailed content of a cell.
    - You can configure whether to return the Base64 encoded string of the cell's image in `src/config.toml`. It is returned by default.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_index` | `int` | The index of the cell to read. | |
| `return_output` | `bool` | Whether to include the cell's output. | `True` |

---

### `delete_cell`

- **Function**: Deletes a cell at a specified index in a Notebook.
- **Output**: Returns the latest structure information of the Notebook after deletion.
- **Important Notes**:
    - Since this operation directly modifies the Notebook's structure, it is not recommended to delete multiple cells at once to avoid accidental deletion.
    - If you must delete multiple cells, explicitly tell the AI to delete them in descending order of their indices.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_index` | `int` | The index of the cell to delete. | |

---

### `insert_cell`

- **Function**: Inserts a new cell above or below a specified index in a Notebook.
- **Output**: Returns the latest structure information of the Notebook after insertion.
- **Important Notes**:
    - Since this operation directly modifies the Notebook's structure, it is not recommended to insert multiple cells at once to avoid confusion in the insertion order.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_index` | `int` | The index of the anchor cell. | |
| `cell_type` | `Literal["code", "markdown"]` | The type of cell to insert. | |
| `cell_content` | `str` | The content of the cell to insert. | |
| `direction` | `Literal["above", "below"]` | Whether to insert `above` or `below` the anchor index. | `"below"` |

---

### `execute_cell`

- **Function**: Executes a cell at a specified index in a Notebook (only for `code` type).
- **Output**: Returns the output of the cell, with support for multimodal output. If execution times out, a timeout error message is returned.
- **Important Notes**: Includes a timeout parameter to prevent indefinite waiting due to an unresponsive kernel.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_index` | `int` | The index of the cell to execute. | |
| `timeout` | `int` | The execution timeout in seconds. | `60` |

---

### `overwrite_cell`

- **Function**: Overwrites (modifies) the content of a cell at a specified index in a Notebook.
- **Output**: Returns a comparison (diff style, `+` for new lines, `-` for deleted lines) of the cell's content.
- **Important Notes**: Used to modify the code or text of an existing cell.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_index` | `int` | The index of the cell to overwrite. | |
| `cell_content` | `str` | The new content for the cell. | |

## Advanced Integrated Cell Function Module

### `append_execute_cell`

- **Function**: Adds a new cell to the end of a Notebook and immediately executes it.
- **Output**: Returns the output of the cell after execution, with support for multimodal output. If execution times out, a timeout error message is returned.
- **Important Notes**: This is a high-frequency operation, equivalent to a combination of `insert_cell` (at the end) and `execute_cell`, designed to reduce the number of tool calls.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_type` | `Literal["code", "markdown"]` | The type of cell to add. | |
| `cell_content` | `str` | The content of the cell to add. | |
| `timeout` | `int` | The execution timeout in seconds. | `60` |

---

### `execute_temporary_cell`

- **Function**: Executes a temporary block of code whose content is not saved to the Notebook.
- **Output**: The output from the kernel after execution, with support for multimodal output.
- **Important Notes**:
    - Interacts directly with the kernel and is not added to the Notebook.
    - **Use Cases**:
        - Executing magic commands (e.g., `%pip install`).
        - Debugging code snippets.
        - Checking the values of intermediate variables (e.g., `print(df.head())`).
    - **Prohibited**:
        - Importing new modules or assigning variables that would affect subsequent Notebook execution.
        - Executing code that requires a long time to run.
- **Parameters**:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | The name of the Notebook. | |
| `cell_content` | `str` | The content of the code to be executed temporarily. | |
