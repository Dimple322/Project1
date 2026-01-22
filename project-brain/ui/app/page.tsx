'use client';

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg shadow-lg p-8">
        <h1 className="text-4xl font-bold mb-4">?? Project Brain</h1>
        <p className="text-lg text-blue-100">
          AI-powered document analysis and entity management system for project intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <FeatureCard
          title="Document Management"
          description="Upload and analyze documents with automatic parsing and chunking"
          icon="??"
          href="/documents"
        />
        <FeatureCard
          title="Intelligent Search"
          description="Search across all documents using semantic understanding"
          icon="??"
          href="/search"
        />
        <FeatureCard
          title="Entity Catalog"
          description="Manage projects, facilities, wells, and subsystems"
          icon="??"
          href="/entities"
        />
        <FeatureCard
          title="Pending Review"
          description="Review and approve AI-extracted items with confidence scores"
          icon="?"
          href="/pending-review"
        />
        <FeatureCard
          title="Status Reports"
          description="Generate comprehensive status cards with claims and evidence"
          icon="??"
          href="/reports"
        />
        <FeatureCard
          title="Knowledge Graph"
          description="Visualize relationships between entities and documents"
          icon="??"
          href="/graph"
        />
      </div>

      <div className="bg-white rounded-lg shadow p-8">
        <h2 className="text-2xl font-bold mb-4">Quick Start</h2>
        <ol className="list-decimal list-inside space-y-2 text-gray-700">
          <li>Upload a document (PDF, DOCX, or TXT)</li>
          <li>Wait for automatic parsing and embedding</li>
          <li>Review extracted issues, actions, and decisions</li>
          <li>Search across documents using natural language</li>
          <li>Generate status reports for your entities</li>
        </ol>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-2">?? Tip</h3>
        <p className="text-gray-700">
          Project Brain uses advanced NLP models (BGE-M3 for embeddings, BGE-Reranker-v2-m3 for ranking) 
          to understand your documents and extract structured information automatically.
        </p>
      </div>
    </div>
  );
}

function FeatureCard({
  title,
  description,
  icon,
  href,
}: {
  title: string;
  description: string;
  icon: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition transform hover:scale-105"
    >
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </a>
  );
}
