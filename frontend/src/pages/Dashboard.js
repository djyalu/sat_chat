import React, { useEffect, useState } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import StatsCard from '../components/StatsCard';
import RecentDetections from '../components/RecentDetections';
import { api } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalDetections: 0,
    activeAlerts: 0,
    monitoredArea: 0,
    detectionRate: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // API 호출 시뮬레이션
      setTimeout(() => {
        setStats({
          totalDetections: 142,
          activeAlerts: 7,
          monitoredArea: 25000,
          detectionRate: 89.3
        });
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
      setLoading(false);
    }
  };

  // 시계열 데이터
  const timeSeriesData = {
    labels: ['1월', '2월', '3월', '4월', '5월', '6월'],
    datasets: [
      {
        label: '폐기물 탐지 건수',
        data: [12, 19, 23, 25, 32, 28],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  // 지역별 분포 데이터
  const regionData = {
    labels: ['서해', '남해', '동해', '제주'],
    datasets: [
      {
        label: '지역별 탐지 건수',
        data: [45, 38, 32, 27],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(251, 146, 60, 0.8)',
          'rgba(147, 51, 234, 0.8)'
        ]
      }
    ]
  };

  // 폐기물 유형별 데이터
  const wasteTypeData = {
    labels: ['플라스틱', '어망', '부표', '기타'],
    datasets: [
      {
        data: [45, 25, 20, 10],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(168, 85, 247, 0.8)'
        ]
      }
    ]
  };

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-500 mt-1">해양 폐기물 모니터링 현황을 한눈에 확인하세요</p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="총 탐지 건수"
          value={stats.totalDetections}
          unit="건"
          icon="🎯"
          trend="+12%"
          loading={loading}
        />
        <StatsCard
          title="활성 알림"
          value={stats.activeAlerts}
          unit="개"
          icon="🔔"
          trend="-5%"
          loading={loading}
        />
        <StatsCard
          title="모니터링 면적"
          value={stats.monitoredArea.toLocaleString()}
          unit="km²"
          icon="📍"
          loading={loading}
        />
        <StatsCard
          title="탐지 정확도"
          value={stats.detectionRate}
          unit="%"
          icon="✅"
          trend="+3%"
          loading={loading}
        />
      </div>

      {/* 차트 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 시계열 차트 */}
        <div className="card">
          <h3 className="card-header">월별 탐지 추이</h3>
          <div className="h-64">
            <Line
              data={timeSeriesData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true
                  }
                }
              }}
            />
          </div>
        </div>

        {/* 지역별 막대 차트 */}
        <div className="card">
          <h3 className="card-header">지역별 탐지 현황</h3>
          <div className="h-64">
            <Bar
              data={regionData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* 하단 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 폐기물 유형 차트 */}
        <div className="card">
          <h3 className="card-header">폐기물 유형별 분포</h3>
          <div className="h-64 flex items-center justify-center">
            <div className="w-48 h-48">
              <Doughnut
                data={wasteTypeData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: {
                        padding: 10,
                        font: {
                          size: 11
                        }
                      }
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>

        {/* 최근 탐지 목록 */}
        <div className="lg:col-span-2">
          <RecentDetections />
        </div>
      </div>

      {/* 빠른 작업 */}
      <div className="card bg-gradient-to-r from-primary-50 to-marine-50">
        <h3 className="card-header">빠른 작업</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn-primary flex items-center justify-center space-x-2">
            <span>🛰️</span>
            <span>새 위성 데이터 수집</span>
          </button>
          <button className="btn-primary flex items-center justify-center space-x-2">
            <span>📊</span>
            <span>리포트 생성</span>
          </button>
          <button className="btn-primary flex items-center justify-center space-x-2">
            <span>🚨</span>
            <span>긴급 알림 발송</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;