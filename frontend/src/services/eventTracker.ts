import { apiService } from './api';
import { v4 as uuidv4 } from 'uuid';

export type EventType = 
  | 'SESSION_START'
  | 'CODE_EDIT'
  | 'CODE_RUN'
  | 'RUN_RESULT'
  | 'ERROR_OCCURRED'
  | 'ERROR_RESOLVED'
  | 'DATA_VIEW'
  | 'AI_PROMPT'
  | 'AI_RESPONSE'
  | 'AI_RESPONSE_USED'
  | 'RESULT_EVALUATED'
  | 'IDLE_GAP';

interface EventData {
  type: EventType;
  event_metadata?: Record<string, any>;
}

class EventTracker {
  private sessionId: string | null = null;
  private eventQueue: EventData[] = [];
  private isProcessing = false;
  private lastActivityTime = Date.now();
  private idleThreshold = 5000; // 5 seconds of inactivity
  private idleTimer?: NodeJS.Timeout;

  initialize(sessionId: string) {
    this.sessionId = sessionId;
    this.startIdleTracking();
    console.log('Event Tracker initialized for session:', sessionId);
  }

  async trackEvent(type: EventType, event_metadata: Record<string, any> = {}) {
    if (!this.sessionId) {
      console.warn('Event tracker not initialized');
      return;
    }

    const eventData: EventData = {
      type,
      event_metadata: {
        ...event_metadata,
        timestamp: new Date().toISOString(),
        client_id: uuidv4(),
      }
    };

    this.eventQueue.push(eventData);
    this.updateActivity();

    if (!this.isProcessing) {
      await this.processQueue();
    }
  }

  private async processQueue() {
    if (this.eventQueue.length === 0 || this.isProcessing) {
      return;
    }

    this.isProcessing = true;

    while (this.eventQueue.length > 0) {
      const event = this.eventQueue.shift();
      if (event && this.sessionId) {
        try {
          await apiService.logEvent({
            session_id: this.sessionId,
            event_type: event.type,
            event_metadata: event.event_metadata
          });
          console.log('Event logged:', event.type, event.event_metadata);
        } catch (error) {
          console.error('Failed to log event:', error);
          // Re-queue the event for retry
          this.eventQueue.unshift(event);
          break;
        }
      }
    }

    this.isProcessing = false;
  }

  private updateActivity() {
    this.lastActivityTime = Date.now();
    this.resetIdleTimer();
  }

  private startIdleTracking() {
    this.resetIdleTimer();
  }

  private resetIdleTimer() {
    if (this.idleTimer) {
      clearTimeout(this.idleTimer);
    }

    this.idleTimer = setTimeout(() => {
      this.trackEvent('IDLE_GAP', {
        idle_duration: Date.now() - this.lastActivityTime
      });
    }, this.idleThreshold);
  }

  // Specific event tracking methods
  trackCodeEdit(code: string, language: string) {
    this.trackEvent('CODE_EDIT', {
      code_length: code.length,
      language,
      lines: code.split('\n').length
    });
  }

  trackCodeRun(code: string, language: string) {
    this.trackEvent('CODE_RUN', {
      code_length: code.length,
      language,
      lines: code.split('\n').length
    });
  }

  trackRunResult(success: boolean, output?: string, error?: string) {
    this.trackEvent('RUN_RESULT', {
      success,
      output_length: output?.length || 0,
      has_error: !!error,
      error_message: error
    });
  }

  trackError(error: string, context?: Record<string, any>) {
    this.trackEvent('ERROR_OCCURRED', {
      error_message: error,
      ...context
    });
  }

  trackErrorResolved(resolution_method?: string) {
    this.trackEvent('ERROR_RESOLVED', {
      resolution_method
    });
  }

  trackDataView(data_info: Record<string, any>) {
    this.trackEvent('DATA_VIEW', data_info);
  }

  trackAIPrompt(prompt: string, intent?: string) {
    this.trackEvent('AI_PROMPT', {
      prompt_length: prompt.length,
      intent
    });
  }

  trackAIResponse(response: string, intent?: string, interactionId?: string) {
    this.trackEvent('AI_RESPONSE', {
      response_length: response.length,
      intent,
      interaction_id: interactionId
    });
  }

  trackAIResponseUsed(interactionId: string, usage_type: string) {
    this.trackEvent('AI_RESPONSE_USED', {
      interaction_id: interactionId,
      usage_type
    });
  }

  trackResultEvaluation(evaluation: Record<string, any>) {
    this.trackEvent('RESULT_EVALUATED', evaluation);
  }

  cleanup() {
    if (this.idleTimer) {
      clearTimeout(this.idleTimer);
    }
    this.sessionId = null;
    this.eventQueue = [];
  }
}

export const eventTracker = new EventTracker();
export default EventTracker;