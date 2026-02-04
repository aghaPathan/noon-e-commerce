import React from 'react';

interface SortIconProps {
  isActive?: boolean;
  direction?: 'asc' | 'desc' | null;
}

export const SortIcon: React.FC<SortIconProps> = ({ isActive = false, direction }) => {
  if (!isActive || !direction) {
    return <span className="text-gray-300">↕</span>;
  }
  return <span className="text-gray-700">{direction === 'asc' ? '↑' : '↓'}</span>;
};

export default SortIcon;
