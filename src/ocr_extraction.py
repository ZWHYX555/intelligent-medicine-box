"""
OCR文字识别与提取模块
支持 PaddleOCR 和 Tesseract
"""
import cv2
import logging
import numpy as np
from pathlib import Path


class OCRExtractor:
    """OCR文字识别类"""
    
    def __init__(self, use_paddleocr=True, languages=["ch", "en"]):
        """
        初始化OCR提取器
        
        Args:
            use_paddleocr: 是否使用PaddleOCR
            languages: 识别语言列表
        """
        self.logger = logging.getLogger(__name__)
        self.use_paddleocr = use_paddleocr
        self.ocr = None
        self.languages = languages
        
        if use_paddleocr:
            self._init_paddleocr()
        else:
            self._init_tesseract()
    
    def _init_paddleocr(self):
        """初始化PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            self.logger.info("PaddleOCR初始化成功")
        except ImportError:
            self.logger.error("PaddleOCR未安装，请执行: pip install paddleocr")
            raise
        except Exception as e:
            self.logger.error(f"PaddleOCR初始化失败: {e}")
            raise
    
    def _init_tesseract(self):
        """初始化Tesseract"""
        try:
            import pytesseract
            self.ocr = pytesseract
            self.logger.info("Tesseract初始化成功")
        except ImportError:
            self.logger.error("pytesseract未安装，请执行: pip install pytesseract")
            raise
        except Exception as e:
            self.logger.error(f"Tesseract初始化失败: {e}")
            raise
    
    def extract_text_from_image(self, image_path):
        """
        从图像中提取文本
        
        Args:
            image_path: 图像路径
            
        Returns:
            dict: 包含文本和检测框的字典
        """
        try:
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
            else:
                image = image_path
            
            if image is None:
                self.logger.error(f"无法加载图像: {image_path}")
                return None
            
            if self.use_paddleocr:
                return self._extract_paddleocr(image)
            else:
                return self._extract_tesseract(image)
        except Exception as e:
            self.logger.error(f"文字识别失败: {e}")
            return None
    
    def _extract_paddleocr(self, image):
        """使用PaddleOCR提取文本"""
        results = self.ocr.ocr(image, cls=True)
        
        texts = []
        boxes = []
        confidences = []
        
        for line in results:
            for word_info in line:
                box = word_info[0]
                text = word_info[1]
                confidence = word_info[2]
                
                boxes.append(box)
                texts.append(text)
                confidences.append(confidence)
        
        return {
            "texts": texts,
            "boxes": boxes,
            "confidences": confidences,
            "full_text": "\n".join(texts)
        }
    
    def _extract_tesseract(self, image):
        """使用Tesseract提取文本"""
        try:
            # 图像预处理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # 提取文本
            text = self.ocr.image_to_string(binary, lang='chi_sim+eng')
            
            return {
                "texts": text.split('\n'),
                "boxes": [],
                "confidences": [],
                "full_text": text
            }
        except Exception as e:
            self.logger.error(f"Tesseract提取失败: {e}")
            return None
    
    def preprocess_image(self, image):
        """
        预处理图像以提高OCR准确度
        
        Args:
            image: 输入图像
            
        Returns:
            np.ndarray: 处理后的图像
        """
        # 转灰度
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 二值化
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # 去噪
        denoised = cv2.medianBlur(binary, 5)
        
        # 膨胀腐蚀
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        processed = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def extract_text_from_file(self, file_path):
        """
        从文件路径提取文本
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            str: 提取的文本
        """
        result = self.extract_text_from_image(file_path)
        if result:
            return result["full_text"]
        return None
    
    def draw_boxes_on_image(self, image_path, output_path):
        """
        在图像上绘制��测框
        
        Args:
            image_path: 输入图像路径
            output_path: 输出图像路径
        """
        image = cv2.imread(image_path)
        result = self.extract_text_from_image(image)
        
        if result and result["boxes"]:
            for box in result["boxes"]:
                box = np.array(box, dtype=np.int32)
                cv2.polylines(image, [box], True, (0, 255, 0), 2)
        
        cv2.imwrite(output_path, image)
        self.logger.info(f"带检测框的图像已保存: {output_path}")
