import { useState } from 'react';
import { FileList } from './components/FileList';
import { StorageStats } from './components/StorageStats';
import { FileUploadSection } from './components/FileUploadSection';

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-gradient-to-r from-slate-800 to-slate-900 shadow-xl border-b border-slate-700">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-100">Abnormal Security - File Hub</h1>
            </div>
            <div className="hidden sm:block">
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="space-y-8">
            <StorageStats />
            <div className="abnormal-card">
              <FileUploadSection onUploadSuccess={handleUploadSuccess} />
            </div>
            <div className="abnormal-card p-4">
              <FileList key={refreshKey} />
            </div>
          </div>
        </div>
      </main>
      <footer className="bg-slate-800 shadow-xl border-t border-slate-700 mt-8">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-slate-400">
            © 2025 File Hub. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
