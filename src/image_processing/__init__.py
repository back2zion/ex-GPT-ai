"""
ex-GPT Image Processing Module
이미지 처리 및 분석 모듈
"""

from .vlm_processor import (
    MultimodalVLMProcessor,
    KoreaExpresswayImageAnalyzer,
    ImageType,
    ImageAnalysisResult
)

try:
    from .ocr_engine import (
        KoreanOCREngine,
        DocumentProcessor,
        OCRResult
    )
except ImportError:
    print("Warning: OCR dependencies not installed")
    KoreanOCREngine = None
    DocumentProcessor = None
    OCRResult = None

try:
    from .image_analyzer import (
        IntegratedImageAnalyzer,
        ProcessingMode,
        ComprehensiveImageAnalysis
    )
except ImportError:
    print("Warning: Image analyzer dependencies not installed")
    IntegratedImageAnalyzer = None
    ProcessingMode = None
    ComprehensiveImageAnalysis = None

__all__ = [
    'MultimodalVLMProcessor',
    'KoreaExpresswayImageAnalyzer',
    'ImageType',
    'ImageAnalysisResult',
    'KoreanOCREngine',
    'DocumentProcessor',
    'OCRResult',
    'IntegratedImageAnalyzer',
    'ProcessingMode',
    'ComprehensiveImageAnalysis'
]

__version__ = '1.0.0'
