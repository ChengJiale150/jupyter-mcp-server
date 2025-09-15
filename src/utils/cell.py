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
    
    def _strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)
    
    def _preprocess_image(self, image_data: bytes) -> bytes:
        """
        对图片进行预处理，包括等比例缩放和基于PIXIV_TOKEN的进一步缩放
        
        Args:
            image_data: 原始图片的字节数据
            
        Returns:
            处理后的图片字节数据
        """
        if not ALLOW_IMG_PREPROCESS:
            return image_data
            
        try:
            # 从字节数据创建PIL图片对象
            img = PILImage.open(io.BytesIO(image_data))
            original_width, original_height = img.size
            
            # 第一步：等比例缩放到最大尺寸限制内
            width_ratio = MAX_WIDTH / original_width if original_width > MAX_WIDTH else 1
            height_ratio = MAX_HEIGHT / original_height if original_height > MAX_HEIGHT else 1
            
            # 选择较小的缩放比例以保持等比例
            scale_ratio = min(width_ratio, height_ratio)
            
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            # 第二步：基于PIXIV_TOKEN进行进一步缩放
            # 将宽度和高度缩小至PIXIV_TOKEN的向下整数倍
            final_width = (new_width // PIXIV_TOKEN) * PIXIV_TOKEN
            final_height = (new_height // PIXIV_TOKEN) * PIXIV_TOKEN
            
            # 确保最终尺寸不为0
            final_width = max(final_width, PIXIV_TOKEN)
            final_height = max(final_height, PIXIV_TOKEN)
            
            # 如果尺寸没有变化，直接返回原始数据
            if final_width == original_width and final_height == original_height:
                return image_data
            
            # 执行图片缩放
            resized_img = img.resize((final_width, final_height), PILImage.Resampling.LANCZOS)
            
            # 将处理后的图片转换回字节数据
            output_buffer = io.BytesIO()
            # 保持原始格式，如果是PNG则保存为PNG
            img_format = img.format if img.format else 'PNG'
            resized_img.save(output_buffer, format=img_format)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            # 如果处理失败，返回原始数据
            return image_data

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
                # 解码base64图片数据
                raw_image_data = base64.b64decode(output['data']['image/png'])
                # 应用图片预处理
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