import os
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_ai_response(prompt, model_type="summary"):
    """
    调用AI大模型获取响应
    :param prompt: 提示词
    :param model_type: 模型类型（summary: 总结, keywords: 提取关键词, json: 返回JSON）
    :return: AI返回的结果
    """
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    
    if not api_key:
        raise ValueError("请在.env文件中配置DEEPSEEK_API_KEY")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    messages = []
    
    if model_type == "summary":
        system_prompt = """你是一个专业的学习笔记助手。请将以下笔记内容进行简明扼要的总结，突出重点内容。
要求：
1. 总结长度不超过200字
2. 使用简洁明了的语言
3. 保留关键知识点和核心内容
4. 不要添加额外信息
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请总结以下笔记内容：\n\n{prompt}"}
        ]
    
    elif model_type == "keywords":
        system_prompt = """你是一个关键词提取专家。请从以下文本中提取最关键的5-10个关键词或短语。
要求：
1. 只返回关键词，用中文逗号分隔
2. 不要解释，不要添加其他内容
3. 关键词要能准确反映文本主题
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请提取以下文本的关键词：\n\n{prompt}"}
        ]
    
    elif model_type == "json":
        system_prompt = """你是一个专业的文本分析助手。请严格按照JSON格式返回结果，不要添加任何额外内容。
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"分析以下文本，返回JSON格式，包含keywords（3个关键词，逗号分隔）和summary（一句话总结，不超过50字）：\n\n{prompt}"}
        ]
    
    elif model_type == "chat":
        messages = [
            {"role": "user", "content": prompt}
        ]
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API调用失败: {str(e)}")

def generate_summary(content):
    """生成笔记总结"""
    return get_ai_response(content, model_type="summary")

def extract_keywords(content):
    """提取关键词"""
    return get_ai_response(content, model_type="keywords")

def generate_keywords_and_summary(content):
    """
    调用AI生成关键词和总结，返回JSON格式
    :param content: 笔记内容
    :return: 包含keywords和summary的字典
    """
    response = get_ai_response(content, model_type="json")
    
    # 尝试解析JSON
    try:
        result = json.loads(response)
        # 验证返回格式
        if 'keywords' not in result or 'summary' not in result:
            # 如果返回不是预期格式，尝试直接提取
            raise ValueError("返回格式不正确")
        return result
    except (json.JSONDecodeError, ValueError):
        # 如果JSON解析失败，尝试从文本中提取
        # 这是一个容错机制，处理模型可能返回非JSON格式的情况
        return {
            'keywords': extract_keywords(content),
            'summary': generate_summary(content)[:50]
        }
