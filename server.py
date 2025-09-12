from fastmcp import FastMCP
import json, asyncio, re, base64
from typing import Annotated, Literal
from pathlib import Path
from fastmcp.utilities.types import Image

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient
from utils.notebook import list_notebook_cell_basic
from utils.cell import Cell
from utils.formatter import format_table

mcp = FastMCP(name="Jupyter-MCP-Server", version="1.0.0")

# 用于管理不同notebook的kernel
kernel_manager = {}

#===========================================
# 内核管理模块(3个)
#===========================================
@mcp.tool()
async def connect_notebook(
    server_url: Annotated[str, "Jupyter服务启动的URL地址"], 
    token: Annotated[str, "认证Token"], 
    project_path: Annotated[Path, "Jupyter项目启动路径(绝对路径)"],
    notebook_name: Annotated[str, "唯一Notebook名称(用于标识不同的Notebook)"],
    notebook_path: Annotated[Path, "连接的Notebook路径(绝对路径)"]) -> str:
    """
    连接指定路径的已经存在的Notebook
    """
    # 检查notebook是否已经连接
    if notebook_name in kernel_manager:
        if kernel_manager[notebook_name]["notebook"]["path"] == notebook_path:
            return f"{notebook_name}已连接,请勿重复连接"
        else:
            return f"{notebook_name}命名已经存在,请重新命名"
    
    # 检查notebook是否存在
    if notebook_path.exists():
        kernel = KernelClient(server_url=server_url, token=token)
        kernel.start()
        # 尝试连接notebook
        try:
            relative_path = str(notebook_path.relative_to(project_path))
            ws_url = get_jupyter_notebook_websocket_url(server_url=server_url, token=token, path=relative_path)
            async with NbModelClient(ws_url) as notebook:
                list_info = list_notebook_cell_basic(notebook)
        except Exception as e:
            kernel.stop()
            return f"""发生错误: {e}\nJupyter环境连接失败,请检查:
            1. Jupyter环境是否启动
            2. URL地址是否正确
            3. Token是否正确
            """
        # 连接成功,将kernel和notebook信息保存到kernel_manager中
        kernel_manager[notebook_name] = {
            "kernel": kernel,
            "notebook": {
                "server_url": server_url,
                "token": token,
                "path": relative_path
            }
        }
        return_info = f"连接成功! {notebook_name}的路径为: {notebook_path}\n"
        return_info += "Cell基本信息如下:\n"
        return_info += list_info
        return return_info
    else:
        return "Notebook不存在,请检查Notebook路径是否正确(注意是绝对路径)"

@mcp.tool()
async def list_notebook() -> str:
    """
    列出所有目前连接的Notebook
    """
    if not kernel_manager:
        return "当前没有连接的Notebook"
    
    # 准备表头
    headers = ["Name", "Path"]
    
    # 准备数据行
    rows = []
    for notebook_name, notebook_info in kernel_manager.items():
        notebook_path = notebook_info["notebook"]["path"]
        rows.append([notebook_name, notebook_path])
    
    # 格式化为Markdown表格
    table = format_table(headers, rows)
    
    return table

@mcp.tool()
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
# Notebook管理模块(2个)
#===========================================

@mcp.tool()
async def create_notebook(
    notebook_path: Annotated[Path, "Notebook绝对路径"]) -> str:
    """
    创建一个空的Notebook文件
    """
    try:
        if not notebook_path.is_absolute():
            return "请提供绝对路径"
        
        # 确保文件扩展名是.ipynb
        if notebook_path.suffix != '.ipynb':
            return "文件扩展名必须是.ipynb"
        
        # 检查文件是否已存在
        if notebook_path.exists():
            return f"文件已存在: {notebook_path}"
        
        # 确保父目录存在
        notebook_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建空的notebook结构
        empty_notebook = {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "codemirror_mode": {
                        "name": "ipython",
                        "version": 3
                    },
                    "file_extension": ".py",
                    "mimetype": "text/x-python",
                    "name": "python",
                    "nbconvert_exporter": "python",
                    "pygments_lexer": "ipython3",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        # 写入文件
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(empty_notebook, f, indent=2, ensure_ascii=False)
        
        return f"Notebook创建成功!\nNotebook路径为: {notebook_path}"
        
    except Exception as e:
        return f"创建Notebook失败!\n错误信息: {str(e)}"

@mcp.tool()
async def list_notebook_cell(
    notebook_name: Annotated[str, "Notebook名称"]) -> str:
    """
    列出指定名称的Notebook的所有Cell的基本信息
    """
    if notebook_name not in kernel_manager:
        return "Notebook不存在,请检查notebook名称是否正确"
    
    ws_url = get_jupyter_notebook_websocket_url(**kernel_manager[notebook_name]["notebook"])
    async with NbModelClient(ws_url) as notebook: 
        table = list_notebook_cell_basic(notebook)
    return table

#===========================================
# Cell基本功能模块(4个)
#===========================================

@mcp.tool()
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

@mcp.tool()
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
        now_notebook_info = list_notebook_cell_basic(notebook)

    return f"删除成功!\n当前Notebook的Cell信息如下:\n{now_notebook_info}"

@mcp.tool()
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
        now_notebook_info = list_notebook_cell_basic(notebook)
        
    return f"插入成功!\n当前Notebook的Cell信息如下:\n{now_notebook_info}"

@mcp.tool()
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
        

#===========================================
# Cell高级集成功能模块(3个)
#===========================================

@mcp.tool()
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

@mcp.tool()
async def append_execute_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_type: Annotated[Literal["code", "markdown"], "Cell类型"],
    cell_content: Annotated[str, "Cell内容"],
    timeout: Annotated[int, "超时时间(秒)"] = 60) -> list[str | Image]:
    """
    在Notebook末尾添加并执行Cell(针对类型为code的Cell)
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

@mcp.tool()
async def execute_temporary_cell(
    notebook_name: Annotated[str, "Notebook名称"],
    cell_content: Annotated[str, "临时执行内容"]) -> list[str | Image]:
    """
    执行临时代码块(不存储到Notebook中)
    
    使用情景:
    1. 执行魔法指令(如`!pip install xxx`安装包,`%whos --module`查看已经导入的模块)
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

