import React from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            🎯 AI Interview Platform
          </h1>
          <p className="text-xl text-gray-600">
            Choose your role to get started
          </p>
        </div>

        {/* Role Selection Cards */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* Candidate Card */}
          <div
            onClick={() => navigate('/candidate')}
            className="bg-white rounded-2xl shadow-xl p-8 cursor-pointer transform transition-all hover:scale-105 hover:shadow-2xl border-2 border-transparent hover:border-blue-500"
          >
            <div className="text-center">
              <div className="text-6xl mb-4">👨‍💻</div>
              <h2 className="text-3xl font-bold text-gray-900 mb-3">
                Candidate
              </h2>
              <p className="text-gray-600 mb-6">
                Take the AI-powered coding interview
              </p>
              
              <div className="space-y-2 text-left mb-6">
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Interactive coding environment
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Jupyter-style notebooks
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  Python & SQL support
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-green-500 mr-2">✓</span>
                  AI assistant for guidance
                </div>
              </div>

              <button className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                Start Interview →
              </button>
            </div>
          </div>

          {/* Recruiter Card */}
          <div
            onClick={() => navigate('/recruiter')}
            className="bg-white rounded-2xl shadow-xl p-8 cursor-pointer transform transition-all hover:scale-105 hover:shadow-2xl border-2 border-transparent hover:border-purple-500"
          >
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-3xl font-bold text-gray-900 mb-3">
                Recruiter
              </h2>
              <p className="text-gray-600 mb-6">
                View analytics and candidate performance
              </p>
              
              <div className="space-y-2 text-left mb-6">
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-purple-500 mr-2">✓</span>
                  Real-time session monitoring
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-purple-500 mr-2">✓</span>
                  Behavioral analytics
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-purple-500 mr-2">✓</span>
                  AI interaction tracking
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <span className="text-purple-500 mr-2">✓</span>
                  Performance insights
                </div>
              </div>

              <button className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 transition-colors">
                View Dashboard →
              </button>
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-12 text-center text-sm text-gray-600">
          <p>
            Powered by AI • Real-time Analytics • Behavioral Insights
          </p>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
