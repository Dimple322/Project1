'use client';

import { useState, useEffect } from 'react';

interface RegistryEntity {
  id: string;
  canonical_name: string;
  type: string;
  aliases: string[];
  status: string;
  owner_person_id?: string;
  parent_id?: string;
}

export function RegistryManager() {
  const [entities, setEntities] = useState<RegistryEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ type: '', status: 'active', q: '' });
  const [selectedEntity, setSelectedEntity] = useState<RegistryEntity | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchEntities();
  }, [filter]);

  const fetchEntities = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.type) params.append('entity_type', filter.type);
      if (filter.status) params.append('status', filter.status);
      if (filter.q) params.append('q', filter.q);

      const res = await fetch(`/api/registry/entities?${params.toString()}`);
      const data = await res.json();
      setEntities(data);
    } catch (error) {
      console.error('Failed to fetch entities:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEntityClick = (entity: RegistryEntity) => {
    setSelectedEntity(entity);
    setShowForm(true);
  };

  return (
    <div className="space-y-4">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold">Project Registry</h2>
      </div>

      {/* Filters */}
      <div className="flex gap-4 p-4 bg-gray-50 rounded">
        <input
          type="text"
          placeholder="Search entities..."
          value={filter.q}
          onChange={(e) => setFilter({ ...filter, q: e.target.value })}
          className="flex-1 px-3 py-2 border rounded"
        />
        <select
          value={filter.type}
          onChange={(e) => setFilter({ ...filter, type: e.target.value })}
          className="px-3 py-2 border rounded"
        >
          <option value="">All Types</option>
          <option value="facility">Facility</option>
          <option value="well">Well</option>
          <option value="subsystem">Subsystem</option>
          <option value="contractor">Contractor</option>
          <option value="person">Person</option>
          <option value="phase">Phase</option>
        </select>
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="px-3 py-2 border rounded"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="pending">Pending</option>
        </select>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + Add Entity
        </button>
      </div>

      {/* Entity List */}
      <div className="grid gap-2">
        {loading ? (
          <p className="text-center text-gray-500">Loading...</p>
        ) : entities.length === 0 ? (
          <p className="text-center text-gray-500">No entities found</p>
        ) : (
          entities.map((entity) => (
            <div
              key={entity.id}
              className="border rounded p-4 cursor-pointer hover:bg-blue-50"
              onClick={() => handleEntityClick(entity)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{entity.canonical_name}</h3>
                  <p className="text-sm text-gray-600">{entity.type}</p>
                  {entity.aliases.length > 0 && (
                    <p className="text-xs text-gray-500">
                      Aliases: {entity.aliases.join(', ')}
                    </p>
                  )}
                </div>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  entity.status === 'active' ? 'bg-green-100 text-green-800' :
                  entity.status === 'archived' ? 'bg-gray-100 text-gray-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {entity.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Entity Form Modal */}
      {showForm && (
        <EntityForm
          entity={selectedEntity}
          onClose={() => {
            setShowForm(false);
            setSelectedEntity(null);
            fetchEntities();
          }}
        />
      )}
    </div>
  );
}

function EntityForm({ entity, onClose }: { entity: RegistryEntity | null; onClose: () => void }) {
  const [formData, setFormData] = useState({
    canonical_name: entity?.canonical_name || '',
    type: entity?.type || 'facility',
    aliases: entity?.aliases.join(', ') || '',
    description: '',
    status: entity?.status || 'active',
  });

  const handleSubmit = async () => {
    try {
      const url = entity
        ? `/api/registry/entities/${entity.id}`
        : '/api/registry/entities';

      const method = entity ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          aliases: formData.aliases.split(',').map(s => s.trim()),
        }),
      });

      if (response.ok) {
        onClose();
      }
    } catch (error) {
      console.error('Failed to save entity:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md">
        <div className="border-b p-4">
          <h2 className="text-xl font-bold">{entity ? 'Edit Entity' : 'New Entity'}</h2>
        </div>
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={formData.canonical_name}
              onChange={(e) => setFormData({ ...formData, canonical_name: e.target.value })}
              className="w-full px-3 py-2 border rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="w-full px-3 py-2 border rounded"
            >
              <option value="facility">Facility</option>
              <option value="well">Well</option>
              <option value="subsystem">Subsystem</option>
              <option value="contractor">Contractor</option>
              <option value="person">Person</option>
              <option value="phase">Phase</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Aliases (comma-separated)</label>
            <input
              type="text"
              value={formData.aliases}
              onChange={(e) => setFormData({ ...formData, aliases: e.target.value })}
              className="w-full px-3 py-2 border rounded"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
