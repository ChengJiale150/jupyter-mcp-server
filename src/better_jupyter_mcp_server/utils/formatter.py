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

def format_notebook(cells: list[Cell]) -> str:
    """
    格式化Notebook中的所有Cell
    Format a list of cells into a notebook
    """
    result = []
    for index, cell in enumerate(cells):
        if cell.get_type() == "code":
            cell_header = f"=====Index: {index}, Type: {cell.get_type()}, Execution Count: {cell.get_execution_count()}=====\n"
        else:
            cell_header = f"=====Index: {index}, Type: {cell.get_type()}=====\n"
        result.append(cell_header+cell.get_source()+"\n\n")
    return "\n".join(result)
