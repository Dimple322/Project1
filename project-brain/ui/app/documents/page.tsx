'use client';

import DocumentUpload from '@/components/DocumentUpload';
import DocumentList from '@/components/DocumentList';
import { useState } from 'react';

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Documents</h1>
      <DocumentUpload onSuccess={() => setRefreshKey(p => p + 1)} />
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Document List</h2>
        <DocumentList key={refreshKey} />
      </div>
    </div>
  );
}
