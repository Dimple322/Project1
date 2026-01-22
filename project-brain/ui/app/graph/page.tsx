'use client';

import KnowledgeGraph from '@/components/KnowledgeGraph';

export default function GraphPage() {
  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Knowledge Graph</h1>
      <p className="text-gray-600">
        Visualize relationships between documents, entities, and extracted information
      </p>
      <KnowledgeGraph />
    </div>
  );
}
