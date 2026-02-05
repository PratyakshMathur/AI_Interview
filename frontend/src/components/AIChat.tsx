import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import { eventTracker } from '../services/eventTracker';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  interactionId?: string;
  intent?: string;
}

interface AIChatProps {
  sessionId: string;
  codeContext?: string;
  errorContext?: string;
  onResponseUsed?: (interactionId: string) => void;
  mode?: 'coding' | 'interview';
  initialQuestion?: string | null;
}

const AIChat: React.FC<AIChatProps> = ({
  sessionId,
  codeContext,
  errorContext,
  onResponseUsed,
  mode = 'coding',
  initialQuestion = null
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    // Only auto-scroll when new messages are added, not on input changes
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages.length]);

  // Add initial interview question when mode changes to interview
  useEffect(() => {
    if (mode === 'interview' && initialQuestion) {
      // Clear previous messages and show only the interview question
      const aiMessage: Message = {
        id: 'initial-question',
        type: 'ai',
        content: initialQuestion,
        timestamp: new Date(),
        intent: 'interview'
      };
      setMessages([aiMessage]);
    }
  }, [mode, initialQuestion]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Track AI prompt (different events for coding vs interview)
    if (mode === 'interview') {
      eventTracker.trackInterviewAnswer(inputValue);
    } else {
      eventTracker.trackAIPrompt(inputValue);
    }
    
    const promptText = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      // Build context data
      const contextData: Record<string, any> = {};
      if (codeContext) contextData.code = codeContext;
      if (errorContext) contextData.error = errorContext;
      contextData.mode = mode;

      // Call backend AI
      const response = await apiService.sendAIPrompt({
        session_id: sessionId,
        user_prompt: promptText,
        context_data: contextData
      });
      
      // Smart AI response based on context and user input
      let aiResponse = response.response || '';
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiResponse,
        timestamp: new Date(),
        interactionId: response.interaction_id || 'id-' + Date.now(),
        intent: response.intent || 'help'
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Track AI response
      if (mode === 'interview') {
        eventTracker.trackInterviewQuestion(aiResponse);
      } else {
        eventTracker.trackAIResponse(
          aiResponse, 
          response.intent || 'help', 
          response.interaction_id || 'id-' + Date.now()
        );
      }

    } catch (error: any) {
      console.error('Error sending AI prompt:', error);
      
      let errorMsg = 'Sorry, I encountered an error. Please try again.';
      if (error.response?.status === 404) {
        errorMsg = 'AI service is temporarily unavailable. Please try again later.';
      } else if (error.message) {
        console.error('Detailed error:', error.message);
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: errorMsg,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleUseResponse = async (message: Message) => {
    if (message.interactionId) {
      try {
        await apiService.markResponseUsed(message.interactionId);
        eventTracker.trackAIResponseUsed(message.interactionId, 'manual_selection');
        onResponseUsed?.(message.interactionId);
      } catch (error) {
        console.error('Error marking response as used:', error);
      }
    }
  };

  const getIntentColor = (intent?: string) => {
    switch (intent) {
      case 'CONCEPT_HELP': return 'bg-blue-100 text-blue-800';
      case 'DEBUG_HELP': return 'bg-red-100 text-red-800';
      case 'APPROACH_HELP': return 'bg-green-100 text-green-800';
      case 'VALIDATION': return 'bg-yellow-100 text-yellow-800';
      case 'DIRECT_SOLUTION': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="h-full flex flex-col bg-white ai-chat-panel">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-2xl mb-2">{mode === 'interview' ? '🎤' : '🤖'}</div>
            <p className="text-sm">
              {mode === 'interview' 
                ? "Interview mode: I'll ask you questions about your approach and code" 
                : "I can help explain concepts, debug issues, and suggest approaches"}
            </p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-lg ${
                message.type === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {message.type === 'ai' && message.intent && (
                <div className="mb-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${getIntentColor(message.intent)}`}>
                    {message.intent.replace('_', ' ')}
                  </span>
                </div>
              )}
              <div className="whitespace-pre-wrap text-sm">{message.content}</div>
              {message.type === 'ai' && message.interactionId && (
                <div className="mt-2 pt-2 border-t border-gray-300">
                  <button
                    onClick={() => handleUseResponse(message)}
                    className="text-xs text-primary-600 hover:text-primary-700"
                  >
                    📋 Use this response
                  </button>
                </div>
              )}
              <div className="text-xs opacity-75 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                <span className="text-sm">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your code or the problem..."
            className="flex-1 resize-none border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>Press Shift+Enter for new line, Enter to send</span>
          {(codeContext || errorContext) && (
            <span className="text-primary-600">
              Context: {codeContext ? '📝 Code' : ''} {errorContext ? '⚠️ Error' : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIChat;