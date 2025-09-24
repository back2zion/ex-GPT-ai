"""
서비스 모듈 테스트 스크립트
각 서비스가 제대로 작동하는지 확인
"""

import asyncio
import sys
import os
from datetime import datetime

# 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("ex-GPT Service Module Test")
print("=" * 50)

# 1. Traffic Analysis 테스트
print("\n[1] Traffic Analysis Service Test")
try:
    # 직접 파일 경로로 임포트
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "traffic_analyzer",
        os.path.join("services", "traffic-analysis", "traffic_analyzer.py")
    )
    traffic_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(traffic_module)
    TrafficAnalyzer = traffic_module.TrafficAnalyzer

    async def test_traffic():
        analyzer = TrafficAnalyzer()

        # 교통 흐름 분석
        traffic_data = await analyzer.analyze_traffic_flow("Seoul IC")
        print(f"[OK] Current traffic: {traffic_data.congestion_level}")
        print(f"  - Average speed: {traffic_data.average_speed:.1f}km/h")
        print(f"  - Vehicle count: {traffic_data.vehicle_count}")

        # 패턴 예측
        from datetime import timedelta
        pattern = await analyzer.predict_traffic_pattern(
            "Seoul IC",
            datetime.now() + timedelta(hours=2)
        )
        print(f"[OK] Prediction (+2h): {pattern.predicted_congestion}")
        print(f"  - Pattern: {pattern.pattern_type}")
        print(f"  - Recommendation: {pattern.recommended_action}")

        return True

    if asyncio.run(test_traffic()):
        print("[SUCCESS] Traffic Analysis Test Passed")

except Exception as e:
    print(f"[ERROR] Traffic Analysis Test Failed: {e}")

# 2. Damage Detection 테스트
print("\n[2] Damage Detection Service Test")
try:
    # 직접 파일 경로로 임포트
    spec = importlib.util.spec_from_file_location(
        "damage_detector",
        os.path.join("services", "damage-detection", "damage_detector.py")
    )
    damage_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(damage_module)
    DamageDetector = damage_module.DamageDetector
    RoadSegment = damage_module.RoadSegment
    DamageType = damage_module.DamageType
    SeverityLevel = damage_module.SeverityLevel
    DamageDetectionResult = damage_module.DamageDetectionResult

    async def test_damage():
        detector = DamageDetector()

        # 도로 구간 정보
        segment = RoadSegment(
            segment_id="TEST_001",
            location="Test Section",
            lane_number=1,
            last_inspection=datetime.now(),
            surface_type="Asphalt"
        )

        # 시뮬레이션 손상 데이터
        mock_detection = DamageDetectionResult(
            damage_type=DamageType.POTHOLE,
            severity=SeverityLevel.MODERATE,
            confidence=0.89,
            location=(100, 100, 50, 50),
            area_percentage=1.5,
            estimated_repair_time=3,
            repair_cost_estimate=750000,
            priority="Normal"
        )

        # 보고서 생성
        report = await detector.generate_inspection_report([mock_detection], segment)
        print(f"[OK] Damages detected: {report['total_damages']}")
        print(f"  - Est. cost: {report['estimated_total_cost']:,} KRW")
        print(f"  - Est. time: {report['estimated_total_time']} hours")

        return True

    if asyncio.run(test_damage()):
        print("[SUCCESS] Damage Detection Test Passed")

except Exception as e:
    print(f"[ERROR] Damage Detection Test Failed: {e}")

# 3. 기존 백엔드 API 테스트
print("\n[3] Backend API Test")
try:
    import requests

    # 헬스체크 (백엔드가 실행 중인 경우)
    try:
        response = requests.get("http://localhost:8201/health", timeout=2)
        if response.status_code == 200:
            print("[OK] Backend API is running")
            print(f"  - Status: {response.json().get('status', 'unknown')}")
    except:
        print("[WARNING] Backend API not running (port 8201)")

except Exception as e:
    print(f"[ERROR] Backend API Test Failed: {e}")

# 4. 설정 파일 테스트
print("\n[4] Configuration Files Test")
try:
    import yaml

    # Development 설정 확인
    with open("config/development.yaml", "r", encoding="utf-8") as f:
        dev_config = yaml.safe_load(f)
        print(f"[OK] Development env: {dev_config['environment']}")
        print(f"  - API port: {dev_config['api']['port']}")
        print(f"  - Debug: {dev_config['debug']}")

    # Production 설정 확인
    with open("config/production.yaml", "r", encoding="utf-8") as f:
        prod_config = yaml.safe_load(f)
        print(f"[OK] Production env: {prod_config['environment']}")
        print(f"  - Workers: {prod_config['api']['workers']}")

    print("[SUCCESS] Configuration Files Test Passed")

except Exception as e:
    print(f"[ERROR] Configuration Files Test Failed: {e}")

print("\n" + "=" * 50)
print("Test Completed!")
print("=" * 50)