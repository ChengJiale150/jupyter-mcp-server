def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """
    格式化数据为TSV格式（制表符分隔值）
    
    Args:
        headers: 表头列表
        rows: 数据行列表，每行是一个字符串列表
    
    Returns:
        格式化的TSV格式字符串
    """
    if not headers or not rows:
        return "没有数据可显示"
    
    result = []
    
    # 构建表头
    header_row = "\t".join(headers)
    result.append(header_row)
    
    # 构建数据行
    for row in rows:
        data_row = "\t".join(str(cell) for cell in row)
        result.append(data_row)
    
    return "\n".join(result)
