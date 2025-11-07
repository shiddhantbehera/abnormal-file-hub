import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fileService } from '../services/fileService';
import {
  DocumentDuplicateIcon,
  CircleStackIcon,
  DocumentIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

export const StorageStats: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['storageStats'],
    queryFn: fileService.getStorageStats,
    refetchInterval: 30000, // 30s
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Storage Statistics</h2>
        <div className="animate-pulse space-y-4">
          <div className="h-20 bg-gray-200 rounded-lg"></div>
          <div className="h-20 bg-gray-200 rounded-lg"></div>
          <div className="h-20 bg-gray-200 rounded-lg"></div>
          <div className="h-20 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to load storage statistics. Please try again later.';
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Storage Statistics</h2>
        <div className="text-sm text-red-600 bg-red-50 p-4 rounded-lg border border-red-200">
          {errorMessage}
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const statCards = [
    {
      title: 'Total Files',
      value: stats.total_files,
      icon: DocumentIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Unique Files',
      value: stats.unique_files,
      icon: CheckCircleIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Duplicate References',
      value: stats.duplicate_references,
      icon: DocumentDuplicateIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      title: 'Storage Saved',
      value: stats.storage_saved_readable,
      icon: CircleStackIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Storage Statistics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card) => (
          <div
            key={card.title}
            className="bg-white rounded-lg shadow p-4 border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              </div>
              <div className={`${card.bgColor} p-3 rounded-lg`}>
                <card.icon className={`h-6 w-6 ${card.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
