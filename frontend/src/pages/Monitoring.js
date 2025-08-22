import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Rectangle, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import DetectionPanel from '../components/DetectionPanel';
import FilterPanel from '../components/FilterPanel';

// Leaflet 마커 아이콘 설정
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const Monitoring = () => {
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: 'week',
    wasteType: 'all',
    confidence: 0.5
  });

  // 한국 해역 경계
  const koreaSeaBounds = {
    west: [[33.0, 124.0], [39.0, 127.0]], // 서해
    south: [[32.0, 126.0], [35.0, 130.0]], // 남해
    east: [[35.0, 128.0], [38.5, 132.0]], // 동해
  };

  // 모의 탐지 데이터
  const mockDetections = [
    { id: 1, lat: 34.5, lng: 126.8, type: '플라스틱', confidence: 0.92, time: '2시간 전', size: 'large' },
    { id: 2, lat: 35.2, lng: 129.1, type: '어망', confidence: 0.85, time: '5시간 전', size: 'medium' },
    { id: 3, lat: 37.5, lng: 130.5, type: '부표', confidence: 0.78, time: '8시간 전', size: 'small' },
    { id: 4, lat: 33.8, lng: 125.5, type: '플라스틱', confidence: 0.95, time: '12시간 전', size: 'large' },
    { id: 5, lat: 36.0, lng: 128.0, type: '기타', confidence: 0.65, time: '1일 전', size: 'small' },
  ];

  useEffect(() => {
    fetchDetections();
  }, [filters, selectedRegion]);

  const fetchDetections = async () => {
    setLoading(true);
    // API 호출 시뮬레이션
    setTimeout(() => {
      setDetections(mockDetections);
      setLoading(false);
    }, 1000);
  };

  const getMarkerColor = (type) => {
    const colors = {
      '플라스틱': '#ef4444',
      '어망': '#f59e0b',
      '부표': '#10b981',
      '기타': '#8b5cf6'
    };
    return colors[type] || '#6b7280';
  };

  const getMarkerSize = (size) => {
    const sizes = {
      'small': 5,
      'medium': 8,
      'large': 12
    };
    return sizes[size] || 8;
  };

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">실시간 모니터링</h1>
          <p className="text-gray-500 mt-1">위성 데이터 기반 해양 폐기물 실시간 탐지</p>
        </div>
        <div className="flex space-x-3">
          <button className="btn-secondary flex items-center space-x-2">
            <span>🔄</span>
            <span>새로고침</span>
          </button>
          <button className="btn-primary flex items-center space-x-2">
            <span>📸</span>
            <span>스냅샷 저장</span>
          </button>
        </div>
      </div>

      {/* 지역 선택 탭 */}
      <div className="bg-white rounded-lg shadow-sm border p-1 inline-flex">
        {['all', 'west', 'south', 'east'].map((region) => (
          <button
            key={region}
            onClick={() => setSelectedRegion(region)}
            className={`px-4 py-2 rounded-md transition-colors duration-200 ${
              selectedRegion === region
                ? 'bg-primary-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {region === 'all' && '전체'}
            {region === 'west' && '서해'}
            {region === 'south' && '남해'}
            {region === 'east' && '동해'}
          </button>
        ))}
      </div>

      {/* 메인 컨텐츠 */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 필터 패널 */}
        <div className="lg:col-span-1">
          <FilterPanel filters={filters} setFilters={setFilters} />
        </div>

        {/* 지도 영역 */}
        <div className="lg:col-span-2">
          <div className="card p-0 h-[600px] relative">
            {loading && (
              <div className="absolute inset-0 bg-white bg-opacity-75 z-10 flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">데이터 로딩중...</p>
                </div>
              </div>
            )}
            <MapContainer
              center={[36.0, 128.0]}
              zoom={6}
              className="h-full w-full rounded-xl"
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              />
              
              {/* 해역 경계 표시 */}
              {selectedRegion !== 'all' && koreaSeaBounds[selectedRegion] && (
                <Rectangle
                  bounds={koreaSeaBounds[selectedRegion]}
                  pathOptions={{ 
                    color: '#3b82f6', 
                    weight: 2, 
                    fillOpacity: 0.1 
                  }}
                />
              )}
              
              {/* 탐지 마커 */}
              {detections.map((detection) => (
                <CircleMarker
                  key={detection.id}
                  center={[detection.lat, detection.lng]}
                  radius={getMarkerSize(detection.size)}
                  pathOptions={{
                    fillColor: getMarkerColor(detection.type),
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                  }}
                >
                  <Popup>
                    <div className="p-2">
                      <h4 className="font-semibold">{detection.type}</h4>
                      <p className="text-sm text-gray-600">신뢰도: {(detection.confidence * 100).toFixed(1)}%</p>
                      <p className="text-sm text-gray-600">탐지 시간: {detection.time}</p>
                      <p className="text-sm text-gray-600">크기: {detection.size}</p>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>

          {/* 범례 */}
          <div className="mt-4 card">
            <h4 className="font-semibold mb-2">범례</h4>
            <div className="flex flex-wrap gap-4">
              {['플라스틱', '어망', '부표', '기타'].map((type) => (
                <div key={type} className="flex items-center space-x-2">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: getMarkerColor(type) }}
                  ></div>
                  <span className="text-sm text-gray-600">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 탐지 상세 패널 */}
        <div className="lg:col-span-1">
          <DetectionPanel detections={detections} />
        </div>
      </div>

      {/* 실시간 상태 바 */}
      <div className="card bg-gradient-to-r from-green-50 to-blue-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">실시간 모니터링 중</span>
            </div>
            <span className="text-sm text-gray-600">마지막 업데이트: 2분 전</span>
          </div>
          <div className="flex items-center space-x-4 text-sm">
            <span>활성 위성: 3개</span>
            <span>처리 속도: 2.3초/이미지</span>
            <span>대기열: 12개</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Monitoring;