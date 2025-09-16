# 配置必要路径

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

## Step1: 确认你的文件地址

首先我们需要确认Jupyter MCP Server项目的地址,用于替换上述参考配置中的`"your/path/to/jupyter-mcp-server"`

### 文件资源管理器

<details>
<summary> Windows 11</summary>

在`文件资源管理器`中找到Jupyter MCP Server对应的文件夹,按下快捷键`ctrl+shift+C`复制文件路径,参考的路径如下:

```bash
C:\Users\username\Desktop\MCP\jupyter-mcp-server
```

此时,需要注意将路径中的`\`替换为`\\`,最终的路径如下:

```bash
C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server
```

最后将上述参考JSON格式中的文件路径替换为复制完毕的路径,示例如下:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

<details>
<summary>MacOS</summary>

在`访达`中找到Jupyter MCP Server对应的文件夹,按下快捷键`option+command+c`复制文件路径,参考的路径如下:

```bash
/Users/username/Documents/mcp/jupyter-mcp-server
```

最后将上述参考JSON格式中的文件路径替换为复制完毕的路径,示例如下:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "/Users/username/Documents/mcp/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

### 终端

<details>
<summary> Windows CMD</summary>

在对应路径下的终端中输入下述命令:

```bash
echo %cd%
```

此时,参考的输出路径如下:

```bash
C:\Users\username\Desktop\MCP\jupyter-mcp-server
```

此时,需要注意将路径中的`\`替换为`\\`,最终的路径如下:

```bash
C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server
```

最后将上述参考JSON格式中的文件路径替换为复制完毕的路径,示例如下:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "C:\\Users\\username\\Desktop\\MCP\\jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

<details>
<summary> MacOS/Linux</summary>

在对应路径下的终端中输入下述命令:

```bash
pwd
```

此时,参考的输出路径如下:

```bash
/Users/username/Documents/mcp/jupyter-mcp-server
```

最后将上述参考JSON格式中的文件路径替换为复制完毕的路径,示例如下:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "/Users/username/Documents/mcp/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```

</details>

## Step2: 在对应客户端里添加MCP服务

接下来在对应客户端里的MCP配置文件中添加MCP服务即可

<details>

<summary> Cursor</summary>

在Cursor右上角打开`Cursor Settings`(⚙图标),选择`Tool & Integrations`在`MCP Tools`中点击`New MCP Sever`就会跳转到`mcp.json`文件,呈现的示例结果如下:

```json
{
  "mcpServers": {
    ...(已有的MCP,若没有则为空)
  }
}
```

在已有的MCP后将之前已经填充完善好的JSON文件黏贴,最终的参考结果如下:

```json
{
  "mcpServers": {
    ...(已有的MCP,若没有则为空),
    "Jupyter-MCP-Server" : {
        ...(上述具体内容)
    }
  }
}
```

最后保存并关闭`mcp.json`文件,返回查看`MCP Tools`中是否出现名为`Jupyter-MCP-Server`的MCP服务,等待片刻,如果黄灯变绿灯则表明MCP服务启动成功

</details>

<details>

<summary> Trae</summary>

在应用边侧打开AI功能管理按钮(⚙图标),选择`MCP`,点击`手动添加`中的`从JSON导入`,输入如下内容:

```json
{
  "mcpServers": {
    "Jupyter-MCP-Server" : {
        ...(上述具体内容)
    }
  }
}
```

点击确认,打开对应的MCP服务器,查看是否连接成功

</details>

<details>

<summary> Cline</summary>

在对话底部打开`Manager MCP Servers`,点击设置按钮(⚙图标),选择`Installed`,点击`Configure MCP Servers`就会跳转到`cline_mcp_settings.json`文件,呈现的示例结果如下:

```json
{
  "mcpServers": {
    ...(已有的MCP,若没有则为空)
  }
}
```

在已有的MCP后添加`,`(英文半角符号)(若无则无需添加),将之前已经填充完善好的JSON文件黏贴之后,最终的参考结果如下:

```json
{
  "mcpServers": {
    ...(已有的MCP,若没有则为空),
    "Jupyter-MCP-Server" : {
        ...(上述具体内容)
    }
  }
}
```

最后保存并关闭`cline_mcp_settings.json`文件,返回查看是否出现名为`Jupyter-MCP-Server`的MCP服务,启动并等待片刻,如果变绿灯则表明MCP服务启动成功

</details>

<details>

<summary> Gemini CLI</summary>

可以直接在终端中输入下述命令:

```bash
gemini mcp add Jupyter-MCP-Server uv run --directory your/path/to/jupyter-mcp-server src/server.py
```

或者也可以在项目中`.gemini`文件夹下的`settings.json`文件中添加如下内容:

```json
{
    ...(已有的配置,若没有则为空),
    "mcpServers":{
        ...(已有的MCP,若没有则为空),
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {}
        }
    }
}
```

</details>

<details>

<summary> Qwen Coder</summary>

可以直接在终端中输入下述命令:

```bash
qwen mcp add Jupyter-MCP-Server uv run --directory your/path/to/jupyter-mcp-server src/server.py
```

或者也可以在项目中`.qwen`文件夹下的`settings.json`文件中添加如下内容:

```json
{
    ...(已有的配置,若没有则为空),
    "mcpServers":{
        ...(已有的MCP,若没有则为空),
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/server.py"
            ],
            "env": {}
        }
    }
}
```

</details>

<details>

<summary> Claude Code</summary>

可以直接在终端中输入下述命令:

```bash
claude mcp add Jupyter-MCP-Server uv run --directory your/path/to/jupyter-mcp-server src/server.py
```

</details>

