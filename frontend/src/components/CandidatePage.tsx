import React, { useState } from 'react';
import SessionSetup from './SessionSetup';
import CandidateWorkspace from './CandidateWorkspace';
import ErrorBoundary from './ErrorBoundary';
import { apiService, SessionCreate, Session } from '../services/api';
import { useNavigate } from 'react-router-dom';

type InterviewState = 'setup' | 'interview' | 'completed';

interface InterviewData {
  session?: Session;
  error?: string;
}

const CandidatePage: React.FC = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<InterviewState>('setup');
  const [data, setData] = useState<InterviewData>({});
  const [loading, setLoading] = useState(false);

  const handleSessionCreate = async (sessionData: SessionCreate) => {
    setLoading(true);
    try {
      const session = await apiService.createSession(sessionData);
      setData({ session });
      setState('interview');
      console.log('Session created:', session);
    } catch (error) {
      console.error('Failed to create session:', error);
      setData({ error: 'Failed to create interview session. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleEndSession = async () => {
    if (data.session) {
      setLoading(true);
      try {
        await apiService.completeSession(data.session.session_id);
        setState('completed');
      } catch (error) {
        console.error('Failed to complete session:', error);
        setState('completed');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleStartNew = () => {
    setData({});
    setState('setup');
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {state === 'setup' ? 'Creating interview session...' : 'Completing session...'}
          </p>
        </div>
      </div>
    );
  }

  if (state === 'setup') {
    return (
      <ErrorBoundary>
        <div className="relative">
          <button
            onClick={handleBackToHome}
            className="absolute top-4 left-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-md transition-colors z-10"
          >
            ← Back to Home
          </button>
          <SessionSetup onSessionCreate={handleSessionCreate} />
          {data.error && (
            <div className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {data.error}
            </div>
          )}
        </div>
      </ErrorBoundary>
    );
  }

  if (state === 'interview' && data.session) {
    return (
      <ErrorBoundary>
        <CandidateWorkspace
          session={data.session}
          onEndSession={handleEndSession}
        />
      </ErrorBoundary>
    );
  }

  if (state === 'completed') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="text-6xl mb-4">✓</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            Interview Session Completed
          </h1>
          <p className="text-gray-600 mb-6">
            Thank you for completing the interview. Your session has been saved and is now being analyzed.
          </p>
          <div className="space-y-3">
            <button
              onClick={handleStartNew}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Start New Interview
            </button>
            <button
              onClick={handleBackToHome}
              className="w-full px-6 py-3 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default CandidatePage;
