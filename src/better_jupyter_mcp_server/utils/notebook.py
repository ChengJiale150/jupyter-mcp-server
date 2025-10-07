from typing import Dict, Any, Optional
from types import TracebackType

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
from jupyter_kernel_client import KernelClient
from jupyter_server_api import JupyterServerClient

from ..__env__ import AUTO_SAVE_NOTEBOOK

class NotebookManager:
    """
    Class for managing multiple Notebooks and their corresponding Kernels
    """
    
    def __init__(self):
        self._notebooks: Dict[str, Dict[str, Any]] = {}
    
    def __contains__(self, name: str) -> bool:
        """
        Support 'in' syntax to check if notebook exists
        
        Args:
            name: Notebook name
            
        Returns:
            Whether exists
        """
        return name in self._notebooks
    
    def __iter__(self):
        """
        Support iterator syntax, returns (notebook_name, notebook_info) tuples
        
        Returns:
            Iterator
        """
        return iter(self._notebooks.items())
    
    def add_notebook(self, 
        name: str, 
        kernel: KernelClient, server_client: JupyterServerClient,
        server_url: str, token: str, path: str) -> None:
        """
        Add a new notebook
        
        Args:
            name: Unique identifier for the notebook
            kernel: Kernel client
            server_url: Jupyter server URL
            token: Authentication token
            path: Notebook file path
        """
        self._notebooks[name] = {
            "kernel": kernel,
            "server_client": server_client,
            "notebook": {
                "server_url": server_url,
                "token": token,
                "path": path
            }
        }
    
    def remove_notebook(self, name: str) -> bool:
        """
        Remove a notebook
        
        Args:
            Notebook name
            
        Returns:
            Whether successfully removed
        """
        if name in self._notebooks:
            try:
                self._notebooks[name]["kernel"].stop()
                self._notebooks[name]["server_client"].close()
            except Exception:
                pass
            finally:
                del self._notebooks[name]
            return True
        return False
    
    def get_kernel(self, name: str) -> Optional[KernelClient]:
        """
        Get the kernel of specified notebook
        
        Args:
            Notebook name
            
        Returns:
            Kernel client or None
        """
        if name in self._notebooks:
            return self._notebooks[name]["kernel"]
        return None
    
    def get_notebook_path(self, name: str) -> Optional[str]:
        """
        Get the path of specified notebook
        
        Args:
            Notebook name
            
        Returns:
            Notebook path or None
        """
        if name in self._notebooks:
            return self._notebooks[name]["notebook"]["path"]
        return None
    
    def restart_notebook(self, name: str) -> bool:
        """
        Restart the kernel of specified notebook
        
        Args:
            Notebook name
            
        Returns:
            Whether successfully restarted
        """
        if name in self._notebooks:
            self._notebooks[name]["kernel"].restart()
            return True
        return False
    
    def is_empty(self) -> bool:
        """
        Check if empty
        
        Returns:
            Whether empty
        """
        return len(self._notebooks) == 0
    
    def get_notebook_connection(self, name: str) -> 'NotebookConnection':
        """
        Get notebook connection context manager
        
        Args:
            Notebook name
            
        Returns:
            Context manager
        """
        if name not in self._notebooks:
            raise ValueError(f"Notebook '{name}' does not exist")
        
        return NotebookConnection(self._notebooks[name]["notebook"], self._notebooks[name]["server_client"])

class NotebookConnection:
    """
    Context manager for Notebook connections
    """
    
    def __init__(self, notebook_info: Dict[str, str], server_client: JupyterServerClient):
        self.notebook_info = notebook_info
        self.server_client = server_client
        self._notebook: Optional[NbModelClient] = None
    
    async def __aenter__(self) -> NbModelClient:
        """Enter context manager"""
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
        """Exit context manager"""
        if self._notebook:
            if AUTO_SAVE_NOTEBOOK:
                self.server_client.contents.save_notebook(self.notebook_info["path"], self._notebook.as_dict())
            await self._notebook.__aexit__(exc_type, exc_val, exc_tb)