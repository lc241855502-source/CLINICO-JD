import re

def extract_jd_fields(raw_text):
    """从原始文本中结构化提取JD各字段"""
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
    
    text = raw_text
    
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
    
    # 岗位目的/职位概述
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
        
        # 教育背景
        edu_match = re.search(r'(?:Education|教育背景|学历)[：:]\s*(.+?)(?:\n|Experience|工作经验)', req_text, re.IGNORECASE | re.DOTALL)
        if edu_match:
            fields['education'] = edu_match.group(1).strip()
        
        # 工作经验
        exp_match = re.search(r'(?:Experience|工作经验)[：:]\s*(.+?)(?:\n|Skills|其他技能|能力)', req_text, re.IGNORECASE | re.DOTALL)
        if exp_match:
            fields['experience'] = exp_match.group(1).strip()
        
        # 技能
        skill_match = re.search(r'(?:Skills|其他技能|专业技能)[：:]\s*(.+?)(?:\n|Ability|能力|$)', req_text, re.IGNORECASE | re.DOTALL)
        if skill_match:
            fields['skills'] = skill_match.group(1).strip()
    
    return fields
