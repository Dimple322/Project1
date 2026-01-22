'use client';

import { useState, useEffect } from 'react';

interface StatusReport {
  entity_id: string;
  entity_name: string;
  entity_type: string;
  state: any;
  conflicts: any[];
  summary: {
    total_claims: number;
    open_issues: number;
    open_actions: number;
    decisions: number;
    conflicts_count: number;
    health_score: number;
  };
}

export function StatusDashboard({ entityId }: { entityId: string }) {
  const [report, setReport] = useState<StatusReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConflict, setSelectedConflict] = useState<any>(null);
  const [resolvingConflict, setResolvingConflict] = useState<any>(null);

  useEffect(() => {
    fetchStatusReport();
  }, [entityId]);

  const fetchStatusReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/state/report/${entityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      
      if (!res.ok) throw new Error('Failed to fetch report');
      const data = await res.json();
      setReport(data.report);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleResolveConflict = async (conflictIndex: number, chosenValue: any) => {
    if (!report) return;

    const conflict = report.conflicts[conflictIndex];
    
    try {
      setResolvingConflict(conflictIndex);
      const res = await fetch(`/api/state/conflicts/${entityId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          field_path: conflict.field_path,
          chosen_value: chosenValue,
          reason: 'Manual resolution',
        })
      });

      if (res.ok) {
        setSelectedConflict(null);
        await fetchStatusReport();
      }
    } catch (error) {
      console.error('Failed to resolve conflict:', error);
    } finally {
      setResolvingConflict(null);
    }
  };

  if (loading) return <p className="text-center text-gray-500">Loading status report...</p>;
  if (error) return <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>;
  if (!report) return <p className="text-center text-gray-500">No report available</p>;

  return (
    <div className="space-y-4">
      <div className="border-b pb-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Status: {report.entity_name}</h2>
          <span className="text-3xl font-bold">
            {Math.round(report.summary.health_score * 100)}%
          </span>
        </div>
      </div>

      {/* Health Score Visualization */}
      <div className="border rounded p-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${report.summary.health_score * 100}%` }}
          />
        </div>
        <p className="text-sm text-gray-600 mt-2">Health Score</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        <div className="border rounded p-3">
          <p className="text-2xl font-bold">{report.summary.total_claims}</p>
          <p className="text-xs text-gray-600">Claims</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-2xl font-bold text-red-600">{report.summary.open_issues}</p>
          <p className="text-xs text-gray-600">Issues</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-2xl font-bold text-orange-600">{report.summary.open_actions}</p>
          <p className="text-xs text-gray-600">Actions</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-2xl font-bold">{report.summary.decisions}</p>
          <p className="text-xs text-gray-600">Decisions</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-2xl font-bold text-yellow-600">{report.summary.conflicts_count}</p>
          <p className="text-xs text-gray-600">Conflicts</p>
        </div>
      </div>

      {/* Claims */}
      {Object.keys(report.state.claims || {}).length > 0 && (
        <div className="border rounded">
          <div className="border-b p-4">
            <h3 className="font-bold">Claims</h3>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {Object.entries(report.state.claims).map(([field, info]: [string, any]) => (
                <div key={field} className="p-2 bg-gray-50 rounded">
                  <p className="font-semibold text-sm">{field}</p>
                  <p className="text-sm text-gray-700">{info.value}</p>
                  <div className="flex gap-1 mt-1">
                    <span className={`text-xs px-2 py-1 rounded ${
                      info.confidence > 0.8 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {Math.round(info.confidence * 100)}%
                    </span>
                    {info.competing_claims && (
                      <span className="text-xs px-2 py-1 rounded bg-red-100 text-red-700">
                        Competing claims
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Conflicts */}
      {report.conflicts.length > 0 && (
        <div className="border border-yellow-300 bg-yellow-50 rounded">
          <div className="border-b border-yellow-300 p-4">
            <h3 className="font-bold text-yellow-900">Conflicts</h3>
          </div>
          <div className="p-4 space-y-2">
            {report.conflicts.map((conflict, idx) => (
              <div key={idx} className="p-2 bg-white rounded border border-yellow-200">
                <p className="font-semibold text-sm">{conflict.field_path}</p>
                <p className="text-sm text-gray-600 mt-1">
                  Competing values: {conflict.competing_values.join(', ')}
                </p>
                <button
                  onClick={() => setSelectedConflict(idx)}
                  className="mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                >
                  Resolve
                </button>
                
                {/* Conflict Resolution Modal */}
                {selectedConflict === idx && (
                  <ConflictResolutionModal
                    conflict={conflict}
                    onResolve={(value) => handleResolveConflict(idx, value)}
                    onCancel={() => setSelectedConflict(null)}
                    resolving={resolvingConflict === idx}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <button
        onClick={fetchStatusReport}
        className="w-full px-4 py-2 border rounded hover:bg-gray-100"
      >
        Refresh Report
      </button>
    </div>
  );
}

function ConflictResolutionModal({
  conflict,
  onResolve,
  onCancel,
  resolving
}: {
  conflict: any;
  onResolve: (value: any) => void;
  onCancel: () => void;
  resolving: boolean;
}) {
  const [chosen, setChosen] = useState<any>(null);

  return (
    <div className="mt-3 p-3 bg-white border rounded">
      <p className="font-semibold text-sm mb-2">Choose correct value:</p>
      <div className="space-y-1 mb-3">
        {conflict.competing_values.map((value: any, idx: number) => (
          <label key={idx} className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={chosen === value}
              onChange={() => setChosen(value)}
              className="w-4 h-4"
            />
            <span className="text-sm">{String(value)}</span>
          </label>
        ))}
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onResolve(chosen)}
          disabled={chosen === null || resolving}
          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {resolving ? 'Resolving...' : 'Resolve'}
        </button>
        <button
          onClick={onCancel}
          disabled={resolving}
          className="px-3 py-1 border rounded text-sm hover:bg-gray-100 disabled:bg-gray-200"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
