"""
常见疾病智能问答系统
基于大模型的7×24小时问答服务
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime


class QASystem:
    """智能问答系统"""
    
    def __init__(self, llm_parser):
        """
        初始化问答系统
        
        Args:
            llm_parser: LLMParser对象
        """
        self.logger = logging.getLogger(__name__)
        self.llm_parser = llm_parser
        self.conversation_history = []
        self.qa_database = self._init_qa_database()
    
    def _init_qa_database(self) -> Dict:
        """初始化常见问题数据库"""
        return {
            "drug_interactions": {
                "description": "药物相互作用",
                "keywords": ["相互作用", "同时服用", "一起吃"]
            },
            "contraindications": {
                "description": "禁忌症",
                "keywords": ["禁忌", "不能用", "禁止"]
            },
            "side_effects": {
                "description": "副作用",
                "keywords": ["副作用", "不良反应", "反应"]
            },
            "dosage": {
                "description": "用法用量",
                "keywords": ["怎么吃", "用量", "剂量"]
            },
            "storage": {
                "description": "储存方法",
                "keywords": ["怎么保存", "储存", "放在哪里"]
            },
            "pregnancy": {
                "description": "妊娠期用药",
                "keywords": ["怀孕", "妊娠", "哺乳"]
            }
        }
    
    def ask(self, question: str, medicine_info: Optional[Dict] = None) -> str:
        """
        提出问题
        
        Args:
            question: 用户问题
            medicine_info: 相关的药品信息
            
        Returns:
            str: 问答系统的回答
        """
        try:
            # 记录到对话历史
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "question",
                "content": question
            })
            
            # 构建提示词
            prompt = self._build_prompt(question, medicine_info)
            
            # 调用LLM获取答案
            answer = self._get_answer_from_llm(prompt)
            
            # 记录回答
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "answer",
                "content": answer
            })
            
            self.logger.info(f"问答完成: {question[:50]}...")
            return answer
        except Exception as e:
            self.logger.error(f"问答失败: {e}")
            return "抱歉，我无法回答这个问题，请咨询医生。"
    
    def _build_prompt(self, question: str, medicine_info: Optional[Dict] = None) -> str:
        """
        构建提示词
        
        Args:
            question: 用户问题
            medicine_info: 药品信息
            
        Returns:
            str: 提示词
        """
        prompt = f"""你是一个专业的医药咨询助手，可以回答关于药物的常见问题。
        
请注意以下原则：
1. 提供准确、科学的药物知识
2. 强调严重情况下应咨询医生
3. 使用通俗易懂的语言
4. 避免误导用户
5. 如果不确定，请说明

"""
        
        if medicine_info:
            prompt += f"""相关药品信息：
药品名称: {medicine_info.get('medicine_name', '未知')}
规格: {medicine_info.get('dosage', '未知')}
用法用量: {medicine_info.get('usage', '未知')}
禁忌症: {medicine_info.get('contraindications', '无')}

"""
        
        prompt += f"""用户问题：{question}

请详细回答上述问题："""
        
        return prompt
    
    def _get_answer_from_llm(self, prompt: str) -> str:
        """
        从LLM获取答案
        
        Args:
            prompt: 提示词
            
        Returns:
            str: 答案
        """
        try:
            if self.llm_parser.provider == "openai":
                import openai
                openai.api_key = self.llm_parser.api_key
                
                response = openai.ChatCompletion.create(
                    model=self.llm_parser.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的医药咨询助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                answer = response.choices[0].message.content
                return answer
            else:
                return "暂不支持的大模型提供商"
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            return "暂时无法获取回答，请稍后重试。"
    
    def ask_about_drug_interaction(self, drug1: str, drug2: str) -> str:
        """
        询问两种药物是否有相互作用
        
        Args:
            drug1: 第一种药物
            drug2: 第二种药物
            
        Returns:
            str: 相互作用信息
        """
        question = f"{drug1}和{drug2}一起服用会有相互作用吗？有什么需要注意的？"
        return self.ask(question)
    
    def ask_about_side_effects(self, medicine_name: str) -> str:
        """
        询问副作用
        
        Args:
            medicine_name: 药品名称
            
        Returns:
            str: 副作用信息
        """
        question = f"{medicine_name}的副作用有哪些？哪些是常见的，哪些是严重的？"
        return self.ask(question)
    
    def ask_about_precautions(self, medicine_name: str) -> str:
        """
        询问注意事项
        
        Args:
            medicine_name: 药品名称
            
        Returns:
            str: 注意事项
        """
        question = f"服用{medicine_name}需要注意什么？有什么禁忌吗？"
        return self.ask(question)
    
    def get_conversation_history(self) -> List[Dict]:
        """
        获取对话历史
        
        Returns:
            list: 对话历史列表
        """
        return self.conversation_history
    
    def clear_conversation_history(self):
        """清除对话历史"""
        self.conversation_history = []
        self.logger.info("对话历史已清除")
    
    def save_conversation_to_file(self, file_path: str) -> bool:
        """
        保存对话记录到文件
        
        Args:
            file_path: 保存路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"对话记录已保存: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存对话记录失败: {e}")
            return False


class MedicationAdvisor:
    """用药顾问"""
    
    def __init__(self, qa_system: QASystem, medication_db):
        """
        初始化用药顾问
        
        Args:
            qa_system: QASystem对象
            medication_db: MedicationDatabase对象
        """
        self.logger = logging.getLogger(__name__)
        self.qa_system = qa_system
        self.medication_db = medication_db
    
    def check_drug_interaction(self, medicine_ids: List[int]) -> Dict:
        """
        检查多种药物是否有相互作用
        
        Args:
            medicine_ids: 药品ID列表
            
        Returns:
            dict: 相互作用检查结果
        """
        try:
            medicines = []
            for med_id in medicine_ids:
                med = self.medication_db.get_medicine(med_id)
                if med:
                    medicines.append(med['medicine_name'])
            
            if len(medicines) < 2:
                return {"status": "error", "message": "至少需要两种药物"}
            
            result = {
                "medicines": medicines,
                "interactions": []
            }
            
            # 检查两两之间的相互作用
            for i in range(len(medicines)):
                for j in range(i + 1, len(medicines)):
                    interaction = self.qa_system.ask_about_drug_interaction(
                        medicines[i], medicines[j]
                    )
                    result["interactions"].append({
                        "drug1": medicines[i],
                        "drug2": medicines[j],
                        "info": interaction
                    })
            
            return result
        except Exception as e:
            self.logger.error(f"检查药物相互作用失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_medication_plan(self, medicine_id: int) -> str:
        """
        获取用药计划建议
        
        Args:
            medicine_id: 药品ID
            
        Returns:
            str: 用药计划建议
        """
        try:
            medicine = self.medication_db.get_medicine(medicine_id)
            if not medicine:
                return "药品信息未找到"
            
            prompt = f"""
请根据以下药品信息，为老年患者制定一个安全的用药计划：

药品名称: {medicine.get('medicine_name')}
规格: {medicine.get('dosage')}
用法用量: {medicine.get('usage')}
注意事项: {medicine.get('precautions')}

请提供：
1. 建议的服药时间
2. 服药方式和注意事项
3. 可能的不良反应及应对方法
4. 何时应该停止用药或咨询医生
"""
            
            answer = self.qa_system.ask(prompt, medicine)
            return answer
        except Exception as e:
            self.logger.error(f"获取用药计划失败: {e}")
            return "无法生成用药计划，请咨询医生"
