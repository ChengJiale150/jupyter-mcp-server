import re, base64, tomllib
from fastmcp.utilities.types import Image
from typing import Any
from pathlib import Path
server_path = Path(__file__).parent.parent

with open(server_path / "config.toml", "rb") as f:
    config = tomllib.load(f)

ALLOW_IMG = config["basic"]["ALLOW_IMG"]

class Cell:
    def __init__(self, cell: dict):
        self.cell = cell
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)

    def _process_output(self, output: dict) -> Any:
        # 标准流输出
        if output['output_type'] == 'stream':
            return self._strip_ansi_codes(output['text'])
        # 错误输出:
        elif output['output_type'] == 'error':
            clean_traceback = [self._strip_ansi_codes(line) for line in output['traceback']]
            error_info = "\n".join(clean_traceback)
            return error_info
        # 可视化化输出
        elif output['output_type'] in ['display_data', 'execute_result']:
            # 图片输出
            if ("image/png" in output['data']) and ALLOW_IMG:
                return Image(data=base64.b64decode(output['data']['image/png']),format="image/png")
            elif "text/plain" in output['data']:
                return self._strip_ansi_codes(output['data']['text/plain'])
            else:
                return f"[Unknown display data type: {list(output['data'].keys())}]"
        else:
            return f"[Unknown output type: {output['output_type']}]"
    
    def get_type(self) -> str:
        return self.cell['cell_type']
    
    def get_source(self) -> str:
        return self.cell['source']

    def get_execution_count(self) -> int:
        return self.cell.get('execution_count', 0)
    
    def get_output_info(self, index: int) -> dict:
        outputs = self.cell.get('outputs', [])
        assert index < len(outputs), "Cell索引超出范围"

        return {
            "output_type": outputs[index]['output_type'],
            "output": self._process_output(outputs[index])
        }
    
    def get_outputs(self) -> list:
        outputs = self.cell.get('outputs', [])
        result = [self._process_output(output) for output in outputs]
        return result