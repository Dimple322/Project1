'use client';

import { useState, ChangeEvent, FormEvent } from 'react';
import { Upload, Loader } from 'lucide-react';
import { useFileUpload } from '@/lib/hooks';

export default function DocumentUpload({ onSuccess }: { onSuccess?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const { upload, isLoading, error, progress } = useFileUpload({ onSuccess });

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    try {
      await upload(file);
      setFile(null);
    } catch (err) {
      console.error('Upload error:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-4">Upload Document</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
          <label className="cursor-pointer flex flex-col items-center">
            <Upload className="text-gray-400 mb-2" size={32} />
            <span className="text-gray-600">Click to select or drag file</span>
            <input
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".pdf,.txt,.md"
              disabled={isLoading}
            />
          </label>
          {file && (
            <div className="mt-4 text-sm text-gray-700">
              Selected: <strong>{file.name}</strong>
            </div>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        {progress > 0 && progress < 100 && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <button
          type="submit"
          disabled={!file || isLoading}
          className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader className="animate-spin" size={18} />
              Uploading...
            </>
          ) : (
            <>
              <Upload size={18} />
              Upload
            </>
          )}
        </button>
      </form>
    </div>
  );
}
