import React from 'react';
import ReactECharts from 'echarts-for-react';

interface ChartData {
  name: string;
  value: number;
  breakdown?: {
    manufacturing?: number;
    shipping?: number;
    usage?: number;
    [key: string]: number | undefined;
  };
}

interface AnalysisChartsProps {
  data: ChartData[];
  title: string;
  unit?: string;
}

export const AnalysisCharts: React.FC<AnalysisChartsProps> = ({ 
  data, 
  title, 
  unit = 'kg CO2e' 
}) => {
  console.log('AnalysisCharts received data:', data);
  // Bar chart for comparison
  const getBarChartOption = () => ({
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#1f2937'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const item = params[0];
        return `${item.name}<br/>${item.seriesName}: ${item.value} ${unit}`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.name),
      axisLabel: {
        rotate: 45,
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      name: unit,
      nameLocation: 'middle',
      nameGap: 50
    },
    series: [{
      name: 'Carbon Emissions',
      type: 'bar',
      data: data.map(item => ({
        value: item.value,
        itemStyle: {
          color: item.value === Math.min(...data.map(d => d.value)) 
            ? '#10b981' // Green for lowest
            : item.value === Math.max(...data.map(d => d.value))
            ? '#ef4444' // Red for highest
            : '#3b82f6' // Blue for middle
        }
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  });

  // Pie chart for breakdown
  const getPieChartOption = (itemData: ChartData) => {
    const breakdownData = itemData.breakdown ? Object.entries(itemData.breakdown)
      .filter(([_, value]) => value !== undefined && value !== null && value > 0)
      .map(([key, value]) => ({
        value: Number(value),
        name: key.charAt(0).toUpperCase() + key.slice(1),
        itemStyle: {
          color: key === 'manufacturing' ? '#ef4444' : 
                 key === 'shipping' ? '#f59e0b' : 
                 key === 'usage' ? '#10b981' : '#3b82f6'
        }
      })) : [];

    // If no breakdown data, create a simple single-value pie
    if (breakdownData.length === 0) {
      breakdownData.push({
        value: itemData.value,
        name: 'Total Emissions',
        itemStyle: { color: '#3b82f6' }
      });
    }

    return {
      title: {
        text: `${itemData.name} Breakdown`,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold',
          color: '#1f2937'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} kg CO2e ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          fontSize: 12
        }
      },
      series: [{
        name: 'Emissions',
        type: 'pie',
        radius: ['20%', '70%'],
        center: ['60%', '50%'],
        data: breakdownData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        }
      }]
    };
  };

  // Stacked bar chart for detailed breakdown
  const getStackedBarOption = () => {
    if (!data.some(item => item.breakdown)) return null;

    const categories = ['manufacturing', 'shipping', 'usage'];
    const series = categories.map(category => ({
      name: category.charAt(0).toUpperCase() + category.slice(1),
      type: 'bar',
      stack: 'total',
      data: data.map(item => item.breakdown?.[category] || 0),
      itemStyle: {
        color: category === 'manufacturing' ? '#ef4444' : 
               category === 'shipping' ? '#f59e0b' : '#10b981'
      }
    }));

    return {
      title: {
        text: `${title} - Detailed Breakdown`,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold',
          color: '#1f2937'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: categories.map(c => c.charAt(0).toUpperCase() + c.slice(1)),
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.name)
      },
      yAxis: {
        type: 'value',
        name: unit,
        nameLocation: 'middle',
        nameGap: 50
      },
      series
    };
  };

  const stackedOption = getStackedBarOption();

  return (
    <div className="space-y-6">
      {/* Main comparison chart */}
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <ReactECharts 
          option={getBarChartOption()} 
          style={{ height: '400px' }}
          opts={{ renderer: 'canvas' }}
        />
      </div>

      {/* Stacked breakdown chart */}
      {stackedOption && (
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <ReactECharts 
            option={stackedOption} 
            style={{ height: '400px' }}
            opts={{ renderer: 'canvas' }}
          />
        </div>
      )}

      {/* Individual pie charts for breakdown */}
      {data.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((item, index) => (
            <div key={index} className="bg-white p-4 rounded-lg shadow-sm border">
              <ReactECharts 
                option={getPieChartOption(item)} 
                style={{ height: '300px' }}
                opts={{ renderer: 'canvas' }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Summary statistics */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">📊 Analysis Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {Math.min(...data.map(d => d.value)).toFixed(1)} {unit}
            </div>
            <div className="text-sm text-gray-600">Lowest Emissions</div>
            <div className="text-xs text-gray-500">
              {data.find(d => d.value === Math.min(...data.map(item => item.value)))?.name}
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {(data.reduce((sum, d) => sum + d.value, 0) / data.length).toFixed(1)} {unit}
            </div>
            <div className="text-sm text-gray-600">Average Emissions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {Math.max(...data.map(d => d.value)).toFixed(1)} {unit}
            </div>
            <div className="text-sm text-gray-600">Highest Emissions</div>
            <div className="text-xs text-gray-500">
              {data.find(d => d.value === Math.max(...data.map(item => item.value)))?.name}
            </div>
          </div>
        </div>
        
        {/* Recommendations */}
        <div className="mt-4 p-3 bg-white rounded border-l-4 border-green-500">
          <h4 className="font-semibold text-gray-800">🌱 Recommendation</h4>
          <p className="text-sm text-gray-600 mt-1">
            Choose <strong>{data.find(d => d.value === Math.min(...data.map(item => item.value)))?.name}</strong> for 
            the lowest carbon footprint. This could save up to{' '}
            <strong>
              {(Math.max(...data.map(d => d.value)) - Math.min(...data.map(d => d.value))).toFixed(1)} {unit}
            </strong>{' '}
            compared to the highest-emission option.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AnalysisCharts;
