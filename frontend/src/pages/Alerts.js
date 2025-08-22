import React, { useState } from 'react';

const Alerts = () => {
  const [filter, setFilter] = useState('all');
  
  const alerts = [
    {
      id: 1,
      type: 'critical',
      title: '대규모 폐기물 집적 탐지',
      description: '서해 인천 해역에서 대규모 플라스틱 폐기물 집적이 탐지되었습니다.',
      location: '서해 인천 해역',
      time: '10분 전',
      status: 'active'
    },
    {
      id: 2,
      type: 'warning',
      title: '폐어망 탐지',
      description: '남해 통영 해역에서 폐어망이 발견되었습니다.',
      location: '남해 통영 해역',
      time: '1시간 전',
      status: 'acknowledged'
    },
    {
      id: 3,
      type: 'info',
      title: '정기 모니터링 완료',
      description: '동해 지역 정기 모니터링이 완료되었습니다.',
      location: '동해 전역',
      time: '3시간 전',
      status: 'resolved'
    }
  ];

  const getAlertIcon = (type) => {
    switch(type) {
      case 'critical': return '🚨';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📢';
    }
  };

  const getAlertColor = (type) => {
    switch(type) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      case 'info': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">알림 센터</h1>
          <p className="text-gray-500 mt-1">실시간 알림 및 경고 관리</p>
        </div>
        <button className="btn-primary">
          + 알림 규칙 추가
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-1 inline-flex">
        {['all', 'active', 'acknowledged', 'resolved'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-md transition-colors duration-200 ${
              filter === status
                ? 'bg-primary-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {status === 'all' && '전체'}
            {status === 'active' && '활성'}
            {status === 'acknowledged' && '확인됨'}
            {status === 'resolved' && '해결됨'}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`card border-l-4 ${getAlertColor(alert.type)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">{getAlertIcon(alert.type)}</span>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                  <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                    <span>📍 {alert.location}</span>
                    <span>🕐 {alert.time}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button className="btn-secondary text-sm">확인</button>
                <button className="btn-primary text-sm">조치</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Alerts;