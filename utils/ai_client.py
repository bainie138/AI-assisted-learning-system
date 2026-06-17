import os
import re
import json
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_ai_response(prompt, model_type="summary"):
    """
    调用AI大模型获取响应
    :param prompt: 提示词
    :param model_type: 模型类型(summary: 总结, keywords: 提取关键词, json: 返回JSON)
    :return: AI返回的结果
    """
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

    if not api_key:
        raise ValueError("❌ API配置错误:请在.env文件中配置DEEPSEEK_API_KEY")

    # 检查API密钥格式是否正确(DeepSeek密钥通常以sk-开头)
    if not api_key.startswith('sk-'):
        raise ValueError("❌ API密钥格式错误:DeepSeek API Key应以'sk-'开头")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    messages = []

    if model_type == "summary":
        system_prompt = """你是一个专业的学习笔记助手。请将以下笔记内容进行简明扼要的总结,突出重点内容。
要求:
1. 总结长度不超过200字
2. 使用简洁明了的语言
3. 保留关键知识点和核心内容
4. 不要添加额外信息
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请总结以下笔记内容:\n\n{prompt}"}
        ]

    elif model_type == "keywords":
        system_prompt = """你是一个关键词提取专家。请从以下文本中提取最关键的5-10个关键词或短语。
要求:
1. 只返回关键词,用中文逗号分隔
2. 不要解释,不要添加其他内容
3. 关键词要能准确反映文本主题
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请提取以下文本的关键词:\n\n{prompt}"}
        ]

    elif model_type == "json":
        system_prompt = """你是一个专业的文本分析助手。请严格按照JSON格式返回结果,不要添加任何额外内容。
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                "分析以下文本,返回JSON格式,"
                "包含keywords(3个关键词,逗号分隔)和summary(一句话总结,不超过50字):"
                f"\n\n{prompt}"
            )}
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

        # 添加更详细的错误处理
        if response.status_code == 401:
            raise ValueError(
                "❌ API认证失败(401错误):\n"
                "1. 请检查API Key是否正确\n"
                "2. 请确认API Key尚未过期\n"
                "3. 请确保已在DeepSeek平台完成实名认证\n"
                "4. 检查API Key是否有足够的余额或免费额度\n"
                "\n"
                "解决方案:\n"
                "- 访问 https://platform.deepseek.com/ 检查API密钥状态\n"
                "- 确保账户已完成实名认证\n"
                "- 查看API使用额度是否充足"
            )

        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()

    except requests.exceptions.RequestException as e:
        raise ValueError(
            "❌ AI API调用失败: " + str(e) + "\n\n"
            "可能的原因:\n"
            "1. 网络连接问题\n"
            "2. API Key无效或过期\n"
            "3. 账户未实名认证\n"
            "4. API额度不足"
        ) from e

    except KeyError as e:
        raise ValueError(f"❌ API返回格式错误:缺少必要字段 {str(e)}") from e


def generate_summary(content):
    """生成笔记总结"""
    return get_ai_response(content, model_type="summary")


def extract_keywords(content):
    """提取关键词"""
    return get_ai_response(content, model_type="keywords")


def _clean_json_response(response):
    """
    清理AI返回的JSON字符串,移除markdown代码块标记等
    :param response: AI返回的原始文本
    :return: 清理后的JSON字符串
    """
    text = response.strip()

    # 移除markdown代码块标记 ```json ... ``` 或 ``` ... ```
    if text.startswith('```'):
        # 移除开头的 ```json 或 ```
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        # 移除结尾的 ```
        text = re.sub(r'\n?```\s*$', '', text)
        text = text.strip()

    return text


def generate_keywords_and_summary(content):
    """
    调用AI生成关键词和总结,返回JSON格式
    :param content: 笔记内容
    :return: 包含keywords和summary的字典
    """
    response = get_ai_response(content, model_type="json")

    # 清理可能的markdown代码块标记
    response = _clean_json_response(response)

    # 尝试解析JSON
    try:
        result = json.loads(response)
        # 验证返回格式
        if 'keywords' in result and 'summary' in result:
            return result
        # 如果缺少必要字段,抛出异常进入fallback
        raise ValueError("返回格式不正确:缺少keywords或summary字段")
    except (json.JSONDecodeError, ValueError):
        # 如果JSON解析失败,回退到分别调用关键词提取和总结生成
        # 分别包装每个调用,确保一个失败不影响另一个
        try:
            keywords = extract_keywords(content)
        except Exception:
            keywords = ""

        try:
            summary = generate_summary(content)
        except Exception:
            summary = ""

        return {
            'keywords': keywords,
            'summary': summary
        }
