#!/usr/bin/env python3
"""
Sentinel Hub 데이터 수집 스크립트
GitHub Actions에서 정기적으로 실행
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.satchat.sentinel_hub_advanced import SentinelHubAdvanced
from src.satchat.debris_detection_pipeline import MarineDebrisDetectionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SentinelDataFetcher:
    """Sentinel Hub 데이터 수집 및 처리"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sentinel_client = None
        self.pipeline = None
        self.data_dir = "data"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """데이터 저장 디렉토리 생성"""
        directories = [
            f"{self.data_dir}/detections",
            f"{self.data_dir}/statistics",
            f"{self.data_dir}/alerts",
            f"{self.data_dir}/images",
            f"{self.data_dir}/raw"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    async def initialize(self):
        """클라이언트 초기화"""
        try:
            self.sentinel_client = SentinelHubAdvanced(
                self.client_id, 
                self.client_secret
            )
            self.pipeline = MarineDebrisDetectionPipeline(self.sentinel_client)
            logger.info("✅ Sentinel Hub client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Sentinel Hub client: {e}")
            return False
    
    async def fetch_data(self, region: str = 'all', priority_only: bool = False) -> Dict:
        """
        Sentinel Hub에서 데이터 수집
        
        Args:
            region: 모니터링 지역 (all, west_sea, south_sea, east_sea)
            priority_only: 우선 지역만 처리 여부
        """
        logger.info(f"🛰️ Starting data fetch for region: {region}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'region': region,
            'priority_only': priority_only,
            'detections': [],
            'statistics': {},
            'alerts': [],
            'errors': []
        }
        
        try:
            # Run detection cycle
            detections = await self.pipeline.run_detection_cycle(region)
            
            # Filter by priority if requested
            if priority_only:
                detections = [d for d in detections if d.priority in ['critical', 'high']]
            
            # Convert to dict format
            results['detections'] = [d.to_dict() for d in detections]
            
            # Get statistics
            results['statistics'] = self.sentinel_client.get_detection_statistics(
                results['detections']
            )
            
            # Get alerts
            results['alerts'] = self.pipeline.alert_queue.copy()
            
            # Performance metrics
            results['performance'] = self.pipeline.get_performance_metrics()
            
            logger.info(f"✅ Found {len(detections)} detections")
            
        except Exception as e:
            logger.error(f"❌ Error during data fetch: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def save_results(self, results: Dict) -> str:
        """결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detections
        detections_file = f"{self.data_dir}/detections/detections_{timestamp}.json"
        with open(detections_file, 'w', encoding='utf-8') as f:
            json.dump(results['detections'], f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved {len(results['detections'])} detections to {detections_file}")
        
        # Save statistics
        stats_file = f"{self.data_dir}/statistics/stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(results['statistics'], f, ensure_ascii=False, indent=2)
        
        # Save alerts
        if results['alerts']:
            alerts_file = f"{self.data_dir}/alerts/alerts_{timestamp}.json"
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(results['alerts'], f, ensure_ascii=False, indent=2)
            logger.info(f"🔔 Saved {len(results['alerts'])} alerts")
        
        # Save latest results for API
        latest_file = f"{self.data_dir}/latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return timestamp
    
    def generate_summary(self, results: Dict) -> str:
        """결과 요약 생성"""
        summary = []
        summary.append("# 🛰️ Sentinel Hub Detection Summary\n")
        summary.append(f"**Timestamp**: {results['timestamp']}\n")
        summary.append(f"**Region**: {results['region']}\n")
        
        # Detection summary
        summary.append("\n## 📊 Detection Results\n")
        summary.append(f"- Total Detections: {len(results['detections'])}\n")
        
        if results['statistics']:
            stats = results['statistics']
            summary.append(f"- By Priority:\n")
            for priority, count in stats.get('by_priority', {}).items():
                summary.append(f"  - {priority}: {count}\n")
            
            summary.append(f"- By Type:\n")
            for debris_type, count in stats.get('by_type', {}).items():
                summary.append(f"  - {debris_type}: {count}\n")
            
            summary.append(f"- Total Area: {stats.get('total_area', 0):.1f} m²\n")
            summary.append(f"- Average Confidence: {stats.get('average_confidence', 0):.1%}\n")
        
        # Alerts summary
        if results['alerts']:
            summary.append(f"\n## 🚨 Alerts ({len(results['alerts'])})\n")
            for alert in results['alerts'][:5]:  # Top 5 alerts
                summary.append(f"- **{alert.get('priority', 'unknown').upper()}**: {alert.get('title', 'No title')}\n")
        
        # Performance metrics
        if results.get('performance'):
            perf = results['performance']
            summary.append(f"\n## ⚡ Performance\n")
            summary.append(f"- Processing Time: {perf.get('average_processing_time', 0):.2f}s\n")
            summary.append(f"- Detection Rate: {perf.get('detection_rate', 0):.1%}\n")
        
        return ''.join(summary)

async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Fetch Sentinel Hub marine debris data')
    parser.add_argument('--region', default='all', 
                       choices=['all', 'west_sea', 'south_sea', 'east_sea'],
                       help='Region to monitor')
    parser.add_argument('--priority-only', action='store_true',
                       help='Process priority zones only')
    args = parser.parse_args()
    
    # Get credentials from environment
    client_id = os.getenv('SENTINEL_CLIENT_ID')
    client_secret = os.getenv('SENTINEL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.warning("⚠️ Sentinel Hub credentials not found, using mock data mode")
        # Use mock credentials for testing
        client_id = "mock_client_id"
        client_secret = "mock_client_secret"
    
    # Initialize fetcher
    fetcher = SentinelDataFetcher(client_id, client_secret)
    
    if not await fetcher.initialize():
        logger.error("Failed to initialize, exiting")
        sys.exit(1)
    
    # Fetch data
    results = await fetcher.fetch_data(
        region=args.region,
        priority_only=args.priority_only
    )
    
    # Save results
    timestamp = fetcher.save_results(results)
    
    # Generate and print summary
    summary = fetcher.generate_summary(results)
    print(summary)
    
    # Write summary to file
    summary_file = f"{fetcher.data_dir}/summary_{timestamp}.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    logger.info(f"✅ Data fetch completed successfully at {timestamp}")
    
    # Exit with appropriate code
    if results['errors']:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())