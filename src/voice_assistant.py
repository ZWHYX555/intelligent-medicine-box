"""
语音助手模块
支持语音播报和语音识别
"""
import pyttsx3
import logging
from typing import Optional


class VoiceAssistant:
    """语音助手类"""
    
    def __init__(self, rate=150, volume=0.9, language="zh"):
        """
        初始化语音助手
        
        Args:
            rate: 语速 (50-300)
            volume: 音量 (0.0-1.0)
            language: 语言 (zh, en)
        """
        self.logger = logging.getLogger(__name__)
        self.rate = rate
        self.volume = volume
        self.language = language
        
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            self._set_voice_language()
            self.logger.info("语音引擎初始化成功")
        except Exception as e:
            self.logger.error(f"语音引擎初始化失败: {e}")
            self.engine = None
    
    def _set_voice_language(self):
        """设置语音语言"""
        try:
            voices = self.engine.getProperty('voices')
            
            if self.language == "zh":
                # 选择中文语音
                for voice in voices:
                    if 'Chinese' in voice.name or 'zh' in voice.languages:
                        self.engine.setProperty('voice', voice.id)
                        return
            elif self.language == "en":
                # 选择英文语音
                for voice in voices:
                    if 'English' in voice.name:
                        self.engine.setProperty('voice', voice.id)
                        return
            
            # 如果找不到对应语言，使用默认
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            self.logger.warning(f"设置语音语言失败: {e}")
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        语音播报文本
        
        Args:
            text: 要播报的文本
            wait: 是否等待播报完成
            
        Returns:
            bool: 播报是否成功
        """
        if self.engine is None:
            self.logger.error("语音引擎未初始化")
            return False
        
        try:
            self.engine.say(text)
            if wait:
                self.engine.runAndWait()
            self.logger.info(f"语音播报: {text}")
            return True
        except Exception as e:
            self.logger.error(f"语音播报失败: {e}")
            return False
    
    def speak_medicine_info(self, medicine_info: dict) -> bool:
        """
        播报药品信息
        
        Args:
            medicine_info: 药品信息字典
            
        Returns:
            bool: 播报是否成功
        """
        try:
            text = f"""现在时间提醒您服药。
            药品名称：{medicine_info.get('medicine_name', '未知')}。
            用法用量：{medicine_info.get('usage', '未知')}。
            """
            
            # 添加注意事项
            precautions = medicine_info.get('precautions', [])
            if precautions:
                text += f"注意事项：{', '.join(precautions)}。"
            
            return self.speak(text)
        except Exception as e:
            self.logger.error(f"播报药品信息失败: {e}")
            return False
    
    def speak_reminder(self, medicine_name: str, usage: str) -> bool:
        """
        播报服药提醒
        
        Args:
            medicine_name: 药品名称
            usage: 用法用量
            
        Returns:
            bool: 提醒是否成功
        """
        text = f"该服药了！请服用{medicine_name}，{usage}。"
        return self.speak(text)
    
    def speak_expiry_warning(self, medicine_name: str, days_left: int) -> bool:
        """
        播报过期预警
        
        Args:
            medicine_name: 药品名称
            days_left: 剩余天数（负数表示已过期）
            
        Returns:
            bool: 警告是否成功
        """
        if days_left < 0:
            text = f"注意！{medicine_name}已经过期，请勿使用。"
        elif days_left == 0:
            text = f"警告！{medicine_name}今天过期，请确认是否还要使用。"
        else:
            text = f"提醒您，{medicine_name}将在{days_left}天后过期。"
        
        return self.speak(text)
    
    def speak_error_message(self, error_msg: str) -> bool:
        """
        播报错误信息
        
        Args:
            error_msg: 错误信息
            
        Returns:
            bool: 播报是否成功
        """
        text = f"出错了：{error_msg}"
        return self.speak(text)
    
    def set_rate(self, rate: int) -> bool:
        """
        设置语速
        
        Args:
            rate: 语速 (50-300)
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if 50 <= rate <= 300:
                self.rate = rate
                self.engine.setProperty('rate', rate)
                return True
            else:
                self.logger.warning(f"语速超出范围: {rate}")
                return False
        except Exception as e:
            self.logger.error(f"设置语速失败: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """
        设置音量
        
        Args:
            volume: 音量 (0.0-1.0)
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if 0.0 <= volume <= 1.0:
                self.volume = volume
                self.engine.setProperty('volume', volume)
                return True
            else:
                self.logger.warning(f"音量超出范围: {volume}")
                return False
        except Exception as e:
            self.logger.error(f"设置音量失败: {e}")
            return False
    
    def test_voice(self) -> bool:
        """
        测试语音
        
        Returns:
            bool: 测试是否成功
        """
        return self.speak("语音测试成功，智能药盒助手已准备就绪。")


class SpeechRecognizer:
    """语音识别类"""
    
    def __init__(self):
        """初始化语音识别器"""
        self.logger = logging.getLogger(__name__)
        
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.logger.info("语音识别器初始化成功")
        except ImportError:
            self.logger.error("speech_recognition未安装")
            self.recognizer = None
    
    def recognize_from_microphone(self, language: str = "zh-CN") -> Optional[str]:
        """
        从麦克风识别语音
        
        Args:
            language: 语言代码
            
        Returns:
            str: 识别的文本
        """
        if self.recognizer is None:
            self.logger.error("语音识别器未初始化")
            return None
        
        try:
            with self.microphone as source:
                self.logger.info("正在监听...")
                audio = self.recognizer.listen(source, timeout=10)
            
            # 使用谷歌语音识别
            text = self.recognizer.recognize_google(audio, language=language)
            self.logger.info(f"识别结果: {text}")
            return text
        except Exception as e:
            self.logger.error(f"语音识别失败: {e}")
            return None
    
    def recognize_from_file(self, file_path: str, language: str = "zh-CN") -> Optional[str]:
        """
        从音频文件识别语音
        
        Args:
            file_path: 音频文件路径
            language: 语言代码
            
        Returns:
            str: 识别的文本
        """
        if self.recognizer is None:
            self.logger.error("语音识别器未初始化")
            return None
        
        try:
            with open(file_path, 'rb') as f:
                audio = self.recognizer.record(f)
            
            text = self.recognizer.recognize_google(audio, language=language)
            self.logger.info(f"识别结果: {text}")
            return text
        except Exception as e:
            self.logger.error(f"文件识别失败: {e}")
            return None
