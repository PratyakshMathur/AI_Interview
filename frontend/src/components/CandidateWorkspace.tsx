import React, { useState, useEffect, useCallback } from 'react';
import CodeEditor from './CodeEditor';
import AIChat from './AIChat';
import NotebookContainer from './NotebookContainer';
import { Session } from '../services/api';
import { eventTracker } from '../services/eventTracker';

interface CandidateWorkspaceProps {
  session: Session;
  onEndSession: () => void;
}

const CandidateWorkspace: React.FC<CandidateWorkspaceProps> = ({
  session,
  onEndSession
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
  const [language, setLanguage] = useState<'python' | 'sql'>('python');
  const [isRunning, setIsRunning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(45 * 60); // 45 minutes
  const [leftPanelWidth, setLeftPanelWidth] = useState(25); // percentage
  const [rightPanelWidth, setRightPanelWidth] = useState(33); // percentage
  const [outputHeight, setOutputHeight] = useState(192); // pixels
  const [viewMode, setViewMode] = useState<'editor' | 'notebook'>('notebook'); // Default to notebook

  // Timer effect
  useEffect(() => {
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
  }, [onEndSession]);

  // Initialize event tracker
  useEffect(() => {
    eventTracker.initialize(session.session_id);
    return () => {
      eventTracker.cleanup();
    };
  }, [session.session_id]);

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

  return (
    <div className="h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-800">
              Interview Session - {session.candidate_name}
            </h1>
            <p className="text-sm text-gray-600">
              {session.interviewer_name && `Interviewer: ${session.interviewer_name} • `}
              Session ID: {session.session_id.slice(0, 8)}...
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* View Mode Toggle */}
            <div className="flex bg-gray-200 rounded-md overflow-hidden">
              <button
                onClick={() => setViewMode('editor')}
                className={`px-3 py-1 text-sm ${
                  viewMode === 'editor' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-transparent text-gray-700 hover:bg-gray-300'
                }`}
              >
                📝 Editor
              </button>
              <button
                onClick={() => setViewMode('notebook')}
                className={`px-3 py-1 text-sm ${
                  viewMode === 'notebook' 
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
            
            <button
              onClick={onEndSession}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              End Session
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Problem Statement */}
        <div 
          className="bg-gray-800 border-r flex flex-col"
          style={{ width: `${leftPanelWidth}%` }}
        >
          <div className="p-4 border-b bg-gray-700">
            <h2 className="text-lg font-semibold text-white">Problem Statement</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="prose prose-sm max-w-none">
              <div 
                className="text-sm text-white leading-relaxed"
                dangerouslySetInnerHTML={{
                  __html: session.problem_statement
                    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                    .replace(/##\s+([^\n]+)/g, '<h3 class="text-lg font-bold text-blue-300 mt-4 mb-2">$1</h3>')
                    .replace(/\n/g, '<br>')
                    .replace(/-\s+([^\n]+)/g, '• $1')
                }}
              />
            </div>
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
          style={{ width: `${100 - leftPanelWidth - rightPanelWidth}%` }}
        >
          {viewMode === 'editor' ? (
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
              language={language}
              onLanguageChange={setLanguage}
              sessionId={session.session_id}
            />
          )}
        </div>

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

        {/* Right Panel - AI Chat (Like VS Code sidebar) */}
        <div 
          className="bg-white border-l flex flex-col"
          style={{ width: `${rightPanelWidth}%` }}
        >
          <div className="bg-gray-100 px-4 py-2 border-b flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">💬 AI Assistant</h3>
            <button className="text-gray-500 hover:text-gray-700 text-xs">✕</button>
          </div>
          <div className="flex-1 min-h-0">
            <AIChat
              sessionId={session.session_id}
              codeContext={code}
              errorContext={error}
              onResponseUsed={handleAIResponseUsed}
            />
          </div>
        </div>
      </div>

      {/* Event Indicator */}
      <div className="event-indicator">
        <div className="bg-green-500 w-3 h-3 rounded-full animate-pulse"></div>
      </div>
    </div>
  );
};

export default CandidateWorkspace;