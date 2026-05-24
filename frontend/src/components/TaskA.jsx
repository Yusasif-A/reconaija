/**
 * Task A Component - Review Generation
 * Simulates how a user would review a restaurant
 */

import React, { useState } from 'react';
import UserDropdown from './UserDropdown';
import ReviewCard from './ReviewCard';
import { generateReview } from '../api';

const TaskA = ({ users }) => {
  const [selectedUser, setSelectedUser] = useState('');
  const [productName, setProductName] = useState('');
  const [productCategory, setProductCategory] = useState('Restaurant');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const categories = [
    'Restaurant',
    'Fast Food',
    'Bar',
    'Cafe',
    'Hotel',
    'Supermarket',
    'Bakery',
    'Other'
  ];

  const handleGenerate = async () => {
    // Validation
    if (!selectedUser) {
      setError('Please select a user');
      return;
    }

    if (!productName.trim()) {
      setError('Please enter a restaurant/place name');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      // Find the selected user's display_name to pass as persona
      const selectedUserObj = users.find(u => u.user_id === selectedUser);
      const userPersona = selectedUserObj ? selectedUserObj.display_name : '';

      const data = {
        user_id: selectedUser,
        persona_text: userPersona,
        product_name: productName,
        product_category: productCategory
      };

      const response = await generateReview(data);
      setResult(response);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-naija-green to-green-600 rounded-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Task A: Simulate a Review</h2>
        <p className="text-green-100">
          Generate an authentic Nigerian review based on a user's style
        </p>
      </div>

      {/* User Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Demo User
        </label>
        <select
          value={selectedUser}
          onChange={(e) => setSelectedUser(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naija-green focus:border-transparent"
        >
          <option value="">-- Choose a user --</option>
          {users.map((user) => (
            <option key={user.user_id} value={user.user_id}>
              {user.display_name}
            </option>
          ))}
        </select>
      </div>

      {/* Restaurant Input */}
      <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Restaurant/Place Name
          </label>
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="E.g., Chicken Republic Lekki, Yellow Chilli..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naija-green focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            value={productCategory}
            onChange={(e) => setProductCategory(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naija-green focus:border-transparent"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full bg-naija-green hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating Review...
            </span>
          ) : (
            'Generate Review'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Generated Review</h3>
          <ReviewCard
            stars={result.stars}
            reviewText={result.review_text}
            styleNote={result.user_style_summary}
          />
        </div>
      )}
    </div>
  );
};

export default TaskA;
