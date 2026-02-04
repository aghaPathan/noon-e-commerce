/**
 * PriceChart - Line chart showing price history over time
 */

import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { PricePoint } from '../../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PriceChartProps {
  history: PricePoint[];
  title?: string;
  height?: number;
}

export function PriceChart({ history, title, height = 300 }: PriceChartProps) {
  // Sort by date ascending for chart
  const sortedHistory = useMemo(() => {
    return [...history].sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [history]);

  const chartData = useMemo(() => {
    const labels = sortedHistory.map(p => {
      const date = new Date(p.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const prices = sortedHistory.map(p => p.price);
    const originalPrices = sortedHistory.map(p => p.original_price || p.price);

    return {
      labels,
      datasets: [
        {
          label: 'Price (AED)',
          data: prices,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: 'Original Price',
          data: originalPrices,
          borderColor: 'rgb(156, 163, 175)',
          borderDash: [5, 5],
          backgroundColor: 'transparent',
          tension: 0.3,
          pointRadius: 2,
          pointHoverRadius: 4,
        },
      ],
    };
  }, [sortedHistory]);

  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: !!title,
        text: title || '',
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y;
            return `${context.dataset.label}: AED ${value.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value: any) => `AED ${value}`,
        },
      },
    },
  }), [title]);

  if (history.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No price history available</p>
      </div>
    );
  }

  return (
    <div style={{ height }}>
      <Line data={chartData} options={options} />
    </div>
  );
}

export default PriceChart;
