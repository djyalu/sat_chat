#!/usr/bin/env python3
"""
대시보드 데이터 업데이트 스크립트
GitHub Actions에서 실행되어 최신 데이터를 API가 사용할 수 있도록 준비
"""

import json
import os
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardUpdater:
    """대시보드 데이터 업데이트"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.dashboard_dir = f"{data_dir}/dashboard"
        os.makedirs(self.dashboard_dir, exist_ok=True)
    
    def load_latest_data(self) -> Dict:
        """최신 데이터 로드"""
        latest_file = f"{self.data_dir}/latest.json"
        if os.path.exists(latest_file):
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def load_processed_data(self) -> Dict:
        """처리된 데이터 로드"""
        processed_file = f"{self.data_dir}/processed_latest.json"
        if os.path.exists(processed_file):
            with open(processed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def generate_dashboard_data(self) -> Dict:
        """대시보드용 데이터 생성"""
        latest = self.load_latest_data()
        processed = self.load_processed_data()
        
        dashboard_data = {
            'last_update': datetime.now().isoformat(),
            'data_source': 'Sentinel Hub',
            
            # Real-time stats
            'realtime': {
                'total_detections': len(latest.get('detections', [])),
                'active_alerts': len(latest.get('alerts', [])),
                'monitored_area': 25000,  # km²
                'detection_rate': latest.get('statistics', {}).get('average_confidence', 0) * 100
            },
            
            # Regional data
            'regions': processed.get('summary', {}).get('by_region', {}),
            
            # Hotspots
            'hotspots': processed.get('summary', {}).get('hotspots', [])[:10],  # Top 10
            
            # Recent detections for map
            'map_data': self._prepare_map_data(latest.get('detections', [])),
            
            # Charts data
            'charts': {
                'trends': processed.get('summary', {}).get('trends', {}),
                'by_type': latest.get('statistics', {}).get('by_type', {}),
                'by_priority': latest.get('statistics', {}).get('by_priority', {})
            },
            
            # Alerts
            'alerts': self._format_alerts(latest.get('alerts', [])),
            
            # Performance metrics
            'performance': latest.get('performance', {})
        }
        
        return dashboard_data
    
    def _prepare_map_data(self, detections: List[Dict]) -> List[Dict]:
        """지도 표시용 데이터 준비"""
        map_data = []
        
        for detection in detections[:100]:  # Limit to 100 for performance
            map_data.append({
                'id': detection.get('id'),
                'lat': detection.get('latitude'),
                'lng': detection.get('longitude'),
                'type': detection.get('debris_type'),
                'confidence': detection.get('confidence'),
                'size': detection.get('patch_size'),
                'priority': detection.get('priority'),
                'popup': self._generate_popup(detection)
            })
        
        return map_data
    
    def _generate_popup(self, detection: Dict) -> str:
        """마커 팝업 내용 생성"""
        return (
            f"<strong>{detection.get('debris_type', 'Unknown')}</strong><br>"
            f"신뢰도: {detection.get('confidence', 0):.1%}<br>"
            f"크기: {detection.get('patch_size', 0):.1f}m²<br>"
            f"우선순위: {detection.get('priority', 'low')}<br>"
            f"시간: {detection.get('detection_time', 'Unknown')}"
        )
    
    def _format_alerts(self, alerts: List[Dict]) -> List[Dict]:
        """알림 포맷팅"""
        formatted = []
        
        for alert in alerts[:20]:  # Latest 20 alerts
            formatted.append({
                'id': alert.get('id'),
                'priority': alert.get('priority'),
                'title': alert.get('title'),
                'message': alert.get('message'),
                'timestamp': alert.get('created_at'),
                'action': alert.get('action_required'),
                'detection_id': alert.get('detection_id')
            })
        
        return formatted
    
    def save_dashboard_data(self, dashboard_data: Dict):
        """대시보드 데이터 저장"""
        # Save main dashboard data
        dashboard_file = f"{self.dashboard_dir}/dashboard.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Dashboard data saved to {dashboard_file}")
        
        # Save individual components for API endpoints
        components = ['realtime', 'regions', 'hotspots', 'map_data', 'charts', 'alerts']
        for component in components:
            if component in dashboard_data:
                component_file = f"{self.dashboard_dir}/{component}.json"
                with open(component_file, 'w', encoding='utf-8') as f:
                    json.dump(dashboard_data[component], f, ensure_ascii=False, indent=2)
    
    def generate_summary_report(self, dashboard_data: Dict) -> str:
        """요약 리포트 생성"""
        report = []
        report.append("# 📊 Marine Debris Detection Dashboard Update\n")
        report.append(f"**Last Update**: {dashboard_data['last_update']}\n")
        report.append(f"**Data Source**: {dashboard_data['data_source']}\n\n")
        
        # Real-time stats
        rt = dashboard_data['realtime']
        report.append("## 🎯 Real-time Statistics\n")
        report.append(f"- Total Detections: **{rt['total_detections']}**\n")
        report.append(f"- Active Alerts: **{rt['active_alerts']}**\n")
        report.append(f"- Monitored Area: **{rt['monitored_area']:,} km²**\n")
        report.append(f"- Detection Rate: **{rt['detection_rate']:.1f}%**\n\n")
        
        # Regional summary
        report.append("## 🗺️ Regional Summary\n")
        for region, stats in dashboard_data['regions'].items():
            report.append(f"### {region}\n")
            report.append(f"- Detections: {stats['count']}\n")
            report.append(f"- Total Area: {stats['total_area']:.1f} m²\n")
            report.append(f"- High Priority: {stats['high_priority']}\n")
        
        # Hotspots
        if dashboard_data['hotspots']:
            report.append("\n## 🔥 Top Hotspots\n")
            for i, hotspot in enumerate(dashboard_data['hotspots'][:5], 1):
                report.append(f"{i}. **{hotspot['center']['lat']:.2f}°N, {hotspot['center']['lon']:.2f}°E**\n")
                report.append(f"   - Detections: {hotspot['detection_count']}\n")
                report.append(f"   - Total Area: {hotspot['total_area']:.1f} m²\n")
        
        # Alerts
        if dashboard_data['alerts']:
            report.append("\n## 🚨 Recent Alerts\n")
            for alert in dashboard_data['alerts'][:5]:
                report.append(f"- **{alert['priority'].upper()}**: {alert['title']}\n")
        
        return ''.join(report)

def main():
    """메인 실행 함수"""
    updater = DashboardUpdater()
    
    logger.info("📊 Updating dashboard data...")
    
    # Generate dashboard data
    dashboard_data = updater.generate_dashboard_data()
    
    # Save dashboard data
    updater.save_dashboard_data(dashboard_data)
    
    # Generate and save summary report
    report = updater.generate_summary_report(dashboard_data)
    report_file = f"{updater.data_dir}/dashboard_summary.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    
    logger.info("✅ Dashboard update completed")

if __name__ == "__main__":
    main()