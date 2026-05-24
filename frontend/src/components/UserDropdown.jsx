/**
 * UserDropdown Component
 * Shared user selector with cold-start toggle
 */

import React from 'react';

const UserDropdown = ({
  users,
  selectedUser,
  onUserChange,
  isColdStart,
  onColdStartToggle,
  personaText,
  onPersonaChange
}) => {
  return (
    <div className="space-y-4">
      {/* Cold Start Toggle */}
      <div className="flex items-center gap-3">
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={isColdStart}
            onChange={(e) => onColdStartToggle(e.target.checked)}
            className="w-5 h-5 text-naija-green border-gray-300 rounded focus:ring-naija-green"
          />
          <span className="ml-2 text-sm font-medium text-gray-700">
            Cold Start (Free Text Persona)
          </span>
        </label>
      </div>

      {/* User Dropdown or Persona Input */}
      {!isColdStart ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Demo User
          </label>
          <select
            value={selectedUser}
            onChange={(e) => onUserChange(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naija-green focus:border-transparent"
          >
            <option value="">Choose a user...</option>
            {users.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.display_name} - {user.name}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Describe Your Persona
          </label>
          <textarea
            value={personaText}
            onChange={(e) => onPersonaChange(e.target.value)}
            placeholder="E.g., I'm a budget-conscious foodie who loves spicy Nigerian food and good vibes..."
            rows="4"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-naija-green focus:border-transparent resize-none"
          />
          <p className="mt-2 text-xs text-gray-500">
            Describe your preferences, style, and what you look for in restaurants
          </p>
        </div>
      )}
    </div>
  );
};

export default UserDropdown;
