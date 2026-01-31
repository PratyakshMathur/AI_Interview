import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface SessionCreate {
  candidate_name: string;
  interviewer_name?: string;
  problem_statement: string;
  session_data?: Record<string, any>;
}

export interface Session {
  session_id: string;
  candidate_name: string;
  interviewer_name?: string;
  problem_statement: string;
  start_time: string;
  end_time?: string;
  status: string;
}

export interface EventCreate {
  session_id: string;
  event_type: string;
  event_metadata?: Record<string, any>;
}

export interface AIPromptRequest {
  session_id: string;
  user_prompt: string;
  context_data?: Record<string, any>;
}

export interface Feature {
  feature_name: string;
  feature_value: number;
  confidence_score: number;
  evidence: string[];
  computed_at: string;
}

class ApiService {
  // Session endpoints
  async getAllSessions(): Promise<Session[]> {
    const response = await api.get('/sessions');
    return response.data;
  }

  async createSession(sessionData: SessionCreate): Promise<Session> {
    const response = await api.post('/sessions', sessionData);
    return response.data;
  }

  async getSession(sessionId: string): Promise<Session> {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  }

  async completeSession(sessionId: string): Promise<void> {
    await api.post(`/sessions/${sessionId}/complete`);
  }

  // Event endpoints
  async logEvent(eventData: EventCreate): Promise<any> {
    const response = await api.post('/events', eventData);
    return response.data;
  }

  async getSessionEvents(sessionId: string): Promise<any[]> {
    const response = await api.get(`/sessions/${sessionId}/events`);
    return response.data;
  }

  // AI interaction endpoints
  async sendAIPrompt(promptRequest: AIPromptRequest): Promise<any> {
    const response = await api.post('/ai/prompt', promptRequest);
    return response.data;
  }

  async markResponseUsed(interactionId: string): Promise<void> {
    await api.post('/ai/response-used', { interaction_id: interactionId });
  }

  // Features endpoint
  async getSessionFeatures(sessionId: string): Promise<Feature[]> {
    const response = await api.get(`/sessions/${sessionId}/features`);
    return response.data;
  }
}

export const apiService = new ApiService();
export default api;