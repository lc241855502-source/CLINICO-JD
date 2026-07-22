from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT
import io
import os

# 公司品牌色 - 金黄色 #FABD00
BRAND_COLOR = RGBColor(0xFA, 0xBD, 0x00)
BRAND_COLOR_HEX = "FABD00"
TEXT_DARK = RGBColor(0x33, 0x33, 0x33)
TEXT_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

def generate_jd_document(data, template_path=None):
    """
    按照公司JD模板生成Word文档
    金黄色主题 + 三列表格结构 + IQCIS价值观附录
    """
    if template_path and os.path.exists(template_path):
        doc = Document(template_path)
        _fill_jd_content(doc, data)
    else:
        doc = Document()
        _setup_document_style(doc)
        _build_template_structure(doc)
        _fill_jd_content(doc, data)
    
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def _setup_document_style(doc):
    """设置文档全局基础样式"""
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(10.5)
    style.font.color.rgb = TEXT_DARK
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)

def _set_cell_background(cell, color_hex):
    """设置单元格背景色"""
    cell_xml = cell._tc
    cell_props = cell_xml.get_or_add_tcPr()
    shading = cell_props.makeelement(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd', {}
    )
    shading.set(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill',
        color_hex
    )
    cell_props.append(shading)

def _build_template_structure(doc):
    """构建公司JD模板完整结构 - 严格匹配三列布局 + 金黄色主题"""
    
    # ===== 文档大标题 =====
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('Job Description 岗位描述')
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = BRAND_COLOR
    
    doc.add_paragraph()
    
    # ===== 基本信息表（三列）=====
    info_table = doc.add_table(rows=8, cols=3)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_table.style = 'Table Grid'
    
    # 表头行（金黄色背景 + 白色文字）
    headers = ['Position', 'Position', 'Position']
    for i, h in enumerate(headers):
        cell = info_table.cell(0, i)
        cell.text = h
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.color.rgb = TEXT_WHITE
                r.font.size = Pt(11)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_cell_background(cell, BRAND_COLOR_HEX)
    
    # 基本信息行标签（中英双语）
    info_labels = [
        'Position Title:\n职务名称：',
        'Department:\n部门：',
        'Line Manager:\n直线经理：',
        'Subordinate：\n下属：',
        'Location：\n工作地点：',
        'Prepared by:\n起草人：',
        'Revision Date:\n修订日期：',
    ]
    
    for i, label in enumerate(info_labels):
        row_idx = i + 1
        info_table.cell(row_idx, 0).text = label
    
    # 设置列宽
    info_table.columns[0].width = Cm(4.5)
    info_table.columns[1].width = Cm(5.5)
    info_table.columns[2].width = Cm(5.5)
    
    doc.add_paragraph()
    
    # ===== 岗位目的部分 =====
    purpose_header = doc.add_paragraph()
    run = purpose_header.add_run(
        'Position purpose (A brief statement indicating the basic purpose of the position)'
    )
    run.bold = True
    run.font.color.rgb = BRAND_COLOR
    run.font.size = Pt(11)
    
    purpose_sub = doc.add_paragraph()
    run_sub = purpose_sub.add_run('岗位目的 （表明该职位基本作用的简要陈述）')
    run_sub.bold = True
    run_sub.font.size = Pt(10)
    
    doc.add_paragraph('{{POSITION_PURPOSE}}')
    doc.add_paragraph()
    
    # ===== 主要职责部分 =====
    resp_header = doc.add_paragraph()
    run = resp_header.add_run('Major tasks and responsibilities of position')
    run.bold = True
    run.font.color.rgb = BRAND_COLOR
    run.font.size = Pt(11)
    
    resp_sub = doc.add_paragraph()
    run_sub = resp_sub.add_run('岗位主要任务与职责')
    run_sub.bold = True
    run_sub.font.size = Pt(10)
    
    doc.add_paragraph('{{RESPONSIBILITIES}}')
    doc.add_paragraph()
    
    # ===== 任职要求部分 =====
    qual_header = doc.add_paragraph()
    run = qual_header.add_run('Qualifications (Education, skills, experiences and abilities)')
    run.bold = True
    run.font.color.rgb = BRAND_COLOR
    run.font.size = Pt(11)
    
    qual_sub = doc.add_paragraph()
    run_sub = qual_sub.add_run('任职要求(教育，技能，经验以及能力)')
    run_sub.bold = True
    run_sub.font.size = Pt(10)
    
    doc.add_paragraph('{{QUALIFICATIONS}}')
    doc.add_paragraph()
    
    # ===== 底部审批栏（三列）=====
    approval_table = doc.add_table(rows=2, cols=3)
    approval_table.style = 'Table Grid'
    approval_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    approval_table.cell(0, 0).text = 'Line manager, date\n直线经理，日期'
    approval_table.cell(0, 2).text = 'Received by, date\n签收人，日期'
    
    approval_table.columns[0].width = Cm(5.5)
    approval_table.columns[1].width = Cm(5.0)
    approval_table.columns[2].width = Cm(5.5)
    
    # ===== 分页：科林价值观IQCIS =====
    doc.add_page_break()
    
    value_title = doc.add_paragraph()
    value_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = value_title.add_run('科林价值观IQCIS')
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = BRAND_COLOR
    
    doc.add_paragraph()
    
    value_table = doc.add_table(rows=6, cols=2)
    value_table.style = 'Table Grid'
    value_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # 表头（金黄色背景）
    value_table.cell(0, 0).text = 'Value\n价值观'
    value_table.cell(0, 1).text = 'Definition\n定义'
    for col in range(2):
        cell = value_table.cell(0, col)
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.color.rgb = TEXT_WHITE
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _set_cell_background(cell, BRAND_COLOR_HEX)
    
    # 价值观内容
    values = [
        ('Integrity\n诚信与尊重', 
         'Be trustworthy, respect others, treat internal and external clients consistently, and deliver on commitments\n值得信赖，尊重他人，对待内、外部客户一致，说到做到'),
        ('Quality\n品质承诺与客户导向', 
         'Always prioritize customers, be results-oriented, focus on quality, and ensure mission accomplishment\n工作始终以客户为第一优先，以结果为导向，注重品质，使命必达'),
        ('Collaboration\n合作与人才发展', 
         'Be good at collaborating with colleagues within and across departments to improve work efficiency, and enhance one\'s professional capabilities through various channels to strive for better performance\n善于与同部门、跨部门进行合作以提升工作效能，并通过各种渠道提升自身专业能力，尝试做得更好'),
        ('Innovation\n创新与持续优化', 
         'Proactively propose innovative ideas to support the company and colleagues in making progress, and continuously optimize and improve oneself\n主动提出创新构想来协助公司与同事进步，并持续不断地优化与提升自我'),
        ('Sustainability\n社会责任与永续发展', 
         'Help people around you through your professional expertise and work achievements, and enable both yourself and those around you to achieve continuous development\n通过自身专业与工作成果帮助到身边的人，让自己与身边的人都能持续得到发展'),
    ]
    
    for i, (val, definition) in enumerate(values, start=1):
        value_table.cell(i, 0).text = val
        value_table.cell(i, 1).text = definition
    
    value_table.columns[0].width = Cm(4.5)
    value_table.columns[1].width = Cm(11.5)

def _fill_jd_content(doc, data):
    """将数据填充到文档模板中"""
    
    # 填充基本信息表（第一个表格）
    if doc.tables:
        info_table = doc.tables[0]
        # 行号对应：1=职位名称 2=部门 3=直线经理 4=下属 5=工作地点
        if data.get('position_title'):
            info_table.cell(1, 1).text = data['position_title']
        if data.get('department'):
            info_table.cell(2, 1).text = data['department']
        if data.get('line_manager'):
            info_table.cell(3, 1).text = data['line_manager']
        if data.get('subordinate'):
            info_table.cell(4, 1).text = data['subordinate']
        if data.get('location'):
            info_table.cell(5, 1).text = data['location']
    
    # 替换段落占位符
    for para in doc.paragraphs:
        text = para.text
        
        if '{{POSITION_PURPOSE}}' in text:
            para.text = data.get('position_purpose', '')
        
        if '{{RESPONSIBILITIES}}' in text:
            para.text = ''
            responsibilities = data.get('responsibilities', '')
            if isinstance(responsibilities, list):
                for item in responsibilities:
                    p = para.insert_paragraph_before(f"• {item}")
                    p.paragraph_format.left_indent = Cm(0.5)
            else:
                lines = [l.strip() for l in responsibilities.split('\n') if l.strip()]
                for line in lines:
                    if not line.startswith('•') and not line.startswith('-'):
                        line = '• ' + line
                    p = para.insert_paragraph_before(line)
                    p.paragraph_format.left_indent = Cm(0.5)
        
        if '{{QUALIFICATIONS}}' in text:
            para.text = ''
            
            if data.get('education'):
                p = para.insert_paragraph_before()
                run = p.add_run('教育背景：')
                run.bold = True
                p.add_run(data['education'])
            
            if data.get('experience'):
                p = para.insert_paragraph_before()
                run = p.add_run('工作经验：')
                run.bold = True
                p.add_run(data['experience'])
            
            if data.get('skills'):
                p = para.insert_paragraph_before()
                run = p.add_run('专业技能：')
                run.bold = True
                p.add_run(data['skills'])
            
            if data.get('abilities'):
                p = para.insert_paragraph_before()
                run = p.add_run('能力要求：')
                run.bold = True
                p.add_run(data['abilities'])
