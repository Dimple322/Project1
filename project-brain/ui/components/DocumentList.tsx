'use client';

import { useEffect, useState } from 'react';
import { documentAPI } from '@/lib/api';
import { FileText, Loader } from 'lucide-react';

export default function DocumentList() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setIsLoading(true);
        const response = await documentAPI.list();
        setDocuments(response.data.documents || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load documents');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin text-blue-600" size={32} />
        <span className="ml-2 text-gray-600">Loading documents...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-md">
        Error: {error}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No documents uploaded yet. Start by uploading a document above.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="border rounded-lg p-4 hover:bg-gray-50 transition"
        >
          <div className="flex items-start gap-3">
            <FileText className="text-blue-600 mt-1" size={24} />
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">{doc.filename}</h3>
              <p className="text-sm text-gray-600">
                {(doc.file_size / 1024).toFixed(2)} KB
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Created: {new Date(doc.created_at).toLocaleString()}
              </p>
            </div>
            <div className="text-right">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                doc.parsing_status === 'completed'
                  ? 'bg-green-100 text-green-800'
                  : doc.parsing_status === 'failed'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {doc.parsing_status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
