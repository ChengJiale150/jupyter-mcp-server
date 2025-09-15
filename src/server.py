from fastmcp import FastMCP
import asyncio
from typing import Annotated, Literal
from fastmcp.utilities.types import Image

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient
from utils import list_cell_basic, Cell, format_table

mcp = FastMCP(name="Jupyter-MCP-Server", version="1.0.0")

# 用于管理不同notebook的kernel
# Used to manage different notebooks' kernels
kernel_manager = {}

#===========================================
# Notebook管理模块(3个)
# Notebook management module (3)
#===========================================
@mcp.tool(tags={"core","notebook","connect_notebook"})
async def connect_notebook(
    server_url: Annotated[str, "Jupyter server URL"], 
    token: Annotated[str, "Authentication Token"], 
    notebook_name: Annotated[str, "Unique name for different notebooks"],
    notebook_path: Annotated[str, "Notebook path (relative path)"],
    mode: Annotated[
        Literal["connect", "create"], 
        "Connection mode (connect: connect to an existing Notebook; create: create a new Notebook and connect)"
        ] = "connect") -> str:
    """
    Connect to a Notebook and corresponding Kernel
    """
    # 检查notebook是否已经连接
    # Check if the notebook is already connected
    if notebook_name in kernel_manager:
        if kernel_manager[notebook_name]["notebook"]["path"] == notebook_path:
            return f"{notebook_name} is already connected, please do not connect again"
        else:
            return f"{notebook_name} name already exists, please rename it"
    
    # 检查Jupyter与Kernel是否正常运行
    # Check if Jupyter and Kernel are running normally
    try:
        kernel = KernelClient(server_url=server_url, token=token)
        kernel.start()
        kernel.execute("print('Hello, World!')")
    except Exception as e:
        kernel.stop()
        return f"""Jupyter environment connection failed! Error: {str(e)}
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
            return f"Error: {exist_result["output"]}"
    elif mode == "create":
        if (exist_result["output_type"] == "execute_result") and ("True" in exist_result["output"]):
            kernel.stop()
            return f"Notebook path already exists, please use connect mode to connect"
        create_code = f'import nbformat as nbf\nfrom pathlib import Path\nnotebook_path = Path("{notebook_path}")\nnb = nbf.v4.new_notebook()\nwith open(notebook_path, "w", encoding="utf-8") as f:\n    nbf.write(nb, f)\nprint("OK")'
        create_result = Cell(kernel.execute(create_code)).get_output_info(0)
        if create_result["output_type"] == "error":
            kernel.stop()
            return f"Error: {create_result["output"]}"
    
    # 尝试连接notebook
    # Try to connect to the notebook
    try:
        ws_url = get_jupyter_notebook_websocket_url(server_url=server_url, token=token, path=notebook_path)
        async with NbModelClient(ws_url) as notebook:
            list_info = list_cell_basic(notebook)
    except Exception as e:
        kernel.stop()
        return f"Notebook connection failed! Error: {e}"
    
    # 连接成功,将kernel和notebook信息保存到kernel_manager中
    # Connection successful, save the kernel and notebook information to kernel_manager
    kernel.restart()
    kernel_manager[notebook_name] = {
        "kernel": kernel,
        "notebook": {
            "server_url": server_url,
            "token": token,
            "path": notebook_path
        }
    }
    return_info = f"{notebook_name} connection successful!\nCell basic information:\n{list_info}"
    return return_info

@mcp.tool(tags={"core","notebook","list_notebook"})
async def list_notebook() -> str:
    """
    List all currently connected Notebooks
    """
    if not kernel_manager:
        return "No notebook is currently connected"
    
    headers = ["Name", "Jupyter URL", "Path"]
    
    rows = []
    for notebook_name, notebook_info in kernel_manager.items():
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
    if notebook_name not in kernel_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    kernel_manager[notebook_name]["kernel"].restart()
    return f"{notebook_name} restart successful"

#===========================================
# Cell基本功能模块(6个)
# Basic Cell Function Module (6)
#===========================================

@mcp.tool(tags={"core","cell","list_cell"})
async def list_cell(
    notebook_name: str) -> str:
    """
    List the basic information of all cells in a specified Notebook
    """
    if notebook_name not in kernel_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook: 
        table = list_cell_basic(notebook, with_count=True)
    return table

@mcp.tool(tags={"core","cell","read_cell"})
async def read_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"],
    include_output: Annotated[bool, "Whether to include output"] = True) -> list[str | Image]:
    '''
    Read the content of a cell at a specified index in a Notebook
    '''
    if notebook_name not in kernel_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
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
            if include_output:
                result.extend(cell.get_outputs())
        else:
            result = cell.get_source()
            
    return result

@mcp.tool(tags={"core","cell","delete_cell"})
async def delete_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"]) -> str:
    """
    Delete a cell at a specified index in a Notebook
    """
    if notebook_name not in kernel_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        ydoc = notebook._doc
        
        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return f"Cell index {cell_index} out of range, Notebook has {len(ydoc._ycells)} cells"
        
        del ydoc._ycells[cell_index]
        now_notebook_info = list_cell_basic(notebook)

    return f"Delete successful!\nCurrent Notebook's Cell information:\n{now_notebook_info}"

@mcp.tool(tags={"core","cell","insert_cell"})
async def insert_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Target index(0-based)"],
    cell_type: Literal["code", "markdown"],
    cell_content: str,
    direction: Literal["above", "below"] = "below") -> str:
    """
    Insert a cell above/below of a target index in a Notebook
    """
    if notebook_name not in kernel_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        cell_index = cell_index + 1 if direction == "below" else cell_index
        if cell_index < 0 or cell_index > len(notebook._doc._ycells):
            return f"Cell index {cell_index} out of range, Notebook has {len(notebook._doc._ycells)} cells"
        
        if cell_type == "code":
            if cell_index == len(notebook._doc._ycells):
                notebook.add_code_cell(cell_content)
            else:
                notebook.insert_code_cell(cell_index, cell_content)
        elif cell_type == "markdown":
            if cell_index == len(notebook._doc._ycells):
                notebook.add_markdown_cell(cell_content)
            else:
                notebook.insert_markdown_cell(cell_index, cell_content)
        now_notebook_info = list_cell_basic(notebook)
        
    return f"Insert successful!\nCurrent Notebook's Cell information:\n{now_notebook_info}"

@mcp.tool(tags={"core","cell","execute_cell"})
async def execute_cell(
    notebook_name: str,
    cell_index: Annotated[int, "Cell index(0-based)"],
    timeout: Annotated[int, "seconds"] = 60) -> list[str | Image]:
    """
    Execute a cell at a specified index in a Notebook
    """
    if notebook_name not in kernel_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        ydoc = notebook._doc
        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return [f"Cell index {cell_index} out of range, Notebook has {len(ydoc._ycells)} cells"]
        
        if ydoc.get_cell(cell_index)['cell_type'] != "code":
            return [f"Cell index {cell_index} is not code, no need to execute"]
        
        kernel = kernel_manager[notebook_name]["kernel"]
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
    Overwrite the content of a cell at a specified index in a Notebook
    """
    if notebook_name not in kernel_manager:
        return "Notebook does not exist, please check if the notebook name is correct"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        if cell_index < 0 or cell_index >= len(notebook._doc._ycells):
            return f"Cell index {cell_index} out of range, Notebook has {len(notebook._doc._ycells)} cells"
        
        raw_content = notebook._doc.get_cell(cell_index)['source']
        notebook.set_cell_source(cell_index, cell_content)

    return f"Overwrite successful!\n\nOriginal content:\n{raw_content}\n\nNew content:\n{cell_content}"

#===========================================
# Cell高级集成功能模块(2个)
# Advanced Integrated Cell Function Module (2)
#===========================================

@mcp.tool(tags={"advanced","cell","append_execute_cell"})
async def append_execute_cell(
    notebook_name: str,
    cell_type: Literal["code", "markdown"],
    cell_content: str,
    timeout: Annotated[int, "seconds"] = 60) -> list[str | Image]:
    """
    Add a new cell to the end of a Notebook and immediately execute it
    """
    if notebook_name not in kernel_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        
        if cell_type == "code":
            cell_index = notebook.add_code_cell(cell_content)
            kernel = kernel_manager[notebook_name]["kernel"]
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
            return [f"Cell index {cell_index} execution successful!"] + cell.get_outputs()
        else:
            cell_index = notebook.add_markdown_cell(cell_content)
            
            return [f"Cell index {cell_index} Markdown Cell addition successful!"]

@mcp.tool(tags={"advanced","cell","execute_temporary_cell"})
async def execute_temporary_cell(
    notebook_name: str,
    cell_content: str) -> list[str | Image]:
    """
    Execute a temporary code block (not saved to the Notebook)
    
    Advise:
    1. Execute Jupyter magic commands
    2. Debug code
    3. View intermediate variable values(e.g., `print(xxx)` or `df.head()`)
    4. Perform temporary statistical calculations(e.g., `np.mean(df['xxx'])`)
    
    DO NOT:
    1. Import new modules and perform variable assignments that affect subsequent Notebook execution
    2. Run code that requires a long time to run
    """
    if notebook_name not in kernel_manager:
        return ["Notebook does not exist, please check if the notebook name is correct"]
    
    kernel = kernel_manager[notebook_name]["kernel"]
    cell = Cell(kernel.execute(cell_content))
    return cell.get_outputs()
    
if __name__ == "__main__":
    mcp.run(transport="stdio")

