import React, { useState, useEffect } from 'react';
import { Line, Bar, Scatter } from 'react-chartjs-2';
import DatePicker from '../components/DatePicker';

const Analysis = () => {
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [selectedMetric, setSelectedMetric] = useState('detection_count');
  const [analysisData, setAnalysisData] = useState(null);

  // 트렌드 분석 데이터
  const trendData = {
    labels: ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월'],
    datasets: [
      {
        label: '플라스틱',
        data: [65, 72, 78, 85, 92, 88, 95, 102],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4
      },
      {
        label: '어망',
        data: [28, 32, 30, 35, 38, 42, 40, 45],
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4
      },
      {
        label: '부표',
        data: [15, 18, 20, 22, 25, 23, 28, 30],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4
      }
    ]
  };

  // 상관관계 분석 데이터
  const correlationData = {
    datasets: [
      {
        label: '해류 속도 vs 폐기물 분포',
        data: Array.from({ length: 50 }, () => ({
          x: Math.random() * 10,
          y: Math.random() * 100
        })),
        backgroundColor: 'rgba(59, 130, 246, 0.5)'
      }
    ]
  };

  // 계절별 분석
  const seasonalData = {
    labels: ['봄', '여름', '가을', '겨울'],
    datasets: [
      {
        label: '평균 탐지 건수',
        data: [120, 185, 95, 65],
        backgroundColor: [
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)'
        ]
      }
    ]
  };

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">데이터 분석</h1>
        <p className="text-gray-500 mt-1">해양 폐기물 데이터의 심층 분석 및 인사이트</p>
      </div>

      {/* 분석 도구 바 */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">분석 지표</label>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="detection_count">탐지 건수</option>
              <option value="waste_volume">폐기물 양</option>
              <option value="confidence_score">신뢰도</option>
              <option value="response_time">대응 시간</option>
            </select>
          </div>
          
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">분석 기간</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>최근 30일</option>
              <option>최근 90일</option>
              <option>최근 1년</option>
              <option>전체 기간</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button className="btn-secondary">
              📥 데이터 내보내기
            </button>
            <button className="btn-primary">
              🔄 분석 실행
            </button>
          </div>
        </div>
      </div>

      {/* 주요 인사이트 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">📈</span>
            <span className="text-sm font-medium text-blue-600">+23%</span>
          </div>
          <h3 className="text-sm font-medium text-gray-700">주요 인사이트</h3>
          <p className="text-lg font-bold text-gray-900 mt-1">서해 지역 증가 추세</p>
          <p className="text-sm text-gray-600 mt-2">지난 3개월 대비 23% 증가</p>
        </div>

        <div className="card bg-gradient-to-br from-green-50 to-green-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🎯</span>
            <span className="text-sm font-medium text-green-600">92%</span>
          </div>
          <h3 className="text-sm font-medium text-gray-700">탐지 정확도</h3>
          <p className="text-lg font-bold text-gray-900 mt-1">AI 모델 성능 향상</p>
          <p className="text-sm text-gray-600 mt-2">평균 신뢰도 92% 달성</p>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">⚡</span>
            <span className="text-sm font-medium text-purple-600">-45min</span>
          </div>
          <h3 className="text-sm font-medium text-gray-700">대응 시간</h3>
          <p className="text-lg font-bold text-gray-900 mt-1">평균 2.5시간</p>
          <p className="text-sm text-gray-600 mt-2">이전 대비 45분 단축</p>
        </div>
      </div>

      {/* 분석 차트 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 트렌드 분석 */}
        <div className="card">
          <h3 className="card-header">폐기물 유형별 트렌드</h3>
          <div className="h-80">
            <Line
              data={trendData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom'
                  },
                  tooltip: {
                    mode: 'index',
                    intersect: false
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: '탐지 건수'
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* 계절별 분포 */}
        <div className="card">
          <h3 className="card-header">계절별 탐지 패턴</h3>
          <div className="h-80">
            <Bar
              data={seasonalData}
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
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: '평균 탐지 건수'
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* 상관관계 분석 */}
        <div className="card">
          <h3 className="card-header">환경 요인 상관관계</h3>
          <div className="h-80">
            <Scatter
              data={correlationData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false
                  }
                },
                scales: {
                  x: {
                    title: {
                      display: true,
                      text: '해류 속도 (m/s)'
                    }
                  },
                  y: {
                    title: {
                      display: true,
                      text: '폐기물 밀도 (kg/km²)'
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* 예측 모델 */}
        <div className="card">
          <h3 className="card-header">예측 모델 결과</h3>
          <div className="space-y-4">
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-medium text-yellow-900 mb-2">⚠️ 주의 구역 예측</h4>
              <p className="text-sm text-yellow-700">다음 7일 이내 서해 중부 지역 폐기물 집중 예상</p>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">예측 정확도</span>
                <span className="font-medium">87.3%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">신뢰 구간</span>
                <span className="font-medium">±5.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">모델 버전</span>
                <span className="font-medium">v2.3.1</span>
              </div>
            </div>

            <button className="w-full btn-primary text-sm">
              상세 예측 보고서 보기
            </button>
          </div>
        </div>
      </div>

      {/* 데이터 테이블 */}
      <div className="card">
        <h3 className="card-header">상세 데이터</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">날짜</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">지역</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">유형</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">건수</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신뢰도</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {[1, 2, 3, 4, 5].map((item) => (
                <tr key={item} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">2024-01-{15 + item}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">서해</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">플라스틱</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{20 + item * 3}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{85 + item}%</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      처리완료
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Analysis;