"""
行为监测与分析模块
使用计算机视觉技术监测老人服药动作
"""
import cv2
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class BehaviorMonitor:
    """行为监测类"""
    
    def __init__(self, camera_index=0, enable_pose_detection=True):
        """
        初始化行为监测器
        
        Args:
            camera_index: 摄像头索引
            enable_pose_detection: 是否启用姿态检测
        """
        self.logger = logging.getLogger(__name__)
        self.camera_index = camera_index
        self.cap = None
        self.enable_pose_detection = enable_pose_detection
        self.pose_detector = None
        self.behavior_logs = []
        
        if enable_pose_detection:
            self._init_pose_detector()
    
    def _init_pose_detector(self):
        """初始化姿态检测器"""
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose_detector = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True
            )
            self.logger.info("姿态检测器初始化成功")
        except ImportError:
            self.logger.error("mediapipe未安装，请执行: pip install mediapipe")
            self.enable_pose_detection = False
        except Exception as e:
            self.logger.error(f"姿态检测器初始化失败: {e}")
            self.enable_pose_detection = False
    
    def initialize_camera(self):
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.logger.error("无法打开摄像头")
                return False
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.logger.info("摄像头初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"摄像头初始化失败: {e}")
            return False
    
    def detect_medication_taking(self, frame) -> Dict:
        """
        检测服药动作
        
        Args:
            frame: 图像帧
            
        Returns:
            dict: 检测结果
        """
        try:
            if not self.enable_pose_detection or self.pose_detector is None:
                return {"detected": False, "action": "unknown"}
            
            # 转换为RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 检测姿态
            results = self.pose_detector.process(rgb_frame)
            
            if not results.pose_landmarks:
                return {"detected": False, "action": "no_person"}
            
            # 分析姿态
            landmarks = results.pose_landmarks.landmark
            action = self._analyze_pose(landmarks)
            
            return {
                "detected": True,
                "action": action,
                "confidence": 0.8,
                "landmarks": landmarks
            }
        except Exception as e:
            self.logger.error(f"姿态检测失败: {e}")
            return {"detected": False, "error": str(e)}
    
    def _analyze_pose(self, landmarks) -> str:
        """
        分析姿态
        
        Args:
            landmarks: 人体关键点
            
        Returns:
            str: 动作名称
        """
        try:
            # 获取关键点坐标
            # 11: 左肩, 12: 右肩, 13: 左肘, 14: 右肘, 15: 左腕, 16: 右腕
            left_hand_y = landmarks[15].y
            right_hand_y = landmarks[16].y
            mouth_y = landmarks[9].y  # 近似口部位置
            
            # 判断手是否在嘴附近（服药动作）
            hand_near_mouth_threshold = 0.1
            
            if (abs(left_hand_y - mouth_y) < hand_near_mouth_threshold or 
                abs(right_hand_y - mouth_y) < hand_near_mouth_threshold):
                return "taking_medicine"
            
            # 判断手的位置
            if left_hand_y < 0.3 or right_hand_y < 0.3:
                return "hands_up"
            elif left_hand_y > 0.7 or right_hand_y > 0.7:
                return "hands_down"
            else:
                return "normal"
        except Exception as e:
            self.logger.error(f"姿态分析失败: {e}")
            return "unknown"
    
    def record_behavior(self, behavior: str, metadata: Dict = None) -> bool:
        """
        记录行为
        
        Args:
            behavior: 行为描述
            metadata: 元数据
            
        Returns:
            bool: 记录是否成功
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "behavior": behavior,
                "metadata": metadata or {}
            }
            
            self.behavior_logs.append(log_entry)
            self.logger.info(f"行为已记录: {behavior}")
            return True
        except Exception as e:
            self.logger.error(f"记录行为失败: {e}")
            return False
    
    def get_behavior_logs(self, days: int = 1) -> List[Dict]:
        """
        获取行为日志
        
        Args:
            days: 查询天数
            
        Returns:
            list: 行为日志列表
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        filtered_logs = []
        
        for log in self.behavior_logs:
            log_time = datetime.fromisoformat(log["timestamp"])
            if log_time > cutoff_time:
                filtered_logs.append(log)
        
        return filtered_logs
    
    def analyze_behavior_pattern(self) -> Dict:
        """
        分析行为模式
        
        Returns:
            dict: 行为分析结果
        """
        try:
            behavior_count = {}
            
            for log in self.behavior_logs:
                behavior = log["behavior"]
                behavior_count[behavior] = behavior_count.get(behavior, 0) + 1
            
            return {
                "total_records": len(self.behavior_logs),
                "behavior_distribution": behavior_count,
                "last_record": self.behavior_logs[-1] if self.behavior_logs else None
            }
        except Exception as e:
            self.logger.error(f"行为分析失败: {e}")
            return {}
    
    def save_behavior_logs(self, file_path: str) -> bool:
        """
        保存行为日志
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.behavior_logs, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"行为日志已保存: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存行为日志失败: {e}")
            return False
    
    def start_monitoring(self, callback=None, record_interval=1):
        """
        启动实时监测
        
        Args:
            callback: 检测回调函数
            record_interval: 记录间隔（秒）
        """
        if not self.initialize_camera():
            return
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # 检测动作
                detection = self.detect_medication_taking(frame)
                
                # 定期记录
                if frame_count % (30 * record_interval) == 0:
                    self.record_behavior(
                        detection.get("action", "unknown"),
                        {"frame": frame_count}
                    )
                
                # 调用回调函数
                if callback:
                    callback(frame, detection)
                
                frame_count += 1
                
                # 按'q'退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            self.logger.info("监测被中断")
        finally:
            self.release()
    
    def release(self):
        """释放资源"""
        if self.cap:
            self.cap.release()
        if self.pose_detector:
            self.pose_detector = None
        cv2.destroyAllWindows()
        self.logger.info("监测资源已释放")


class BehaviorAnalyzer:
    """行为分析器"""
    
    def __init__(self, db):
        """
        初始化行为分析器
        
        Args:
            db: MedicationDatabase对象
        """
        self.logger = logging.getLogger(__name__)
        self.db = db
    
    def analyze_medication_compliance(self, days: int = 30) -> Dict:
        """
        分析用药依从性
        
        Args:
            days: 分析天数
            
        Returns:
            dict: 分析结果
        """
        try:
            medications = self.db.get_all_medicines()
            
            compliance_data = {}
            
            for med in medications:
                history = self.db.get_medication_history(med['id'], days)
                
                total = len(history)
                taken = sum(1 for h in history if h['status'] == 'taken')
                missed = sum(1 for h in history if h['status'] == 'missed')
                
                compliance_rate = (taken / total * 100) if total > 0 else 0
                
                compliance_data[med['medicine_name']] = {
                    "total_scheduled": total,
                    "taken": taken,
                    "missed": missed,
                    "compliance_rate": compliance_rate
                }
            
            return compliance_data
        except Exception as e:
            self.logger.error(f"用药依从性分析失败: {e}")
            return {}
    
    def get_medication_alerts(self) -> List[Dict]:
        """
        获取用药警报
        
        Returns:
            list: 警报列表
        """
        try:
            alerts = []
            
            # 检查过期药品
            expired = self.db.check_expiry()
            for med in expired:
                alerts.append({
                    "type": "expiry_warning",
                    "medicine": med['medicine_name'],
                    "expiry_date": med['expiry_date'],
                    "severity": "high"
                })
            
            # 检查用药依从性
            compliance = self.analyze_medication_compliance()
            for med_name, data in compliance.items():
                if data['compliance_rate'] < 50:
                    alerts.append({
                        "type": "low_compliance",
                        "medicine": med_name,
                        "compliance_rate": data['compliance_rate'],
                        "severity": "medium"
                    })
            
            return alerts
        except Exception as e:
            self.logger.error(f"获取用药警报失败: {e}")
            return []
