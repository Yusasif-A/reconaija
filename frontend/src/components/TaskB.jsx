/**
 * Task B Component - Recommendations
 * Recommends restaurants based on user preferences
 */

import React, { useState } from 'react';
import UserDropdown from './UserDropdown';
import { getRecommendations } from '../api';

const TaskB = ({ users }) => {
  const [selectedUser, setSelectedUser] = useState('');
  const [isColdStart, setIsColdStart] = useState(false);
  const [personaText, setPersonaText] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRecommend = async () => {
    // Validation
    if (!isColdStart && !selectedUser) {
      setError('Please select a user or enable cold start mode');
      return;
    }

    if (isColdStart && !personaText.trim()) {
      setError('Please describe your persona');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const data = {
        user_id: isColdStart ? 'cold_start' : selectedUser,
        persona_text: personaText,
        top_k: topK
      };

      const response = await getRecommendations(data);
      setResult(response);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-naija-green rounded-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Task B: Get Recommendations</h2>
        <p className="text-green-100">
          Discover the best Nigerian restaurants based on your preferences
        </p>
      </div>

      {/* User Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <UserDropdown
          users={users}
          selectedUser={selectedUser}
          onUserChange={setSelectedUser}
          isColdStart={isColdStart}
          onColdStartToggle={setIsColdStart}
          personaText={personaText}
          onPersonaChange={setPersonaText}
        />
      </div>

      {/* Number of Recommendations */}
      <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Recommendations
          </label>
          <input
            type="range"
            min="3"
            max="10"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-naija-green"
          />
          <div className="flex justify-between text-sm text-gray-600 mt-2">
            <span>3</span>
            <span className="font-semibold text-naija-green">{topK}</span>
            <span>10</span>
          </div>
        </div>

        {/* Recommend Button */}
        <button
          onClick={handleRecommend}
          disabled={loading}
          className="w-full bg-naija-green hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Finding Recommendations...
            </span>
          ) : (
            'Get Recommendations'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Mode Badge */}
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              result.mode === 'history_based'
                ? 'bg-blue-100 text-blue-800'
                : 'bg-purple-100 text-purple-800'
            }`}>
              {result.mode === 'history_based' ? '📊 Based on Review History' : '🆕 Cold-Start'}
            </span>
          </div>

          {/* Recommendations */}
          <div className="space-y-3">
            {result.recommendations.map((rec, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow-md overflow-hidden border-l-4 border-naija-green hover:shadow-lg transition duration-200"
              >
                <div className="flex items-start gap-4 p-5">
                  <div className="flex-shrink-0 w-10 h-10 bg-naija-green text-white rounded-full flex items-center justify-center font-bold text-lg">
                    {index + 1}
                  </div>

                  {/* Category icon */}
                  <div className="flex-shrink-0 w-16 h-16 bg-green-50 rounded-lg flex items-center justify-center text-2xl">
                    {rec.category?.toLowerCase().includes('bar') || rec.category?.toLowerCase().includes('nightlife') ? '🍸' :
                     rec.category?.toLowerCase().includes('cafe') || rec.category?.toLowerCase().includes('coffee') ? '☕' :
                     rec.category?.toLowerCase().includes('pizza') ? '🍕' :
                     rec.category?.toLowerCase().includes('fast food') ? '🍗' :
                     rec.category?.toLowerCase().includes('bakery') || rec.category?.toLowerCase().includes('bakeries') ? '🧁' :
                     '🍽️'}
                  </div>

                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-800 mb-1">
                      {rec.name}
                    </h3>
                    <p className="text-sm text-gray-500 mb-2">
                      {rec.category}
                    </p>
                    <p className="text-gray-700 leading-relaxed">
                      {rec.reason}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Nigerian Flag */}
          <div className="text-center">
            <span className="text-3xl">🇳🇬</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskB;
