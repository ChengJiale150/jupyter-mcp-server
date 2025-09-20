import re, base64, tomllib, io
from fastmcp.utilities.types import Image
from typing import Any
from pathlib import Path
from PIL import Image as PILImage
server_path = Path(__file__).parent.parent

with open(server_path / "config.toml", "rb") as f:
    config = tomllib.load(f)

ALLOW_IMG = config["basic"]["ALLOW_IMG"]
ALLOW_IMG_PREPROCESS = config["basic"]["ALLOW_IMG_PREPROCESS"]
MAX_WIDTH = config["img"]["MAX_WIDTH"]
MAX_HEIGHT = config["img"]["MAX_HEIGHT"]
PIXIV_TOKEN = config["img"]["PIXIV_TOKEN"]

class Cell:
    def __init__(self, cell: dict):
        self.cell = cell
    
    def _strip_ansi_codes(self, text: str | list[str]) -> str:
        """
        删除ANSI转义序列
        Remove ANSI escape sequences from text
        """
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        if isinstance(text, list):
            text = "\n".join(text)
        return ansi_escape.sub('', text)
    
    def _preprocess_image(self, image_data: bytes) -> bytes:
        """
        对图片进行预处理，包括等比例缩放和基于PIXIV_TOKEN的进一步缩放
        Process the image, including proportional scaling and further scaling based on PIXIV_TOKEN
        
        Args:
            image_data: 原始图片的字节数据
            image_data: The original image data in bytes
            
        Returns:
            处理后的图片字节数据
            The processed image data in bytes
        """
        if not ALLOW_IMG_PREPROCESS:
            return image_data
            
        try:
            img = PILImage.open(io.BytesIO(image_data))
            original_width, original_height = img.size
            
            width_ratio = MAX_WIDTH / original_width if original_width > MAX_WIDTH else 1
            height_ratio = MAX_HEIGHT / original_height if original_height > MAX_HEIGHT else 1
            
            scale_ratio = min(width_ratio, height_ratio)
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            final_width = (new_width // PIXIV_TOKEN) * PIXIV_TOKEN
            final_height = (new_height // PIXIV_TOKEN) * PIXIV_TOKEN

            final_width = max(final_width, PIXIV_TOKEN)
            final_height = max(final_height, PIXIV_TOKEN)
            
            if final_width == original_width and final_height == original_height:
                return image_data
            
            resized_img = img.resize((final_width, final_height), PILImage.Resampling.LANCZOS)
            output_buffer = io.BytesIO()
            img_format = img.format if img.format else 'PNG'
            resized_img.save(output_buffer, format=img_format)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            return image_data

    def _process_output(self, output: dict) -> Any:
        # 标准流输出
        # Standard stream output
        if output['output_type'] == 'stream':
            return self._strip_ansi_codes(output['text'])
        # 错误输出:
        # Error output:
        elif output['output_type'] == 'error':
            clean_traceback = [self._strip_ansi_codes(line) for line in output['traceback']]
            error_info = "\n".join(clean_traceback)
            return error_info
        # 可视化化输出
        # Visualization output:
        elif output['output_type'] in ['display_data', 'execute_result']:
            if ("image/png" in output['data']) and ALLOW_IMG:
                raw_image_data = base64.b64decode(output['data']['image/png'])
                processed_image_data = self._preprocess_image(raw_image_data)
                return Image(data=processed_image_data, format="image/png")
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

    def get_execution_count(self) -> int | str:
        return self.cell.get('execution_count', 'N/A')
    
    def get_output_info(self, index: int) -> dict:
        outputs = self.cell.get('outputs', [])
        assert index < len(outputs), "Cell index out of range"

        return {
            "output_type": outputs[index]['output_type'],
            "output": self._process_output(outputs[index])
        }
    
    def get_outputs(self) -> list:
        outputs = self.cell.get('outputs', [])
        result = [self._process_output(output) for output in outputs]
        return result