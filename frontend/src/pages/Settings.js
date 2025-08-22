import React, { useState } from 'react';
import { toast } from 'react-toastify';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      slack: false,
      discord: false,
      kakao: true
    },
    monitoring: {
      interval: '15',
      confidence: 0.7,
      autoProcess: true
    },
    satellite: {
      sentinel: true,
      planet: true,
      kompsat: false
    }
  });

  const handleSave = () => {
    toast.success('설정이 저장되었습니다.');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">설정</h1>
        <p className="text-gray-500 mt-1">시스템 설정 및 환경 구성</p>
      </div>

      <div className="flex space-x-6">
        {/* 사이드바 */}
        <div className="w-64">
          <nav className="space-y-1">
            {[
              { id: 'general', label: '일반 설정', icon: '⚙️' },
              { id: 'notifications', label: '알림 설정', icon: '🔔' },
              { id: 'monitoring', label: '모니터링', icon: '📡' },
              { id: 'satellite', label: '위성 데이터', icon: '🛰️' },
              { id: 'api', label: 'API 키', icon: '🔑' },
              { id: 'team', label: '팀 관리', icon: '👥' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-600'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <span>{tab.icon}</span>
                <span className="font-medium">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* 콘텐츠 영역 */}
        <div className="flex-1">
          <div className="card">
            {activeTab === 'general' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold">일반 설정</h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    시스템 언어
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option>한국어</option>
                    <option>English</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    시간대
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option>Asia/Seoul (UTC+9)</option>
                    <option>UTC</option>
                  </select>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold">알림 설정</h2>
                
                <div className="space-y-4">
                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">이메일 알림</p>
                      <p className="text-sm text-gray-500">중요 알림을 이메일로 받습니다</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.notifications.email}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: { ...settings.notifications, email: e.target.checked }
                      })}
                      className="w-4 h-4"
                    />
                  </label>

                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Slack 알림</p>
                      <p className="text-sm text-gray-500">Slack 채널로 알림을 받습니다</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.notifications.slack}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: { ...settings.notifications, slack: e.target.checked }
                      })}
                      className="w-4 h-4"
                    />
                  </label>

                  <label className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">카카오톡 알림</p>
                      <p className="text-sm text-gray-500">카카오톡으로 알림을 받습니다</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.notifications.kakao}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: { ...settings.notifications, kakao: e.target.checked }
                      })}
                      className="w-4 h-4"
                    />
                  </label>
                </div>
              </div>
            )}

            {activeTab === 'monitoring' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold">모니터링 설정</h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    모니터링 주기 (분)
                  </label>
                  <input
                    type="number"
                    value={settings.monitoring.interval}
                    onChange={(e) => setSettings({
                      ...settings,
                      monitoring: { ...settings.monitoring, interval: e.target.value }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    최소 신뢰도: {(settings.monitoring.confidence * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={settings.monitoring.confidence}
                    onChange={(e) => setSettings({
                      ...settings,
                      monitoring: { ...settings.monitoring, confidence: parseFloat(e.target.value) }
                    })}
                    className="w-full"
                  />
                </div>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.monitoring.autoProcess}
                    onChange={(e) => setSettings({
                      ...settings,
                      monitoring: { ...settings.monitoring, autoProcess: e.target.checked }
                    })}
                    className="mr-2"
                  />
                  <span>자동 처리 활성화</span>
                </label>
              </div>
            )}

            {activeTab === 'satellite' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold">위성 데이터 소스</h2>
                
                <div className="space-y-4">
                  <label className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="font-medium">Sentinel-2</p>
                      <p className="text-sm text-gray-500">ESA Copernicus 프로그램</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.satellite.sentinel}
                      onChange={(e) => setSettings({
                        ...settings,
                        satellite: { ...settings.satellite, sentinel: e.target.checked }
                      })}
                      className="w-4 h-4"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="font-medium">Planet Labs</p>
                      <p className="text-sm text-gray-500">고해상도 상업 위성</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.satellite.planet}
                      onChange={(e) => setSettings({
                        ...settings,
                        satellite: { ...settings.satellite, planet: e.target.checked }
                      })}
                      className="w-4 h-4"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <p className="font-medium">KOMPSAT</p>
                      <p className="text-sm text-gray-500">한국 다목적 실용위성</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.satellite.kompsat}
                      onChange={(e) => setSettings({
                        ...settings,
                        satellite: { ...settings.satellite, kompsat: e.target.checked }
                      })}
                      className="w-4 h-4"
                    />
                  </label>
                </div>
              </div>
            )}

            <div className="mt-6 pt-6 border-t flex justify-end space-x-3">
              <button className="btn-secondary">취소</button>
              <button className="btn-primary" onClick={handleSave}>저장</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;