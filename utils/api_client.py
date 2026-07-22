import requests
import json

def polish_jd_with_api(fields, api_url, api_key=None):
    """
    调用外部大模型API对JD内容进行润色和缺失字段补全
    兼容OpenAI接口规范（DeepSeek、GPT、通义千问等）
    自动对齐科林IQCIS价值观
    """
    prompt = f"""
    你是专业的HR岗位说明书优化专家。请基于以下提取的JD信息，按照科林公司IQCIS价值观进行润色优化，
    补全缺失的字段内容，输出严格的JSON格式。

    科林价值观IQCIS：
    - Integrity 诚信与尊重：值得信赖，尊重他人，对待内、外部客户一致，说到做到
    - Quality 品质承诺与客户导向：工作始终以客户为第一优先，以结果为导向，注重品质，使命必达
    - Collaboration 合作与人才发展：善于与同部门、跨部门进行合作以提升工作效能，并通过各种渠道提升自身专业能力，尝试做得更好
    - Innovation 创新与持续优化：主动提出创新构想来协助公司与同事进步，并持续不断地优化与提升自我
    - Sustainability 社会责任与永续发展：通过自身的专业与工作成果帮助到身边的人，让自己与身边的人都能持续得到发展

    当前提取的字段信息：
    职位名称：{fields['position_title']}
    部门：{fields['department']}
    直线经理：{fields['line_manager']}
    下属：{fields['subordinate']}
    工作地点：{fields['location']}
    岗位目的：{fields['position_purpose']}
    主要职责：{fields['responsibilities']}
    教育背景：{fields['education']}
    工作经验：{fields['experience']}
    技能要求：{fields['skills']}

    请输出JSON，包含以下字段：
    position_title, department, line_manager, subordinate, location,
    position_purpose（100字以内，精炼专业）,
    responsibilities（数组格式，8-12条，每条不超过50字，结合IQCIS价值观）,
    education, experience, skills, abilities（软能力要求）
    
    所有字段都用中文输出。
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
        return polished_data
        
    except Exception as e:
        print(f"API调用失败: {e}")
        # API失败时返回原始字段，不阻塞流程
        return fields
