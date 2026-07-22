import re
import json
import requests

def extract_jd_fields(raw_text, api_url=None, api_key=None):
    """
    从原始文本中结构化提取JD各字段
    优先使用AI智能提取（准确率高），API不可用时降级为正则提取
    """
    # 如果有API配置，优先用AI智能提取
    if api_url and api_key:
        result = _ai_extract(raw_text, api_url, api_key)
        if result:
            return result
    
    # 降级：正则提取
    return _regex_extract(raw_text)

def _ai_extract(raw_text, api_url, api_key):
    """使用大模型AI智能提取JD字段"""
    prompt = f"""
    你是专业的HR岗位说明书解析专家。请从以下原始JD文本中，智能提取并结构化输出各个字段。
    仔细阅读全文，理解语义后提取，不要简单匹配关键词。

    原始JD文本：
    {raw_text}

    请严格输出JSON格式，包含以下字段：
    - position_title: 职位名称
    - department: 所属部门
    - line_manager: 直线经理/汇报对象
    - subordinate: 下属/下属人数
    - location: 工作地点
    - position_purpose: 岗位目的/职位概述（一段话总结）
    - responsibilities: 主要职责（数组格式，每条一句话）
    - education: 教育背景/学历要求
    - experience: 工作经验要求
    - skills: 专业技能要求
    - abilities: 能力要求/软技能

    规则：
    1. 原文中没有的字段，填空字符串
    2. 职责部分拆分成数组，每条清晰完整
    3. 所有字段用中文输出
    4. 只输出JSON，不要其他解释文字
    """
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        data = json.loads(content)
        
        # 确保所有字段都存在
        required_fields = [
            'position_title', 'department', 'line_manager', 'subordinate',
            'location', 'position_purpose', 'responsibilities',
            'education', 'experience', 'skills', 'abilities'
        ]
        for field in required_fields:
            if field not in data:
                data[field] = ''
        
        # responsibilities确保是数组
        if isinstance(data['responsibilities'], str):
            data['responsibilities'] = [
                line.strip('•- ').strip()
                for line in data['responsibilities'].split('\n')
                if line.strip()
            ]
        
        return data
    except Exception as e:
        print(f"AI提取失败: {e}")
        return None

def _regex_extract(text):
    """正则提取（降级方案）"""
    fields = {
        'position_title': '',
        'department': '',
        'line_manager': '',
        'subordinate': '',
        'location': '',
        'position_purpose': '',
        'responsibilities': '',
        'education': '',
        'experience': '',
        'skills': '',
        'abilities': ''
    }
    
    # 职位名称匹配
    title_patterns = [
        r'(?:Title|职位|职务名称|岗位名称)[：:]\s*(.+)',
        r'(?:Position Title)[：:]\s*(.+)',
        r'^(.+?专员|.+?经理|.+?工程师|.+?主管)\s*$'
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            fields['position_title'] = match.group(1).strip()
            break
    
    # 部门匹配
    dept_patterns = [
        r'(?:Department|部门)[：:]\s*(.+)',
        r'(?:所属部门)[：:]\s*(.+)'
    ]
    for pattern in dept_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields['department'] = match.group(1).strip()
            break
    
    # 汇报对象/直线经理
    manager_patterns = [
        r'(?:Report to|汇报对象|直线经理|Line Manager)[：:]\s*(.+)',
    ]
    for pattern in manager_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields['line_manager'] = match.group(1).strip()
            break
    
    # 下属
    sub_patterns = [
        r'(?:Subordinate|下属|下属人数)[：:]\s*(.+)',
    ]
    for pattern in sub_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields['subordinate'] = match.group(1).strip()
            break
    
    # 工作地点
    loc_patterns = [
        r'(?:Location|工作地点|地点)[：:]\s*(.+)',
    ]
    for pattern in loc_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields['location'] = match.group(1).strip()
            break
    
    # 岗位目的
    purpose_sections = [
        r'(?:Position Summary|职位概述|岗位目的|岗位概述)[：:\n](.+?)(?:\n\n|\n[A-Z][a-z]+|任职要求|主要职责)',
    ]
    for pattern in purpose_sections:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            fields['position_purpose'] = match.group(1).strip()
            break
    
    # 主要职责
    resp_patterns = [
        r'(?:Main Tasks|主要职责|岗位职责|工作描述|Job Description)[：:\n](.+?)(?:\n\n|\n[A-Z][a-z]+|任职要求|Requirements)',
        r'(?:Responsibilities)[：:\n](.+?)(?:\n\n|\nRequirements|任职要求)',
    ]
    for pattern in resp_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            fields['responsibilities'] = match.group(1).strip()
            break
    
    # 任职要求拆分
    req_pattern = r'(?:Requirements|任职要求|岗位要求)[：:\n](.+)'
    match = re.search(req_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        req_text = match.group(1)
        
        edu_match = re.search(r'(?:Education|教育背景|学历)[：:]\s*(.+?)(?:\n|Experience|工作经验)', req_text, re.IGNORECASE | re.DOTALL)
        if edu_match:
            fields['education'] = edu_match.group(1).strip()
        
        exp_match = re.search(r'(?:Experience|工作经验)[：:]\s*(.+?)(?:\n|Skills|其他技能|能力)', req_text, re.IGNORECASE | re.DOTALL)
        if exp_match:
            fields['experience'] = exp_match.group(1).strip()
        
        skill_match = re.search(r'(?:Skills|其他技能|专业技能)[：:]\s*(.+?)(?:\n|Ability|能力|$)', req_text, re.IGNORECASE | re.DOTALL)
        if skill_match:
            fields['skills'] = skill_match.group(1).strip()
    
    return fields
