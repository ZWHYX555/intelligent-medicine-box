"""
大模型解析模块
调用LLM API将OCR文本解析为结构化信息
"""
import json
import logging
import requests
from typing import Dict, Any, Optional


class LLMParser:
    """大模型解析器"""
    
    def __init__(self, provider="openai", api_key=None, model=None):
        """
        初始化LLM解析器
        
        Args:
            provider: 大模型提供商 (openai, baidu, xunfei)
            api_key: API密钥
            model: 模型名称
        """
        self.logger = logging.getLogger(__name__)
        self.provider = provider
        self.api_key = api_key
        self.model = model or "gpt-3.5-turbo"
    
    def parse_medicine_info(self, text: str) -> Dict[str, Any]:
        """
        解析药品信息
        
        Args:
            text: OCR提取的文本
            
        Returns:
            dict: 结构化的药品信息
        """
        prompt = f"""请从以下药品包装文字中提取关键信息，并以JSON格式返回。
        
要求：
1. 返回格式必须是标准JSON
2. 如果某个字段无法识别，使用null
3. 有效期格式为 YYYY-MM-DD

要提取的字段：
- medicine_name: 药品名称
- generic_name: 通用名
- manufacturer: 生产厂家
- batch_number: 批号
- expiry_date: 有效期（YYYY-MM-DD格式）
- dosage: 规格（如 10mg×30片）
- usage: 用法用量（具体描述）
- precautions: 注意事项（列表形式）
- side_effects: 副作用（列表形式）
- contraindications: 禁忌症（列表形式）
- storage: 储存方法
- ingredients: 主要成分

药品包装文字：
{text}

返回JSON格式的结构化信息："""
        
        try:
            if self.provider == "openai":
                return self._parse_openai(prompt)
            elif self.provider == "baidu":
                return self._parse_baidu(prompt)
            elif self.provider == "xunfei":
                return self._parse_xunfei(prompt)
            else:
                self.logger.error(f"不支持的提供商: {self.provider}")
                return None
        except Exception as e:
            self.logger.error(f"LLM解析失败: {e}")
            return None
    
    def _parse_openai(self, prompt: str) -> Dict[str, Any]:
        """使用OpenAI API解析"""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的药品信息提取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # 如果不是纯JSON，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"raw_response": result_text}
            
            self.logger.info("OpenAI解析成功")
            return result
        except Exception as e:
            self.logger.error(f"OpenAI API调用失败: {e}")
            return None
    
    def _parse_baidu(self, prompt: str) -> Dict[str, Any]:
        """使用百度千帆API解析"""
        try:
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-bot"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            # 需要获取access_token
            access_token = self._get_baidu_access_token()
            url += f"?access_token={access_token}"
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result_json = response.json()
            result_text = result_json.get("result", "")
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                result = {"raw_response": result_text}
            
            self.logger.info("百度API解析成功")
            return result
        except Exception as e:
            self.logger.error(f"百度API调用失败: {e}")
            return None
    
    def _parse_xunfei(self, prompt: str) -> Dict[str, Any]:
        """使用讯飞API解析"""
        try:
            # 这里需要根据讯飞实际API进行调整
            self.logger.warning("讯飞API尚未实现，请补充相应代码")
            return None
        except Exception as e:
            self.logger.error(f"讯飞API调用失败: {e}")
            return None
    
    def _get_baidu_access_token(self) -> str:
        """获取百度API的access_token"""
        try:
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": "your_secret_key"
            }
            response = requests.post(url, params=params, timeout=10)
            result = response.json()
            return result.get("access_token", "")
        except Exception as e:
            self.logger.error(f"获取百度access_token失败: {e}")
            return ""
    
    def validate_medicine_info(self, info: Dict) -> bool:
        """
        验证提取的药品信息是否有效
        
        Args:
            info: 药品信息字典
            
        Returns:
            bool: 是否有效
        """
        required_fields = ["medicine_name", "expiry_date", "usage"]
        
        for field in required_fields:
            if field not in info or not info[field]:
                self.logger.warning(f"缺少必要字段: {field}")
                return False
        
        return True
    
    def format_medicine_info(self, info: Dict) -> str:
        """
        格式化药品信息为易读的文本
        
        Args:
            info: 药品信息字典
            
        Returns:
            str: 格式化的文本
        """
        formatted = f"""
【药品信息】
名称: {info.get('medicine_name', '未知')}
通用名: {info.get('generic_name', '未知')}
规格: {info.get('dosage', '未知')}
生产厂家: {info.get('manufacturer', '未知')}
批号: {info.get('batch_number', '未知')}
有效期: {info.get('expiry_date', '未知')}

【用法用量】
{info.get('usage', '未知')}

【注意事项】
{', '.join(info.get('precautions', [])) if info.get('precautions') else '无'}

【副作用】
{', '.join(info.get('side_effects', [])) if info.get('side_effects') else '未知'}

【禁忌症】
{', '.join(info.get('contraindications', [])) if info.get('contraindications') else '无'}

【储存方法】
{info.get('storage', '阴凉干燥处')}
"""
        return formatted.strip()
