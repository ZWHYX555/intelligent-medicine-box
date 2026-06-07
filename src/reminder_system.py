"""
定时提醒系统模块
管理服药提醒和通知
"""
import schedule
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from threading import Thread, Event


class ReminderSystem:
    """定时提醒系统"""
    
    def __init__(self):
        """初始化提醒系统"""
        self.logger = logging.getLogger(__name__)
        self.reminders: Dict[int, Dict] = {}
        self.scheduler_running = False
        self.scheduler_thread: Optional[Thread] = None
        self.stop_event = Event()
    
    def add_reminder(self, reminder_id: int, medicine_id: int, time_str: str, 
                    callback: Callable, frequency: str = "daily") -> bool:
        """
        添加提醒
        
        Args:
            reminder_id: 提醒ID
            medicine_id: 药品ID
            time_str: 提醒时间 (HH:MM格式)
            callback: 回调函数
            frequency: 频率 (daily, weekly, custom)
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.reminders[reminder_id] = {
                "medicine_id": medicine_id,
                "time": time_str,
                "callback": callback,
                "frequency": frequency,
                "enabled": True,
                "job": None
            }
            
            # 注册任务
            self._register_job(reminder_id, time_str, callback, frequency)
            
            self.logger.info(f"提醒已添加: ID={reminder_id}, 时间={time_str}")
            return True
        except Exception as e:
            self.logger.error(f"添加提醒失败: {e}")
            return False
    
    def _register_job(self, reminder_id: int, time_str: str, 
                     callback: Callable, frequency: str):
        """
        注册定时任务
        
        Args:
            reminder_id: 提醒ID
            time_str: 时间字符串
            callback: 回调函数
            frequency: 频率
        """
        try:
            if frequency == "daily":
                job = schedule.every().day.at(time_str).do(callback)
            elif frequency == "weekly":
                job = schedule.every().week.at(time_str).do(callback)
            else:
                job = schedule.every().day.at(time_str).do(callback)
            
            self.reminders[reminder_id]["job"] = job
        except Exception as e:
            self.logger.error(f"任务注册失败: {e}")
    
    def remove_reminder(self, reminder_id: int) -> bool:
        """
        删除提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if reminder_id in self.reminders:
                job = self.reminders[reminder_id]["job"]
                if job:
                    schedule.cancel_job(job)
                
                del self.reminders[reminder_id]
                self.logger.info(f"提醒已删除: ID={reminder_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"删除提醒失败: {e}")
            return False
    
    def enable_reminder(self, reminder_id: int) -> bool:
        """
        启用提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 启用是否成功
        """
        try:
            if reminder_id in self.reminders:
                self.reminders[reminder_id]["enabled"] = True
                self.logger.info(f"提醒已启用: ID={reminder_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"启用提醒失败: {e}")
            return False
    
    def disable_reminder(self, reminder_id: int) -> bool:
        """
        禁用提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 禁用是否成功
        """
        try:
            if reminder_id in self.reminders:
                self.reminders[reminder_id]["enabled"] = False
                self.logger.info(f"提醒已禁用: ID={reminder_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"禁用提醒失败: {e}")
            return False
    
    def get_reminder(self, reminder_id: int) -> Optional[Dict]:
        """
        获取提醒信息
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            dict: 提醒信息
        """
        return self.reminders.get(reminder_id)
    
    def get_all_reminders(self) -> Dict:
        """
        获取所有提醒
        
        Returns:
            dict: 所有提醒
        """
        return self.reminders
    
    def start_scheduler(self):
        """启动调度器"""
        if self.scheduler_running:
            self.logger.warning("调度器已在运行")
            return
        
        self.scheduler_running = True
        self.stop_event.clear()
        
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("提醒调度器已启动")
    
    def _run_scheduler(self):
        """运行调度器"""
        while not self.stop_event.is_set():
            try:
                pending = schedule.run_pending()
                if pending:
                    self.logger.debug(f"执行了 {len(pending)} 个待定任务")
                
                # 检查是否需要执行
                schedule.idle_seconds
            except Exception as e:
                self.logger.error(f"调度器运行出错: {e}")
            
            # 减少CPU占用
            import time
            time.sleep(1)
    
    def stop_scheduler(self):
        """停止调度器"""
        if not self.scheduler_running:
            self.logger.warning("调度器未在运行")
            return
        
        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.scheduler_running = False
        self.logger.info("提醒调度器已停止")
    
    def get_next_reminder(self) -> Optional[Dict]:
        """
        获取下一个提醒
        
        Returns:
            dict: 下一个提醒的信息
        """
        try:
            pending_jobs = schedule.get_jobs()
            if pending_jobs:
                next_job = pending_jobs[0]
                return {
                    "time": next_job.next_run,
                    "job": next_job
                }
            return None
        except Exception as e:
            self.logger.error(f"获取下一个提醒失败: {e}")
            return None
    
    def is_time_for_reminder(self, reminder_id: int) -> bool:
        """
        检查是否是提醒时间
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            bool: 是否是提醒时间
        """
        try:
            if reminder_id not in self.reminders:
                return False
            
            reminder = self.reminders[reminder_id]
            if not reminder["enabled"]:
                return False
            
            time_str = reminder["time"]
            now_time = datetime.now().strftime("%H:%M")
            
            # 允许5分钟的时间差
            current = datetime.strptime(now_time, "%H:%M")
            reminder_time = datetime.strptime(time_str, "%H:%M")
            time_diff = abs((current - reminder_time).total_seconds())
            
            return time_diff < 300  # 5分钟内
        except Exception as e:
            self.logger.error(f"检查提醒时间失败: {e}")
            return False


class ReminderNotification:
    """提醒通知类"""
    
    def __init__(self, enable_popup=True, enable_voice=True):
        """
        初始化提醒通知
        
        Args:
            enable_popup: 是否启用弹窗
            enable_voice: 是否启用语音
        """
        self.logger = logging.getLogger(__name__)
        self.enable_popup = enable_popup
        self.enable_voice = enable_voice
        self.voice_assistant = None
    
    def set_voice_assistant(self, voice_assistant):
        """
        设置语音助手
        
        Args:
            voice_assistant: VoiceAssistant对象
        """
        self.voice_assistant = voice_assistant
    
    def notify(self, medicine_info: Dict, advance_minutes: int = 0) -> bool:
        """
        发送通知
        
        Args:
            medicine_info: 药品信息
            advance_minutes: 提前分钟数
            
        Returns:
            bool: 通知是否成功
        """
        try:
            if advance_minutes > 0:
                message = f"提醒您在{advance_minutes}分钟后服用{medicine_info.get('medicine_name')}"
            else:
                message = f"该服药了！请服用{medicine_info.get('medicine_name')}"
            
            success = True
            
            if self.enable_popup:
                success = success and self._show_popup(medicine_info)
            
            if self.enable_voice and self.voice_assistant:
                success = success and self.voice_assistant.speak_medicine_info(medicine_info)
            
            return success
        except Exception as e:
            self.logger.error(f"发送通知失败: {e}")
            return False
    
    def _show_popup(self, medicine_info: Dict) -> bool:
        """
        显示弹窗
        
        Args:
            medicine_info: 药品信息
            
        Returns:
            bool: 弹窗是否显示成功
        """
        try:
            # 这里可以集成GUI弹窗
            self.logger.info(f"弹窗通知: {medicine_info.get('medicine_name')}")
            return True
        except Exception as e:
            self.logger.error(f"显示弹窗失败: {e}")
            return False
