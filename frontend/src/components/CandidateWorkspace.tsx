import React, { useState, useEffect, useCallback } from 'react';
import CodeEditor from './CodeEditor';
import AIChat from './AIChat';
import NotebookContainer from './NotebookContainer';
import { Session } from '../services/api';
import { eventTracker } from '../services/eventTracker';
import { apiService } from '../services/api';

interface CandidateWorkspaceProps {
  session: Session;
  onEndSession: () => void;
  viewMode?: 'readonly' | 'normal';
}

const CandidateWorkspace: React.FC<CandidateWorkspaceProps> = ({
  session,
  onEndSession,
  viewMode = 'normal'
}) => {
  const [code, setCode] = useState(
    `# Welcome to your data analysis challenge!
# Use this workspace to explore, analyze, and solve the problem.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Sample data loading (this would be provided in a real interview)
# df = pd.read_csv('customer_data.csv')

# Start your analysis here...
print("Let's begin the data analysis!")
`
  );
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const language = 'sql'; // Fixed to SQL only
  const [isRunning, setIsRunning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(45 * 60); // 45 minutes
  const [leftPanelWidth, setLeftPanelWidth] = useState(25); // percentage
  const [rightPanelWidth, setRightPanelWidth] = useState(33); // percentage
  const [outputHeight, setOutputHeight] = useState(192); // pixels
  const [editorViewMode, setEditorViewMode] = useState<'editor' | 'notebook'>('notebook'); // Default to notebook
  const [showAIHelper, setShowAIHelper] = useState(viewMode !== 'readonly');
  const [problemDescription, setProblemDescription] = useState<string>('');
  const [loadingProblem, setLoadingProblem] = useState(true);
  const [phase, setPhase] = useState(session.phase || 'coding');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [firstInterviewQuestion, setFirstInterviewQuestion] = useState<string | null>(null);

  // Timer effect
  useEffect(() => {
    if (viewMode === 'readonly') return; // Don't start timer in readonly mode
    
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          onEndSession();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onEndSession, viewMode]);

  // Initialize event tracker
  useEffect(() => {
    eventTracker.initialize(session.session_id);
    return () => {
      eventTracker.cleanup();
    };
  }, [session.session_id]);

  // Fetch problem description if problem_id exists
  useEffect(() => {
    const fetchProblem = async () => {
      if (session.problem_id) {
        try {
          const problem = await apiService.getProblem(session.problem_id);
          setProblemDescription(problem.description);
        } catch (error) {
          console.error('Failed to fetch problem:', error);
          setProblemDescription(session.problem_statement); // Fallback to session problem_statement
        }
      } else {
        setProblemDescription(session.problem_statement);
      }
      setLoadingProblem(false);
    };
    
    fetchProblem();
  }, [session.problem_id, session.problem_statement]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeColor = () => {
    if (timeRemaining > 15 * 60) return 'text-green-600';
    if (timeRemaining > 5 * 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleCodeChange = useCallback((newCode: string) => {
    setCode(newCode);
  }, []);

  const handleRunCode = useCallback(async () => {
    if (isRunning) return;
    
    setIsRunning(true);
    setOutput('');
    setError('');
    
    // Track code run
    eventTracker.trackCodeRun(code, language);

    try {
      // Execute Python code using eval (safe for demo purposes)
      const pythonOutput = await executePythonCode(code);
      setOutput(pythonOutput);
      eventTracker.trackRunResult(true, pythonOutput);
      
    } catch (err: any) {
      const errorMsg = err.message || 'Execution failed. Please check your code.';
      setError(errorMsg);
      eventTracker.trackError(errorMsg, { code_snippet: code });
      eventTracker.trackRunResult(false, undefined, errorMsg);
    } finally {
      setIsRunning(false);
    }
  }, [code, language, isRunning]);

  // Execute Python code via backend API (REAL Python execution)
  const executePythonCode = async (pythonCode: string): Promise<string> => {
    try {
      const response = await fetch('http://localhost:8000/api/execute-python', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: pythonCode,
          language: 'python'
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        return result.output || '';
      } else {
        // Throw error so it shows in the error panel
        throw new Error(result.error || 'Code execution failed');
      }
      
    } catch (error: any) {
      throw error;
    }
  };

  const handleAIResponseUsed = (interactionId: string) => {
    console.log('AI response used:', interactionId);
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    eventTracker.trackPhaseSubmitted();
    
    try {
      const response = await fetch(`http://localhost:8000/api/sessions/${session.session_id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPhase(data.phase || 'interview');
        eventTracker.trackInterviewStarted();
        
        // Store first interview question
        if (data.first_question) {
          setFirstInterviewQuestion(data.first_question);
          console.log('Interview started with question:', data.first_question);
        }
      } else {
        console.error('Failed to submit phase');
      }
    } catch (error) {
      console.error('Error submitting phase:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-800">
              {viewMode === 'readonly' ? '📓 Submitted Notebook - ' : 'Interview Session - '}{session.candidate_name}
            </h1>
            <p className="text-sm text-gray-600">
              {session.interviewer_name && `Interviewer: ${session.interviewer_name} • `}
              Session ID: {session.session_id.slice(0, 8)}...
              {viewMode === 'readonly' && ' • Status: ' + (session.status || 'completed')}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {viewMode === 'readonly' ? (
              <div className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md font-semibold border border-gray-300">
                👁️ Read-Only View
              </div>
            ) : (
              <>
                {/* View Mode Toggle */}
                <div className="flex bg-gray-200 rounded-md overflow-hidden">
                  <button
                    onClick={() => setEditorViewMode('editor')}
                    className={`px-3 py-1 text-sm ${
                      editorViewMode === 'editor' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-transparent text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    📝 Editor
                  </button>
                  <button
                    onClick={() => setEditorViewMode('notebook')}
                    className={`px-3 py-1 text-sm ${
                      editorViewMode === 'notebook' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-transparent text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    📓 Notebook
                  </button>
                </div>

                <div className="text-right">
                  <div className={`text-lg font-mono font-semibold ${getTimeColor()}`}>
                    {formatTime(timeRemaining)}
                  </div>
                  <div className="text-xs text-gray-500">Time Remaining</div>
                </div>
                
                {phase === 'coding' && (
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? 'Submitting...' : '✓ Submit & Start Interview'}
                  </button>
                )}
                
                {phase === 'interview' && (
                  <div className="px-4 py-2 bg-blue-600 text-white rounded-md font-semibold">
                    📝 Interview Mode
                  </div>
                )}
                
                <button
                  onClick={onEndSession}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  End Session
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Problem Statement */}
        <div 
          className="bg-white border-r flex flex-col"
          style={{ width: `${leftPanelWidth}%` }}
        >
          <div className="p-4 border-b bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-800">Problem Statement</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {loadingProblem ? (
              <div className="text-gray-500 text-center py-8">Loading problem...</div>
            ) : (
              <div className="prose prose-sm max-w-none">
                <div 
                  className="text-sm text-gray-800 leading-relaxed"
                  dangerouslySetInnerHTML={{
                    __html: problemDescription
                      .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
                      .replace(/###\s+([^\n]+)/g, '<h4 class="text-sm font-bold text-gray-900 mt-3 mb-1">$1</h4>')
                      .replace(/##\s+([^\n]+)/g, '<h3 class="text-base font-bold text-gray-900 mt-4 mb-2">$1</h3>')
                      .replace(/#\s+([^\n]+)/g, '<h2 class="text-lg font-bold text-gray-900 mt-5 mb-3">$1</h2>')
                      .replace(/\n/g, '<br>')
                      .replace(/-\s+([^\n]+)/g, '<div class="ml-4 mb-1">• $1</div>')
                      .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
                  }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Resize Handle - Left */}
        <div 
          className="w-1 bg-gray-400 cursor-col-resize hover:bg-blue-500 transition-colors"
          onMouseDown={(e) => {
            const startX = e.clientX;
            const startWidth = leftPanelWidth;
            const handleMouseMove = (e: MouseEvent) => {
              const deltaX = e.clientX - startX;
              const newWidth = Math.max(15, Math.min(40, startWidth + (deltaX / window.innerWidth) * 100));
              setLeftPanelWidth(newWidth);
            };
            const handleMouseUp = () => {
              document.removeEventListener('mousemove', handleMouseMove);
              document.removeEventListener('mouseup', handleMouseUp);
            };
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
          }}
        />

        {/* Center Panel - Code Editor + Terminal OR Notebook */}
        <div 
          className="flex flex-col"
          style={{ width: `${100 - leftPanelWidth - (showAIHelper && viewMode !== 'readonly' ? rightPanelWidth : 0)}%` }}
        >
          {editorViewMode === 'editor' ? (
            <>
              {/* Code Editor */}
              <div className="flex-1 p-4 min-h-0">
                <CodeEditor
                  value={code}
                  onChange={handleCodeChange}
                  language={language}
                  onRun={handleRunCode}
                />
              </div>
              
              {/* Vertical Resize Handle - Terminal */}
              <div 
                className="h-1 bg-gray-400 cursor-row-resize hover:bg-blue-500 transition-colors"
                onMouseDown={(e) => {
                  const startY = e.clientY;
                  const startHeight = outputHeight;
                  const handleMouseMove = (e: MouseEvent) => {
                    const deltaY = e.clientY - startY;
                    const newHeight = Math.max(100, Math.min(400, startHeight + deltaY));
                    setOutputHeight(newHeight);
                  };
                  const handleMouseUp = () => {
                    document.removeEventListener('mousemove', handleMouseMove);
                    document.removeEventListener('mouseup', handleMouseUp);
                  };
                  document.addEventListener('mousemove', handleMouseMove);
                  document.addEventListener('mouseup', handleMouseUp);
                }}
              />
              
              {/* Terminal Panel (Static at bottom like VS Code) */}
              <div 
                className="bg-gray-900 text-green-400 font-mono text-sm border-t"
                style={{ height: `${outputHeight}px` }}
              >
                <div className="flex border-b border-gray-700 bg-gray-800">
                  <div className="flex space-x-2 px-4 py-2">
                    <button className="text-xs text-gray-300 hover:text-white px-2 py-1 bg-gray-700 rounded">
                      🖥️ Terminal
                    </button>
                    <button className="text-xs text-gray-300 hover:text-white px-2 py-1 hover:bg-gray-700 rounded">
                      📝 Output
                    </button>
                    <button className="text-xs text-gray-300 hover:text-white px-2 py-1 hover:bg-gray-700 rounded">
                      ⚠️ Problems
                    </button>
                  </div>
                </div>
                <div className="flex" style={{ height: `${outputHeight - 40}px` }}>
                  <div className="flex-1 p-4 overflow-y-auto border-r border-gray-700">
                    <div className="text-green-400 text-xs mb-2">$ python main.py</div>
                    {isRunning ? (
                      <div className="flex items-center space-x-2 text-yellow-400">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
                        <span>Executing code...</span>
                      </div>
                    ) : (
                      <pre className="whitespace-pre-wrap text-green-400">{output || 'Ready to execute Python code. Click Run to see output here.'}</pre>
                    )}
                  </div>
                  <div className="flex-1 p-4 overflow-y-auto">
                    <div className="text-red-400 text-xs mb-2">Errors & Warnings:</div>
                    {error ? (
                      <pre className="whitespace-pre-wrap text-red-400">{error}</pre>
                    ) : (
                      <div className="text-gray-500 text-sm">No errors</div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* Notebook View */
            <NotebookContainer 
              sessionId={session.session_id}
              readonly={viewMode === 'readonly'}
            />
          )}
        </div>

        {/* Right Panel - AI Chat (Like VS Code sidebar) */}
        {showAIHelper && viewMode !== 'readonly' && (
          <>
            {/* Resize Handle - Right */}
            <div 
              className="w-1 bg-gray-400 cursor-col-resize hover:bg-blue-500 transition-colors"
              onMouseDown={(e) => {
                const startX = e.clientX;
                const startWidth = rightPanelWidth;
                const handleMouseMove = (e: MouseEvent) => {
                  const deltaX = e.clientX - startX;
                  const newWidth = Math.max(20, Math.min(50, startWidth - (deltaX / window.innerWidth) * 100));
                  setRightPanelWidth(newWidth);
                };
                const handleMouseUp = () => {
                  document.removeEventListener('mousemove', handleMouseMove);
                  document.removeEventListener('mouseup', handleMouseUp);
                };
                document.addEventListener('mousemove', handleMouseMove);
                document.addEventListener('mouseup', handleMouseUp);
              }}
            />

            <div 
              className="bg-white border-l flex flex-col"
              style={{ width: `${rightPanelWidth}%` }}
            >
              <div className="bg-gray-100 px-4 py-2 border-b flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800">
                  {phase === 'interview' ? '🎤 AI Interviewer' : '💬 AI Assistant'}
                </h3>
                <button 
                  onClick={() => setShowAIHelper(false)}
                  className="text-gray-500 hover:text-gray-700 text-xs"
                >
                  ✕
                </button>
              </div>
              <div className="flex-1 min-h-0">
                <AIChat
                  sessionId={session.session_id}
                  codeContext={code}
                  errorContext={error}
                  onResponseUsed={handleAIResponseUsed}
                  mode={phase === 'interview' ? 'interview' : 'coding'}
                  initialQuestion={firstInterviewQuestion}
                />
              </div>
            </div>
          </>
        )}

        {/* Toggle AI Helper Button when hidden */}
        {!showAIHelper && viewMode !== 'readonly' && (
          <button
            onClick={() => setShowAIHelper(true)}
            className="fixed right-4 top-24 bg-blue-600 text-white px-3 py-2 rounded-l-lg shadow-lg hover:bg-blue-700 transition-colors z-50"
            title="Show AI Assistant"
          >
            💬
          </button>
        )}
      </div>

      {/* Event Indicator */}
      <div className="event-indicator">
        <div className="bg-green-500 w-3 h-3 rounded-full animate-pulse"></div>
      </div>
    </div>
  );
};

export default CandidateWorkspace;