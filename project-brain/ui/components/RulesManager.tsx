'use client';

import { useState, useEffect } from 'react';

interface CurationRule {
  id: string;
  rule_type: string;
  priority: number;
  enabled: boolean;
  created_from_event_id?: string;
  created_at: string;
}

export function RulesManager() {
  const [rules, setRules] = useState<CurationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ type: '', enabled: true });
  const [selectedRule, setSelectedRule] = useState<CurationRule | null>(null);

  useEffect(() => {
    fetchRules();
  }, [filter]);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.type) params.append('rule_type', filter.type);
      params.append('enabled', String(filter.enabled));

      const res = await fetch(`/api/rules/?${params.toString()}`);
      const data = await res.json();
      setRules(data.rules || []);
    } catch (error) {
      console.error('Failed to fetch rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRule = async (rule: CurationRule) => {
    try {
      await fetch(`/api/rules/${rule.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !rule.enabled }),
      });
      fetchRules();
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Delete this rule?')) return;
    try {
      await fetch(`/api/rules/${ruleId}`, { method: 'DELETE' });
      fetchRules();
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold">Curation Rules</h2>
      </div>

      {/* Filters */}
      <div className="flex gap-4 p-4 bg-gray-50 rounded">
        <select
          value={filter.type}
          onChange={(e) => setFilter({ ...filter, type: e.target.value })}
          className="px-3 py-2 border rounded"
        >
          <option value="">All Types</option>
          <option value="LINK_FIX_RULE">Link Fix</option>
          <option value="LEXICON_NORMALIZATION_RULE">Lexicon Normalization</option>
          <option value="PARSING_ANCHOR_RULE">Parsing Anchor</option>
          <option value="CLAIM_OVERRIDE_RULE">Claim Override</option>
        </select>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={filter.enabled}
            onChange={(e) => setFilter({ ...filter, enabled: e.target.checked })}
          />
          <span className="text-sm">Enabled Only</span>
        </label>
      </div>

      {/* Rules List */}
      <div className="space-y-2">
        {loading ? (
          <p className="text-center text-gray-500">Loading...</p>
        ) : rules.length === 0 ? (
          <p className="text-center text-gray-500">No rules found</p>
        ) : (
          rules.map((rule) => (
            <div key={rule.id} className="border rounded p-4 bg-white">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold flex items-center gap-2">
                    {rule.rule_type}
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      rule.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {rule.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Priority: <strong>{rule.priority}</strong>
                  </p>
                  {rule.created_from_event_id && (
                    <p className="text-xs text-gray-500 mt-1">
                      From event: {rule.created_from_event_id}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleRule(rule)}
                    className="px-3 py-1 border rounded text-sm hover:bg-gray-100"
                  >
                    {rule.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => setSelectedRule(rule)}
                    className="px-3 py-1 border rounded text-sm hover:bg-gray-100"
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleDeleteRule(rule.id)}
                    className="px-3 py-1 border rounded text-sm hover:bg-red-50 text-red-600"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Rule Details Modal */}
      {selectedRule && (
        <RuleDetailsModal
          rule={selectedRule}
          onClose={() => setSelectedRule(null)}
        />
      )}
    </div>
  );
}

function RuleDetailsModal({ rule, onClose }: { rule: CurationRule; onClose: () => void }) {
  const [ruleDetails, setRuleDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuleDetails();
  }, [rule.id]);

  const fetchRuleDetails = async () => {
    try {
      const res = await fetch(`/api/rules/${rule.id}`);
      const data = await res.json();
      setRuleDetails(data);
    } catch (error) {
      console.error('Failed to fetch rule details:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-96 overflow-auto">
        <div className="border-b p-4">
          <h2 className="text-xl font-bold">{rule.rule_type}</h2>
        </div>
        <div className="p-4 space-y-4">
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : (
            <>
              <div>
                <h4 className="font-semibold mb-2">Payload</h4>
                <pre className="bg-gray-100 p-2 rounded text-xs overflow-auto">
                  {JSON.stringify(ruleDetails?.payload, null, 2)}
                </pre>
              </div>
              {ruleDetails?.test_cases && ruleDetails.test_cases.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Test Cases ({ruleDetails.test_cases.length})</h4>
                  <div className="space-y-1 text-sm">
                    {ruleDetails.test_cases.map((tc: any, idx: number) => (
                      <p key={idx} className="text-gray-600">
                        {tc.description || `Test ${idx + 1}`}
                      </p>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex justify-end gap-2">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border rounded hover:bg-gray-100"
                >
                  Close
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
