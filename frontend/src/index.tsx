import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Ultra-comprehensive ResizeObserver error suppression
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

// Override console methods
console.error = function(...args: any[]) {
  const errorMessage = args.join(' ').toString();
  if (
    errorMessage.includes('ResizeObserver loop') ||
    errorMessage.includes('ResizeObserver loop completed') ||
    errorMessage.includes('undelivered notifications') ||
    errorMessage.includes('handleError') ||
    errorMessage.includes('Non-passive event listener')
  ) {
    return; // Completely suppress
  }
  originalConsoleError.apply(console, args);
};

console.warn = function(...args: any[]) {
  const warnMessage = args.join(' ').toString();
  if (
    warnMessage.includes('ResizeObserver loop') ||
    warnMessage.includes('ResizeObserver loop completed') ||
    warnMessage.includes('undelivered notifications')
  ) {
    return; // Suppress warnings too
  }
  originalConsoleWarn.apply(console, args);
};

// Multiple window error handlers for maximum coverage
const errorHandler = (e: any) => {
  const message = e.message || e.error?.message || e.reason?.message || '';
  if (
    message.includes('ResizeObserver loop') ||
    message.includes('ResizeObserver loop completed') ||
    message.includes('undelivered notifications') ||
    message.includes('handleError')
  ) {
    e.preventDefault();
    e.stopImmediatePropagation();
    e.stopPropagation();
    return false;
  }
};

// Handle all possible error events
window.addEventListener('error', errorHandler, true);
window.addEventListener('unhandledrejection', errorHandler, true);

// Override the global error handler
window.onerror = function(message: string | Event, source?: string, lineno?: number, colno?: number, error?: Error) {
  if (
    (typeof message === 'string' && message.includes('ResizeObserver loop')) ||
    (typeof message === 'string' && message.includes('undelivered notifications')) ||
    error?.message?.includes('ResizeObserver loop')
  ) {
    return true; // Suppress the error
  }
  return false; // Let other errors through
};

// Intercept ResizeObserver at the source
const OriginalResizeObserver = window.ResizeObserver;
window.ResizeObserver = class extends OriginalResizeObserver {
  constructor(callback: ResizeObserverCallback) {
    super((entries: ResizeObserverEntry[], observer: ResizeObserver) => {
      try {
        callback(entries, observer);
      } catch (error: any) {
        if (!error?.message?.includes('ResizeObserver loop')) {
          throw error; // Re-throw if not ResizeObserver error
        }
        // Silently ignore ResizeObserver loop errors
      }
    });
  }
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Final ResizeObserver nuclear option
if (process.env.NODE_ENV === 'development') {
  // Completely disable ResizeObserver error reporting
  const origAddEventListener = EventTarget.prototype.addEventListener;
  EventTarget.prototype.addEventListener = function(type: string, listener: any, options?: any) {
    if (type === 'error' && typeof listener === 'function') {
      const wrappedListener = function(this: any, e: any) {
        if (e.message?.includes('ResizeObserver') || 
            e.error?.message?.includes('ResizeObserver')) {
          return false; // Block the event
        }
        return listener.call(this, e);
      };
      return origAddEventListener.call(this, type, wrappedListener, options);
    }
    return origAddEventListener.call(this, type, listener, options);
  };
}
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
