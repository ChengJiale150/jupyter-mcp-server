# 🛠️ 工具使用说明

本文档详细介绍了 Jupyter MCP Server 提供的所有工具，旨在帮助用户理解和使用这些工具与Jupyter Notebook进行交互。

## Notebook管理模块

### `connect_notebook`

- **作用**: 连接或创建指定路径的Notebook。
- **输出内容**: 成功连接或创建Notebook后，返回Notebook的Cell基本信息(如Cell的索引、类型、首行内容等)
- **必要说明**: 
    - 需要在提示词中提供Jupyter服务连接参数(URL地址和Token),否则工具无法正常工作。
    - `notebook_name`用于标识不同Notebook的唯一名称,必须唯一。
    - 由于此工具需要启动Jupyter Kernel，执行时间可能较长（10-30秒）。
    - 如果使用`connect`模式连接Notebook，则Notebook路径必须存在。
    - 如果使用`create`模式创建Notebook，则Notebook路径必须不存在。
    - 如果使用`reconnect`模式重新连接Notebook，则Notebook路径必须与之前连接的Notebook路径相同。
    - 连接信息可以持久保存,但在MCP服务器重启后,连接的Notebook会丢失,需要重新连接。
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `server_url` | `str` | Jupyter服务启动的URL地址 | |
| `token` | `str` | 用于Jupyter服务认证的Token | |
| `notebook_name` | `str` | 用于标识不同Notebook的唯一名称 | |
| `notebook_path` | `str` | Notebook的相对路径 | |
| `mode` | `Literal["connect", "create", "reconnect"]` | 连接模式。`connect`用于连接已存在的Notebook，`create`用于创建新的Notebook，`reconnect`用于重新连接已存在的Notebook。 | `"connect"` |

---

### `list_notebook`

- **作用**: 列出所有当前已连接的Notebook。
- **输出内容**: 以表格形式返回所有已连接的Notebook的名称、Jupyter URL地址和Notebook路径。
- **必要说明**: 用于查看已连接的Notebook，方便AI在多个Notebook之间进行切换和操作。
- **参数说明**: 无输入参数

---

### `restart_notebook`

- **作用**: 重启指定Notebook的内核，此操作会清除所有已导入的包和已定义的变量。
- **输出内容**: 返回重启Notebook的结果信息。
- **必要说明**: 当内核无响应或需要重置环境时使用。
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | 要重启的Notebook的名称 | |

---

### `read_notebook`

- **作用**: 读取指定Notebook的源内容(不包含输出)，支持分页功能。
- **输出内容**: 返回Notebook的源内容(包括索引、类型、执行计数和完整源代码)，支持分页显示以避免一次性返回过多内容。
- **必要说明**: 
    - 仅在明确要求时才使用。
    - 支持分页功能，可以通过`start_index`和`limit`参数控制返回的Cell范围。
    - 当Notebook包含大量Cell时，建议使用分页功能分批读取。
- **参数说明**:
| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | 要读取的Notebook的名称 | |
| `start_index` | `int` | 起始Cell索引(从0开始)，用于分页 | `0` |
| `limit` | `int` | 最大返回的Cell数量(0表示无限制) | `20` |

## Cell基本功能模块

### `list_cell`

- **作用**: 列出指定Notebook中所有Cell的基本信息。
- **输出内容**: Notebook的Cell基本信息(如Cell的索引、类型、执行计数、首行内容等)
- **必要说明**: 
    - 用于快速概览Notebook的结构与状态，定位特定Cell的索引和内容类型。
    - 为了节省Token消耗,仅返回首行内容,因此推荐在首行内容中包含足够的信息(如该Cell的作用),方便AI定位具体Cell。
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |

---

### `read_cell`

- **作用**: 读取Notebook中指定索引的Cell内容。
- **输出内容**: 返回Cell的源代码、执行计数以及多模态输出内容(如文本、图片等),以列表形式返回。
- **必要说明**: 
    - 支持读取Cell块的所有内容,可以与`list_cell`工具结合使用,方便AI具体了解Cell详细内容。
    - 可以在`src/config.toml`中配置是否返回Cell的图像编码的Base64字符串,默认返回。
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |
| `cell_index` | `int` | 要读取的Cell的索引 | |
| `return_output` | `bool` | 是否包含Cell的输出内容 | `True` |

---

### `delete_cell`

- **作用**: 删除Notebook中指定索引的Cell。
- **输出内容**: 返回删除后当前Notebook的最新结构信息
- **必要说明**: 
    - 由于删除操作会直接修改Notebook的结构,因此不推荐一次性删除多个Cell,以免误删
    - 如果非要删除多个Cell,请明确告诉AI按索引从大到小依次删除
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称。 | |
| `cell_index` | `int` | 要删除的Cell的索引 | |

---

### `insert_cell`

- **作用**: 在Notebook中指定索引的上方或下方插入一个新的Cell。
- **输出内容**: 返回插入后当前Notebook的最新结构信息
- **必要说明**: 
    - 插入操作会直接修改Notebook的结构,因此不推荐一次性插入多个Cell,以免插入顺序混乱
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |
| `cell_index` | `int` | 作为锚点的Cell的索引 | |
| `cell_type` | `Literal["code", "markdown"]` | 要插入的Cell的类型 | |
| `cell_content` | `str` | 要插入的Cell的内容 | |
| `direction` | `Literal["above", "below"]` | 在锚点索引的`上方`或`下方`插入 | `"below"` |

---

### `execute_cell`

- **作用**: 执行Notebook中指定索引的Cell（仅限`code`类型）。
- **输出内容**: 返回Cell的输出结果,支持多模态输出。如果执行超时,将返回超时错误信息。
- **必要说明**: 带超时时间参数,防止因为Kernel无响应导致一直等待
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |
| `cell_index` | `int` | 要执行的Cell的索引 | |
| `timeout` | `int` | 执行的超时时间（秒） | `60` |

---

### `overwrite_cell`

- **作用**: 覆盖（修改）Notebook中指定索引的Cell内容。
- **输出内容**: 返回覆盖前后Cell的内容对比(diff风格, `+`表示新行, `-`表示删除行)
- **必要说明**: 用于修改已有Cell的代码或文本
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |
| `cell_index` | `int` | 要覆盖的Cell的索引 | |
| `cell_content` | `str` | 新的Cell内容 | |

## Cell高级集成功能模块

### `append_execute_cell`

- **作用**: 在Notebook的末尾添加一个新的Cell并立即执行它。
- **输出内容**: 返回执行后Cell的输出结果,支持多模态输出。如果执行超时,将返回超时错误信息。
- **必要说明**: 这是一个高频操作,等同于`insert_cell`（在末尾）和`execute_cell`的组合,旨在减少工具调用次数。
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |
| `cell_type` | `Literal["code", "markdown"]` | 要添加的Cell的类型 | |
| `cell_content` | `str` | 要添加的Cell的内容 | |
| `timeout` | `int` | 执行的超时时间（秒） | `60` |

---

### `execute_temporary_cell`

- **作用**: 执行临时的代码块，其内容不会被保存到Notebook中。
- **输出内容**: 内核执行后的输出结果,支持多模态输出
- **必要说明**:
    - 直接与内核交互,不添加到Notebook中
    - **适用场景**:
        - 执行魔法指令（如 `%pip install`）。
        - 调试代码片段。
        - 查看中间变量的值（如 `print(df.head())`）。
    - **禁止**:
        - 导入新模块或进行变量赋值等任何会对后续Notebook运行产生影响的操作。
        - 执行需要长时间运行的代码。
- **参数说明**:

| 参数名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| `notebook_name` | `str` | Notebook的名称 | |
| `cell_content` | `str` | 要临时执行的代码内容 | |
