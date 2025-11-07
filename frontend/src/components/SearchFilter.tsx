import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MagnifyingGlassIcon, XMarkIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { FilterCriteria } from '../types/file';

interface SearchFilterProps {
  onFilterChange: (filters: FilterCriteria) => void;
}

const FILE_TYPES = [
  { value: 'application/pdf', label: 'PDF' },
  { value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'DOCX' },
  { value: 'image/png', label: 'PNG' },
  { value: 'image/jpeg', label: 'JPG' },
  { value: 'application/zip', label: 'ZIP' },
  { value: 'text/plain', label: 'TXT' },
  { value: 'text/csv', label: 'CSV' },
];

export const SearchFilter: React.FC<SearchFilterProps> = ({ onFilterChange }) => {
  console.log('[SearchFilter] Component rendered');
  
  const [search, setSearch] = useState('');
  const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
  const [minSize, setMinSize] = useState('');
  const [maxSize, setMaxSize] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sizeError, setSizeError] = useState('');
  const [dateError, setDateError] = useState('');
  
  console.log('[SearchFilter] Current state:', { search, selectedFileTypes, minSize, maxSize, startDate, endDate });

  const onFilterChangeRef = useRef(onFilterChange);
  onFilterChangeRef.current = onFilterChange;

  const emitFilterChange = useCallback(() => {
    if (minSize && maxSize) {
      const min = parseFloat(minSize);
      const max = parseFloat(maxSize);
      if (isNaN(min) || isNaN(max)) {
        setSizeError('Size values must be valid numbers');
        return;
      }
      if (min < 0 || max < 0) {
        setSizeError('Size values cannot be negative');
        return;
      }
      if (min > max) {
        setSizeError('Minimum size cannot be greater than maximum size');
        return;
      }
    }
    
    if (minSize) {
      const min = parseFloat(minSize);
      if (isNaN(min) || min < 0) {
        setSizeError('Minimum size must be a non-negative number');
        return;
      }
    }
    
    if (maxSize) {
      const max = parseFloat(maxSize);
      if (isNaN(max) || max < 0) {
        setSizeError('Maximum size must be a non-negative number');
        return;
      }
    }
    
    setSizeError('');

    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        setDateError('Invalid date format');
        return;
      }
      
      if (start > end) {
        setDateError('Start date cannot be after end date');
        return;
      }
    }
    
    if (startDate) {
      const start = new Date(startDate);
      if (isNaN(start.getTime())) {
        setDateError('Invalid start date format');
        return;
      }
    }
    
    if (endDate) {
      const end = new Date(endDate);
      if (isNaN(end.getTime())) {
        setDateError('Invalid end date format');
        return;
      }
    }
    
    setDateError('');

    const filters: FilterCriteria = {};

    if (search.trim()) {
      filters.search = search.trim();
    }

    if (selectedFileTypes.length > 0) {
      filters.fileTypes = selectedFileTypes;
    }

    if (minSize) {
      const minBytes = parseFloat(minSize) * 1024;
      if (!isNaN(minBytes) && minBytes >= 0) {
        filters.minSize = minBytes;
      }
    }

    if (maxSize) {
      const maxBytes = parseFloat(maxSize) * 1024;
      if (!isNaN(maxBytes) && maxBytes >= 0) {
        filters.maxSize = maxBytes;
      }
    }

    if (startDate) {
      try {
        filters.startDate = new Date(startDate).toISOString();
      } catch (e) {
        setDateError('Invalid start date');
        return;
      }
    }

    if (endDate) {
      try {
        const endDateTime = new Date(endDate);
        endDateTime.setHours(23, 59, 59, 999);
        filters.endDate = endDateTime.toISOString();
      } catch (e) {
        setDateError('Invalid end date');
        return;
      }
    }

    onFilterChangeRef.current(filters);
  }, [search, selectedFileTypes, minSize, maxSize, startDate, endDate]);

  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const timer = setTimeout(() => {
      emitFilterChange();
    }, 300);

    return () => clearTimeout(timer);
  }, [emitFilterChange]);

  const handleFileTypeToggle = (fileType: string) => {
    console.log('[SearchFilter] handleFileTypeToggle called with:', fileType);
    setSelectedFileTypes(prev => {
      const newValue = prev.includes(fileType)
        ? prev.filter(t => t !== fileType)
        : [...prev, fileType];
      console.log('[SearchFilter] selectedFileTypes changing from', prev, 'to', newValue);
      return newValue;
    });
  };

  const removeFilter = (filterType: string, value?: string) => {
    switch (filterType) {
      case 'search':
        setSearch('');
        break;
      case 'fileType':
        if (value) {
          setSelectedFileTypes(prev => prev.filter(t => t !== value));
        }
        break;
      case 'minSize':
        setMinSize('');
        break;
      case 'maxSize':
        setMaxSize('');
        break;
      case 'startDate':
        setStartDate('');
        break;
      case 'endDate':
        setEndDate('');
        break;
    }
  };

  const clearAllFilters = () => {
    setSearch('');
    setSelectedFileTypes([]);
    setMinSize('');
    setMaxSize('');
    setStartDate('');
    setEndDate('');
    setSizeError('');
    setDateError('');
  };

  const hasActiveFilters = search || selectedFileTypes.length > 0 || minSize || maxSize || startDate || endDate;

  const getFileTypeLabel = (value: string) => {
    return FILE_TYPES.find(ft => ft.value === value)?.label || value;
  };

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <div className="flex items-center mb-4">
        <FunnelIcon className="h-5 w-5 text-gray-500 mr-2" />
        <h3 className="text-lg font-medium text-gray-900">Search & Filter</h3>
      </div>

      {/* Search Input */}
      <div className="mb-4">
        <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
          Search by filename
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            id="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search files..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          />
        </div>
      </div>

      {/* File Type Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          File Types
        </label>
        <div className="flex flex-wrap gap-2">
          {FILE_TYPES.map((fileType) => (
            <button
              key={fileType.value}
              onClick={() => handleFileTypeToggle(fileType.value)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFileTypes.includes(fileType.value)
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {fileType.label}
            </button>
          ))}
        </div>
      </div>

      {/* Size Range Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          File Size (KB)
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <input
              type="number"
              value={minSize}
              onChange={(e) => setMinSize(e.target.value)}
              placeholder="Min size"
              min="0"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
          <div>
            <input
              type="number"
              value={maxSize}
              onChange={(e) => setMaxSize(e.target.value)}
              placeholder="Max size"
              min="0"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        </div>
        {sizeError && (
          <p className="mt-1 text-sm text-red-600">{sizeError}</p>
        )}
      </div>

      {/* Date Range Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload Date
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
          <div>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        </div>
        {dateError && (
          <p className="mt-1 text-sm text-red-600">{dateError}</p>
        )}
      </div>

      {/* Active Filters Chips */}
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Active Filters:</span>
            <button
              onClick={clearAllFilters}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Clear all
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {search && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800">
                Search: {search}
                <button
                  onClick={() => removeFilter('search')}
                  className="ml-2 inline-flex items-center"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            )}
            {selectedFileTypes.map((fileType) => (
              <span
                key={fileType}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800"
              >
                Type: {getFileTypeLabel(fileType)}
                <button
                  onClick={() => removeFilter('fileType', fileType)}
                  className="ml-2 inline-flex items-center"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            ))}
            {minSize && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800">
                Min: {minSize} KB
                <button
                  onClick={() => removeFilter('minSize')}
                  className="ml-2 inline-flex items-center"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            )}
            {maxSize && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800">
                Max: {maxSize} KB
                <button
                  onClick={() => removeFilter('maxSize')}
                  className="ml-2 inline-flex items-center"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            )}
            {startDate && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800">
                From: {new Date(startDate).toLocaleDateString()}
                <button
                  onClick={() => removeFilter('startDate')}
                  className="ml-2 inline-flex items-center"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            )}
            {endDate && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800">
                To: {new Date(endDate).toLocaleDateString()}
                <button
                  onClick={() => removeFilter('endDate')}
                  className="ml-2 inline-flex items-center"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
