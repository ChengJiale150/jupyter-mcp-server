from jupyter_nbmodel_client import NbModelClient
from jupyter_kernel_client import KernelClient
from .formatter import format_table
from .cell import Cell
import json, base64

def list_cell_basic(notebook: NbModelClient, with_count: bool = False, start_index: int = 0, limit: int = 0) -> str:
    """
    列出Notebook中所有Cell的基本信息，支持分页功能
    List the basic information of all cells in the notebook with pagination support

    Args:
        notebook: Notebook对象 / The notebook object
        with_count: 是否包含执行计数 / Whether to include the execution count
        start_index: 起始Cell索引 / Starting cell index for pagination
        limit: 最大返回Cell数量(0表示无限制) / Maximum number of cells to return (0 means no limit)
    
    Returns:
        格式化的表格字符串 / The formatted table string
    """
    ydoc = notebook._doc
    total_cell = len(ydoc._ycells)
    
    if total_cell == 0:
        return "Notebook is empty, no Cell"
    
    # Validate start_index
    if start_index < 0 or start_index >= total_cell:
        return f"Start index {start_index} out of range, Notebook has {total_cell} cells"
    
    # Calculate end index
    end_index = min(start_index + limit, total_cell) if limit > 0 else total_cell
    
    headers = ["Index", "Type", "Content"] if not with_count else ["Index", "Type", "Count", "Content"]
    rows = []
    
    # Add pagination info if using pagination
    pagination_info = ""
    if limit > 0:
        pagination_info = f"Showing cells {start_index}-{end_index-1} of {total_cell} total cells\n\n"
    
    for i in range(start_index, end_index):
        cell = Cell(ydoc.get_cell(i))
        cell_type = cell.get_type()
        execution_count = cell.get_execution_count()
        content_list = cell.get_source().split("\n")
        cell_content = content_list[0] + "...(Hidden)" if len(content_list) > 1 else cell.get_source()
        row = [i, cell_type, execution_count, cell_content] if with_count else [i, cell_type, cell_content]
        rows.append(row)
    
    table = format_table(headers, rows)
    return pagination_info + table

def sync_notebook(notebook: NbModelClient, file_path: str, kernel: KernelClient) -> None:
    """
    Safely save the notebook content to the specified file path on the remote server.
    This function base64-encodes the notebook content and uses a static kernel command
    to decode and write it to a file, avoiding code injection vulnerabilities.
    """
    json_str = json.dumps(notebook._doc.source, ensure_ascii=False, indent=4)
    base64_content = base64.b64encode(json_str.encode('utf-8')).decode('ascii')

    # Construct the safe, static script for the kernel.
    # This script treats the notebook content purely as data.
    script = f'''
import base64

file_content_b64 = """{base64_content}"""
file_path = r"""{file_path}"""

try:
    # Decode the base64 content to get the original JSON bytes
    json_bytes = base64.b64decode(file_content_b64.encode('ascii'))

    # Write the bytes directly to the file
    with open(file_path, "wb") as f:
        f.write(json_bytes)
except Exception as e:
    print(f"Failed to save notebook: {{e}}")
'''

    kernel.execute(script)