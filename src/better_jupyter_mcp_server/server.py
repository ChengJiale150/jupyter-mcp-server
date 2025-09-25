import asyncio, difflib
from fastmcp import FastMCP
from typing import Annotated, Literal
from mcp.types import ImageContent
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient
from .utils import list_cell_basic, Cell, format_table, format_notebook, NotebookManager
from . import __version__
from .__env__ import FORCE_SYNC

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
    
    # 检查Jupyter与Kernel是否正常运行
    # Check if Jupyter and Kernel are running normally
    try:
        kernel = KernelClient(server_url=server_url, token=token)
        kernel.start()
        kernel.execute("print('Hello, World!')")
    except Exception as e:
        kernel.stop()
        return f"""Jupyter environment connection failed! 
        Error as below: 
        ```
        {str(e)}
        ```
        
        Please check: 
        1. Jupyter environment is successfully started 
        2. URL address is correct and can be accessed normally
        3. Token is correct"""

    exist_result = Cell(kernel.execute(f'from pathlib import Path\nPath("{notebook_path}").exists()')).get_output_info(0)
    if mode == "connect":
        if (exist_result["output_type"] == "execute_result") and ("True" not in exist_result["output"]):
            kernel.stop()
            return f"Notebook path does not exist, please check if the path is correct"
        elif exist_result["output_type"] == "error":
            kernel.stop()
            return f"Error: {exist_result['output']}"
    elif mode == "create":
        if (exist_result["output_type"] == "execute_result") and ("True" in exist_result["output"]):
            kernel.stop()
            return f"Notebook path already exists, please use connect mode to connect"
        create_code = f'import nbformat as nbf\nfrom pathlib import Path\nnotebook_path = Path("{notebook_path}")\nnb = nbf.v4.new_notebook()\nnb.cells.append(nbf.v4.new_markdown_cell("overwrite this cell for real notebook metadata"))\nwith open(notebook_path, "w", encoding="utf-8") as f:\n    nbf.write(nb, f)\nprint("OK")'
        create_result = Cell(kernel.execute(create_code)).get_output_info(0)
        if create_result["output_type"] == "error":
            kernel.stop()
            return f"Error: {create_result['output']}"
    
    # 尝试连接notebook
    # Try to connect to the notebook
    try:
        ws_url = get_jupyter_notebook_websocket_url(server_url=server_url, token=token, path=notebook_path)
        async with NbModelClient(ws_url) as notebook:
            list_info = list_cell_basic(notebook, limit=20)
    except Exception as e:
        kernel.stop()
        return f"Notebook connection failed! Error: {e}"
    
    # 连接成功,将kernel和notebook信息保存到notebook_manager中
    # Connection successful, save the kernel and notebook information to notebook_manager
    kernel.restart()
    notebook_manager.add_notebook(notebook_name, kernel, server_url, token, notebook_path)
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
    for notebook_name, notebook_info in notebook_manager.get_all_notebooks().items():
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
        ydoc = notebook._doc
        total_cells = len(ydoc._ycells)
        
        # Validate start_index
        if start_index < 0 or start_index >= total_cells:
            return f"Start index {start_index} out of range, Notebook has {total_cells} cells"
        
        end_index = min(start_index + limit, total_cells) if limit > 0 else total_cells
        
        cells = [
            Cell(ydoc.get_cell(i))
            for i in range(start_index, end_index)
        ]
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
        ydoc = notebook._doc

        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return [f"Cell index {cell_index} out of range, Notebook has {len(ydoc._ycells)} cells"]
        
        cell = Cell(ydoc.get_cell(cell_index))
        if cell.get_type() == "markdown":
            result = [cell.get_source()]
        elif cell.get_type() == "code":
            result = [
                cell.get_source(),
                f"Current execution count: {cell.get_execution_count()}"
            ]
            if return_output:
                result.extend(cell.get_outputs())
        else:
            result = cell.get_source()
            
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
        ydoc = notebook._doc
        
        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return f"Cell index {cell_index} out of range, Notebook has {len(ydoc._ycells)} cells"
        
        deleted_cell_content = Cell(ydoc.get_cell(cell_index)).get_source()
        del ydoc._ycells[cell_index]
        
        # Get surrounding cells info (5 above and 5 below the deleted position)
        total_cells = len(ydoc._ycells)
        start_index = max(0, cell_index - 5)
        limit = 10 if total_cells > 0 else 0
        
        if total_cells > 0:
            # Adjust start_index if we're near the end
            if start_index + limit > total_cells:
                start_index = max(0, total_cells - limit)
            surrounding_info = list_cell_basic(notebook, with_count=True, start_index=start_index, limit=limit)
        else:
            surrounding_info = "Notebook is now empty, no cells remaining"

        if FORCE_SYNC:
            notebook_manager.sync_notebook(notebook, notebook_name)

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
        total_cells = len(notebook._doc._ycells)
        
        if cell_index < 0 or cell_index > total_cells:
            return f"Cell index {cell_index} out of range, Notebook has {total_cells} cells"
        
        if cell_type == "code":
            if cell_index == total_cells:
                notebook.add_code_cell(cell_content)
            else:
                notebook.insert_code_cell(cell_index, cell_content)
        elif cell_type == "markdown":
            if cell_index == total_cells:
                notebook.add_markdown_cell(cell_content)
            else:
                notebook.insert_markdown_cell(cell_index, cell_content)

        # Get surrounding cells info (5 above and 5 below the inserted position)
        new_total_cells = len(notebook._doc._ycells)
        start_index = max(0, cell_index - 5)
        limit = min(10, new_total_cells)
        
        # Adjust start_index if we're near the end
        if start_index + limit > new_total_cells:
            start_index = max(0, new_total_cells - limit)
        
        surrounding_info = list_cell_basic(notebook, with_count=True, start_index=start_index, limit=limit)

        if FORCE_SYNC:
            notebook_manager.sync_notebook(notebook, notebook_name)
        
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
        ydoc = notebook._doc
        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return [f"Cell index {cell_index} out of range, Notebook has {len(ydoc._ycells)} cells"]
        
        if ydoc.get_cell(cell_index)['cell_type'] != "code":
            return [f"Cell index {cell_index} is not code, no need to execute"]
        
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
    
    cell = Cell(ydoc.get_cell(cell_index))
    return cell.get_outputs()

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
        if cell_index < 0 or cell_index >= len(notebook._doc._ycells):
            return f"Cell index {cell_index} out of range, Notebook has {len(notebook._doc._ycells)} cells"
        
        raw_content = Cell(notebook._doc.get_cell(cell_index)).get_source()
        notebook.set_cell_source(cell_index, cell_content)
        if FORCE_SYNC:
            notebook_manager.sync_notebook(notebook, notebook_name)
        
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
        
        cell = Cell(notebook._doc.get_cell(cell_index))
            
        if FORCE_SYNC:
            notebook_manager.sync_notebook(notebook, notebook_name)
        
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

