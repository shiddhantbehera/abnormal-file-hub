import React, { useState } from 'react';
import { FunnelIcon, MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { FileFilters } from '../types/file';

// Get unique file types for filtering
const DEFAULT_FILE_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
];

interface SearchFilterProps {
  onFilterChange: (filters: FileFilters) => void;
  fileTypes: string[];
}

export const SearchFilter: React.FC<SearchFilterProps> = ({ 
  onFilterChange,
  fileTypes = DEFAULT_FILE_TYPES
}) => {
  const [filters, setFilters] = useState<FileFilters>({});
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const updatedFilters = { ...filters, search: e.target.value };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  
  const handleFileTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const updatedFilters = { ...filters, file_types: e.target.value || undefined };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  
  const handleSizeChange = (field: 'min_size' | 'max_size', value: string) => {
    // Convert KB to bytes
    const sizeInBytes = value ? parseInt(value) * 1024 : undefined;
    const updatedFilters = { ...filters, [field]: sizeInBytes };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };

  const handleDateChange = (field: 'start_date' | 'end_date', value: string) => {
    // Convert date to ISO 8601 format if value exists
    const isoDate = value ? new Date(value).toISOString() : undefined;
    const updatedFilters = { ...filters, [field]: isoDate };
    setFilters(updatedFilters);
    onFilterChange(updatedFilters);
  };
  

  
  const resetFilters = () => {
    setFilters({});
    onFilterChange({});
  };
  
  const toggleFilterPanel = () => {
    setIsFilterPanelOpen(!isFilterPanelOpen);
  };

  // Helper to determine if any filters are active
  const hasActiveFilters = () => {
    return Object.values(filters).some(value => 
      value !== undefined && value !== '' && 
      (typeof value !== 'number' || value > 0)
    );
  };
  
  return (
    <div className="abnormal-card p-4 mb-6">
      <div className="flex flex-col sm:flex-row items-center">
        <div className="relative flex-grow mb-2 sm:mb-0">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-slate-400" aria-hidden="true" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-slate-600 rounded-md leading-5 bg-slate-700 placeholder-slate-400 text-slate-100 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder="Search files by name..."
            value={filters.search || ''}
            onChange={handleSearchChange}
          />
        </div>
        
        <div className="flex space-x-2 ml-0 sm:ml-4">
          <button
            type="button"
            onClick={toggleFilterPanel}
            className={`inline-flex items-center px-3 py-2 border shadow-sm text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200 ${
              hasActiveFilters() 
                ? 'border-primary-500 text-primary-300 bg-primary-900 hover:bg-primary-800' 
                : 'border-slate-600 text-slate-300 bg-slate-700 hover:bg-slate-600'
            }`}
          >
            <FunnelIcon className={`h-4 w-4 mr-1 ${hasActiveFilters() ? 'text-primary-400' : 'text-slate-400'}`} /> 
            Filters
            {hasActiveFilters() && (
              <span className="ml-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-800 text-primary-200 border border-primary-600">
                Active
              </span>
            )}
          </button>
        </div>
      </div>
      
      {isFilterPanelOpen && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="file-type" className="block text-sm font-medium text-slate-300">
                File Type
              </label>
              <select
                id="file-type"
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-slate-600 bg-slate-700 text-slate-100 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.file_types || ''}
                onChange={handleFileTypeChange}
              >
                <option value="">All file types</option>
                {fileTypes.map(type => (
                  <option key={type} value={type}>
                    {type.split('/')[1].toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="min-size" className="block text-sm font-medium text-slate-300">
                Min Size (KB)
              </label>
              <input
                type="number"
                id="min-size"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-slate-600 bg-slate-700 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                placeholder="Min size"
                value={filters.min_size ? (filters.min_size / 1024).toString() : ''}
                onChange={e => handleSizeChange('min_size', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="max-size" className="block text-sm font-medium text-slate-300">
                Max Size (KB)
              </label>
              <input
                type="number"
                id="max-size"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-slate-600 bg-slate-700 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                placeholder="Max size"
                value={filters.max_size ? (filters.max_size / 1024).toString() : ''}
                onChange={e => handleSizeChange('max_size', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-slate-300">
                Uploaded After
              </label>
              <input
                type="date"
                id="start-date"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-slate-600 bg-slate-700 text-slate-100 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.start_date ? new Date(filters.start_date).toISOString().split('T')[0] : ''}
                onChange={e => handleDateChange('start_date', e.target.value)}
              />
            </div>
            
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-slate-300">
                Uploaded Before
              </label>
              <input
                type="date"
                id="end-date"
                className="mt-1 block w-full pl-3 pr-3 py-2 text-base border-slate-600 bg-slate-700 text-slate-100 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                value={filters.end_date ? new Date(filters.end_date).toISOString().split('T')[0] : ''}
                onChange={e => handleDateChange('end_date', e.target.value)}
              />
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={resetFilters}
              className="inline-flex items-center px-4 py-2 border border-primary-500 shadow-sm text-sm font-medium rounded-md text-primary-300 bg-slate-700 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
            >
              <XMarkIcon className="h-4 w-4 mr-1" />
              Reset Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}; 