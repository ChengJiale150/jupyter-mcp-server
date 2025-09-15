from jupyter_nbmodel_client import NbModelClient
from .formatter import format_table

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
        cell = ydoc.get_cell(i)
        content_list = cell['source'].split("\n")
        execution_count = cell.get('execution_count', '')
        if len(content_list) > 1:
            content = content_list[0] + "...(Full Content In Cell)"
        else:
            content = cell['source']
        row = [i, cell['cell_type'], execution_count, content] if with_count else [i, cell['cell_type'], content]
        rows.append(row)
    
    table = format_table(headers, rows)
    return table