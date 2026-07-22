# 科林JD智能生成系统

基于Streamlit构建的岗位说明书智能转换工具，支持任意格式JD上传、AI润色补全、按公司模板标准化输出。

## 功能特性

- 📤 **多格式导入**：支持DOCX、PDF、PPTX、TXT等格式的JD文件解析
- 🧠 **智能字段提取**：自动识别职位、部门、职责、任职要求等核心字段
- ✨ **AI润色补全**：接入大模型API，自动优化表述、补全缺失内容、对齐IQCIS价值观
- 🎨 **模板精准匹配**：严格遵循公司JD模板格式、金黄色主题（#FABD00）、三列表格结构
- 📥 **双格式导出**：一键下载标准Word版和PDF版
- 🌐 **Web端部署**：基于Streamlit，开箱即用

## 快速开始

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/jd-template-generator.git
cd jd-template-generator

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
streamlit run app.py
```

### 部署到Streamlit Community Cloud

1. 将代码推送到GitHub仓库
2. 登录 [share.streamlit.io](https://share.streamlit.io)
3. 点击 "New app"，选择对应仓库和分支
4. 主文件路径填写 `app.py`
5. 点击 "Deploy" 完成部署

## 配置说明

### API配置
系统支持接入符合OpenAI格式的大模型API（DeepSeek、GPT、通义千问等）：
- 在侧边栏输入API地址和密钥
- 支持JSON模式输出，确保字段结构化返回
- API密钥仅在当前会话使用，不会持久化存储

### 自定义模板
1. 在侧边栏勾选"使用自定义模板"
2. 上传带公司样式的.docx模板文件
3. 模板中使用 `{{占位符}}` 标记填充位置

## 项目结构

```
jd-template-generator/
├── app.py                 # Streamlit主应用
├── requirements.txt       # 依赖清单
├── utils/
│   ├── parser.py          # 多格式文档解析
│   ├── extractor.py       # JD字段提取
│   ├── api_client.py      # AI API客户端
│   ├── generator.py       # 模板渲染生成
│   └── pdf_converter.py   # DOC转PDF
└── README.md
```

## 技术栈

- **前端框架**：Streamlit 1.30+
- **文档处理**：python-docx, pdfplumber, python-pptx
- **PDF转换**：docx2pdf（依赖本地Office）
- **AI集成**：兼容OpenAI API规范
- **品牌色**：#FABD00 金黄色

## 注意事项

1. PDF转换功能需要Windows环境且安装Microsoft Office
2. 建议上传.docx格式以获得最佳解析效果
3. 内置模板严格匹配公司标准JD格式与IQCIS价值观附录

## 维护团队

科林集团人力资源部 - HR数字化项目组
