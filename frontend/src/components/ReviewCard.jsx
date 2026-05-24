/**
 * ReviewCard Component
 * Displays generated review with Nigerian styling
 */

import React from 'react';
import StarRating from './StarRating';

const ReviewCard = ({ stars, reviewText, styleNote }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-naija-green">
      {/* Stars */}
      <div className="mb-4">
        <StarRating rating={stars} />
      </div>

      {/* Review Text */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
          Generated Review
        </h3>
        <p className="text-gray-800 text-lg leading-relaxed whitespace-pre-wrap">
          {reviewText}
        </p>
      </div>

      {/* Style Note */}
      {styleNote && (
        <div className="pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 italic">
            <span className="font-semibold">Style Note:</span> {styleNote}
          </p>
        </div>
      )}

      {/* Nigerian Flag Emoji */}
      <div className="mt-4 text-right">
        <span className="text-2xl">🇳🇬</span>
      </div>
    </div>
  );
};

export default ReviewCard;
