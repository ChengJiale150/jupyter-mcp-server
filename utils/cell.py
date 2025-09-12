import re
import base64
from fastmcp.utilities.types import Image

class Cell:
    def __init__(self, cell: dict):
        self.cell = cell
    
    def get_type(self) -> str:
        return self.cell['cell_type']
    
    def get_source(self) -> str:
        return self.cell['source']

    def get_execution_count(self) -> int:
        return self.cell.get('execution_count', 0)
    
    def get_outputs(self) -> list:
        outputs = self.cell.get('outputs', [])
        result = []
        for output in outputs:
            # 标准流输出
            if output['output_type'] == 'stream':
                result.append(output['text'])
            # 执行结果输出
            elif output['output_type'] == 'execute_result':
                result.append(output['data']['text/plain'])
            # 错误输出:
            elif output['output_type'] == 'error':
                clean_traceback = []
                for line in output['traceback']:
                    # 移除ANSI转义序列
                    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                    clean_traceback.append(clean_line)
                error_info = "\n".join(clean_traceback)
                result.append(error_info)
            # 可视化化输出
            elif output['output_type'] == 'display_data':
                # 图片输出
                if "image/png" in output['data']:
                    result.append(Image(data=base64.b64decode(output['data']['image/png']),format="image/png"))
                elif "text/plain" in output['data']:
                    result.append(output['data']['text/plain'])
                else:
                    result.append(f"[Unknown display data type: {list(output['data'].keys())}]")
            else:
                result.append(f"[Unknown output type: {output['output_type']}]")
            
        return result