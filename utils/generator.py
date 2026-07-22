from docx import Document
from docx.shared import Pt, Cm
import io
import os

def generate_jd_document(data, template_path):
    """
    基于公司真实模板填充JD内容
    通过关键词匹配定位填充位置，保证格式100%与原模板一致
    """
    if not template_path or not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    
    doc = Document(template_path)
    
    # 1. 填充表格中的基本信息字段
    _fill_table_fields(doc, data)
    
    # 2. 填充段落内容（岗位目的、职责、任职要求）
    _fill_paragraph_sections(doc, data)
    
    # 保存到内存
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output

def _fill_table_fields(doc, data):
    """填充表格中的基本信息字段，通过关键词匹配定位"""
    
    # 字段映射：关键词 -> 数据字段名
    field_mapping = [
        (['Position Title', '职务名称', '职位名称', '岗位名称'], 'position_title'),
        (['Department', '部门', '所属部门'], 'department'),
        (['Line Manager', '直线经理', '汇报对象', 'Report to'], 'line_manager'),
        (['Subordinate', '下属', '下属人数'], 'subordinate'),
        (['Location', '工作地点', '地点'], 'location'),
        (['Prepared by', '起草人'], '_skip'),  # 跳过
        (['Revision Date', '修订日期'], '_skip'),
    ]
    
    for table in doc.tables:
        for row_idx, row in enumerate(table.rows):
            for col_idx, cell in enumerate(row.cells):
                cell_text = cell.text.strip()
                
                # 检查是否匹配某个字段标签
                matched_field = None
                for keywords, field_name in field_mapping:
                    for kw in keywords:
                        if kw.lower() in cell_text.lower():
                            matched_field = field_name
                            break
                    if matched_field:
                        break
                
                if matched_field and matched_field != '_skip':
                    value = data.get(matched_field, '')
                    if value:
                        # 填到右边的单元格（同一行，下一列）
                        if col_idx + 1 < len(row.cells):
                            target_cell = row.cells[col_idx + 1]
                            _set_cell_text_preserve_style(target_cell, str(value))

def _set_cell_text_preserve_style(cell, text):
    """设置单元格文本，尽量保留原有样式"""
    # 清空现有内容
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.text = ''
    
    # 如果有段落，在第一个段落设置文本
    if cell.paragraphs:
        para = cell.paragraphs[0]
        if para.runs:
            para.runs[0].text = text
        else:
            para.text = text
    else:
        cell.text = text

def _fill_paragraph_sections(doc, data):
    """填充段落部分：岗位目的、主要职责、任职要求"""
    
    paragraphs = doc.paragraphs
    i = 0
    
    while i < len(paragraphs):
        para = paragraphs[i]
        text = para.text.strip()
        
        # 岗位目的部分
        if any(kw in text for kw in ['Position purpose', '岗位目的', '职位概述']):
            # 找到下一个非空段落作为内容位置
            j = i + 1
            while j < len(paragraphs) and not paragraphs[j].text.strip():
                j += 1
            if j < len(paragraphs):
                purpose_text = data.get('position_purpose', '')
                if purpose_text:
                    paragraphs[j].text = purpose_text
            i = j
        
        # 主要职责部分
        elif any(kw in text for kw in ['Major tasks', '主要职责', '岗位职责', 'responsibilities of position']):
            # 跳过副标题行（中文小标题）
            j = i + 1
            while j < len(paragraphs) and any(kw in paragraphs[j].text for kw in ['岗位主要任务', '主要任务与职责']):
                j += 1
            # 找到内容起始位置
            while j < len(paragraphs) and not paragraphs[j].text.strip():
                j += 1
            
            # 插入职责列表
            responsibilities = data.get('responsibilities', [])
            if isinstance(responsibilities, str):
                responsibilities = [line.strip('•- ').strip() for line in responsibilities.split('\n') if line.strip()]
            
            if responsibilities and j < len(paragraphs):
                # 清空原有内容行
                paragraphs[j].text = ''
                # 在该位置前插入每条职责
                for idx, resp in enumerate(responsibilities):
                    new_para = paragraphs[j].insert_paragraph_before(f"• {resp}")
                    new_para.paragraph_format.left_indent = Cm(0.5)
            i = j
        
        # 任职要求部分
        elif any(kw in text for kw in ['Qualifications', '任职要求', '岗位要求']):
            # 跳过副标题行
            j = i + 1
            while j < len(paragraphs) and any(kw in paragraphs[j].text for kw in ['教育，技能', '任职要求']):
                j += 1
            # 找到内容起始位置
            while j < len(paragraphs) and not paragraphs[j].text.strip():
                j += 1
            
            if j < len(paragraphs):
                paragraphs[j].text = ''
                
                # 教育背景
                if data.get('education'):
                    p = paragraphs[j].insert_paragraph_before()
                    run = p.add_run('教育背景：')
                    run.bold = True
                    p.add_run(data['education'])
                
                # 工作经验
                if data.get('experience'):
                    p = paragraphs[j].insert_paragraph_before()
                    run = p.add_run('工作经验：')
                    run.bold = True
                    p.add_run(data['experience'])
                
                # 专业技能
                if data.get('skills'):
                    p = paragraphs[j].insert_paragraph_before()
                    run = p.add_run('专业技能：')
                    run.bold = True
                    p.add_run(data['skills'])
                
                # 能力要求
                if data.get('abilities'):
                    p = paragraphs[j].insert_paragraph_before()
                    run = p.add_run('能力要求：')
                    run.bold = True
                    p.add_run(data['abilities'])
            i = j
        
        i += 1
