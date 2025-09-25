from jupyter_nbmodel_client import NbModelClient
from .cell import Cell

def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """
    格式化数据为TSV格式（制表符分隔值）
    Format data as TSV (Tab-Separated Values)
    
    Args:
        headers: 表头列表
        headers: The list of headers
        rows: 数据行列表，每行是一个字符串列表
        rows: The list of data rows, each row is a list of strings
    
    Returns:
        格式化的TSV格式字符串
        The formatted TSV string
    """
    if not headers or not rows:
        return "No data to display"
    
    result = []
    
    header_row = "\t".join(headers)
    result.append(header_row)
    
    for row in rows:
        data_row = "\t".join(str(cell) for cell in row)
        result.append(data_row)
    
    return "\n".join(result)

def format_notebook(cells: list[Cell], start_index: int = 0, total_cells: int = None) -> str:
    """
    格式化Notebook中的所有Cell，支持分页显示
    Format a list of cells into a notebook with pagination support
    
    Args:
        cells: Cell列表 / List of cells
        start_index: 起始索引 / Starting index for pagination
        total_cells: 总Cell数量 / Total number of cells in the notebook
    """
    result = []
    
    # 添加分页信息头部
    # Add pagination header information
    if total_cells is not None:
        end_index = start_index + len(cells) - 1
        pagination_info = f"=====Showing cells {start_index}-{end_index} of {total_cells} total cells====="
        result.append(pagination_info)
        result.append("")
    
    for relative_index, cell in enumerate(cells):
        actual_index = start_index + relative_index
        if cell.get_type() == "code":
            cell_header = f"=====Index: {actual_index}, Type: {cell.get_type()}, Execution Count: {cell.get_execution_count()}=====\n"
        else:
            cell_header = f"=====Index: {actual_index}, Type: {cell.get_type()}=====\n"
        result.append(cell_header+cell.get_source()+"\n\n")
    return "\n".join(result)

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
        cell_content = content_list[0] + f"...({len(content_list)-1} lines hidden)" if len(content_list) > 1 else cell.get_source()
        row = [i, cell_type, execution_count, cell_content] if with_count else [i, cell_type, cell_content]
        rows.append(row)
    
    table = format_table(headers, rows)
    return pagination_info + table