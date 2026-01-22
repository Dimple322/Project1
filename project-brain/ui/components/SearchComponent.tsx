'use client';

import { FormEvent, useState } from 'react';
import { Search, Loader, Send } from 'lucide-react';

interface SearchResult {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
  page_number?: number;
}

interface AskResponse {
  answer: string;
  sources: Array<{ filename: string; doc_id: string; score: number }>;
  context_chunks: number;
  status: string;
}

export default function SearchComponent() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [mode, setMode] = useState<'search' | 'ask'>('search');
  const [askResponse, setAskResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setIsLoading(true);
      setHasSearched(true);
      setError(null);
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/search`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, limit: 10 }),
          credentials: 'include',
        }
      );

      if (!response.ok) throw new Error(`Search failed: ${response.statusText}`);
      
      const data = await response.json();
      setResults(data.results || []);
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'Search failed');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAsk = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setIsLoading(true);
      setHasSearched(true);
      setError(null);
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/ask`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: query, max_context_chunks: 3 }),
          credentials: 'include',
        }
      );

      if (!response.ok) throw new Error(`Ask failed: ${response.statusText}`);
      
      const data = await response.json();
      setAskResponse(data);
    } catch (err: any) {
      console.error('Ask error:', err);
      setError(err.message || 'Ask failed');
      setAskResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Search & Ask</h2>
        
        {/* Mode Selector */}
        <div className="mb-4 flex gap-2">
          <button
            onClick={() => {
              setMode('search');
              setAskResponse(null);
              setResults([]);
            }}
            className={`px-4 py-2 rounded-md font-medium transition flex items-center gap-2 ${
              mode === 'search'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <Search size={18} />
            Search Documents
          </button>
          <button
            onClick={() => {
              setMode('ask');
              setResults([]);
            }}
            className={`px-4 py-2 rounded-md font-medium transition flex items-center gap-2 ${
              mode === 'ask'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <Send size={18} />
            Ask with RAG
          </button>
        </div>
        
        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded-md text-sm mb-4 border border-red-200">
            ? Error: {error}
          </div>
        )}
        
        {/* Search/Ask Form */}
        <form onSubmit={mode === 'search' ? handleSearch : handleAsk} className="flex gap-2 mb-6">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={mode === 'search' ? "Search documents..." : "Ask a question about documents..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2 transition"
          >
            {isLoading ? (
              <>
                <Loader className="animate-spin" size={18} />
                {mode === 'search' ? 'Searching...' : 'Asking...'}
              </>
            ) : mode === 'search' ? (
              <>
                <Search size={18} />
                Search
              </>
            ) : (
              <>
                <Send size={18} />
                Ask
              </>
            )}
          </button>
        </form>

        {/* Search Results */}
        {mode === 'search' && hasSearched && (
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-700">
              {results.length === 0 ? 'No results found' : `${results.length} Results Found`}
            </h3>
            <div className="space-y-3">
              {results.map((result, idx) => (
                <div 
                  key={idx} 
                  className="p-4 bg-gray-50 rounded-md border-l-4 border-blue-600 hover:shadow-md transition"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium text-blue-600">
                      Relevance: {(result.score * 100).toFixed(0)}%
                    </span>
                    {result.page_number && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        Page {result.page_number}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-4 mb-2">{result.text}</p>
                  <p className="text-xs text-gray-500">
                    ?? Doc: {result.document_id.substring(0, 12)}... | ?? Chunk: {result.chunk_id.substring(0, 12)}...
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Ask Results (RAG) */}
        {mode === 'ask' && askResponse && (
          <div className="space-y-4">
            {/* Answer */}
            <div className="p-4 bg-green-50 rounded-md border-l-4 border-green-600">
              <h3 className="font-semibold text-green-900 mb-2">?? Answer</h3>
              <p className="text-green-800 whitespace-pre-wrap leading-relaxed">{askResponse.answer}</p>
            </div>

            {/* Sources */}
            {askResponse.sources && askResponse.sources.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-700 mb-2">?? Sources</h3>
                <div className="space-y-2">
                  {askResponse.sources.map((source, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded border border-gray-200">
                      <p className="font-medium text-gray-700">{source.filename}</p>
                      <p className="text-xs text-gray-500">Relevance: {(source.score * 100).toFixed(0)}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="p-2 bg-blue-50 rounded text-xs text-gray-600 border-l-2 border-blue-300">
              Status: <span className="font-medium">{askResponse.status}</span> | 
              Context chunks used: <span className="font-medium">{askResponse.context_chunks}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
