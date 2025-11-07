import { useState } from 'react';
import { FileUpload } from './FileUpload';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface FileUploadSectionProps {
  onUploadSuccess: () => void;
}

export const FileUploadSection: React.FC<FileUploadSectionProps> = ({ onUploadSuccess }) => {
  const [resetKey, setResetKey] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  const handleUploadSuccess = () => {
    onUploadSuccess();
    setResetKey(prev => prev + 1);
  };

  const handleClose = () => {
    setIsVisible(false);
  };

  const handleReopen = () => {
    setIsVisible(true);
  };

  if (!isVisible) {
    return (
      <div className="abnormal-card p-4">
        <button
          onClick={handleReopen}
          className="w-full flex items-center justify-center py-3 px-4 border border-primary-500 rounded-md shadow-sm text-sm font-medium text-primary-300 bg-slate-700 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200"
        >
          <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          Show Upload Section
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={handleClose}
        className="absolute top-4 right-4 z-10 p-2 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors duration-200"
        aria-label="Close upload section"
      >
        <XMarkIcon className="h-5 w-5" />
      </button>
      <FileUpload key={resetKey} onUploadSuccess={handleUploadSuccess} />
    </div>
  );
};
