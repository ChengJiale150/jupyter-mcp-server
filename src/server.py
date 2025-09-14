from fastmcp import FastMCP
import asyncio
from typing import Annotated, Literal
from fastmcp.utilities.types import Image

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient
from utils import list_cell_basic, Cell, format_table

mcp = FastMCP(name="Jupyter-MCP-Server", version="1.0.0")

# 用于管理不同notebook的kernel
kernel_manager = {}

#===========================================
# Notebook管理模块(3个)
#===========================================
@mcp.tool(tags={"core","notebook","connect_notebook"})
async def connect_notebook(
    server_url: Annotated[str, "Jupyter服务启动的URL地址"], 
    token: Annotated[str, "认证Token"], 
    notebook_name: Annotated[str, "用于标识不同的Notebook的唯一名称"],
    notebook_path: Annotated[str, "Notebook路径(相对路径)"],
    mode: Annotated[
        Literal["connect", "create"], 
        "连接模式(connect: 连接已经存在的Notebook; create: 创建新的Notebook并连接)"
        ] = "connect") -> str:
    """
    连接指定路径的Notebook
    """
    # 检查notebook是否已经连接
    if notebook_name in kernel_manager:
        if kernel_manager[notebook_name]["notebook"]["path"] == notebook_path:
            return f"{notebook_name}已连接,请勿重复连接"
        else:
            return f"{notebook_name}命名已经存在,请重新命名"
    
    # 检查Jupyter与Kernel是否正常运行
    try:
        kernel = KernelClient(server_url=server_url, token=token)
        kernel.start()
        kernel.execute("print('Hello, World!')")
    except Exception as e:
        kernel.stop()
        return f"""Jupyter环境连接失败!发生错误: {str(e)}
        请检查: 
        1. Jupyter环境是否成功启动 
        2. URL地址是否正确且能正常访问
        3. Token是否正确"""
    
    # 不同的连接方式的核验
    # 先检查notebook路径是否存在
    exist_result = Cell(kernel.execute(f'from pathlib import Path\nPath("{notebook_path}").exists()')).get_output_info(0)
    if mode == "connect":
        if (exist_result["output_type"] == "execute_result") and ("True" not in exist_result["output"]):
            kernel.stop()
            return f"Notebook路径不存在,请检查路径是否正确"
        elif exist_result["output_type"] == "error":
            kernel.stop()
            return f"发生错误: {exist_result["output"]}"
    elif mode == "create":
        # 检查notebook路径是否已经存在
        if (exist_result["output_type"] == "execute_result") and ("True" in exist_result["output"]):
            kernel.stop()
            return f"Notebook路径已经存在,请使用connect模式连接"    
        # 创建新的notebook
        create_code = f'import nbformat as nbf\nfrom pathlib import Path\nnotebook_path = Path("{notebook_path}")\nnb = nbf.v4.new_notebook()\nwith open(notebook_path, "w", encoding="utf-8") as f:\n    nbf.write(nb, f)\nprint("OK")'
        create_result = Cell(kernel.execute(create_code)).get_output_info(0)
        if create_result["output_type"] == "error":
            kernel.stop()
            return f"发生错误: {create_result["output"]}"
    
    # 尝试连接notebook
    try:
        ws_url = get_jupyter_notebook_websocket_url(server_url=server_url, token=token, path=notebook_path)
        async with NbModelClient(ws_url) as notebook:
            list_info = list_cell_basic(notebook)
    except Exception as e:
        kernel.stop()
        return f"Notebook连接失败!发生错误: {e}"
    
    # 连接成功,将kernel和notebook信息保存到kernel_manager中
    kernel.restart()
    kernel_manager[notebook_name] = {
        "kernel": kernel,
        "notebook": {
            "server_url": server_url,
            "token": token,
            "path": notebook_path
        }
    }
    return_info = f"{notebook_name}连接成功!\nCell基本信息如下:\n{list_info}"
    return return_info

@mcp.tool(tags={"core","notebook","list_notebook"})
async def list_notebook() -> str:
    """
    列出所有目前连接的Notebook
    """
    if not kernel_manager:
        return "当前没有连接的Notebook"
    
    # 准备表头
    headers = ["Name", "Jupyter URL", "Path"]
    
    # 准备数据行
    rows = []
    for notebook_name, notebook_info in kernel_manager.items():
        notebook_path = notebook_info["notebook"]["path"]
        server_url = notebook_info["notebook"]["server_url"]
        rows.append([notebook_name, server_url, notebook_path])
    
    # 格式化为Markdown表格
    table = format_table(headers, rows)
    
    return table

@mcp.tool(tags={"core","notebook","restart_notebook"})
async def restart_notebook(
    notebook_name: Annotated[str, "Notebook名称"]) -> str:
    """
    重启指定名称的Notebook的内核,清除所有导入包与变量
    """
    if notebook_name not in kernel_manager:
        return "Notebook不存在,请检查notebook名称是否正确"
    
    kernel_manager[notebook_name]["kernel"].restart()
    return f"{notebook_name} 重启成功"

#===========================================
# Cell基本功能模块(6个)
#===========================================

@mcp.tool(tags={"core","cell","list_cell"})
async def list_cell(
    notebook_name: Annotated[str, "Notebook名称"]) -> str:
    """
    列出Notebook的所有Cell的基本信息
    """
    if notebook_name not in kernel_manager:
        return "Notebook不存在,请检查notebook名称是否正确"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook: 
        table = list_cell_basic(notebook, with_count=True)
    return table

@mcp.tool(tags={"core","cell","read_cell"})
async def read_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_index: Annotated[int, "Cell索引"],
    include_output: Annotated[bool, "是否包含输出"] = True) -> list[str | Image]:
    '''
    读取Notebook指定索引的Cell内容
    '''
    if notebook_name not in kernel_manager:
        return ["Notebook不存在,请检查notebook名称是否正确"]
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        ydoc = notebook._doc

        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return [f"Cell索引{cell_index}超出范围,Notebook有{len(ydoc._ycells)}个Cell"]
        
        cell = Cell(ydoc.get_cell(cell_index))
        if cell.get_type() == "markdown":
            result = [cell.get_source()]
        elif cell.get_type() == "code":
            result = [
                cell.get_source(),
                f"当前执行计数: {cell.get_execution_count()}"
            ]
            if include_output:
                result.extend(cell.get_outputs())
        else:
            result = cell.get_source()
            
    return result

@mcp.tool(tags={"core","cell","delete_cell"})
async def delete_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_index: Annotated[int, "Cell索引"]) -> str:
    """
    删除Notebook指定索引的Cell
    """
    if notebook_name not in kernel_manager:
        return "Notebook不存在,请检查notebook名称是否正确"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        ydoc = notebook._doc
        
        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return f"Cell索引{cell_index}超出范围,Notebook有{len(ydoc._ycells)}个Cell"
        
        del ydoc._ycells[cell_index]
        now_notebook_info = list_cell_basic(notebook)

    return f"删除成功!\n当前Notebook的Cell信息如下:\n{now_notebook_info}"

@mcp.tool(tags={"core","cell","insert_cell"})
async def insert_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_index: Annotated[int, "锚定索引"],
    cell_type: Annotated[Literal["code", "markdown"], "Cell类型"],
    cell_content: Annotated[str, "Cell内容"],
    location: Annotated[Literal["above", "below"], "插入位置"] = "below") -> str:
    """
    在Notebook指定索引处上方/下方插入Cell
    """
    if notebook_name not in kernel_manager:
        return "Notebook不存在,请检查notebook名称是否正确"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        cell_index = cell_index + 1 if location == "below" else cell_index
        if cell_index < 0 or cell_index > len(notebook._doc._ycells):
            return f"Cell索引{cell_index}超出范围,Notebook有{len(notebook._doc._ycells)}个Cell"
        
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
        
    return f"插入成功!\n当前Notebook的Cell信息如下:\n{now_notebook_info}"

@mcp.tool(tags={"core","cell","execute_cell"})
async def execute_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_index: Annotated[int, "Cell索引"],
    timeout: Annotated[int, "超时时间(秒)"] = 60) -> list[str | Image]:
    """
    执行Notebook指定索引的Cell(类型需要为code)
    """
    if notebook_name not in kernel_manager:
        return ["Notebook不存在,请检查notebook名称是否正确"]
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        ydoc = notebook._doc
        if cell_index < 0 or cell_index >= len(ydoc._ycells):
            return [f"Cell索引{cell_index}超出范围,Notebook有{len(ydoc._ycells)}个Cell"]
        
        if ydoc.get_cell(cell_index)['cell_type'] != "code":
            return [f"Cell索引{cell_index}的类型不是code,无需执行"]
        
        # 执行Cell(带超时)
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
    notebook_name: Annotated[str, "Notebook名称"],
    cell_index: Annotated[int, "Cell索引"],
    cell_content: Annotated[str, "Cell内容"]) -> str:
    """
    覆盖Notebook指定索引的Cell内容
    """
    if notebook_name not in kernel_manager:
        return "Notebook不存在,请检查notebook名称是否正确"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook:
        if cell_index < 0 or cell_index >= len(notebook._doc._ycells):
            return f"Cell索引{cell_index}超出范围,Notebook有{len(notebook._doc._ycells)}个Cell"
        
        raw_content = notebook._doc.get_cell(cell_index)['source']
        notebook.set_cell_source(cell_index, cell_content)

    return f"覆盖成功!\n\n原内容:\n{raw_content}\n\n新内容:\n{cell_content}"

#===========================================
# Cell高级集成功能模块(2个)
#===========================================

@mcp.tool(tags={"advanced","cell","append_execute_cell"})
async def append_execute_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_type: Annotated[Literal["code", "markdown"], "Cell类型"],
    cell_content: Annotated[str, "Cell内容"],
    timeout: Annotated[int, "超时时间(秒)"] = 60) -> list[str | Image]:
    """
    在Notebook末尾添加并执行Cell
    """
    if notebook_name not in kernel_manager:
        return ["Notebook不存在,请检查notebook名称是否正确"]
    
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
            return [f"索引为{cell_index}的Cell执行成功!"] + cell.get_outputs()
        else:
            cell_index = notebook.add_markdown_cell(cell_content)
            
            return [f"索引为{cell_index}的Markdown Cell添加成功!"]

@mcp.tool(tags={"advanced","cell","execute_temporary_cell"})
async def execute_temporary_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_content: Annotated[str, "临时执行内容"]) -> list[str | Image]:
    """
    执行临时代码块(不存储到Notebook中)
    
    使用情景:
    1. 执行魔法指令(如`%pip install xxx`安装包,`%whos --module`查看已经导入的模块)
    2. 进行代码片段调试
    3. 查看中间变量取值(例如`print(xxx)`或`df.head()`)
    4. 进行临时统计计算(例如`np.mean(df['xxx'])`)
    
    严禁:
    1. 导入新模块与进行变量赋值等任何对后续Notebook运行有影响的操作
    2. 需要长时间运行的代码片段
    """
    if notebook_name not in kernel_manager:
        return ["Notebook不存在,请检查notebook名称是否正确"]
    
    kernel = kernel_manager[notebook_name]["kernel"]
    cell = Cell(kernel.execute(cell_content))
    return cell.get_outputs()
    
if __name__ == "__main__":
    mcp.run(transport="stdio")

