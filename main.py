"""
主应用入口
集成所有模块的完整智能药盒系统
"""
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import load_config, setup_logging, create_directory_structure
from src.image_capture import ImageCapture
from src.ocr_extraction import OCRExtractor
from src.llm_parser import LLMParser
from src.medication_database import MedicationDatabase
from src.voice_assistant import VoiceAssistant
from src.reminder_system import ReminderSystem, ReminderNotification
from src.qa_system import QASystem, MedicationAdvisor
from src.behavior_monitor import BehaviorMonitor, BehaviorAnalyzer


class IntelligentMedicineBox:
    """智能药盒主类"""
    
    def __init__(self, config_path="config/config.yaml"):
        """
        初始化智能药盒系统
        
        Args:
            config_path: 配置文件路径
        """
        # 创建目录结构
        create_directory_structure()
        
        # 初始化日志
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = load_config(config_path)
        if not self.config:
            self.logger.error("配置加载失败")
            sys.exit(1)
        
        self.logger.info("="*50)
        self.logger.info("智能药盒助手系统启动")
        self.logger.info("="*50)
        
        # 初始化各模块
        self._init_modules()
    
    def _init_modules(self):
        """初始化所有模块"""
        try:
            # 初始化图像采集
            self.image_capture = ImageCapture(
                camera_index=self.config.get("image", {}).get("camera_index", 0),
                save_path=self.config.get("image", {}).get("save_path", "data/medicine_images")
            )
            
            # 初始化OCR提取器
            self.ocr_extractor = OCRExtractor(
                use_paddleocr=self.config.get("ocr", {}).get("use_paddleocr", True)
            )
            
            # 初始化LLM解析器
            api_config = self.config.get("api", {})
            self.llm_parser = LLMParser(
                provider=api_config.get("llm_provider", "openai"),
                api_key=api_config.get(f"{api_config.get('llm_provider')}_api_key"),
                model=api_config.get("openai_model", "gpt-3.5-turbo")
            )
            
            # 初始化数据库
            self.medication_db = MedicationDatabase(
                db_path=self.config.get("database", {}).get("path", "data/medicine_info.db")
            )
            
            # 初始化语音助手
            voice_config = self.config.get("voice", {})
            self.voice_assistant = VoiceAssistant(
                rate=voice_config.get("rate", 150),
                volume=voice_config.get("volume", 0.9),
                language=voice_config.get("language", "zh")
            )
            
            # 初始化提醒系统
            self.reminder_system = ReminderSystem()
            self.reminder_notification = ReminderNotification(
                enable_popup=self.config.get("reminder", {}).get("enable_popup", True),
                enable_voice=self.config.get("reminder", {}).get("enable_voice", True)
            )
            self.reminder_notification.set_voice_assistant(self.voice_assistant)
            
            # 初始化问答系统
            self.qa_system = QASystem(self.llm_parser)
            self.medication_advisor = MedicationAdvisor(self.qa_system, self.medication_db)
            
            # 初始化行为监测
            self.behavior_monitor = BehaviorMonitor(
                camera_index=self.config.get("image", {}).get("camera_index", 0),
                enable_pose_detection=self.config.get("behavior", {}).get("enable_monitoring", True)
            )
            self.behavior_analyzer = BehaviorAnalyzer(self.medication_db)
            
            self.logger.info("所有模块初始化成功")
        except Exception as e:
            self.logger.error(f"模块初始化失败: {e}")
            raise
    
    def capture_and_register_medicine(self, medicine_id: str, parts: int = 1):
        """
        拍摄并注册药品
        
        Args:
            medicine_id: 药品ID
            parts: 拍摄份数
        """
        try:
            self.logger.info(f"开始拍摄药品: {medicine_id}")
            
            if not self.image_capture.initialize_camera():
                self.logger.error("摄像头初始化失败")
                return
            
            medicine_images = []
            
            for part in range(1, parts + 1):
                self.logger.info(f"拍摄第 {part} 部分...")
                self.voice_assistant.speak(f"现在拍摄第{part}部分，准备好请按'c'键")
                
                image_path = self.image_capture.capture_and_save(medicine_id, part)
                if image_path:
                    medicine_images.append(image_path)
                    self.logger.info(f"图像已保存: {image_path}")
            
            self.image_capture.release()
            
            # 提取文本
            if medicine_images:
                self.logger.info("开始提取药品信息...")
                all_text = ""
                
                for image_path in medicine_images:
                    result = self.ocr_extractor.extract_text_from_file(image_path)
                    if result:
                        all_text += result + "\n"
                
                # 使用LLM解析
                if all_text:
                    medicine_info = self.llm_parser.parse_medicine_info(all_text)
                    if medicine_info:
                        medicine_info['image_path'] = medicine_images[0]
                        
                        # 保存到数据库
                        med_id = self.medication_db.add_medicine(medicine_info)
                        
                        if med_id:
                            self.logger.info(f"药品已注册: ID={med_id}")
                            self.voice_assistant.speak("药品信息已注册成功")
                            return med_id
        
        except Exception as e:
            self.logger.error(f"药品注册失败: {e}")
            self.voice_assistant.speak(f"错误: {str(e)}")
    
    def set_medication_reminder(self, medicine_id: int, time_str: str, frequency: str = "daily"):
        """
        设置用药提醒
        
        Args:
            medicine_id: 药品ID
            time_str: 提醒时间 (HH:MM格式)
            frequency: 频率
        """
        try:
            medicine = self.medication_db.get_medicine(medicine_id)
            if not medicine:
                self.logger.error(f"药品不存在: {medicine_id}")
                return False
            
            def reminder_callback():
                self.logger.info(f"触发提醒: {medicine['medicine_name']}")
                self.reminder_notification.notify(medicine)
            
            reminder_id = len(self.reminder_system.reminders) + 1
            self.reminder_system.add_reminder(
                reminder_id, medicine_id, time_str, reminder_callback, frequency
            )
            
            self.logger.info(f"提醒已设置: {medicine['medicine_name']} at {time_str}")
            return True
        except Exception as e:
            self.logger.error(f"设置提醒失败: {e}")
            return False
    
    def start_reminders(self):
        """启动提醒系统"""
        self.reminder_system.start_scheduler()
        self.logger.info("提醒系统已启动")
    
    def stop_reminders(self):
        """停止提醒系统"""
        self.reminder_system.stop_scheduler()
        self.logger.info("提醒系统已停止")
    
    def get_all_medicines(self):
        """获取所有药品"""
        return self.medication_db.get_all_medicines()
    
    def check_expiry_medicines(self):
        """检查过期药品"""
        expired = self.medication_db.check_expiry()
        if expired:
            self.logger.warning(f"发现 {len(expired)} 种过期或即将过期的药品")
            for med in expired:
                self.logger.warning(f"- {med['medicine_name']}: {med['expiry_date']}")
        return expired
    
    def ask_question(self, question: str, medicine_id: int = None):
        """
        提出医药咨询问题
        
        Args:
            question: 问题
            medicine_id: 相关药品ID
            
        Returns:
            str: 回答
        """
        medicine_info = None
        if medicine_id:
            medicine_info = self.medication_db.get_medicine(medicine_id)
        
        answer = self.qa_system.ask(question, medicine_info)
        self.logger.info(f"问答: Q: {question[:50]}... A: {answer[:100]}...")
        return answer
    
    def export_data(self):
        """导出数据"""
        csv_path = self.medication_db.export_to_csv()
        if csv_path:
            self.logger.info(f"数据已导出到: {csv_path}")
        return csv_path
    
    def generate_report(self):
        """生成健康报告"""
        try:
            report = {
                "medicines_count": len(self.get_all_medicines()),
                "expired_medicines": len(self.check_expiry_medicines()),
                "medication_compliance": self.behavior_analyzer.analyze_medication_compliance(),
                "alerts": self.behavior_analyzer.get_medication_alerts()
            }
            
            self.logger.info("健康报告已生成")
            return report
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            return None


def main():
    """主函数"""
    try:
        # 初始化系统
        system = IntelligentMedicineBox()
        
        # 测试语音
        system.voice_assistant.test_voice()
        
        # 启动提醒系统
        system.start_reminders()
        
        # 示例: 获取所有药品
        medicines = system.get_all_medicines()
        print(f"系统中有 {len(medicines)} 种药品")
        
        # 生成报告
        report = system.generate_report()
        print("\n=== 健康报告 ===")
        print(f"药品总数: {report['medicines_count']}")
        print(f"过期药品: {report['expired_medicines']}")
        
        print("\n系统已启动，按 Ctrl+C 退出")
        
        # 保持运行
        import time
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n系统正在关闭...")
        system.stop_reminders()
        print("系统已关闭")
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
