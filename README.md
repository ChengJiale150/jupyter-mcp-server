<div align="center">

<!-- omit in toc -->

# 🪐 Jupyter MCP Server

<img title="cover" src="https://raw.githubusercontent.com/ChengJiale150/jupyter-mcp-server/main/assets/cover.png" alt="Jupyter MCP Server" data-align="center" width="700">

<strong>专门为AI连接与管理Jupyter Notebook而开发的MCP服务</strong>

*由 [ChengJiale150](https://github.com/ChengJiale150) 开发*

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/better-jupyter-mcp-server.svg)](https://pypi.org/project/better-jupyter-mcp-server/)
[![mcp-registry](https://img.shields.io/badge/mcp--registry-v1.1.0-blue)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.ChengJiale150/jupyter-mcp-server)

[English](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/README_EN.md) | 中文

</div>

## 📖 目录

- [项目简介](#-项目简介)
- [工具一览](#-工具一览)
- [快速上手](#-快速上手)
- [最佳实践](#-最佳实践)
- [贡献指南](#-贡献指南)
- [致谢](#-致谢)

## 🎯 项目简介

Jupyter MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的服务，为目前最先进的的AI IDE(如 [Cursor](https://www.cursor.com/)) 与CLI工具(如[Gemini CLI](https://github.com/google-gemini/gemini-cli))提供连接与管理Jupyter Notebook的能力。使得AI能够操作Notebook，进行数据分析、可视化、机器学习等任务。

### 🤔 为什么需要Jupyter MCP Server

Jupyter Notebook 是数据科学家最常用的工具之一，它提供了一个交互式的环境，使其可以方便地进行数据分析、可视化、机器学习等探索性任务。然而，由于Notebook自身的格式限制，使得其难以像纯文本文件（如Markdown、Python文件）一样被AI直接理解。

现有的提供操作Notebook的工具或MCP服务，要么仅能阅读与编辑Notebook，要么仅能操纵单个Notebook，难以满足同时操纵多个Notebook的复杂需求。此外，大多数工具也不支持多模态输出，无法充分利用目前最先进的多模态大模型（如Gemini 2.5）的强大图文理解能力。

Jupyter MCP Server 就是为了解决这个问题而开发的。它通过MCP协议，向AI提供了管理Jupyter Kernel与Notebook的工具，使其能够操纵**多个Notebook**进行**交互式**的任务执行，并输出**多模态**结果，助力数据科学家提高分析效率。

### ✨ 关键亮点

- 🔌 **MCP兼容**: 能够在任何支持MCP协议的IDE或CLI工具中使用
- 📚 **多Notebook管理**: 支持同时管理多个Notebook
- 🔁 **交互式执行**: 能够根据Cell的输出自动调整执行策略
- 📊 **多模态输出**: 支持输出多模态结果，如文本、图片、表格等

## 🔧 工具一览

### Notebook管理模块

| 名称               | 描述                 | 说明                                  |
|:----------------:|:------------------:|:-----------------------------------:|
| connect_notebook | 连接/创建指定路径的Notebook | 因为需要启动Kernel,工具执行时间较长(10s~30s)      |
| list_notebook    | 列出所有目前连接的Notebook  | 用于查看目前已经连接的Notebook,方便多Notebook任务执行 |
| restart_notebook | 重启指定名称的Notebook    | 清除所有导入包与变量                          |
| read_notebook    | 读取指定名称的Notebook的源内容(不包含输出) | 用于查看Notebook的源内容,仅在明确要求时才使用 |

### Cell基本功能模块

| 名称           | 描述                             | 说明              |
|:------------:|:------------------------------:|:---------------:|
| list_cell    | 列出指定名称的Notebook的所有Cell的基本信息    | 用于定位Cell的索引与作用  |
| read_cell    | 读取指定名称的Notebook指定索引的Cell内容     | 支持图像、表格、文本等多种输出 |
| delete_cell  | 删除指定名称的Notebook指定索引的Cell       |                 |
| insert_cell  | 在指定名称的Notebook指定索引处上方/下方插入Cell |                 |
| execute_cell | 执行指定名称的Notebook指定索引的Cell       | 返回Cell的输出结果     |
| overwrite_cell | 覆盖指定名称的Notebook指定索引的Cell内容 | 用于修改Cell内容     |

### Cell高级集成功能模块

| 名称                     | 描述                     | 说明                                   |
|:----------------------:|:----------------------:|:------------------------------------:|
| append_execute_code_cell    | 在Notebook末尾添加并执行Code Cell   | insert+execute的组合为高频操作,将其组合减少工具的调用次数 |
| execute_temporary_code | 执行临时代码块(不存储到Notebook中) | 用于进行魔法指令执行、代码片段调试、查看中间变量取值等临时操作      |

工具的具体内容详见[工具文档](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/tools.md)

## 🛠️ 快速上手

### 环境准备

- Python 3.12+(推荐使用[Anaconda](https://www.anaconda.com/))
- uv(安装详见[安装指南](https://docs.astral.sh/uv/getting-started/installation/))

### 安装Jupyter MCP Server

<details>

<summary>uvx 快速安装(推荐)</summary>

在安装uv后,直接配置MCP的JSON格式即可,示例如下:

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uvx",
            "args": [
                "better-jupyter-mcp-server"
            ],
            "env": {
                "ALLOW_IMG": "true"
            },
            "transport": "stdio"
        }
    }
}
```

具体客户端集成详见[集成文档](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/integration.md)

</details>

<details>

<summary>源代码</summary>

1. **克隆项目并安装依赖**

```bash
git clone https://github.com/ChengJiale150/jupyter-mcp-server
cd jupyter-mcp-server
uv sync
```

2. **(可选)配置config.toml**

进入[src/config.toml](./src/config.toml)文件,根据需要配置参数(如是否允许返回图片数据)

3. **启动Jupyter MCP Server**

```bash
uv run fastmcp run src/main.py
```

如果成功启动,会输出类似如下信息代表启动成功:

```bash
[09/14/25 20:14:59] INFO     Starting MCP server 'Jupyter-MCP-Server' with transport 'stdio'  
```

4. **配置标准JSON格式**

```json
{
    "mcpServers":{
        "Jupyter-MCP-Server":{
            "command": "uv",
            "args": [
                "run",
                "--directory",
                "your/path/to/jupyter-mcp-server",
                "src/main.py"
            ],
            "env": {},
            "transport": "stdio"
        }
    }
}
```


具体客户端集成详见[集成文档](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/integration.md)

</details>

### 使用Jupyter MCP Server

<details>

<summary>本地手动启动Jupyter Server</summary>

在正式使用前,需要连接Jupyter Server,这里介绍如何在本地手动启动Jupyter Server:

1. **打开终端并激活环境**:

打开计算机终端命令行,并激活环境

对于使用conda(Anaconda)的用户,可以使用以下命令激活环境:

```bash
conda activate your_environment_name
```

这里为了方便起见,这里可以直接使用`base`环境(`conda activate base`)

然后切换到你当前的项目目录,方便后续的文件操作

```bash
cd your/path/to/your/project
```

2. **安装必要依赖**:

```bash
pip uninstall -y pycrdt datalayer_pycrdt
pip install jupyter nbformat datalayer_pycrdt jupyter-collaboration
```

3. **启动Jupyter Server**:

使用下述命令启动Jupyter Server

```bash
jupyter lab
```

成功启动后会弹出浏览器窗口,你可以在此查看根路径是否为工程目录

4. **获取认证Token**:

使用下述命令获取认证Token

```bash
jupyter server list
```

运行后会输出类似如下信息:

```bash
http://localhost:8888/?token=YOUR_TOKEN :: YOUR_PROJECT_PATH
```

其中`YOUR_TOKEN`为认证Token

5. **添加提示词与规则**

在正式使用前,你**必须**添加如下提示词于规则文件中以提供Jupyter MCP Server的必要连接信息:

```
以下是Jupyter服务器连接参数:
URL = http://localhost:8888
Token = YOUR_TOKEN
```

此外,推荐在提示词中添加关键Notebook路径信息,方便AI快速定位目标Notebook提高`connect_notebook`工具的执行效率,可以在Jupyter Lab网页中右键点击目标Notebook文件,选择`Copy Path`获取相对路径

在提供上述内容后,你就可以开始使用Jupyter MCP Server了!

</details>

<details>

<summary>使用LLM托管Jupyter Server</summary>

1. **安装必要依赖**:

```bash
pip uninstall -y pycrdt datalayer_pycrdt
pip install jupyter nbformat datalayer_pycrdt jupyter-collaboration
```

2. **提供提示词与规则文档**:

```markdown
## Jupyter MCP Server 使用指南

在正式使用Jupyter MCP Server前,你**必须**完成如下步骤:

1. **启动Jupyter Server**:

在当前项目目录中以不阻塞当前终端的方式在命令行终端中输入启动Jupyter Server,例如:
- `Window`: `start jupyter lab`
- `MacOS/Linux`: `nohup jupyter lab &`

2. **获取URL与认证Token**:

使用`jupyter server list`获取URL与认证Token

仅当完成上述步骤后,你才可以使用Jupyter MCP Server
```

</details>

## ✅ 最佳实践

- 使用支持多模态输入的大模型(如Gemini 2.5 Pro)进行交互,以充分利用最先进的多模态理解能力
- 使用支持MCP协议返回图像数据并支持解析的客户端(如Cursor、Gemini CLI等),部分客户端可能不支持该功能
- 将复杂任务(如数据科学建模)拆分为多个子任务(如数据清洗、特征工程、模型训练、模型评估等),并逐步执行
- 给出结构清晰的提示词与规则,这里可以参考[提示词与规则文档](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/docs/prompt_example.md)
- 在提示词中融入**专家经验与智慧**(如数据清洗、特征工程的技巧),这是AI最缺乏的,也是最需要补充的
- 尽可能提供丰富的上下文信息(如现有数据集的字段解释,文件路径,详细的任务要求等)
- 提供Few Shot案例,提供Baseline或已有Workflow作为参考

### 示例

- [Titanic数据集分析](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/example/Titanic)

## 🤝 贡献指南

我们欢迎社区贡献！如果您想为Jupyter MCP Server项目做出贡献，请：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 贡献类型

- 🐛 Bug修复
- 📝 旧功能完善
- ✨ 新功能开发
- 📚 文档改进
- 🌍 国际化支持

### 开发帮助文档

- 可以详见[项目架构文档](https://github.com/ChengJiale150/jupyter-mcp-server/blob/main/src/README.md)辅助理解项目架构与关键通信流程

## 🤗 致谢

本项目受到以下项目的帮助,在此表示感谢:

- [DataLayer](https://github.com/datalayer): 感谢DataLayer开源的[jupyter_nbmodel_client](https://github.com/datalayer/jupyter-nbmodel-client)与[jupyter_kernel_client](https://github.com/datalayer/jupyter-kernel-client)库,为Jupyter MCP的快速开发提供了极大的帮助
- [FastMCP](https://github.com/jlowin/fastmcp): 感谢FastMCP的开发者们,没有FastMCP就没有Jupyter MCP的快速集成

此外,本项目还参考了以下已有Jupyter MCP服务的实现,在此也一并表示感谢:

- [datalayer/jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)
- [jjsantos01/jupyter-notebook-mcp](https://github.com/jjsantos01/jupyter-notebook-mcp)
- [ihrpr/mcp-server-jupyter](https://github.com/ihrpr/mcp-server-jupyter)
- [itisaevalex/jupyter-mcp-extended](https://github.com/itisaevalex/jupyter-mcp-extended)

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

Made with ❤️ by [ChengJiale150](https://github.com/ChengJiale150)

</div>