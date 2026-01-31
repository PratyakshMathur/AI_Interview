import React from 'react';
import RecruiterDashboard from './RecruiterDashboard';
import { useNavigate } from 'react-router-dom';

const RecruiterPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="relative">
      <button
        onClick={() => navigate('/')}
        className="absolute top-4 left-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-md transition-colors z-10"
      >
        ← Back to Home
      </button>
      <RecruiterDashboard />
    </div>
  );
};

export default RecruiterPage;
