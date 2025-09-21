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
