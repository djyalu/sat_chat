import React from 'react';

const FilterPanel = ({ filters, setFilters }) => {
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="card">
      <h3 className="card-header">필터</h3>
      
      <div className="space-y-4">
        {/* 기간 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            기간
          </label>
          <select
            value={filters.dateRange}
            onChange={(e) => handleFilterChange('dateRange', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="today">오늘</option>
            <option value="week">최근 1주</option>
            <option value="month">최근 1개월</option>
            <option value="year">최근 1년</option>
          </select>
        </div>

        {/* 폐기물 유형 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            폐기물 유형
          </label>
          <div className="space-y-2">
            {['all', 'plastic', 'net', 'buoy', 'other'].map((type) => (
              <label key={type} className="flex items-center">
                <input
                  type="radio"
                  name="wasteType"
                  value={type}
                  checked={filters.wasteType === type}
                  onChange={(e) => handleFilterChange('wasteType', e.target.value)}
                  className="mr-2 text-primary-600"
                />
                <span className="text-sm">
                  {type === 'all' && '전체'}
                  {type === 'plastic' && '플라스틱'}
                  {type === 'net' && '어망'}
                  {type === 'buoy' && '부표'}
                  {type === 'other' && '기타'}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* 신뢰도 필터 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            최소 신뢰도: {(filters.confidence * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={filters.confidence}
            onChange={(e) => handleFilterChange('confidence', parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* 위성 소스 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            위성 소스
          </label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" defaultChecked />
              <span className="text-sm">Sentinel-2</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" defaultChecked />
              <span className="text-sm">Planet Labs</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" />
              <span className="text-sm">KOMPSAT</span>
            </label>
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="pt-4 space-y-2">
          <button className="w-full btn-primary text-sm">
            필터 적용
          </button>
          <button 
            onClick={() => setFilters({ dateRange: 'week', wasteType: 'all', confidence: 0.5 })}
            className="w-full btn-secondary text-sm"
          >
            초기화
          </button>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;