from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient
from .formatter import format_table
from .cell import Cell
import json, base64

def list_cell_basic(notebook: NbModelClient, with_count: bool = False) -> str:
    """
    列出Notebook中所有Cell的基本信息
    List the basic information of all cells in the notebook

    Args:
        notebook: Notebook对象
        notebook: The notebook object
        with_count: 是否包含执行计数
        with_count: Whether to include the execution count
    
    Returns:
        格式化的表格字符串
        The formatted table string
    """
    ydoc = notebook._doc
    total_cell = len(ydoc._ycells)
    
    if total_cell == 0:
        return "Notebook is empty, no Cell"
    
    headers = ["Index", "Type", "Content"] if not with_count else ["Index", "Type", "Count", "Content"]
    rows = []
    for i in range(total_cell):
        cell = Cell(ydoc.get_cell(i))
        cell_type = cell.get_type()
        execution_count = cell.get_execution_count()
        content_list = cell.get_source().split("\n")
        cell_content = content_list[0] + "...(Hidden)" if len(content_list) > 1 else cell.get_source()
        row = [i, cell_type, execution_count, cell_content] if with_count else [i, cell_type, cell_content]
        rows.append(row)
    
    table = format_table(headers, rows)
    return table

def sync_notebook(notebook: NbModelClient, file_path: str, kernel: KernelClient) -> None:
    """
    Save the notebook to the file path
    """
    json_str = json.dumps(notebook._doc.source, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    base64_bytes = base64.b64encode(json_bytes)
    base64_str = base64_bytes.decode('utf-8')
    kernel.execute(f'import base64,json\nwith open("{file_path}", "w", encoding="utf-8") as json_file:\n    json.dump(json.loads(base64.b64decode("{base64_str}".encode("utf-8")).decode("utf-8")), json_file, indent=4, ensure_ascii=False)')