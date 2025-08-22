import React from 'react';

const StatsCard = ({ title, value, unit, icon, trend, loading }) => {
  const isPositive = trend && trend.startsWith('+');
  
  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      {loading ? (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{icon}</span>
            {trend && (
              <span className={`text-sm font-medium ${
                isPositive ? 'text-green-600' : 'text-red-600'
              }`}>
                {trend}
              </span>
            )}
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
          <p className="text-2xl font-bold text-gray-900">
            {value}
            <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>
          </p>
        </>
      )}
    </div>
  );
};

export default StatsCard;