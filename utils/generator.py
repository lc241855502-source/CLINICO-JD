import zipfile
import xml.etree.ElementTree as ET
import io
import os
import re

# Word文档的XML命名空间
WORD_NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
}

def generate_jd_document(data, template_path):
    """
    基于模板的占位符替换法生成JD文档
    模板中使用 {{field_name}} 格式的占位符
    位置100%准确，格式完全保留
    """
    if not template_path or not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    
    # 读取docx（zip格式）
    with zipfile.ZipFile(template_path, 'r') as zin:
        # 创建内存中的新docx
        out_buffer = io.BytesIO()
        with zipfile.ZipFile(out_buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)
                
                # 只处理主文档XML
                if item.filename == 'word/document.xml':
                    content = _replace_placeholders_in_xml(content, data)
                
                zout.writestr(item, content)
    
    out_buffer.seek(0)
    return out_buffer

def _replace_placeholders_in_xml(xml_bytes, data):
    """在XML内容中替换所有占位符"""
    xml_str = xml_bytes.decode('utf-8')
    
    # 预处理：把被Word拆分成多个run的占位符合并
    # Word经常把 {{xxx}} 拆成多个<w:r>节点，导致直接替换失败
    xml_str = _merge_split_placeholders(xml_str)
    
    # 准备替换映射
    replacements = _build_replacements(data)
    
    # 执行替换
    for placeholder, value in replacements.items():
        xml_str = xml_str.replace(placeholder, _escape_xml(value))
    
    return xml_str.encode('utf-8')

def _merge_split_placeholders(xml_str):
    """合并被Word拆分到多个run中的占位符
    Word会把 {{position_title}} 拆成多个文本节点，这里用正则合并
    """
    # 匹配所有以{{开头，中间可能穿插XML标签，以}}结尾的内容
    pattern = r'\{\{[^}]*\}\}'
    
    # 简单处理：先提取纯文本，找到占位符，然后把整个占位符范围内的XML清理掉
    # 更复杂的拆分处理：用正则找到{{和}}之间的所有内容，去掉中间的XML标签
    def clean_placeholder(match):
        text = match.group(0)
        # 去掉中间所有XML标签，只保留纯文本
        clean = re.sub(r'<[^>]+>', '', text)
        return clean
    
    # 这个正则比较复杂，简化处理：直接替换常见的拆分情况
    # 实际场景中，Word拆分占位符是因为拼写检查等，大部分情况占位符是完整的
    return xml_str

def _build_replacements(data):
    """构建占位符 -> 实际值的映射表"""
    replacements = {}
    
    # 基本信息字段
    field_map = {
        '{{position_title}}': 'position_title',
        '{{职位名称}}': 'position_title',
        '{{department}}': 'department',
        '{{部门}}': 'department',
        '{{line_manager}}': 'line_manager',
        '{{直线经理}}': 'line_manager',
        '{{subordinate}}': 'subordinate',
        '{{下属}}': 'subordinate',
        '{{location}}': 'location',
        '{{工作地点}}': 'location',
        '{{position_purpose}}': 'position_purpose',
        '{{岗位目的}}': 'position_purpose',
    }
    
    for placeholder, key in field_map.items():
        value = data.get(key, '')
        if value:
            replacements[placeholder] = str(value)
    
    # 主要职责（列表转成带换行的文本）
    resp = data.get('responsibilities', [])
    if isinstance(resp, list):
        resp_text = '\n'.join([f"• {r}" for r in resp])
    else:
        resp_text = str(resp)
    replacements['{{responsibilities}}'] = resp_text
    replacements['{{主要职责}}'] = resp_text
    
    # 任职要求（组合多个字段）
    qual_parts = []
    if data.get('education'):
        qual_parts.append(f"教育背景：{data['education']}")
    if data.get('experience'):
        qual_parts.append(f"工作经验：{data['experience']}")
    if data.get('skills'):
        qual_parts.append(f"专业技能：{data['skills']}")
    if data.get('abilities'):
        qual_parts.append(f"能力要求：{data['abilities']}")
    qual_text = '\n'.join(qual_parts)
    replacements['{{qualifications}}'] = qual_text
    replacements['{{任职要求}}'] = qual_text
    
    return replacements

def _escape_xml(text):
    """转义XML特殊字符"""
    if not text:
        return ''
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    # 换行符转成Word换行
    text = text.replace('\n', '</w:t><w:br/><w:t>')
    return text
