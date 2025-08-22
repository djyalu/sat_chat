import React, { useState } from 'react';

const DetectionPanel = ({ detections }) => {
  const [selectedDetection, setSelectedDetection] = useState(null);

  const getPriorityColor = (confidence) => {
    if (confidence > 0.9) return 'text-red-600 bg-red-50';
    if (confidence > 0.7) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  return (
    <div className="space-y-4">
      <div className="card">
        <h3 className="card-header">탐지 목록 ({detections.length})</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {detections.map((detection) => (
            <div
              key={detection.id}
              onClick={() => setSelectedDetection(detection)}
              className={`p-3 border rounded-lg cursor-pointer transition-all duration-200 ${
                selectedDetection?.id === detection.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-1 text-xs font-medium rounded ${getPriorityColor(detection.confidence)}`}>
                  {(detection.confidence * 100).toFixed(0)}%
                </span>
                <span className="text-xs text-gray-500">{detection.time}</span>
              </div>
              <p className="font-medium text-gray-900">{detection.type}</p>
              <p className="text-sm text-gray-600">
                위치: {detection.lat.toFixed(2)}°N, {detection.lng.toFixed(2)}°E
              </p>
            </div>
          ))}
        </div>
      </div>

      {selectedDetection && (
        <div className="card">
          <h3 className="card-header">상세 정보</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">유형</p>
              <p className="font-medium">{selectedDetection.type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">좌표</p>
              <p className="font-medium">
                {selectedDetection.lat.toFixed(4)}°N, {selectedDetection.lng.toFixed(4)}°E
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">신뢰도</p>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{ width: `${selectedDetection.confidence * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium">
                  {(selectedDetection.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-600">추정 크기</p>
              <p className="font-medium capitalize">{selectedDetection.size}</p>
            </div>
            <div className="pt-3 space-y-2">
              <button className="w-full btn-primary text-sm">
                상세 분석 보기
              </button>
              <button className="w-full btn-secondary text-sm">
                알림 생성
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetectionPanel;