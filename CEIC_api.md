这是一份为您将提供的PDF文本内容转换而成的Markdown文档，并在保留所有原始文本的同时，按照逻辑分层进行了格式化处理：

CEIC API 用户手册 (2.2版) 



©2018 CEIC Data。版权所有。 CEIC 1 



------

1. 产品概述 



CEIC 2 CEIC API v2 提供了获取CEIC 不同时间数列数据和CDMNext 数据分析文件(即数据模板)的直接途径。 CEIC API Python、PHP 和JavaScript SDK库允许用户使用首选编程语言与CEIC API v2 实现交互。 



2. CEIC API 特征 



CEIC API v2 版本具有如下关键特征: 



- RESTful API 

  

  

- 通过CEIC 数据时间数列实现强大的搜索功能 

  

  

- 时间点和元数据提取 

  

  

- 时间数列位置参考(布局树复制) 

  

  

- 全面的数据模板文档检索 

  

  

- 词典参考资源 

  

  

- CDMNext 用户界面,用于管理API访问和生成API调用 

  

  

- XML JSON 和CSV 等输出格式 

  

  

- 时间数据馈送能力-检索和比较数据时间点的变化 

  

  

- 交互式在线文档 

  

  

- Python、PHP 和 JavaScript SDKs 

  

  

- 访问 CEIC API 





**安装环境:** 



- 当前 CEIC 数据订阅用户 

  

  

- CDMNext 和CEIC API访问权限已激活 

  

  

- 拥有CDMNext 用户名和密码 CEIC 3 

  

  

- 有效的CEIC API访问密钥,可在CDMNext平台上生成(请参阅下面的访问密钥部分) 

  

  

- 可选:CEIC API Python、JavaScript 和 PHP SDKs(适用于使用这些语言与API实现交互的用户) 

  

  



**访问秘钥:** 



> 15+ 15+ 山图表 土下载 E 通过API秘钥管理CEIC API访问权限。 Emily Jiang ejiang@ceicdata.com 中文 English 日本語 한국어 Pусский Bahasa 个人资料 偏好设置 数字格式 来宾模式 键盘快捷键 键入Shift+?查看 快捷键设置 Excel插件 CEIC API访问权限 登出 

API 密钥基于CDMNext 用户信息生成或完成验证。 生成新密钥后,旧密钥将自动失效。 



> CEIC API访问权限 您已经生成了API密钥。您可以在此验证您的API密钥,或者生成新密钥来替换您以前的密钥 粘贴您的API密钥 以验证密钥 开启 CEIC API帮助 验证秘钥 生成新秘钥 



**安装和更新 CEIC API SDKS** 



用户首次使用 CEIC API SDK时,需要首先将其添加到相应的语言库中。 在手动安装语言库时,用户可使用CDMNext 帮助页面的最新文件或直接在相应的知识库进行查找: 





**Python SDK** `pip install --extra-index-url https://downloads.ceicdata.com/python ceic_api_client-upgrade` 





**PHP SDK** In your composer.json add the following code: 



JSON

```
"require": { [cite: 65]
"ceic/api": [cite: 66]
}, [cite: 67]
"repositories": [ [cite: 68]
11 [cite: 69]
X [cite: 70]
{ [cite: 71]
"type": "composer", [cite: 72]
"url": "https://downloads.ceicdata.com/php/" [cite: 73]
} [cite: 74]
] [cite: 75]
```

CEIC Then run: `composer update` 





**JavaScript SDK** `npm install npm install https://downloads.ceicdata.com/javascript/CeicApi-1.2.0.tar.gz` JavaScript SDK `npm install https://downloads-stage.ceicdata.com/javascript/CeicApi-1.2.0.tar.gz` 



4. API文档 





**CEIC API 文档** 



CEIC API v2 具有交互式在线文档,点击此处进行访问。 如需测试文档输出功能,用户需要使用有效的CEIC API v2 密钥。 用户还可在同一页面找到具体的Python、PHP 和JavaScript SDK 文档链接,包括不同语言的代码实例。 



5. CDMNEXT 用户界面可生成 API调用 



API 用户可使用复制到剪贴板(CTC)选项,适用于以下 CDMNext 板块: 





**CDMNext 搜索板块的API CTC 选项** 



> China GDP 数据库 全部 数列 数据集 重点数列 全部数据库 70匹配数据模板| 世界趋势数据库(307,416中的77)  + 全球数据库(3,400,137中的902) 11,007 数列 筛选 复制为URL 复制为R代码 </> 复制为API调用  > <> HTTP请求 Python代码 列 PHP代码 15 JavaScript代码 

CEIC 5 



API 的复制到剪贴板选项可生成一个API http 调用或一个Python/PHP/JavaScript代码,均可在各平台按所选定的筛选条件来执行相同的搜索。 





**CDMNext 下载板块的API CTC选项:** 



> 下载/仅限于CTC数据(数列标签) 下载搜索结果(1条数列) 数列 格式 X 制图 观测时间 全部 范围 样本 API类型 HTTP请求 缺失观测值 过滤没有观测的日期 响应格式 JSON √ 始终询问我导出设置 <1> CEIC API帮助 APE 重设 取消 复制到剪贴板 X 

API 复制到剪贴板功能可生成一个API http 调用或一个Python/PHP/JavaScript代码,并在平台中检索已定义选项的选定数列。 用户可自行定义数列检索的时间段和缺失观测值的格式,选择以json、xml 或 csv 格式来检索数列。 





***关于可操作数列的注意事项\*** 从CEIC API 2.2版本开始,用户将能够检索带有应用函数的时间数列数据。 若为CEIC API 2.1 或更低版本,如果用户尝试使用CDMNext CTC 函数导出带有应用函数的数列,经函数转换的数据将会丢失,只能检索出基础数据。 



> 下载/CTC全部数据模板(制图标签) 下载所选数列(所有制图条数列) 数列 制图 格式 X XLS FDF <1> APT API类型 响应格式 始终询问我导出设置 HTTP请求 XLSX 

CEIC 6 



> 重设 取消 复制到剪贴板 X 

API 的复制到剪贴板选项可以就此生成一个API http 调用或Python / PHP / JavaScript代码,并根据用户具体选择的标准,检索整个数据模板为excel 或pdf文件。 



6. 支持 



CEIC API v2 由CEIC 数据库团队开发。 如有任何问题或疑问,请联系您的CEIC 客户经理或使用CDMNext 帮助菜单栏下的自助服务和联系选项。 



> 帮助 申请帮助 Excel件 打开X API R Eviews 联系我们 电邮我们 CEIC数据可以通过CEIC API直接访问,使用支持的SDK、用于支持的编程语言的CEIC API SDK的新版本可以使用下面的文件手动安装,或直接从相应的存储库安装 知识库 诊断 Select SDK: Python 问题反馈 在线聊天启 申请 pip install extra Indes url https://dwal nada, [celedata.com/python](https://www.google.com/search?q=https://celedata.com/python) csic_spi_cllent perad Excel插件 视频教学 下载CEIC API SDK API 虚拟学习 R Download Python SDK 文件名:ceic_api_client-1.1.0.tar.gz 快速开始向导 EViews 搜索帮助 键盘快捷键 文件 CEIC API Documentation CEIC Python SDK Development Guide ● CEIC API 快速入门指南(2.1版) 

------

请问您是否还需要对其中的SDK配置部分或其它内容进行进一步梳理和调整？