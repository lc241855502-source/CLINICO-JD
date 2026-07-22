import requests
import json

# 公司行业背景
COMPANY_INDUSTRY = "眼科医疗仪器贸易与研发"
COMPANY_NAME = "科林集团"

def polish_jd_with_api(fields, api_url, api_key=None):
    """
    调用大模型API对JD进行扩写优化 + 缺失字段自动创作
    - 文字扩写、规范化、专业化
    - 缺失内容根据岗位+行业自动补全
    - 结合眼科医疗仪器贸易与研发行业特性
    """
    
    # 检查哪些字段缺失，标记需要补全
    missing_fields = []
    if not fields.get('position_purpose') or len(str(fields['position_purpose']).strip()) < 10:
        missing_fields.append('岗位目的')
    if not fields.get('responsibilities') or len(fields['responsibilities']) < 3:
        missing_fields.append('主要职责')
    if not fields.get('education') or len(str(fields['education']).strip()) < 3:
        missing_fields.append('教育背景')
    if not fields.get('experience') or len(str(fields['experience']).strip()) < 3:
        missing_fields.append('工作经验')
    if not fields.get('skills') or len(str(fields['skills']).strip()) < 3:
        missing_fields.append('专业技能')
    
    missing_note = f"以下字段内容缺失或不完整，请根据岗位名称和行业特性自动创作补全：{', '.join(missing_fields)}" if missing_fields else "所有字段均有内容，请在原有基础上扩写优化。"
    
    prompt = f"""
你是资深HR岗位说明书撰写专家，熟悉{COMPANY_INDUSTRY}行业的人才标准和JD规范。
请基于以下提取的JD原始信息，进行专业化扩写和优化，输出规范的岗位说明书内容。

【公司背景】
公司名称：{COMPANY_NAME}
行业：{COMPANY_INDUSTRY}（进口眼科设备代理 + 自主研发生产）

【原始信息】
职位名称：{fields['position_title']}
部门：{fields.get('department', '待补充')}
直线经理：{fields.get('line_manager', '')}
下属：{fields.get('subordinate', '')}
工作地点：{fields.get('location', '')}
岗位目的：{fields.get('position_purpose', '')}
主要职责：{fields.get('responsibilities', [])}
教育背景：{fields.get('education', '')}
工作经验：{fields.get('experience', '')}
技能要求：{fields.get('skills', '')}

【处理要求】
{missing_note}

1. 岗位目的：100字以内，清晰说明该岗位存在的核心价值和主要目标，结合{COMPANY_INDUSTRY}行业特点
2. 主要职责：输出8-12条，每条不超过50字，用动词开头，覆盖核心工作内容，符合{COMPANY_INDUSTRY}行业该岗位的通用职责
3. 任职要求：
   - 教育背景：明确学历和专业要求
   - 工作经验：明确年限和相关领域经验
   - 专业技能：岗位必备的硬技能
   - 能力要求：软能力、综合素质

4. 语言风格：正式、专业、简洁，符合医疗器械行业HR文档规范
5. 原有内容如果比较简略，请扩写充实；如果完全缺失，请结合行业通用标准自动创作
6. 所有内容用中文输出

请严格输出JSON格式，包含以下字段：
position_title, department, line_manager, subordinate, location,
position_purpose, responsibilities（数组格式）,
education, experience, skills, abilities
"""
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        # 解析返回的JSON内容
        content = result['choices'][0]['message']['content']
        polished_data = json.loads(content)
        
        # 确保所有字段存在
        for key in ['position_title', 'department', 'line_manager', 'subordinate', 
                    'location', 'position_purpose', 'responsibilities', 
                    'education', 'experience', 'skills', 'abilities']:
            if key not in polished_data:
                polished_data[key] = fields.get(key, '')
        
        # 确保responsibilities是数组
        if isinstance(polished_data.get('responsibilities'), str):
            polished_data['responsibilities'] = [
                line.strip('•- ').strip() 
                for line in polished_data['responsibilities'].split('\n') 
                if line.strip()
            ]
        
        return polished_data
        
    except Exception as e:
        print(f"API调用失败: {e}")
        # API失败时返回原始字段，不阻塞流程
        return fields
