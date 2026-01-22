'use client';

import { useEffect, useState } from 'react';
import { reportAPI } from '@/lib/api';
import { Loader, AlertCircle } from 'lucide-react';

interface StatusCard {
  subject_id: string;
  subject_type: string;
  subject_name: string;
  summary: {
    status: string;
    progress: number;
    issues: number;
    blockers: number;
  };
}

export default function ReportsPage() {
  const [reports, setReports] = useState<StatusCard[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setIsLoading(true);
        // Fetch reports data
        // const response = await reportAPI.list();
        // setReports(response.data.reports || []);
        setReports([]);
      } catch (err: any) {
        setError(err.message || 'Failed to load reports');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin text-blue-600" size={32} />
        <span className="ml-2 text-gray-600">Loading reports...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-md flex gap-2">
        <AlertCircle size={20} />
        <div>Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Total Reports</h3>
          <p className="text-3xl font-bold text-gray-900">{reports.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Active Issues</h3>
          <p className="text-3xl font-bold text-red-600">
            {reports.reduce((sum, r) => sum + (r.summary?.issues || 0), 0)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-600 text-sm font-medium">Blockers</h3>
          <p className="text-3xl font-bold text-orange-600">
            {reports.reduce((sum, r) => sum + (r.summary?.blockers || 0), 0)}
          </p>
        </div>
      </div>

      {reports.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No reports available yet
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.subject_id} className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900">
                {report.subject_name}
              </h3>
              <p className="text-sm text-gray-600">Type: {report.subject_type}</p>
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-600">Status</p>
                  <p className="text-lg font-semibold">{report.summary?.status}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Progress</p>
                  <p className="text-lg font-semibold">{report.summary?.progress}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Issues</p>
                  <p className="text-lg font-semibold text-red-600">
                    {report.summary?.issues}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Blockers</p>
                  <p className="text-lg font-semibold text-orange-600">
                    {report.summary?.blockers}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
