import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fileService } from '../services/fileService';
import { StorageStats as StorageStatsType } from '../types/file';
import { ChartBarIcon, DocumentDuplicateIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';

export const StorageStats: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery<StorageStatsType>({
    queryKey: ['fileStats'],
    queryFn: fileService.getStorageStats,
  });

  if (isLoading) {
    return (
      <div className="abnormal-card p-6 mb-6 animate-pulse">
        <div className="h-4 bg-slate-700 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="h-32 bg-slate-700 rounded"></div>
          <div className="h-32 bg-slate-700 rounded"></div>
          <div className="h-32 bg-slate-700 rounded"></div>
          <div className="h-32 bg-slate-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return null;
  }

  return (
    <div className="abnormal-card p-6">
      <div className="flex items-center mb-6">
        <ChartBarIcon className="h-6 w-6 text-primary-500 mr-2" />
        <h2 className="text-xl font-semibold text-slate-100">Storage Optimization</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-5 border border-blue-700 hover:shadow-xl transition-all duration-200 hover:scale-105">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-blue-800 rounded-md p-2">
              <svg className="h-5 w-5 text-blue-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-200 mb-1">Total Files</p>
              <p className="text-3xl font-bold text-blue-50">{stats.total_files}</p>
              <div className="mt-2 text-xs text-blue-300">
                <div>All uploaded files</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-5 border border-green-700 hover:shadow-xl transition-all duration-200 hover:scale-105">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-green-800 rounded-md p-2">
              <svg className="h-5 w-5 text-green-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-200 mb-1">Unique Files</p>
              <p className="text-3xl font-bold text-green-50">{stats.unique_files}</p>
              <div className="mt-2 text-xs text-green-300">
                <div>Original files stored</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-amber-900 to-amber-800 rounded-lg p-5 border border-amber-700 hover:shadow-xl transition-all duration-200 hover:scale-105">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-amber-800 rounded-md p-2">
              <DocumentDuplicateIcon className="h-5 w-5 text-amber-300" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-amber-200 mb-1">Duplicate References</p>
              <p className="text-3xl font-bold text-amber-50">{stats.duplicate_references}</p>
              <div className="mt-2 text-xs text-amber-300">
                <div>Deduplicated files</div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-5 border border-purple-700 hover:shadow-xl transition-all duration-200 hover:scale-105">
          <div className="flex items-start">
            <div className="flex-shrink-0 bg-purple-800 rounded-md p-2">
              <ArrowTrendingUpIcon className="h-5 w-5 text-purple-300" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-purple-200 mb-1">Storage Saved</p>
              <p className="text-3xl font-bold text-purple-50">{stats.storage_saved_readable}</p>
              <div className="mt-2 text-xs text-purple-300">
                <div>Through deduplication</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 