from jupyter_nbmodel_client import NbModelClient
from .formatter import format_table

def list_notebook_cell_basic(notebook: NbModelClient) -> str:
    ydoc = notebook._doc
    total_cell = len(ydoc._ycells)
    
    if total_cell == 0:
        return "Notebook为空,没有Cell"
    
    headers = ["Index", "Type", "Content"]
    rows = []
    for i in range(total_cell):
        cell = ydoc.get_cell(i)
        content_list = cell['source'].split("\n")
        if len(content_list) > 1:
            content = content_list[0] + "..."
        else:
            content = cell['source']
        rows.append([i, cell['cell_type'], content])
    
    table = format_table(headers, rows)
    return table