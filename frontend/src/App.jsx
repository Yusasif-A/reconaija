/**
 * Main App Component
 * RecoNaija - Nigerian Yelp Review Agent
 */

import React, { useState, useEffect } from 'react';
import TaskA from './components/TaskA';
import TaskB from './components/TaskB';
import { getDemoUsers } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('task-a');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch demo users on mount
    const fetchUsers = async () => {
      try {
        const data = await getDemoUsers();
        setUsers(data);
      } catch (err) {
        setError('Failed to load demo users. Please check if the backend is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            RecoNaija 🇳🇬
          </h1>
          <p className="text-gray-600 text-lg">
            Discover Your Next Favorite Spot
          </p>
        </header>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-naija-green mx-auto mb-4"></div>
            <p className="text-gray-600">Loading demo users...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded mb-6">
            <p className="text-red-700">{error}</p>
            <p className="text-sm text-red-600 mt-2">
              Make sure the backend is running at http://localhost:8000
            </p>
          </div>
        )}

        {/* Main Content */}
        {!loading && !error && (
          <>
            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-md mb-6 p-2 flex gap-2">
              <button
                onClick={() => setActiveTab('task-a')}
                className={`flex-1 py-3 px-6 rounded-lg font-semibold transition duration-200 ${
                  activeTab === 'task-a'
                    ? 'bg-naija-green text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                📝 Simulate Review
              </button>
              <button
                onClick={() => setActiveTab('task-b')}
                className={`flex-1 py-3 px-6 rounded-lg font-semibold transition duration-200 ${
                  activeTab === 'task-b'
                    ? 'bg-naija-green text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                🎯 Get Recommendations
              </button>
            </div>

            {/* Tab Content */}
            <div>
              {activeTab === 'task-a' && <TaskA users={users} />}
              {activeTab === 'task-b' && <TaskB users={users} />}
            </div>
          </>
        )}

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>Built with ❤️ for BCT Hackathon 2026</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
