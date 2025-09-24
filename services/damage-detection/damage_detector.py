"""
도로 손상 AI 감지 서비스
한국도로공사 도로 상태 자동 진단 시스템
"""

import numpy as np
from PIL import Image
import cv2
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DamageType(Enum):
    """도로 손상 유형"""
    POTHOLE = "포트홀"
    CRACK = "균열"
    SUBSIDENCE = "침하"
    DAMAGE = "파손"
    PEELING = "박리"
    WEAR = "마모"
    NORMAL = "정상"


class SeverityLevel(Enum):
    """손상 심각도"""
    MINOR = "경미"
    MODERATE = "보통"
    SEVERE = "심각"
    CRITICAL = "긴급"


@dataclass
class DamageDetectionResult:
    """손상 감지 결과"""
    damage_type: DamageType
    severity: SeverityLevel
    confidence: float
    location: Tuple[int, int, int, int]  # x, y, width, height
    area_percentage: float
    estimated_repair_time: int  # 예상 수리 시간 (시간)
    repair_cost_estimate: int  # 예상 수리 비용 (원)
    priority: str


@dataclass
class RoadSegment:
    """도로 구간 정보"""
    segment_id: str
    location: str
    lane_number: int
    last_inspection: datetime
    surface_type: str  # 아스팔트, 콘크리트


class DamageDetector:
    """도로 손상 감지 시스템"""

    def __init__(self):
        self.damage_thresholds = {
            DamageType.POTHOLE: 0.8,
            DamageType.CRACK: 0.7,
            DamageType.SUBSIDENCE: 0.75,
            DamageType.DAMAGE: 0.7,
            DamageType.PEELING: 0.65,
            DamageType.WEAR: 0.6
        }

        self.severity_criteria = {
            "area": {  # 손상 면적 기준 (m²)
                SeverityLevel.MINOR: (0, 0.1),
                SeverityLevel.MODERATE: (0.1, 0.5),
                SeverityLevel.SEVERE: (0.5, 1.0),
                SeverityLevel.CRITICAL: (1.0, float('inf'))
            },
            "depth": {  # 손상 깊이 기준 (cm)
                SeverityLevel.MINOR: (0, 2),
                SeverityLevel.MODERATE: (2, 5),
                SeverityLevel.SEVERE: (5, 10),
                SeverityLevel.CRITICAL: (10, float('inf'))
            }
        }

    async def detect_damage(
        self,
        image_path: str,
        road_segment: RoadSegment
    ) -> List[DamageDetectionResult]:
        """
        도로 이미지에서 손상 감지

        Args:
            image_path: 분석할 이미지 경로
            road_segment: 도로 구간 정보
        """
        # 이미지 로드 및 전처리
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"이미지 로드 실패: {image_path}")
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        # 손상 감지 (시뮬레이션)
        detections = self._simulate_damage_detection(gray, road_segment)

        results = []
        for detection in detections:
            # 손상 영역 계산
            x, y, w, h = detection['bbox']
            area_percentage = (w * h) / (width * height) * 100

            # 심각도 판정
            severity = self._determine_severity(
                detection['damage_type'],
                area_percentage,
                detection.get('depth', 0)
            )

            # 수리 시간 및 비용 예측
            repair_time = self._estimate_repair_time(
                detection['damage_type'],
                severity,
                area_percentage
            )
            repair_cost = self._estimate_repair_cost(
                detection['damage_type'],
                severity,
                area_percentage
            )

            # 우선순위 결정
            priority = self._determine_priority(
                severity,
                road_segment.lane_number,
                detection['damage_type']
            )

            results.append(DamageDetectionResult(
                damage_type=detection['damage_type'],
                severity=severity,
                confidence=detection['confidence'],
                location=(x, y, w, h),
                area_percentage=area_percentage,
                estimated_repair_time=repair_time,
                repair_cost_estimate=repair_cost,
                priority=priority
            ))

        return results

    def _simulate_damage_detection(
        self,
        image: np.ndarray,
        road_segment: RoadSegment
    ) -> List[Dict]:
        """손상 감지 시뮬레이션"""
        detections = []

        # 엣지 검출로 균열 찾기
        edges = cv2.Canny(image, 50, 150)

        # 컨투어 검출
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours[:5]:  # 최대 5개 손상
            x, y, w, h = cv2.boundingRect(contour)

            # 최소 크기 필터링
            if w < 20 or h < 20:
                continue

            # 랜덤 손상 타입 할당 (실제로는 AI 모델 사용)
            damage_types = list(DamageType)
            damage_types.remove(DamageType.NORMAL)
            damage_type = np.random.choice(damage_types)

            confidence = np.random.uniform(0.7, 0.95)

            detections.append({
                'damage_type': damage_type,
                'bbox': (x, y, w, h),
                'confidence': confidence,
                'depth': np.random.uniform(1, 15)  # cm
            })

        return detections

    def _determine_severity(
        self,
        damage_type: DamageType,
        area_percentage: float,
        depth: float
    ) -> SeverityLevel:
        """손상 심각도 판정"""
        # 포트홀과 침하는 깊이 기준 우선
        if damage_type in [DamageType.POTHOLE, DamageType.SUBSIDENCE]:
            for level, (min_d, max_d) in self.severity_criteria["depth"].items():
                if min_d <= depth < max_d:
                    return level

        # 나머지는 면적 기준
        area_m2 = area_percentage * 0.01  # 퍼센트를 m² 근사치로 변환
        for level, (min_a, max_a) in self.severity_criteria["area"].items():
            if min_a <= area_m2 < max_a:
                return level

        return SeverityLevel.MODERATE

    def _estimate_repair_time(
        self,
        damage_type: DamageType,
        severity: SeverityLevel,
        area_percentage: float
    ) -> int:
        """예상 수리 시간 계산 (시간)"""
        base_time = {
            DamageType.POTHOLE: 2,
            DamageType.CRACK: 1,
            DamageType.SUBSIDENCE: 8,
            DamageType.DAMAGE: 4,
            DamageType.PEELING: 3,
            DamageType.WEAR: 6
        }

        severity_multiplier = {
            SeverityLevel.MINOR: 1.0,
            SeverityLevel.MODERATE: 1.5,
            SeverityLevel.SEVERE: 2.0,
            SeverityLevel.CRITICAL: 3.0
        }

        time = base_time.get(damage_type, 2)
        time *= severity_multiplier.get(severity, 1.0)
        time *= (1 + area_percentage / 100)  # 면적에 따른 조정

        return int(time)

    def _estimate_repair_cost(
        self,
        damage_type: DamageType,
        severity: SeverityLevel,
        area_percentage: float
    ) -> int:
        """예상 수리 비용 계산 (원)"""
        base_cost = {
            DamageType.POTHOLE: 500000,
            DamageType.CRACK: 300000,
            DamageType.SUBSIDENCE: 2000000,
            DamageType.DAMAGE: 800000,
            DamageType.PEELING: 600000,
            DamageType.WEAR: 1000000
        }

        severity_multiplier = {
            SeverityLevel.MINOR: 0.5,
            SeverityLevel.MODERATE: 1.0,
            SeverityLevel.SEVERE: 2.0,
            SeverityLevel.CRITICAL: 3.0
        }

        cost = base_cost.get(damage_type, 500000)
        cost *= severity_multiplier.get(severity, 1.0)
        cost *= (1 + area_percentage / 50)  # 면적에 따른 조정

        return int(cost)

    def _determine_priority(
        self,
        severity: SeverityLevel,
        lane_number: int,
        damage_type: DamageType
    ) -> str:
        """수리 우선순위 결정"""
        if severity == SeverityLevel.CRITICAL:
            return "긴급"
        elif severity == SeverityLevel.SEVERE or lane_number == 1:
            return "높음"
        elif damage_type == DamageType.POTHOLE:
            return "높음"
        elif severity == SeverityLevel.MODERATE:
            return "보통"
        else:
            return "낮음"

    async def generate_inspection_report(
        self,
        detections: List[DamageDetectionResult],
        road_segment: RoadSegment
    ) -> Dict:
        """
        도로 검사 보고서 생성

        Args:
            detections: 감지된 손상 리스트
            road_segment: 도로 구간 정보
        """
        report = {
            "inspection_date": datetime.now().isoformat(),
            "segment_id": road_segment.segment_id,
            "location": road_segment.location,
            "total_damages": len(detections),
            "summary": {},
            "damages": [],
            "recommendations": [],
            "estimated_total_cost": 0,
            "estimated_total_time": 0
        }

        # 손상 유형별 집계
        damage_counts = {}
        severity_counts = {}
        total_cost = 0
        total_time = 0

        for detection in detections:
            # 집계
            damage_type = detection.damage_type.value
            severity = detection.severity.value

            damage_counts[damage_type] = damage_counts.get(damage_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            total_cost += detection.repair_cost_estimate
            total_time += detection.estimated_repair_time

            # 상세 정보
            report["damages"].append({
                "type": damage_type,
                "severity": severity,
                "confidence": round(detection.confidence, 2),
                "area_percentage": round(detection.area_percentage, 2),
                "repair_time": detection.estimated_repair_time,
                "repair_cost": detection.repair_cost_estimate,
                "priority": detection.priority
            })

        report["summary"] = {
            "damage_types": damage_counts,
            "severity_distribution": severity_counts
        }
        report["estimated_total_cost"] = total_cost
        report["estimated_total_time"] = total_time

        # 권장 사항
        if SeverityLevel.CRITICAL.value in severity_counts:
            report["recommendations"].append("긴급 수리 필요 - 즉시 차선 통제 권장")
        if len(detections) > 5:
            report["recommendations"].append("전면 재포장 검토 필요")
        if DamageType.SUBSIDENCE.value in damage_counts:
            report["recommendations"].append("지반 조사 필요")

        return report


# 사용 예시
async def main():
    detector = DamageDetector()

    # 도로 구간 정보
    segment = RoadSegment(
        segment_id="SEG_001",
        location="경부고속도로 서울-수원 구간",
        lane_number=1,
        last_inspection=datetime(2024, 1, 1),
        surface_type="아스팔트"
    )

    # 손상 감지 (테스트용 이미지 필요)
    # detections = await detector.detect_damage("road_image.jpg", segment)

    # 시뮬레이션 결과 생성
    mock_detections = [
        DamageDetectionResult(
            damage_type=DamageType.POTHOLE,
            severity=SeverityLevel.SEVERE,
            confidence=0.92,
            location=(100, 200, 50, 50),
            area_percentage=2.5,
            estimated_repair_time=4,
            repair_cost_estimate=1000000,
            priority="높음"
        )
    ]

    # 보고서 생성
    report = await detector.generate_inspection_report(mock_detections, segment)
    print(f"검사 보고서: {report['summary']}")
    print(f"총 수리 비용: {report['estimated_total_cost']:,}원")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())