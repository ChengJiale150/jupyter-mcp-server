import json, base64
from typing import Dict, Any, Optional
from types import TracebackType

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient

def _sync_notebook(notebook: NbModelClient, file_path: str, kernel: KernelClient) -> None:
    """
    Safely save the notebook content to the specified file path on the remote server.
    This function base64-encodes the notebook content and uses a static kernel command
    to decode and write it to a file, avoiding code injection vulnerabilities.
    """
    json_str = json.dumps(notebook._doc.source, ensure_ascii=False, indent=4)
    base64_content = base64.b64encode(json_str.encode('utf-8')).decode('ascii')

    # Construct the safe, static script for the kernel.
    # This script treats the notebook content purely as data.
    script = f'''
import base64

file_content_b64 = """{base64_content}"""
file_path = r"""{file_path}"""

try:
    # Decode the base64 content to get the original JSON bytes
    json_bytes = base64.b64decode(file_content_b64.encode('ascii'))

    # Write the bytes directly to the file
    with open(file_path, "wb") as f:
        f.write(json_bytes)
except Exception as e:
    print(f"Failed to save notebook: {{e}}")
'''

    kernel.execute(script)

class NotebookManager:
    """
    管理多个Notebook与对应的Kernel的类
    Class for managing multiple Notebooks and their corresponding Kernels
    """
    
    def __init__(self):
        self._notebooks: Dict[str, Dict[str, Any]] = {}
    
    def __contains__(self, name: str) -> bool:
        """
        支持 in 语法检查notebook是否存在
        Support 'in' syntax to check if notebook exists
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            是否存在 / Whether exists
        """
        return name in self._notebooks
    
    def add_notebook(self, name: str, kernel: KernelClient, server_url: str, token: str, path: str) -> None:
        """
        添加一个新的notebook
        Add a new notebook
        
        Args:
            name: notebook的唯一标识符 / Unique identifier for the notebook
            kernel: kernel客户端 / Kernel client
            server_url: Jupyter服务器URL / Jupyter server URL
            token: 认证token / Authentication token
            path: notebook文件路径 / Notebook file path
        """
        self._notebooks[name] = {
            "kernel": kernel,
            "notebook": {
                "server_url": server_url,
                "token": token,
                "path": path
            }
        }
    
    def remove_notebook(self, name: str) -> bool:
        """
        删除一个notebook
        Remove a notebook
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            是否成功删除 / Whether successfully removed
        """
        if name in self._notebooks:
            try:
                self._notebooks[name]["kernel"].stop()
            except Exception:
                pass
            finally:
                del self._notebooks[name]
            return True
        return False
    
    def get_kernel(self, name: str) -> Optional[KernelClient]:
        """
        获取指定notebook的kernel
        Get the kernel of specified notebook
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            kernel客户端或None / Kernel client or None
        """
        if name in self._notebooks:
            return self._notebooks[name]["kernel"]
        return None
    
    def get_notebook_info(self, name: str) -> Optional[Dict[str, str]]:
        """
        获取指定notebook的信息
        Get the info of specified notebook
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            notebook信息字典或None / Notebook info dict or None
        """
        if name in self._notebooks:
            return self._notebooks[name]["notebook"]
        return None
    
    def get_notebook_path(self, name: str) -> Optional[str]:
        """
        获取指定notebook的路径
        Get the path of specified notebook
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            notebook路径或None / Notebook path or None
        """
        if name in self._notebooks:
            return self._notebooks[name]["notebook"]["path"]
        return None
    
    def get_all_notebooks(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有notebook信息
        Get all notebooks info
        
        Returns:
            所有notebook信息 / All notebooks info
        """
        return self._notebooks
    
    def restart_notebook(self, name: str) -> bool:
        """
        重启指定notebook的kernel
        Restart the kernel of specified notebook
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            是否成功重启 / Whether successfully restarted
        """
        if name in self._notebooks:
            self._notebooks[name]["kernel"].restart()
            return True
        return False
    
    def is_empty(self) -> bool:
        """
        检查是否为空
        Check if empty
        
        Returns:
            是否为空 / Whether empty
        """
        return len(self._notebooks) == 0
    
    def get_notebook_connection(self, name: str) -> 'NotebookConnection':
        """
        获取notebook连接的上下文管理器
        Get notebook connection context manager
        
        Args:
            name: notebook名称 / Notebook name
            
        Returns:
            上下文管理器 / Context manager
        """
        if name not in self._notebooks:
            raise ValueError(f"Notebook '{name}' does not exist")
        
        return NotebookConnection(self._notebooks[name]["notebook"])
    
    def sync_notebook(self, notebook: NbModelClient, notebook_name: str) -> None:
        """
        同步notebook到文件
        Sync notebook to file
        
        Args:
            notebook: notebook对象 / Notebook object
            notebook_name: notebook名称 / Notebook name
        """
        if notebook_name not in self._notebooks:
            raise ValueError(f"Notebook '{notebook_name}' does not exist")
        
        file_path = self._notebooks[notebook_name]["notebook"]["path"]
        kernel = self._notebooks[notebook_name]["kernel"]
        
        # 使用原有的sync_notebook函数
        _sync_notebook(notebook, file_path, kernel)

class NotebookConnection:
    """
    Notebook连接的上下文管理器
    Context manager for Notebook connections
    """
    
    def __init__(self, notebook_info: Dict[str, str]):
        self.notebook_info = notebook_info
        self._notebook: Optional[NbModelClient] = None
    
    async def __aenter__(self) -> NbModelClient:
        """进入上下文管理器 / Enter context manager"""
        ws_url = get_jupyter_notebook_websocket_url(**self.notebook_info)
        self._notebook = NbModelClient(ws_url)
        await self._notebook.__aenter__()
        return self._notebook
    
    async def __aexit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> None:
        """退出上下文管理器 / Exit context manager"""
        if self._notebook:
            await self._notebook.__aexit__(exc_type, exc_val, exc_tb)