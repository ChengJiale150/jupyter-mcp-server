import asyncio, difflib, os
from fastmcp import FastMCP
from pathlib import Path
from typing import Annotated, Literal
from mcp.types import ImageContent

# 设置环境变量以避免Jupyter平台目录警告
# Set environment variable to avoid Jupyter platform directory warnings
os.environ.setdefault("JUPYTER_PLATFORM_DIRS", "1")

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient
from jupyter_server_api import JupyterServerClient,NotFoundError
from .utils import list_cell_basic, Cell, format_table, format_notebook, NotebookManager
from . import __version__

mcp = FastMCP(name="Jupyter-MCP-Server", version=__version__)

# 用于管理不同notebook的kernel
# Used to manage different notebooks' kernels
notebook_manager = NotebookManager()

#===========================================
# Notebook管理模块(4个)
# Notebook management module (4)
#===========================================
@mcp.tool(tags={"core","notebook","connect_notebook"})
async def connect_notebook(
    server_url: Annotated[str, "Jupyter server URL (e.g., http://localhost:8888)"], 
    token: Annotated[str, "Jupyter authentication token"], 
    notebook_name: Annotated[str, "Unique identifier, used to reference this notebook in subsequent operations"],
    notebook_path: Annotated[str, "Path to the notebook file relative to Jupyter server root (e.g., './analysis.ipynb')"],
    mode: Annotated[
        Literal["connect", "create", "reconnect"], 
        "`connect`: connect to an existing notebook; `create`: create a new notebook (not exist) and connect; `reconnect`: reconnect to an existing notebook"
        ] = "connect") -> str:
    """
    Connect to a notebook and corresponding kernel. 
    It is the FIRST STEP before ANY subsequent operations.
    """
    # 检查notebook是否已经连接
    # Check if the notebook is already connected
    if notebook_name in notebook_manager:
        if mode == "reconnect":
            if notebook_manager.get_notebook_path(notebook_name) == notebook_path:
                notebook_manager.remove_notebook(notebook_name)
            else:
                return f"{notebook_name} should be connected to {notebook_manager.get_notebook_path(notebook_name)} not {notebook_path}!"
        elif notebook_manager.get_notebook_path(notebook_name) == notebook_path:
            return f"{notebook_name} is already connected, please do not connect again"
        else:
            return f"{notebook_name} is already connected to {notebook_manager.get_notebook_path(notebook_name)}, please rename it"
    
    # Check if Jupyter are running normally
    server_client = JupyterServerClient(base_url=server_url, token=token)
    try:
        server_client.get_status()
    except Exception as e:
        return f"""Jupyter environment connection failed! 
        Error as below: 
        ```
        {str(e)}
        ```
        
        Please check: 
        1. Jupyter environment is successfully started 
        2. URL address is correct and can be accessed normally
        3. Token is correct
        """
    
    # Check if notebook path exists
    path = Path(notebook_path)
    try:
        # For relative paths starting with just filename, assume current directory
        parent_path = path.parent.as_posix() if path.parent.as_posix() != "." else ""
        
        if parent_path:
            dir_contents = server_client.contents.list_directory(parent_path)
        else:
            # Check in the root directory of Jupyter server
            dir_contents = server_client.contents.list_directory("")
            
        if mode == "connect":
            file_exists = any(file.name == path.name for file in dir_contents)
            if not file_exists:
                return f"'{notebook_path}' not found in jupyter server, please check the notebook already exists."
    except NotFoundError:
        parent_dir = path.parent.as_posix() if path.parent.as_posix() != "." else "root directory"
        return f"'{parent_dir}' not found in jupyter server, please check the directory path already exists."
    except Exception as e:
        return f"Failed to check the path '{notebook_path}': {e}"
    
    # Create notebook
    if mode == "create":
        content = {
            "cells": [{
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "Overwrite this cell with Notebook Metadata",
                ]
            }],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        server_client.contents.create_notebook(notebook_path, content)
    
    # Create kernel client
    kernel = KernelClient(
        server_url=server_url,
        token=token,
    )
    kernel.start(path=parent_path)

    # Try to connect to the notebook
    try:
        ws_url = get_jupyter_notebook_websocket_url(server_url=server_url, token=token, path=notebook_path)
        async with NbModelClient(ws_url) as notebook:
            list_info = list_cell_basic(notebook, limit=20)
    except Exception as e:
        kernel.stop()
        return f"Notebook connection failed! Error: {e}"
    
    # Connection successful, save the kernel and notebook information to notebook_manager
    notebook_manager.add_notebook(notebook_name, kernel, server_client, server_url, token, notebook_path)
    return_info = f"{notebook_name} connection successful!\n{list_info}"
    return return_info

@mcp.tool(tags={"core","notebook","list_notebook"})
async def list_notebook() -> str:
    """
    List all currently connected Notebooks.
    It will return unique name, Jupyter URL and Path of all connected Notebooks
    """
    if notebook_manager.is_empty():
        return "No notebook is currently connected"
    
    headers = ["Name", "Jupyter URL", "Path"]
    
    rows = []
    for notebook_name, notebook_info in notebook_manager:
        notebook_path = notebook_info["notebook"]["path"]
        server_url = notebook_info["notebook"]["server_url"]
        rows.append([notebook_name, server_url, notebook_path])
    
    table = format_table(headers, rows)
    
    return table

@mcp.tool(tags={"core","notebook","restart_notebook"})
async def restart_notebook(
    notebook_name: str) -> str:
    """
    Restart the kernel of a specified Notebook, clear all imported packages and variables
    """
    if notebook_name not in notebook_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    if notebook_manager.restart_notebook(notebook_name):
        return f"{notebook_name} restart successful"
    else:
        return f"Failed to restart {notebook_name}"

@mcp.tool(tags={"core","notebook","read_notebook"})
async def read_notebook(
    notebook_name: str,
    start_index: Annotated[int, "Starting cell index (0-based) for pagination"] = 0,
    limit: Annotated[int, "Maximum number of cells to return (0 means no limit)"] = 20) -> str:
    """
    Read the source content (without output) of a connected Notebook.
    It will return the formatted content of the Notebook (including Index, Cell Type, Execution Count and Full Source Content).
    ONLY used when the user explicitly instructs to read the full content of the Notebook.
    """
    if notebook_name not in notebook_manager:
        return "Notebook does not exist, please connect it first"

    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        total_cells = len(notebook)
        if start_index < 0 or start_index >= total_cells:
            return f"Start index {start_index} out of range, Notebook has {total_cells} cells"
        
        end_index = min(start_index + limit, total_cells) if limit > 0 else total_cells
        
        cells = [Cell(notebook[i]) for i in range(start_index, end_index)]
        formatted_content = format_notebook(cells, start_index, total_cells)
    
    return formatted_content

#===========================================
# Cell基本功能模块(6个)
# Basic Cell Function Module (6)
#===========================================

@mcp.tool(tags={"core","cell","list_cell"})
async def list_cell(
    notebook_name: str,
    start_index: Annotated[int, "Starting cell index (0-based) for pagination"] = 0,
    limit: Annotated[int, "Maximum number of cells to return (0 means no limit)"] = 50) -> str:
    """
    List the basic information of cells.
    It will return Index, Type, Execution Count and First Line of the Cell.
    It will be used to quickly overview the structure and current status of the Notebook or locate the index of specific cells for following operations(e.g. delete, insert).
    """
    if notebook_name not in notebook_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook: 
        table = list_cell_basic(notebook, with_count=True, start_index=start_index, limit=limit)
    
    return table

@mcp.tool(tags={"core","cell","read_cell"})
async def read_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"],
    return_output: Annotated[bool, "Whether to return output"] = True) -> list[str | ImageContent]:
    '''
    Read the detailed content of a specific cell.
    It will return the source code, execution count and output of the cell.
    '''
    if notebook_name not in notebook_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        if cell_index < 0 or cell_index >= len(notebook):
            return [f"Cell index {cell_index} out of range, Notebook has {len(notebook)} cells"]
        
        cell = Cell(notebook[cell_index])
        if cell.type == "markdown":
            result = [cell.source]
        elif cell.type == "code":
            result = [
                cell.source,
                f"Current execution count: {cell.execution_count}"
            ]
            if return_output:
                result.extend(cell.get_outputs())
        else:
            result = cell.source
            
    return result

@mcp.tool(tags={"core","cell","delete_cell"})
async def delete_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"]) -> str:
    """
    Delete a specific cell.
    When deleting many cells, MUST delete them in descending order of their index.
    """
    if notebook_name not in notebook_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        if cell_index < 0 or cell_index >= len(notebook):
            return f"Cell index {cell_index} out of range, Notebook has {len(notebook)} cells"
        
        deleted_cell_content = Cell(notebook.delete_cell(cell_index)).source
        # Get surrounding cells info (5 above and 5 below the deleted position)
        total_cells = len(notebook)
        if total_cells > 0:
            limit = min(10, total_cells)
            # Adjust start_index if we're near the end
            start_index = max(0, cell_index - 5) 
            if start_index + limit > total_cells:
                start_index = max(0, total_cells - limit)
            surrounding_info = list_cell_basic(notebook, with_count=True, start_index=start_index, limit=limit)
        else:
            surrounding_info = "Notebook is now empty, no cells remaining"

    return f"Delete successful!\nDeleted cell content:\n{deleted_cell_content}\nSurrounding cells information:\n{surrounding_info}"

@mcp.tool(tags={"core","cell","insert_cell"})
async def insert_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index to insert at (0-based)"],
    cell_type: Literal["code", "markdown"],
    cell_content: str) -> str:
    """
    Insert a cell at the specified index.
    When inserting many cells, MUST insert them in ascending order of their index.
    """
    if notebook_name not in notebook_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        if cell_index < 0 or cell_index > len(notebook):
            return f"Cell index {cell_index} out of range, Notebook has {len(notebook)} cells"
        
        notebook.insert_cell(cell_index, cell_content, cell_type)
        # Get surrounding cells info (5 above and 5 below the inserted position)
        total_cells = len(notebook)
        limit = min(10, total_cells)
        # Adjust start_index if we're near the end
        start_index = max(0, cell_index - 5)
        if start_index + limit > total_cells:
            start_index = max(0, total_cells - limit)
        surrounding_info = list_cell_basic(notebook, with_count=True, start_index=start_index, limit=limit)

    return f"Insert successful!\nSurrounding cells information:\n{surrounding_info}"

@mcp.tool(tags={"core","cell","execute_cell"})
async def execute_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"],
    timeout: Annotated[int, "seconds"] = 60) -> list[str | ImageContent]:
    """
    Execute a specific cell with a timeout.
    It will return the output of the cell.
    """
    if notebook_name not in notebook_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        if cell_index < 0 or cell_index >= len(notebook):
            return [f"Cell index {cell_index} out of range, Notebook has {len(notebook)} cells"]
        
        if Cell(notebook[cell_index]).type != "code":
            return [f"Cell index {cell_index} is not code, need to execute a code cell"]
        
        kernel = notebook_manager.get_kernel(notebook_name)
        execution_task = asyncio.create_task(
            asyncio.to_thread(notebook.execute_cell, cell_index, kernel)
        )
        
        try:
            await asyncio.wait_for(execution_task, timeout=timeout)
        except asyncio.TimeoutError:
            execution_task.cancel()
            if kernel and hasattr(kernel, 'interrupt'):
                kernel.interrupt()
            return [f"[TIMEOUT ERROR: Cell execution exceeded {timeout} seconds]"]
        
        # Get cell outputs within the context manager while notebook is still connected
        cell = Cell(notebook[cell_index])
        outputs = cell.get_outputs()
    
    return outputs

@mcp.tool(tags={"core","cell","overwrite_cell"})
async def overwrite_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"],
    cell_content: str) -> str:
    """
    Overwrite the content of a specific cell
    It will return a comparison (diff style, `+` for new lines, `-` for deleted lines) of the cell's content.
    """
    if notebook_name not in notebook_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        if cell_index < 0 or cell_index >= len(notebook):
            return f"Cell index {cell_index} out of range, Notebook has {len(notebook)} cells"
        
        raw_content = Cell(notebook[cell_index]).source
        notebook.set_cell_source(cell_index, cell_content)
        
        diff = difflib.unified_diff(raw_content.splitlines(keepends=False), cell_content.splitlines(keepends=False))
        diff = "\n".join(list(diff)[3:])

    return f"Overwrite successful!\n\n```diff\n{diff}\n```"

#===========================================
# Cell高级集成功能模块(2个)
# Advanced Integrated Cell Function Module (2)
#===========================================

@mcp.tool(tags={"advanced","cell","append_execute_code_cell"})
async def append_execute_code_cell(
    notebook_name: str,
    cell_content: str,
    timeout: Annotated[int, "seconds"] = 60) -> list[str | ImageContent]:
    """
    Add a new code cell to the end of a Notebook and immediately execute it.
    It is highly recommended for replacing the combination of `insert_cell` and `execute_cell` for a code cell at the end of the Notebook.
    It will return the output of the cell.
    """
    if notebook_name not in notebook_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    async with notebook_manager.get_notebook_connection(notebook_name) as notebook:
        cell_index = notebook.add_code_cell(cell_content)
        kernel = notebook_manager.get_kernel(notebook_name)
        execution_task = asyncio.create_task(
            asyncio.to_thread(notebook.execute_cell, cell_index, kernel)
        )
        
        try:
            await asyncio.wait_for(execution_task, timeout=timeout)
        except asyncio.TimeoutError:
            execution_task.cancel()
            if kernel and hasattr(kernel, 'interrupt'):
                kernel.interrupt()
            return [f"[TIMEOUT ERROR: Cell execution exceeded {timeout} seconds]"]
        
        cell = Cell(notebook[cell_index])
        
        return [f"Cell index {cell_index} execution successful!"] + cell.get_outputs()

@mcp.tool(tags={"advanced","cell","execute_temporary_code"})
async def execute_temporary_code(
    notebook_name: str,
    cell_content: str) -> list[str | ImageContent]:
    """
    Execute a temporary code block (not saved to the Notebook) and will return the output.
    
    It will recommend to use in following cases:
    1. Execute Jupyter magic commands(e.g., `%timeit`, `%pip install xxx`)
    2. Debug code
    3. View intermediate variable values(e.g., `print(xxx)`, `df.head()`)
    4. Perform temporary statistical calculations(e.g., `np.mean(df['xxx'])`)
    
    DO NOT USE IN THE FOLLOWING CASES:
    1. Import new modules and perform variable assignments that affect subsequent Notebook execution
    2. Run code that requires a long time to run
    """
    if notebook_name not in notebook_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    kernel = notebook_manager.get_kernel(notebook_name)
    cell = Cell(kernel.execute(cell_content))
    return cell.get_outputs()
    
def main():
    """Main entry point for the better-jupyter-mcp-server command."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

