# 智能药盒助手 - 高级开发者指南

## 📋 项目概述

这是一个基于多模态大模型的老人用药智能监护协同系统，集成了图像识别、OCR文字提取、大模型解析、语音播报、定时提醒、智能问答和行为监测等功能。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────┐
│          智能药盒助手系统                             │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐  ┌───────────��──┐  ┌────────────┐ │
│  │  图像采集    │  │  文字识别    │  │  信息解析  │ │
│  │ (OpenCV)    │→ │  (OCR)      │→ │  (LLM)    │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│         ▲                                     │       │
│         │                                     ▼       │
│  ┌──────────────────────────────────────────────────┐│
│  │         数据库管理 (SQLite + CSV)               ││
│  └──────────────────────────────────────────────────┘│
│         ▲                 ▲              ▲            │
│         │                 │              │            │
│  ┌──────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ 定时提醒 │  │  智能问答系统   │  │ 行为监测    │ │
│  │(Scheduler)│ │  (QA System)    │  │ (Behavior)  │ │
│  └──────────┘  └─────────────────┘  └─────────────┘ │
│         ▲              ▲                  ▲           │
│         └──────────────┼──────────────────┘           │
│                        ▼                              │
│                 ┌────────────────┐                    │
│                 │  语音系统      │                    │
│                 │  (pyttsx3)     │                    │
│                 └────────────────┘                    │
│                        ▲                              │
│                        │                              │
│                 ┌────────────────┐                    │
│                 │   PyQt5 GUI    │                    │
│                 └────────────────┘                    │
│                                                       │
└──────────────────────────────────────────���──────────┘
```

## 📦 核心模块说明

### 1. 图像采集模块 (`src/image_capture.py`)

**功能**：
- 实时摄像头图像采集
- 批量药品图像保存
- 支持多面拍摄（yp001-1.jpg, yp001-2.jpg等）

**关键方法**：
```python
capture = ImageCapture()
capture.initialize_camera()
capture.start_preview()  # 实时预览
capture.capture_and_save("001", 1)  # 保存单张
```

### 2. OCR提取模块 (`src/ocr_extraction.py`)

**功能**：
- PaddleOCR 和 Tesseract 双引擎
- 图像预处理和优化
- 文本框检测和绘制

**关键方法**：
```python
ocr = OCRExtractor(use_paddleocr=True)
result = ocr.extract_text_from_image("path/to/image.jpg")
# 返回: {"texts": [...], "boxes": [...], "confidences": [...], "full_text": "..."}
```

### 3. LLM解析模块 (`src/llm_parser.py`)

**功能**：
- 支持 OpenAI, 百度千帆, 讯飞API
- 结构化信息提取
- JSON格式输出

**关键方法**：
```python
parser = LLMParser(provider="openai", api_key="...")
info = parser.parse_medicine_info(ocr_text)
# 返回结构化的药品信息
```

**提取字段**：
- medicine_name: 药品名称
- expiry_date: 有效期 (YYYY-MM-DD)
- usage: 用法用量
- precautions: 注意事项
- side_effects: 副作用
- contraindications: 禁忌症

### 4. 数据库管理模块 (`src/medication_database.py`)

**功能**：
- SQLite数据库管理
- CSV导入导出
- 用药记录和历史

**关键方法**：
```python
db = MedicationDatabase()
med_id = db.add_medicine(medicine_info)
db.check_expiry()  # 检查过期
db.export_to_csv()  # 导出数据
```

### 5. 定时提醒系统 (`src/reminder_system.py`)

**功能**：
- 灵活的定时任务调度
- 支持每日/每周提醒
- 弹窗+语音双通知

**关键方法**：
```python
reminder_sys = ReminderSystem()
reminder_sys.add_reminder(1, med_id, "09:00", callback, "daily")
reminder_sys.start_scheduler()
```

### 6. 语音系统 (`src/voice_assistant.py`)

**功能**：
- 中文/英文语音播报
- 语速/音量可调
- 药品信息播报

**关键方法**：
```python
voice = VoiceAssistant(language="zh")
voice.speak("现在是服药时间")
voice.speak_medicine_info(medicine_info)
voice.speak_expiry_warning(med_name, days_left)
```

### 7. 智能问答系统 (`src/qa_system.py`)

**功能**：
- 7×24小时医药咨询
- 药物相互作用检查
- 用药建议生成

**关键方法**：
```python
qa = QASystem(llm_parser)
answer = qa.ask("阿司匹林和布洛芬能一起吃吗？")
answer = qa.ask_about_drug_interaction("药物1", "药物2")
```

### 8. 行为监测模块 (`src/behavior_monitor.py`)

**功能**：
- MediaPipe姿态检测
- 服药动作识别
- 行为日志记录

**关键方法**：
```python
monitor = BehaviorMonitor()
detection = monitor.detect_medication_taking(frame)
monitor.start_monitoring(callback)
monitor.save_behavior_logs("logs/behavior.json")
```

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API
编辑 `config/config.yaml`：
```yaml
api:
  llm_provider: "openai"
  openai_api_key: "your-api-key"
  openai_model: "gpt-4-vision"
```

### 运行应用

**命令行模式**：
```bash
python main.py
```

**GUI模式**：
```python
from main import IntelligentMedicineBox
from ui.main_window import run_gui

system = IntelligentMedicineBox()
run_gui(system)
```

## 💡 使用示例

### 1. 药品注册
```python
system = IntelligentMedicineBox()
med_id = system.capture_and_register_medicine("001", parts=2)
```

### 2. 设置提醒
```python
system.set_medication_reminder(med_id, "09:00", "daily")
system.start_reminders()
```

### 3. 智能咨询
```python
answer = system.ask_question("感冒能吃阿司匹林吗?")
print(answer)
```

### 4. 行为监测
```python
from src.behavior_monitor import BehaviorMonitor
monitor = BehaviorMonitor()
monitor.start_monitoring()
```

## 📊 数据结构

### 药品信息结构
```json
{
  "id": 1,
  "medicine_name": "阿司匹林",
  "generic_name": "乙酰水杨酸",
  "manufacturer": "拜耳",
  "batch_number": "20230101",
  "expiry_date": "2025-12-31",
  "dosage": "100mg×30片",
  "usage": "口服，每日一次，每次1片",
  "precautions": ["饭后服用", "避免空腹"],
  "side_effects": ["胃部不适", "过敏"],
  "contraindications": ["对阿司匹林过敏"],
  "storage": "阴凉干燥处",
  "ingredients": ["乙酰水杨酸"],
  "image_path": "data/medicine_images/yp001.jpg"
}
```

## 🔧 配置说明

### 图像处理配置
```yaml
image:
  camera_index: 0          # 摄像头索引
  image_width: 1280        # 图像宽度
  image_height: 720        # 图像高度
  quality: 95              # 图像质量
```

### OCR配置
```yaml
ocr:
  use_paddleocr: true      # 使用PaddleOCR
  language: ["ch", "en"]   # 支持语言
  use_gpu: false           # 是否使用GPU
```

### 提醒配置
```yaml
reminder:
  enable_popup: true       # 启用弹窗
  enable_voice: true       # 启用语音
  reminder_advance_minutes: 10  # 提前提醒
```

## 🔐 安全建议

1. **API密钥管理**
   - 不要在代码中硬编码API密钥
   - 使用环境变量或配置文件
   - 定期轮换密钥

2. **隐私保护**
   - 本地存储用户数据
   - 加密敏感信息
   - 遵守GDPR/CCPA

3. **数据备份**
   - 定期导出数据
   - 多地备份
   - 测试恢复流程

## 🐛 常见问题

### Q: 摄像头无法打开
**A**: 检查摄像头驱动，确保没有其他应用占用

### Q: OCR识别不准
**A**: 确保光线充足，拍照角度正确，使用 `preprocess_image()` 优化

### Q: LLM API超时
**A**: 检查网络连接，增加超时时间，考虑使用代理

### Q: 语音播报没有声音
**A**: 检查系统音量，验证pyttsx3是否正确安装

## 📚 扩展开发

### 添加新的大模型
```python
# 在 llm_parser.py 中添加新的提供商
def _parse_newprovider(self, prompt: str):
    # 实现新提供商的调用逻辑
    pass
```

### 自定义行为识别
```python
# 在 behavior_monitor.py 中扩展
def _analyze_pose(self, landmarks):
    # 自定义姿态分析算法
    pass
```

### 集成新的硬件
```python
# 创建新的设备接口模块
# 集成IoT传感器、智能手表等
```

## 📞 联系与反馈

- 提交Issue: https://github.com/ZWHYX555/intelligent-medicine-box/issues
- 讨论功能: https://github.com/ZWHYX555/intelligent-medicine-box/discussions

## 📄 许可证

MIT License

---

**最后更新**: 2026-06-07
