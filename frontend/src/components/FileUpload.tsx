import React, { useState, useRef } from 'react';
import { fileService } from '../services/fileService';
import { CloudArrowUpIcon } from '@heroicons/react/24/outline';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const uploadMutation = useMutation({
    mutationFn: fileService.uploadFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      queryClient.invalidateQueries({ queryKey: ['fileStats'] });
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setSelectedFile(null);
      onUploadSuccess();
    },
    onError: (error) => {
      setError('Failed to upload file. Please try again.');
      console.error('Upload error:', error);
    },
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    try {
      setError(null);
      await uploadMutation.mutateAsync(selectedFile);
    } catch (err) {
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center mb-6">
        <CloudArrowUpIcon className="h-6 w-6 text-primary-500 mr-2" />
        <h2 className="text-xl font-semibold text-slate-100">Upload File</h2>
      </div>
      <div className="mt-6 space-y-5">
        <div className="flex justify-center px-6 pt-5 pb-6 border-2 border-slate-600 border-dashed rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors duration-200">
          <div className="space-y-2 text-center">
            <div className="mx-auto h-12 w-12 text-primary-400">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div className="flex text-sm text-slate-300 justify-center">
              <label
                htmlFor="file-upload"
                className="relative cursor-pointer bg-slate-800 rounded-md font-medium text-primary-400 hover:text-primary-300 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500 px-3 py-2 border border-slate-600"
              >
                <span>Upload a file</span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  onChange={handleFileSelect}
                  disabled={uploadMutation.isPending}
                  ref={fileInputRef}
                />
              </label>
              <p className="pl-1 self-center">or drag and drop</p>
            </div>
            <p className="text-xs text-slate-400">Any file up to 10MB</p>
          </div>
        </div>
        {selectedFile && (
          <div className="text-sm bg-blue-900 text-blue-200 p-3 rounded-md border border-blue-700">
            Selected: <span className="font-medium">{selectedFile.name}</span>
          </div>
        )}
        {error && (
          <div className="text-sm text-red-200 bg-red-900 p-3 rounded-md border border-red-700">
            {error}
          </div>
        )}
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploadMutation.isPending}
          className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white transition-colors duration-200 ${
            !selectedFile || uploadMutation.isPending
              ? 'bg-slate-600 cursor-not-allowed'
              : 'bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
          }`}
        >
          {uploadMutation.isPending ? (
            <>
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Uploading...
            </>
          ) : (
            'Upload'
          )}
        </button>
      </div>
    </div>
  );
}; 