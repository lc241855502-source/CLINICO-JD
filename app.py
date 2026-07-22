import streamlit as st
import io
import os
import sys
import tempfile

# 添加工具包路径
sys.path.append(os.path.dirname(__file__))

from utils.parser import parse_document
from utils.extractor import extract_jd_fields
from utils.api_client import polish_jd_with_api
from utils.generator import generate_jd_document
from utils.pdf_converter import docx_to_pdf

# 页面配置
st.set_page_config(
    page_title="科林JD智能生成系统",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 金黄色主题自定义样式
st.markdown("""
<style>
    .stButton>button {
        background-color: #FABD00;
        color: #333333;
        border: none;
        font-weight: 600;
        border-radius: 6px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #E6AC00;
        color: #333333;
        box-shadow: 0 2px 8px rgba(250, 189, 0, 0.3);
    }
    .stButton>button:disabled {
        background-color: #f0f0f0;
        color: #999;
    }
    h1, h2, h3 {
        color: #333333;
    }
    hr {
        border-color: #FABD00;
        opacity: 0.3;
    }
</style>
""", unsafe_allow_html=True)

# 模板文件路径
DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), 'template', 'company_template.docx')

# 侧边栏配置
with st.sidebar:
    st.title("⚙️ 系统配置")
    
    st.subheader("API设置")
    api_enabled = st.checkbox("启用AI智能提取+润色", value=True)
    api_url = st.text_input(
        "API接口地址",
        value="https://api.deepseek.com/chat/completions",
        help="兼容OpenAI格式的大模型API端点"
    )
    api_key = st.text_input(
        "API Key",
        type="password",
        help="API密钥仅在当前会话使用，不会存储"
    )
    
    st.divider()
    
    st.subheader("模板设置")
    use_custom_template = st.checkbox("使用自定义模板", value=False)
    if use_custom_template:
        custom_template_file = st.file_uploader(
            "上传公司JD模板 (.docx)",
            type=['docx'],
            help="上传带有公司完整样式的Word模板文件"
        )
    else:
        st.info("✅ 使用内置公司标准模板")
    
    st.divider()
    st.caption("科林集团 HR数字化工具 v2.0")

# 主界面
st.title("📋 JD智能匹配生成系统")
st.markdown("上传任意格式的岗位说明书，AI智能提取字段，自动填充公司标准模板，一键导出DOC/PDF")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 上传原始JD")
    uploaded_file = st.file_uploader(
        "支持格式：DOCX, PDF, PPTX, TXT",
        type=['docx', 'pdf', 'pptx', 'txt'],
        help="拖拽或点击上传任意格式的JD文件"
    )
    
    extracted_fields = None
    
    if uploaded_file:
        st.success(f"✅ 已上传：{uploaded_file.name}")
        
        # 解析文档
        with st.spinner("正在解析文档内容..."):
            file_bytes = uploaded_file.read()
            raw_text = parse_document(file_bytes, uploaded_file.name)
        
        with st.expander("查看原始文本", expanded=False):
            st.text_area("解析结果", raw_text, height=200, label_visibility="collapsed")
        
        # AI智能提取字段
        if api_enabled and api_key:
            with st.spinner("🤖 AI正在智能提取JD字段..."):
                extracted_fields = extract_jd_fields(raw_text, api_url, api_key)
                st.success("✅ AI字段提取完成！")
        else:
            # 降级为正则提取
            with st.spinner("正在提取JD字段..."):
                extracted_fields = extract_jd_fields(raw_text)
                st.info("ℹ️ 未配置API，使用基础提取模式")
        
        st.subheader("2. 字段确认与编辑")
        st.caption("AI自动提取的字段，可手动修改后再生成")
        
        if extracted_fields:
            with st.form("jd_editor_form"):
                # 基本信息
                position_title = st.text_input("职位名称", value=extracted_fields.get('position_title', ''))
                department = st.text_input("部门", value=extracted_fields.get('department', ''))
                line_manager = st.text_input("直线经理", value=extracted_fields.get('line_manager', ''))
                subordinate = st.text_input("下属", value=extracted_fields.get('subordinate', ''))
                location = st.text_input("工作地点", value=extracted_fields.get('location', ''))
                
                # 岗位目的
                position_purpose = st.text_area(
                    "岗位目的",
                    value=extracted_fields.get('position_purpose', ''),
                    height=80
                )
                
                # 主要职责
                resp_value = extracted_fields.get('responsibilities', '')
                if isinstance(resp_value, list):
                    resp_value = '\n'.join([f"• {r}" for r in resp_value])
                responsibilities = st.text_area(
                    "主要职责",
                    value=resp_value,
                    height=150
                )
                
                # 任职要求
                col_a, col_b = st.columns(2)
                with col_a:
                    education = st.text_input("教育背景", value=extracted_fields.get('education', ''))
                    experience = st.text_input("工作经验", value=extracted_fields.get('experience', ''))
                with col_b:
                    skills = st.text_input("专业技能", value=extracted_fields.get('skills', ''))
                    abilities = st.text_input("能力要求", value=extracted_fields.get('abilities', ''))
                
                submit_col1, submit_col2 = st.columns(2)
                with submit_col1:
                    polish_button = st.form_submit_button("✨ AI润色优化", use_container_width=True)
                with submit_col2:
                    generate_button = st.form_submit_button("📄 直接生成", use_container_width=True)
        else:
            st.warning("字段提取失败，请检查文件格式")
            polish_button = False
            generate_button = False
    else:
        polish_button = False
        generate_button = False

with col2:
    st.subheader("3. 生成结果")
    
    # 会话状态保存润色结果
    if 'polished_data' not in st.session_state:
        st.session_state.polished_data = None
    
    # 未上传文件时显示提示
    if not uploaded_file:
        st.info("👈 请先在左侧上传JD文件")
    
    # 处理AI润色
    if uploaded_file and polish_button:
        if not api_enabled or not api_key:
            st.warning("请先在侧边栏启用API并填写API Key")
        else:
            with st.spinner("AI正在润色优化JD内容，对齐IQCIS价值观..."):
                current_data = {
                    'position_title': position_title,
                    'department': department,
                    'line_manager': line_manager,
                    'subordinate': subordinate,
                    'location': location,
                    'position_purpose': position_purpose,
                    'responsibilities': responsibilities,
                    'education': education,
                    'experience': experience,
                    'skills': skills,
                    'abilities': abilities
                }
                
                polished = polish_jd_with_api(current_data, api_url, api_key)
                st.session_state.polished_data = polished
                st.success("✅ AI润色完成！")
                
                with st.expander("查看润色详情", expanded=True):
                    st.json(polished)
    
    # 生成文档
    if uploaded_file and (generate_button or (polish_button and st.session_state.polished_data)):
        data_to_use = st.session_state.polished_data if st.session_state.polished_data else {
            'position_title': position_title,
            'department': department,
            'line_manager': line_manager,
            'subordinate': subordinate,
            'location': location,
            'position_purpose': position_purpose,
            'responsibilities': responsibilities,
            'education': education,
            'experience': experience,
            'skills': skills,
            'abilities': abilities
        }
        
        with st.spinner("正在生成标准JD文档..."):
            # 确定模板路径
            template_path = DEFAULT_TEMPLATE
            if use_custom_template and custom_template_file:
                tmp = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
                tmp.write(custom_template_file.getvalue())
                template_path = tmp.name
                tmp.close()
            
            # 检查模板是否存在
            if not os.path.exists(template_path):
                st.error(f"模板文件不存在: {template_path}")
                st.stop()
            
            # 生成Word（基于真实模板填充）
            docx_bytes = generate_jd_document(data_to_use, template_path)
            
            # 生成PDF
            try:
                pdf_bytes = docx_to_pdf(docx_bytes)
                pdf_available = True
            except Exception as e:
                st.warning(f"PDF生成失败（需Windows+Office环境）: {str(e)[:50]}")
                pdf_available = False
        
        st.success("✅ 文档生成完成！格式与公司模板完全一致")
        
        # 下载按钮
        file_name = f"JD_{data_to_use.get('position_title', '岗位')}_{data_to_use.get('department', '')}"
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 下载 Word 版",
                data=docx_bytes.getvalue(),
                file_name=f"{file_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        with col_d2:
            if pdf_available:
                st.download_button(
                    label="📥 下载 PDF 版",
                    data=pdf_bytes.getvalue(),
                    file_name=f"{file_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("📥 下载 PDF 版", disabled=True, use_container_width=True, 
                         help="PDF转换需要Windows环境且安装Microsoft Office")
        
        # 内容预览
        with st.expander("文档内容预览", expanded=True):
            st.subheader(data_to_use.get('position_title', ''))
            st.caption(f"部门：{data_to_use.get('department', '')} | 地点：{data_to_use.get('location', '')}")
            
            st.markdown("**岗位目的**")
            st.write(data_to_use.get('position_purpose', ''))
            
            st.markdown("**主要职责**")
            resp = data_to_use.get('responsibilities', '')
            if isinstance(resp, list):
                for item in resp:
                    st.write(f"- {item}")
            else:
                st.write(resp)
            
            st.markdown("**任职要求**")
            st.write(f"- 教育背景：{data_to_use.get('education', '')}")
            st.write(f"- 工作经验：{data_to_use.get('experience', '')}")
            st.write(f"- 专业技能：{data_to_use.get('skills', '')}")
            st.write(f"- 能力要求：{data_to_use.get('abilities', '')}")

# 底部
st.divider()
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
    科林集团人力资源部 | IQCIS价值观驱动 | 基于公司标准模板生成
</div>
""", unsafe_allow_html=True)
