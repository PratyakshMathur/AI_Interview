import React, { useState, useEffect } from 'react';
import { apiService, Session, Feature } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Enhanced ResizeObserver error suppression
const debounce = (func: Function, wait: number) => {
  let timeout: NodeJS.Timeout;
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Error-safe ResponsiveContainer wrapper
const SafeResponsiveContainer: React.FC<{ children: React.ReactNode; width: string | number; height: number }> = ({ children, width, height }) => {
  useEffect(() => {
    // Suppress ResizeObserver errors for chart components
    const handleResizeError = () => {
      // Silently catch ResizeObserver errors
    };
    
    const resizeObserver = new ResizeObserver(handleResizeError);
    const chartContainer = document.querySelector('.recharts-responsive-container');
    if (chartContainer) {
      resizeObserver.observe(chartContainer);
    }
    
    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <ResponsiveContainer width={width as any} height={height}>
      {children}
    </ResponsiveContainer>
  );
};

interface RecruiterDashboardProps {
  sessionId?: string;
  onBack?: () => void;
}

interface Event {
  event_id: string;
  timestamp: string;
  event_type: string;
  metadata: any;
  sequence_number: number;
}

const RecruiterDashboard: React.FC<RecruiterDashboardProps> = ({ sessionId, onBack }) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(sessionId || null);
  const [session, setSession] = useState<Session | null>(null);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Component-level ResizeObserver error suppression
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      if (
        event.message?.includes('ResizeObserver loop') ||
        event.error?.message?.includes('ResizeObserver loop')
      ) {
        event.preventDefault();
        event.stopPropagation();
        return false;
      }
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  useEffect(() => {
    // Suppress ResizeObserver loop errors
    const resizeObserverErrDiv = document.getElementById('webpack-dev-server-client-overlay-div');
    const resizeObserverErr = document.getElementById('webpack-dev-server-client-overlay');
    if (resizeObserverErrDiv) {
      resizeObserverErrDiv.style.display = 'none';
    }
    if (resizeObserverErr) {
      resizeObserverErr.style.display = 'none';
    }
    
    // Handle ResizeObserver errors
    const originalConsoleError = console.error;
    console.error = (...args) => {
      if (args[0] && args[0].toString().includes('ResizeObserver loop limit exceeded')) {
        return;
      }
      originalConsoleError.apply(console, args);
    };

    loadDashboardData();

    return () => {
      console.error = originalConsoleError;
    };
  }, [selectedSessionId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // If no sessionId is selected, load all sessions
      if (!selectedSessionId) {
        const allSessions = await apiService.getAllSessions();
        setSessions(allSessions);
        setLoading(false);
        return;
      }
      
      // Load specific session data
      const [sessionData, featuresData, eventsData] = await Promise.all([
        apiService.getSession(selectedSessionId),
        apiService.getSessionFeatures(selectedSessionId),
        apiService.getSessionEvents(selectedSessionId)
      ]);
      
      setSession(sessionData);
      setFeatures(featuresData);
      setEvents(eventsData);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    if (score >= 0.4) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    if (score >= 0.4) return 'Fair';
    return 'Needs Improvement';
  };

  const formatDuration = (start: string, end?: string) => {
    const startTime = new Date(start).getTime();
    const endTime = end ? new Date(end).getTime() : Date.now();
    const duration = Math.floor((endTime - startTime) / 1000 / 60);
    return `${duration} minutes`;
  };

  const radarData = features.map(feature => ({
    feature: feature.feature_name.replace(' vs ', '\nvs '),
    value: Math.round(feature.feature_value * 100),
    fullName: feature.feature_name
  }));

  const barData = features.map(feature => ({
    name: feature.feature_name.length > 15 
      ? feature.feature_name.substring(0, 15) + '...' 
      : feature.feature_name,
    score: Math.round(feature.feature_value * 100),
    confidence: Math.round(feature.confidence_score * 100),
    fullName: feature.feature_name
  }));

  const eventCounts = events.reduce((acc, event) => {
    acc[event.event_type] = (acc[event.event_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading recruiter insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <p className="text-red-600 mb-4">{error}</p>
          {onBack && (
            <button onClick={onBack} className="px-4 py-2 bg-gray-600 text-white rounded">
              Go Back
            </button>
          )}
        </div>
      </div>
    );
  }

  // Show sessions list if no session is selected
  if (!selectedSessionId) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">📊 Recruiter Dashboard</h1>
                <p className="text-gray-600">View all interview sessions and analytics</p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto p-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Total Sessions</h3>
              <div className="text-3xl font-bold text-gray-900 mt-2">{sessions.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Active Sessions</h3>
              <div className="text-3xl font-bold text-blue-600 mt-2">
                {sessions.filter(s => s.status === 'active').length}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500">Completed</h3>
              <div className="text-3xl font-bold text-green-600 mt-2">
                {sessions.filter(s => s.status === 'completed').length}
              </div>
            </div>
          </div>

          {/* Sessions List */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-800">Interview Sessions</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Candidate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Started
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sessions.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                        No sessions found. Create a new interview to get started.
                      </td>
                    </tr>
                  ) : (
                    sessions.map((s) => (
                      <tr key={s.session_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{s.candidate_name}</div>
                          <div className="text-sm text-gray-500">{s.session_id.slice(0, 8)}...</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            s.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {s.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(s.start_time).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDuration(s.start_time, s.end_time)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => setSelectedSessionId(s.session_id)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Details →
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Behavioral Analysis - {session?.candidate_name}
              </h1>
              <p className="text-gray-600">
                Session ID: {selectedSessionId} • 
                Duration: {session && formatDuration(session.start_time, session.end_time)}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedSessionId(null)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                ← All Sessions
              </button>
              {onBack && (
                <button
                  onClick={onBack}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Home
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Overall Performance</h3>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {Math.round((features.reduce((sum, f) => sum + f.feature_value, 0) / features.length) * 100)}%
            </div>
            <p className="text-sm text-gray-600">Average across all dimensions</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Events</h3>
            <div className="text-2xl font-bold text-gray-900 mt-1">{events.length}</div>
            <p className="text-sm text-gray-600">Behavioral interactions tracked</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">AI Interactions</h3>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {eventCounts['AI_PROMPT'] || 0}
            </div>
            <p className="text-sm text-gray-600">Times AI assistant was used</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Code Iterations</h3>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {eventCounts['CODE_RUN'] || 0}
            </div>
            <p className="text-sm text-gray-600">Times code was executed</p>
          </div>
        </div>

        {/* Feature Scores */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-800">Behavioral Dimensions</h2>
            <p className="text-gray-600 text-sm mt-1">
              Key skills and traits evaluated during the interview session
            </p>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {features.map((feature, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-800">{feature.feature_name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`px-2 py-1 text-xs rounded-full ${getScoreColor(feature.feature_value)}`}>
                          {getScoreLabel(feature.feature_value)}
                        </span>
                        <span className="text-sm text-gray-500">
                          {Math.round(feature.confidence_score * 100)}% confidence
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-gray-900">
                        {Math.round(feature.feature_value * 100)}%
                      </div>
                    </div>
                  </div>
                  
                  {/* Progress bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                    <div 
                      className={`h-2 rounded-full ${
                        feature.feature_value >= 0.8 ? 'bg-green-500' :
                        feature.feature_value >= 0.6 ? 'bg-yellow-500' :
                        feature.feature_value >= 0.4 ? 'bg-orange-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${feature.feature_value * 100}%` }}
                    ></div>
                  </div>
                  
                  {/* Evidence */}
                  {feature.evidence && feature.evidence.length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                        Evidence
                      </h4>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {feature.evidence.slice(0, 3).map((evidence, i) => (
                          <li key={i} className="flex items-start">
                            <span className="text-primary-500 mr-2">•</span>
                            {evidence}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Visualizations */}
        <div className="grid grid-cols-1 gap-6">
          {/* Bar Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Score Breakdown</h3>
            <SafeResponsiveContainer width="100%" height={400}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  tick={{ fontSize: 10 }}
                />
                <YAxis domain={[0, 100]} />
                <Tooltip 
                  formatter={(value, name) => [
                    `${value}%`, 
                    name === 'score' ? 'Score' : 'Confidence'
                  ]}
                />
                <Bar dataKey="score" fill="#3B82F6" />
                <Bar dataKey="confidence" fill="#94A3B8" />
              </BarChart>
            </SafeResponsiveContainer>
          </div>
        </div>

        {/* Event Timeline Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Activity Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Object.entries(eventCounts).map(([eventType, count]) => (
              <div key={eventType} className="text-center p-3 border rounded">
                <div className="text-lg font-bold text-gray-900">{count}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {eventType.replace('_', ' ').toLowerCase()}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-6">
          <h3 className="text-lg font-semibold text-blue-800 mb-3">Hiring Recommendations</h3>
          <div className="text-blue-700 space-y-2">
            <p>• <strong>Strengths:</strong> Review highest-scoring dimensions for role fit</p>
            <p>• <strong>Development Areas:</strong> Consider lower scores as coaching opportunities</p>
            <p>• <strong>AI Collaboration:</strong> Evaluate strategic vs. over-reliant AI usage patterns</p>
            <p>• <strong>Process Focus:</strong> This measures thinking approach, not just final results</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecruiterDashboard;