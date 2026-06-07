"""
主窗口UI模块
使用PyQt5构建可视化界面
"""
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QTextEdit,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QColor
from pathlib import Path


class MedicineTableWidget(QWidget):
    """药品列表widget"""
    
    def __init__(self, medicine_box):
        super().__init__()
        self.medicine_box = medicine_box
        self.logger = logging.getLogger(__name__)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        btn_add = QPushButton("添加药品")
        btn_add.clicked.connect(self.add_medicine)
        button_layout.addWidget(btn_add)
        
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh_table)
        button_layout.addWidget(btn_refresh)
        
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(self.delete_medicine)
        button_layout.addWidget(btn_delete)
        
        btn_export = QPushButton("导出")
        btn_export.clicked.connect(self.export_data)
        button_layout.addWidget(btn_export)
        
        layout.addLayout(button_layout)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "药品名称", "规格", "有效期", "用法用量", "状态"
        ])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """刷新表格"""
        medicines = self.medicine_box.get_all_medicines()
        self.table.setRowCount(len(medicines))
        
        for row, med in enumerate(medicines):
            self.table.setItem(row, 0, QTableWidgetItem(str(med.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(med.get('medicine_name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(med.get('dosage', '')))
            self.table.setItem(row, 3, QTableWidgetItem(med.get('expiry_date', '')))
            self.table.setItem(row, 4, QTableWidgetItem(med.get('usage', '')[:30] + '...'))
            self.table.setItem(row, 5, QTableWidgetItem("正常"))
    
    def add_medicine(self):
        """添加药品"""
        dialog = AddMedicineDialog(self.medicine_box)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_table()
    
    def delete_medicine(self):
        """删除药品"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            med_id = int(self.table.item(current_row, 0).text())
            self.medicine_box.medication_db.delete_medicine(med_id)
            self.refresh_table()
    
    def export_data(self):
        """导出数据"""
        file_path = QFileDialog.getSaveFileName(self, "保存文件", "", "CSV Files (*.csv)")[0]
        if file_path:
            self.medicine_box.medication_db.export_to_csv()
            QMessageBox.information(self, "成功", "数据已导出")


class AddMedicineDialog(QDialog):
    """添加药品对话框"""
    
    def __init__(self, medicine_box):
        super().__init__()
        self.medicine_box = medicine_box
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        layout.addRow("药品名称:", self.name_input)
        
        self.dosage_input = QLineEdit()
        layout.addRow("规格:", self.dosage_input)
        
        self.usage_input = QTextEdit()
        layout.addRow("用法用量:", self.usage_input)
        
        self.expiry_input = QLineEdit("YYYY-MM-DD")
        layout.addRow("有效期:", self.expiry_input)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        self.setWindowTitle("添加药品")
    
    def accept(self):
        """确认添加"""
        medicine_info = {
            "medicine_name": self.name_input.text(),
            "dosage": self.dosage_input.text(),
            "usage": self.usage_input.toPlainText(),
            "expiry_date": self.expiry_input.text()
        }
        
        if medicine_info['medicine_name']:
            self.medicine_box.medication_db.add_medicine(medicine_info)
            QMessageBox.information(self, "成功", "药品已添加")
            super().accept()
        else:
            QMessageBox.warning(self, "错误", "请输入药品名称")


class ReminderWidget(QWidget):
    """提醒设置widget"""
    
    def __init__(self, medicine_box):
        super().__init__()
        self.medicine_box = medicine_box
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 按钮
        btn_add = QPushButton("添加提醒")
        btn_add.clicked.connect(self.add_reminder)
        layout.addWidget(btn_add)
        
        # 提醒列表
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["药品", "时间", "频率"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_reminders()
    
    def add_reminder(self):
        """添加提醒"""
        dialog = AddReminderDialog(self.medicine_box)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_reminders()
    
    def refresh_reminders(self):
        """刷新提醒列表"""
        reminders = self.medicine_box.reminder_system.get_all_reminders()
        self.table.setRowCount(len(reminders))
        
        for row, (rid, reminder) in enumerate(reminders.items()):
            med = self.medicine_box.medication_db.get_medicine(reminder['medicine_id'])
            self.table.setItem(row, 0, QTableWidgetItem(med.get('medicine_name', '') if med else ''))
            self.table.setItem(row, 1, QTableWidgetItem(reminder.get('time', '')))
            self.table.setItem(row, 2, QTableWidgetItem(reminder.get('frequency', '')))


class AddReminderDialog(QDialog):
    """添加提醒对话框"""
    
    def __init__(self, medicine_box):
        super().__init__()
        self.medicine_box = medicine_box
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QFormLayout()
        
        self.medicine_combo = QComboBox()
        medicines = self.medicine_box.get_all_medicines()
        for med in medicines:
            self.medicine_combo.addItem(med['medicine_name'], med['id'])
        layout.addRow("药品:", self.medicine_combo)
        
        self.time_input = QLineEdit("09:00")
        layout.addRow("时间 (HH:MM):", self.time_input)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["daily", "weekly"])
        layout.addRow("频率:", self.frequency_combo)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        self.setWindowTitle("添加提醒")
    
    def accept(self):
        """确认添加"""
        medicine_id = self.medicine_combo.currentData()
        time_str = self.time_input.text()
        frequency = self.frequency_combo.currentText()
        
        self.medicine_box.set_medication_reminder(medicine_id, time_str, frequency)
        QMessageBox.information(self, "成功", "提醒已设置")
        super().accept()


class QAWidget(QWidget):
    """问答widget"""
    
    def __init__(self, medicine_box):
        super().__init__()
        self.medicine_box = medicine_box
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 问题输入
        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("输入您的医药问题...")
        layout.addWidget(QLabel("问题:"))
        layout.addWidget(self.question_input)
        
        # 查询按钮
        btn_ask = QPushButton("查询")
        btn_ask.clicked.connect(self.ask_question)
        layout.addWidget(btn_ask)
        
        # 答案显示
        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True)
        layout.addWidget(QLabel("回答:"))
        layout.addWidget(self.answer_display)
        
        self.setLayout(layout)
    
    def ask_question(self):
        """提出问题"""
        question = self.question_input.toPlainText()
        if question:
            answer = self.medicine_box.ask_question(question)
            self.answer_display.setText(answer)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, medicine_box):
        super().__init__()
        self.medicine_box = medicine_box
        self.logger = logging.getLogger(__name__)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("智能药盒助手")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建标签页
        tabs = QTabWidget()
        
        tabs.addTab(MedicineTableWidget(self.medicine_box), "药品管理")
        tabs.addTab(ReminderWidget(self.medicine_box), "提醒设置")
        tabs.addTab(QAWidget(self.medicine_box), "医药问答")
        
        self.setCentralWidget(tabs)
        
        # 启动提醒系统
        self.medicine_box.start_reminders()
    
    def closeEvent(self, event):
        """关闭事件"""
        self.medicine_box.stop_reminders()
        event.accept()


def run_gui(medicine_box):
    """运行GUI"""
    app = QApplication(sys.argv)
    window = MainWindow(medicine_box)
    window.show()
    sys.exit(app.exec_())
