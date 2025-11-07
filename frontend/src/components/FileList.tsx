import React, { useState, useEffect } from 'react';
import { fileService } from '../services/fileService';
import { FileFilters, File as FileType, PaginatedResponse } from '../types/file';
import { DocumentIcon, TrashIcon, ArrowDownTrayIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SearchFilter } from './SearchFilter';

export const FileList: React.FC = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<FileFilters>({});
  const [uniqueFileTypes, setUniqueFileTypes] = useState<string[]>([]);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: response, isLoading, error } = useQuery<PaginatedResponse<FileType>>({
    queryKey: ['files', filters],
    queryFn: () => fileService.searchFiles(filters)
  });

  const files = response?.results || [];

  useEffect(() => {
    if (files && files.length > 0) {
      const fileTypes = Array.from(new Set(files.map(file => file.file_type)));
      setUniqueFileTypes(fileTypes);
    }
  }, [files]);

  const deleteMutation = useMutation({
    mutationFn: fileService.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      queryClient.invalidateQueries({ queryKey: ['fileStats'] });
      setDeleteError(null);
    },
    onError: (error: any) => {
      console.error('Delete error:', error);
      setDeleteError('Failed to delete file. Please try again.');
    }
  });

  const downloadMutation = useMutation({
    mutationFn: ({ fileUrl, filename }: { fileUrl: string; filename: string }) =>
      fileService.downloadFile(fileUrl, filename),
  });

  const handleDelete = async (id: string) => {
    try {
      setDeleteError(null);
      await deleteMutation.mutateAsync(id);
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  const handleDownload = async (fileUrl: string, filename: string) => {
    try {
      await downloadMutation.mutateAsync({ fileUrl, filename });
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  const handleFilterChange = (newFilters: FileFilters) => {
    setFilters(newFilters);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <SearchFilter onFilterChange={handleFilterChange} fileTypes={uniqueFileTypes} />
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-700 rounded w-1/4"></div>
          <div className="space-y-3">
            <div className="h-8 bg-slate-700 rounded"></div>
            <div className="h-8 bg-slate-700 rounded"></div>
            <div className="h-8 bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <SearchFilter onFilterChange={handleFilterChange} fileTypes={uniqueFileTypes} />
        <div className="bg-red-900 border-l-4 border-red-500 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-200">Failed to load files. Please try again.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const filesList = files || [];

  return (
    <div className="p-6">
      <SearchFilter onFilterChange={handleFilterChange} fileTypes={uniqueFileTypes} />
      
      {deleteError && (
        <div className="bg-red-900 border-l-4 border-red-500 p-4 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-200">{deleteError}</p>
            </div>
          </div>
        </div>
      )}
      
      <h2 className="text-xl font-semibold text-slate-100 mb-4">Uploaded Files</h2>
      {filesList.length === 0 ? (
        <div className="text-center py-12">
          <DocumentIcon className="mx-auto h-12 w-12 text-slate-500" />
          <h3 className="mt-2 text-sm font-medium text-slate-300">No files</h3>
          <p className="mt-1 text-sm text-slate-400">
            Get started by uploading a file
          </p>
        </div>
      ) : (
        <div className="mt-6 flow-root">
          <ul className="-my-5 divide-y divide-slate-700">
            {filesList.map((file) => (
              <li key={file.id} className="py-4">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {file.is_duplicate ? (
                      <DocumentDuplicateIcon className="h-8 w-8 text-amber-400" />
                    ) : (
                      <DocumentIcon className="h-8 w-8 text-slate-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-100 truncate">
                      {file.original_filename}
                      {file.is_duplicate && (
                        <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-900 text-amber-200 border border-amber-700">
                          Duplicate
                        </span>
                      )}
                    </p>
                    <p className="text-sm text-slate-400">
                      {file.file_type} • {formatBytes(file.size)}
                    </p>
                    <p className="text-sm text-slate-400">
                      Uploaded {new Date(file.uploaded_at).toLocaleString()}
                    </p>
                    {file.is_duplicate && file.storage_saved > 0 && (
                      <p className="text-sm text-green-400">
                        Storage saved: {formatBytes(file.storage_saved)}
                      </p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    {file.file && (
                      <button
                        onClick={() => handleDownload(file.file!, file.original_filename)}
                        disabled={downloadMutation.isPending}
                        className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
                      >
                        <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                        Download
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(file.id)}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors duration-200"
                    >
                      <TrashIcon className="h-4 w-4 mr-1" />
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}; 