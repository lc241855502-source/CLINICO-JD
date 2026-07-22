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
    """填充表格中的字段，通过关键词匹配定位
    包括基本信息字段和大段内容区域
    """
    
    # 短字段映射：关键词 -> 数据字段名（填右边单元格）
    short_field_mapping = [
        (['Position Title', '职务名称', '职位名称', '岗位名称'], 'position_title'),
        (['Department', '部门', '所属部门'], 'department'),
        (['Line Manager', '直线经理', '汇报对象', 'Report to'], 'line_manager'),
        (['Subordinate', '下属', '下属人数'], 'subordinate'),
        (['Location', '工作地点', '地点'], 'location'),
    ]
    
    # 长内容字段映射：关键词 -> 数据字段名（填下方单元格或同行剩余单元格）
    content_field_mapping = [
        (['Position purpose', '岗位目的', '职位概述', 'Position Summary'], 'position_purpose'),
        (['Major tasks', '主要职责', '岗位职责', 'Responsibilities', '工作描述'], 'responsibilities'),
        (['Qualifications', '任职要求', '岗位要求', 'Requirements'], 'qualifications'),
    ]
    
    for table in doc.tables:
        for row_idx, row in enumerate(table.rows):
            for col_idx, cell in enumerate(row.cells):
                cell_text = cell.text.strip()
                
                # 1. 短字段：填右边格
                matched_field = None
                for keywords, field_name in short_field_mapping:
                    for kw in keywords:
                        if kw.lower() in cell_text.lower():
                            matched_field = field_name
                            break
                    if matched_field:
                        break
                
                if matched_field:
                    value = data.get(matched_field, '')
                    if value and col_idx + 1 < len(row.cells):
                        target_cell = row.cells[col_idx + 1]
                        _set_cell_text_preserve_style(target_cell, str(value))
                    continue
                
                # 2. 长内容字段：填下方单元格
                matched_content = None
                for keywords, field_name in content_field_mapping:
                    for kw in keywords:
                        if kw.lower() in cell_text.lower():
                            matched_content = field_name
                            break
                    if matched_content:
                        break
                
                if matched_content:
                    # 找下方的单元格填内容
                    if row_idx + 1 < len(table.rows):
                        target_cell = table.rows[row_idx + 1].cells[col_idx]
                        if matched_content == 'responsibilities':
                            resp = data.get('responsibilities', [])
                            if isinstance(resp, list):
                                resp_text = '\n'.join([f"• {r}" for r in resp])
                            else:
                                resp_text = str(resp)
                            _set_cell_text_preserve_style(target_cell, resp_text)
                        elif matched_content == 'qualifications':
                            parts = []
                            if data.get('education'):
                                parts.append(f"教育背景：{data['education']}")
                            if data.get('experience'):
                                parts.append(f"工作经验：{data['experience']}")
                            if data.get('skills'):
                                parts.append(f"专业技能：{data['skills']}")
                            if data.get('abilities'):
                                parts.append(f"能力要求：{data['abilities']}")
                            _set_cell_text_preserve_style(target_cell, '\n'.join(parts))
                        else:
                            value = data.get(matched_content, '')
                            if value:
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
    """填充段落部分：岗位目的、主要职责、任职要求
    策略：找到各部分标题，定位内容区间，清空后插入新内容
    """
    
    paragraphs = doc.paragraphs
    
    # 第一步：找到所有章节标题的位置
    sections = {}  # name -> start_index
    
    for i, para in enumerate(paragraphs):
        text = para.text.strip().lower()
        
        # 岗位目的标题
        if any(kw in text for kw in ['position purpose', '岗位目的', '职位概述', 'position summary']):
            if 'purpose' not in sections:
                sections['purpose'] = i
        
        # 主要职责标题
        elif any(kw in text for kw in ['major task', '主要职责', '岗位职责', 'responsibilities', '工作描述']):
            if 'responsibilities' not in sections:
                sections['responsibilities'] = i
        
        # 任职要求标题
        elif any(kw in text for kw in ['qualification', '任职要求', '岗位要求', 'requirements']):
            if 'qualifications' not in sections:
                sections['qualifications'] = i
        
        # 审批栏/底部签名（作为结束标记）
        elif any(kw in text for kw in ['line manager', '签收人', 'approved by', '审批']):
            if 'end' not in sections:
                sections['end'] = i
    
    # 第二步：确定每个section的内容范围并填充
    
    # 1. 填充岗位目的
    if 'purpose' in sections:
        start = sections['purpose'] + 1
        end = sections.get('responsibilities', sections.get('end', start + 5))
        # 跳过副标题行（中文小标题）
        while start < end and paragraphs[start].text.strip():
            text = paragraphs[start].text.strip()
            if any(kw in text for kw in ['岗位目的', '表明该职位', '简要陈述', 'brief statement']):
                start += 1
            else:
                break
        # 跳空行
        while start < end and not paragraphs[start].text.strip():
            start += 1
        
        # 清空内容区域第一行，填入岗位目的
        purpose_text = data.get('position_purpose', '')
        if purpose_text and start < len(paragraphs):
            # 清空原有内容到下一个标题前
            _clear_paragraph_range(paragraphs, start, end)
            paragraphs[start].text = purpose_text
    
    # 2. 填充主要职责
    if 'responsibilities' in sections:
        start = sections['responsibilities'] + 1
        end = sections.get('qualifications', sections.get('end', start + 20))
        # 跳过副标题
        while start < end and paragraphs[start].text.strip():
            text = paragraphs[start].text.strip()
            if any(kw in text for kw in ['岗位主要任务', '主要任务与职责', 'position']):
                start += 1
            else:
                break
        # 跳空行
        while start < end and not paragraphs[start].text.strip():
            start += 1
        
        responsibilities = data.get('responsibilities', [])
        if isinstance(responsibilities, str):
            responsibilities = [line.strip('•- ').strip() for line in responsibilities.split('\n') if line.strip()]
        
        if responsibilities and start < len(paragraphs):
            # 清空原有内容区域
            _clear_paragraph_range(paragraphs, start, end)
            
            # 倒序插入（因为insert_paragraph_before是往前插）
            for resp in reversed(responsibilities):
                new_para = paragraphs[start].insert_paragraph_before(f"• {resp}")
                new_para.paragraph_format.left_indent = Cm(0.5)
    
    # 3. 填充任职要求
    if 'qualifications' in sections:
        start = sections['qualifications'] + 1
        end = sections.get('end', start + 20)
        # 跳过副标题
        while start < end and paragraphs[start].text.strip():
            text = paragraphs[start].text.strip()
            if any(kw in text for kw in ['教育，技能', '任职要求', '教育']):
                start += 1
            else:
                break
        # 跳空行
        while start < end and not paragraphs[start].text.strip():
            start += 1
        
        if start < len(paragraphs):
            # 清空原有内容区域
            _clear_paragraph_range(paragraphs, start, end)
            
            # 倒序插入各项
            items = []
            if data.get('education'):
                items.append(('教育背景：', data['education']))
            if data.get('experience'):
                items.append(('工作经验：', data['experience']))
            if data.get('skills'):
                items.append(('专业技能：', data['skills']))
            if data.get('abilities'):
                items.append(('能力要求：', data['abilities']))
            
            for label, value in reversed(items):
                p = paragraphs[start].insert_paragraph_before()
                run = p.add_run(label)
                run.bold = True
                p.add_run(value)

def _clear_paragraph_range(paragraphs, start, end):
    """清空指定范围内的段落文本"""
    for i in range(start, min(end, len(paragraphs))):
        paragraphs[i].text = ''
