import React from 'react';

const RecentDetections = () => {
  const detections = [
    {
      id: 1,
      location: '서해 인천 해역',
      type: '플라스틱 폐기물',
      confidence: 92,
      time: '10분 전',
      status: 'new',
      image: '🔴'
    },
    {
      id: 2,
      location: '남해 부산 해역',
      type: '폐어망',
      confidence: 85,
      time: '35분 전',
      status: 'processing',
      image: '🟡'
    },
    {
      id: 3,
      location: '동해 울산 해역',
      type: '부표',
      confidence: 78,
      time: '1시간 전',
      status: 'resolved',
      image: '🟢'
    },
    {
      id: 4,
      location: '서해 군산 해역',
      type: '플라스틱 폐기물',
      confidence: 95,
      time: '2시간 전',
      status: 'new',
      image: '🔴'
    },
    {
      id: 5,
      location: '제주 서귀포 해역',
      type: '기타 폐기물',
      confidence: 65,
      time: '3시간 전',
      status: 'processing',
      image: '🟡'
    }
  ];

  const getStatusBadge = (status) => {
    const badges = {
      new: 'bg-red-100 text-red-800',
      processing: 'bg-yellow-100 text-yellow-800',
      resolved: 'bg-green-100 text-green-800'
    };
    const labels = {
      new: '신규',
      processing: '처리중',
      resolved: '완료'
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${badges[status]}`}>
        {labels[status]}
      </span>
    );
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header mb-0">최근 탐지 내역</h3>
        <button className="text-sm text-primary-600 hover:text-primary-700">
          전체보기 →
        </button>
      </div>
      
      <div className="space-y-3">
        {detections.map((detection) => (
          <div
            key={detection.id}
            className="border-l-4 border-gray-200 hover:border-primary-400 pl-4 py-2 transition-colors duration-200 cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-lg">{detection.image}</span>
                  <h4 className="font-medium text-gray-900">{detection.location}</h4>
                  {getStatusBadge(detection.status)}
                </div>
                <p className="text-sm text-gray-600">{detection.type}</p>
                <div className="flex items-center space-x-4 mt-1">
                  <span className="text-xs text-gray-500">
                    신뢰도: {detection.confidence}%
                  </span>
                  <span className="text-xs text-gray-500">
                    {detection.time}
                  </span>
                </div>
              </div>
              <button className="p-1 hover:bg-gray-100 rounded">
                <span className="text-gray-400">⋮</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentDetections;