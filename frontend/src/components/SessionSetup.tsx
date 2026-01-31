import React, { useState } from 'react';
import { SessionCreate } from '../services/api';

interface SessionSetupProps {
  onSessionCreate: (sessionData: SessionCreate) => void;
}

const SessionSetup: React.FC<SessionSetupProps> = ({ onSessionCreate }) => {
  const [formData, setFormData] = useState({
    candidate_name: '',
    interviewer_name: '',
    problem_statement: `# Data Analysis Challenge

You are a data analyst at a fast-growing e-commerce company. The marketing team has provided you with customer transaction data and wants insights to optimize their campaigns.

## Your Task
1. **Explore the data** to understand customer behavior patterns
2. **Identify key insights** about customer segments and purchasing trends  
3. **Recommend data-driven strategies** to improve customer retention
4. **Present your findings** with supporting visualizations

## Data Description
- Customer demographics (age, location, registration date)
- Transaction history (purchase amounts, frequency, product categories)
- Marketing touchpoints (campaign interactions, channel preferences)

## Tools Available
- Python with pandas, numpy, matplotlib, seaborn
- Sample dataset will be provided
- AI assistant for guidance (use wisely!)

**Time Limit:** 45 minutes

*Remember: We're evaluating your problem-solving process, not just the final answer.*`
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.candidate_name && formData.problem_statement) {
      onSessionCreate({
        candidate_name: formData.candidate_name,
        interviewer_name: formData.interviewer_name || undefined,
        problem_statement: formData.problem_statement
      });
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="bg-primary-600 text-white p-6">
          <h1 className="text-3xl font-bold mb-2">AI Interview Platform</h1>
          <p className="text-primary-100">
            Welcome to your behavioral interview session for data roles
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Candidate Name *
              </label>
              <input
                type="text"
                value={formData.candidate_name}
                onChange={(e) => handleChange('candidate_name', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter your full name"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Interviewer Name (Optional)
              </label>
              <input
                type="text"
                value={formData.interviewer_name}
                onChange={(e) => handleChange('interviewer_name', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Interviewer's name"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Problem Statement *
            </label>
            <textarea
              value={formData.problem_statement}
              onChange={(e) => handleChange('problem_statement', e.target.value)}
              className="w-full h-64 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
              placeholder="Enter the interview problem statement..."
              required
            />
          </div>
          
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  How This Interview Works
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <ul className="list-disc list-inside space-y-1">
                    <li>You'll work in a coding environment with an AI assistant</li>
                    <li>We track your problem-solving process, not just final answers</li>
                    <li>Ask the AI for help, but use it strategically</li>
                    <li>Your thinking and debugging approach is what matters most</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end">
            <button
              type="submit"
              className="px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              Start Interview Session
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SessionSetup;