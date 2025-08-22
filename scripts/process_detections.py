#!/usr/bin/env python3
"""
탐지 데이터 처리 및 분석 스크립트
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectionProcessor:
    """탐지 데이터 처리 클래스"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.detections_dir = f"{data_dir}/detections"
        
    def get_latest_detections(self, hours: int = 24) -> List[Dict]:
        """최근 N시간 내의 탐지 데이터 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        all_detections = []
        
        for filename in os.listdir(self.detections_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.detections_dir, filename)
                
                # 파일 시간 체크
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time > cutoff_time:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        detections = json.load(f)
                        all_detections.extend(detections)
        
        return all_detections
    
    def aggregate_by_region(self, detections: List[Dict]) -> Dict:
        """지역별 집계"""
        aggregated = {
            '서해': {'count': 0, 'total_area': 0, 'high_priority': 0},
            '남해': {'count': 0, 'total_area': 0, 'high_priority': 0},
            '동해': {'count': 0, 'total_area': 0, 'high_priority': 0}
        }
        
        for detection in detections:
            region = detection.get('region', '')
            if region in aggregated:
                aggregated[region]['count'] += 1
                aggregated[region]['total_area'] += detection.get('patch_size', 0)
                if detection.get('priority') in ['critical', 'high']:
                    aggregated[region]['high_priority'] += 1
        
        return aggregated
    
    def identify_hotspots(self, detections: List[Dict], threshold: int = 5) -> List[Dict]:
        """핫스팟 지역 식별"""
        from collections import defaultdict
        
        # Grid-based clustering (0.1 degree cells)
        grid_size = 0.1
        hotspots = defaultdict(list)
        
        for detection in detections:
            lat = detection.get('latitude', 0)
            lon = detection.get('longitude', 0)
            
            # Grid cell
            grid_lat = round(lat / grid_size) * grid_size
            grid_lon = round(lon / grid_size) * grid_size
            grid_key = f"{grid_lat:.1f},{grid_lon:.1f}"
            
            hotspots[grid_key].append(detection)
        
        # Filter hotspots
        significant_hotspots = []
        for grid_key, detections_list in hotspots.items():
            if len(detections_list) >= threshold:
                lat, lon = map(float, grid_key.split(','))
                total_area = sum(d.get('patch_size', 0) for d in detections_list)
                avg_confidence = sum(d.get('confidence', 0) for d in detections_list) / len(detections_list)
                
                significant_hotspots.append({
                    'center': {'lat': lat, 'lon': lon},
                    'detection_count': len(detections_list),
                    'total_area': total_area,
                    'average_confidence': avg_confidence,
                    'detections': detections_list
                })
        
        return sorted(significant_hotspots, key=lambda x: x['detection_count'], reverse=True)
    
    def calculate_trends(self, days: int = 7) -> Dict:
        """트렌드 분석"""
        daily_counts = defaultdict(int)
        daily_areas = defaultdict(float)
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(self.detections_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.detections_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time > cutoff_time:
                    date_key = file_time.strftime('%Y-%m-%d')
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        detections = json.load(f)
                        daily_counts[date_key] += len(detections)
                        daily_areas[date_key] += sum(d.get('patch_size', 0) for d in detections)
        
        # Calculate trend direction
        dates = sorted(daily_counts.keys())
        if len(dates) >= 2:
            first_half = dates[:len(dates)//2]
            second_half = dates[len(dates)//2:]
            
            first_avg = sum(daily_counts[d] for d in first_half) / max(1, len(first_half))
            second_avg = sum(daily_counts[d] for d in second_half) / max(1, len(second_half))
            
            trend = "increasing" if second_avg > first_avg * 1.1 else \
                   "decreasing" if second_avg < first_avg * 0.9 else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            'daily_counts': dict(daily_counts),
            'daily_areas': dict(daily_areas),
            'trend': trend,
            'period_days': days
        }
    
    def generate_processed_data(self) -> Dict:
        """처리된 데이터 생성"""
        # Get recent detections
        recent_detections = self.get_latest_detections(hours=24)
        
        # Process data
        processed = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_24h': len(recent_detections),
                'by_region': self.aggregate_by_region(recent_detections),
                'hotspots': self.identify_hotspots(recent_detections),
                'trends': self.calculate_trends()
            },
            'recent_detections': recent_detections[:50]  # Latest 50
        }
        
        return processed
    
    def save_processed_data(self, processed_data: Dict):
        """처리된 데이터 저장"""
        output_file = f"{self.data_dir}/processed_latest.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Processed data saved to {output_file}")

def main():
    """메인 실행 함수"""
    processor = DetectionProcessor()
    
    logger.info("🔄 Processing detection data...")
    processed_data = processor.generate_processed_data()
    
    # Save processed data
    processor.save_processed_data(processed_data)
    
    # Print summary
    print(f"📊 Processed {processed_data['summary']['total_24h']} detections from last 24 hours")
    print(f"📍 Identified {len(processed_data['summary']['hotspots'])} hotspot areas")
    print(f"📈 Trend: {processed_data['summary']['trends']['trend']}")
    
    # Print regional summary
    print("\n🗺️ Regional Summary:")
    for region, stats in processed_data['summary']['by_region'].items():
        print(f"  {region}: {stats['count']} detections, "
              f"{stats['total_area']:.1f}m² total area, "
              f"{stats['high_priority']} high priority")

if __name__ == "__main__":
    main()