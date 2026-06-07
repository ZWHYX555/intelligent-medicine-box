"""
药品数据库管理模块
支持SQLite和CSV格式的数据存储
"""
import sqlite3
import pandas as pd
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional


class MedicationDatabase:
    """药品数据库管理器"""
    
    def __init__(self, db_path="data/medicine_info.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.csv_path = db_path.replace('.db', '.csv')
        
        # 创建数据库目录
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建药品信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine_name TEXT NOT NULL,
                    generic_name TEXT,
                    manufacturer TEXT,
                    batch_number TEXT,
                    expiry_date TEXT,
                    dosage TEXT,
                    usage TEXT,
                    precautions TEXT,
                    side_effects TEXT,
                    contraindications TEXT,
                    storage TEXT,
                    ingredients TEXT,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建用药记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medication_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine_id INTEGER NOT NULL,
                    scheduled_time TEXT,
                    taken_time TEXT,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
                )
            ''')
            
            # 创建提醒设置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine_id INTEGER NOT NULL,
                    reminder_time TEXT,
                    frequency TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库初始化成功")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
    
    def add_medicine(self, medicine_info: Dict) -> int:
        """
        添加药品信息
        
        Args:
            medicine_info: 药品信息字典
            
        Returns:
            int: 新添加的药品ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO medicines (
                    medicine_name, generic_name, manufacturer, batch_number,
                    expiry_date, dosage, usage, precautions, side_effects,
                    contraindications, storage, ingredients, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                medicine_info.get('medicine_name'),
                medicine_info.get('generic_name'),
                medicine_info.get('manufacturer'),
                medicine_info.get('batch_number'),
                medicine_info.get('expiry_date'),
                medicine_info.get('dosage'),
                medicine_info.get('usage'),
                str(medicine_info.get('precautions', [])),
                str(medicine_info.get('side_effects', [])),
                str(medicine_info.get('contraindications', [])),
                medicine_info.get('storage'),
                str(medicine_info.get('ingredients', [])),
                medicine_info.get('image_path')
            ))
            
            medicine_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"药品添加成功: ID={medicine_id}")
            return medicine_id
        except Exception as e:
            self.logger.error(f"添加药品失败: {e}")
            return None
    
    def get_medicine(self, medicine_id: int) -> Dict:
        """
        获取药品信息
        
        Args:
            medicine_id: 药品ID
            
        Returns:
            dict: 药品信息
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"获取药品信息失败: {e}")
            return None
    
    def get_all_medicines(self) -> List[Dict]:
        """
        获取所有药品信息
        
        Returns:
            list: 药品列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM medicines ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取药品列表失败: {e}")
            return []
    
    def update_medicine(self, medicine_id: int, medicine_info: Dict) -> bool:
        """
        更新药品信息
        
        Args:
            medicine_id: 药品ID
            medicine_info: 更新的信息
            
        Returns:
            bool: 更新是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 动态构建UPDATE语句
            fields = []
            values = []
            for key, value in medicine_info.items():
                if key != 'id':
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            values.append(medicine_id)
            
            query = f"UPDATE medicines SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"药品更新成功: ID={medicine_id}")
            return True
        except Exception as e:
            self.logger.error(f"更新药品失败: {e}")
            return False
    
    def delete_medicine(self, medicine_id: int) -> bool:
        """
        删除药品
        
        Args:
            medicine_id: 药品ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM medicines WHERE id = ?', (medicine_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"药品删除成功: ID={medicine_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除药品失败: {e}")
            return False
    
    def check_expiry(self) -> List[Dict]:
        """
        检查已过期或即将过期的药品
        
        Returns:
            list: 过期或即将过期的药品列表
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查询已过期或30天内过期的药品
            cursor.execute('''
                SELECT * FROM medicines 
                WHERE expiry_date <= ? OR expiry_date >= ?
                ORDER BY expiry_date ASC
            ''', (today, today))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"检查过期药品失败: {e}")
            return []
    
    def export_to_csv(self) -> str:
        """
        导出所有药品信息到CSV
        
        Returns:
            str: CSV文件路径
        """
        try:
            medicines = self.get_all_medicines()
            df = pd.DataFrame(medicines)
            df.to_csv(self.csv_path, index=False, encoding='utf-8')
            
            self.logger.info(f"数据导出成功: {self.csv_path}")
            return self.csv_path
        except Exception as e:
            self.logger.error(f"数据导出失败: {e}")
            return None
    
    def import_from_csv(self, csv_path: str) -> bool:
        """
        从CSV导入药品信息
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            bool: 导入是否成功
        """
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            for _, row in df.iterrows():
                self.add_medicine(row.to_dict())
            
            self.logger.info(f"数据导入成功: {csv_path}")
            return True
        except Exception as e:
            self.logger.error(f"数据导入失败: {e}")
            return False
    
    def add_medication_record(self, medicine_id: int, scheduled_time: str, status: str = "pending") -> bool:
        """
        添加用药记录
        
        Args:
            medicine_id: 药品ID
            scheduled_time: 计划服药时间
            status: 状态 (pending, taken, missed)
            
        Returns:
            bool: 添加是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO medication_records (medicine_id, scheduled_time, status)
                VALUES (?, ?, ?)
            ''', (medicine_id, scheduled_time, status))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            self.logger.error(f"添加用药记录失败: {e}")
            return False
    
    def get_medication_history(self, medicine_id: int, days: int = 30) -> List[Dict]:
        """
        获取用药历史
        
        Args:
            medicine_id: 药品ID
            days: 查询天数
            
        Returns:
            list: 用药记录列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM medication_records 
                WHERE medicine_id = ? AND created_at > datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            ''', (medicine_id, days))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取用药历史失败: {e}")
            return []
