'use client';

import { useEffect, useState, useRef } from 'react';
import { Network, Loader } from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: string;
  properties: any;
}

interface Edge {
  source: string;
  target: string;
  type: string;
  label: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  total_nodes: number;
  total_edges: number;
  warning?: string;
}

export default function KnowledgeGraph() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchGraph();
  }, []);

  const fetchGraph = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/graph`,
        { credentials: 'include' }
      );

      if (!response.ok) throw new Error(`Failed to fetch graph: ${response.statusText}`);
      
      const data = await response.json();
      setGraph(data);
      setError(null);
    } catch (err: any) {
      console.error('Graph error:', err);
      setError(err.message || 'Failed to load knowledge graph');
      setGraph(null);
    } finally {
      setIsLoading(false);
    }
  };

  const drawSimpleGraph = () => {
    if (!canvasRef.current || !graph || graph.nodes.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const nodeRadius = 20;
    const positions: { [key: string]: { x: number; y: number } } = {};

    // Simple grid layout
    const cols = Math.ceil(Math.sqrt(graph.nodes.length));
    graph.nodes.forEach((node, idx) => {
      const row = Math.floor(idx / cols);
      const col = idx % cols;
      positions[node.id] = {
        x: 50 + col * (canvas.width - 100) / Math.max(1, cols - 1),
        y: 50 + row * (canvas.height - 100) / Math.max(1, Math.ceil(graph.nodes.length / cols) - 1),
      };
    });

    // Draw edges
    ctx.strokeStyle = '#cccccc';
    ctx.lineWidth = 1;
    graph.edges.forEach((edge) => {
      const from = positions[edge.source];
      const to = positions[edge.target];
      if (from && to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      }
    });

    // Draw nodes
    graph.nodes.forEach((node) => {
      const pos = positions[node.id];
      if (!pos) return;

      // Node circle
      ctx.fillStyle = getNodeColor(node.type);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
      ctx.fill();

      // Node label
      ctx.fillStyle = '#000000';
      ctx.font = '10px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const label = node.label.substring(0, 10);
      ctx.fillText(label, pos.x, pos.y);
    });
  };

  const getNodeColor = (type: string): string => {
    const colors: { [key: string]: string } = {
      'document': '#4CAF50',
      'chunk': '#2196F3',
      'entity': '#FF9800',
      'unknown': '#9E9E9E',
    };
    return colors[type] || colors['unknown'];
  };

  // Draw graph after state updates
  useEffect(() => {
    if (canvasRef.current) {
      drawSimpleGraph();
    }
  }, [graph]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Network size={28} />
            Knowledge Graph
          </h2>
          <button
            onClick={fetchGraph}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader className="animate-spin" size={18} />
                Loading...
              </>
            ) : (
              'Refresh'
            )}
          </button>
        </div>

        {error && (
          <div className="p-3 bg-yellow-50 text-yellow-700 rounded-md text-sm border border-yellow-200 mb-4">
            ?? {error}
          </div>
        )}

        {graph && (
          <div className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-blue-50 p-3 rounded text-center">
                <p className="text-2xl font-bold text-blue-600">{graph.total_nodes}</p>
                <p className="text-sm text-gray-600">Nodes</p>
              </div>
              <div className="bg-green-50 p-3 rounded text-center">
                <p className="text-2xl font-bold text-green-600">{graph.total_edges}</p>
                <p className="text-sm text-gray-600">Relationships</p>
              </div>
              <div className="bg-gray-50 p-3 rounded text-center">
                <p className="text-sm text-gray-600">Status</p>
                <p className="text-sm font-medium text-gray-700">
                  {graph.warning ? '?? Limited' : '? Connected'}
                </p>
              </div>
            </div>

            {/* Canvas Graph */}
            <div className="border border-gray-300 rounded-md overflow-hidden">
              <canvas
                ref={canvasRef}
                width={800}
                height={400}
                className="w-full bg-white"
              />
            </div>

            {/* Legend */}
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="font-semibold text-gray-700 mb-2">Legend</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getNodeColor('document') }}></div>
                  <span>Document</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getNodeColor('chunk') }}></div>
                  <span>Chunk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: getNodeColor('entity') }}></div>
                  <span>Entity</span>
                </div>
              </div>
            </div>

            {/* Node List */}
            {graph.nodes.length > 0 && (
              <details className="bg-gray-50 rounded-md p-4">
                <summary className="font-semibold text-gray-700 cursor-pointer">
                  View All Nodes ({graph.nodes.length})
                </summary>
                <div className="mt-3 space-y-2 max-h-48 overflow-y-auto">
                  {graph.nodes.map((node) => (
                    <div key={node.id} className="text-sm p-2 bg-white rounded border border-gray-200">
                      <p className="font-medium text-gray-700">{node.label}</p>
                      <p className="text-xs text-gray-500">{node.type}</p>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
