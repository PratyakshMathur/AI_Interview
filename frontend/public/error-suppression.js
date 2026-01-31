// Emergency ResizeObserver error suppression
// This script loads before React to catch errors at the earliest possible moment

(function() {
  'use strict';

  // Store original methods
  const originalError = console.error;
  const originalWarn = console.warn;
  const originalLog = console.log;

  // Create comprehensive error detection
  function isResizeObserverError(args) {
    const message = args.join(' ').toLowerCase();
    return message.includes('resizeobserver') ||
           message.includes('undelivered notifications') ||
           message.includes('handleerror') ||
           message.includes('bundle.js:29551') ||
           message.includes('bundle.js:29570');
  }

  // Override console methods before React loads
  console.error = function() {
    if (!isResizeObserverError(Array.from(arguments))) {
      originalError.apply(console, arguments);
    }
  };

  console.warn = function() {
    if (!isResizeObserverError(Array.from(arguments))) {
      originalWarn.apply(console, arguments);
    }
  };

  // Intercept all error events immediately
  window.addEventListener('error', function(e) {
    const message = (e.message || '').toLowerCase();
    if (message.includes('resizeobserver') || message.includes('undelivered notifications')) {
      e.preventDefault();
      e.stopImmediatePropagation();
      return false;
    }
  }, true); // Use capture phase

  // Override global error handler
  const originalOnError = window.onerror;
  window.onerror = function(message, source, lineno, colno, error) {
    const msg = (message || '').toLowerCase();
    if (msg.includes('resizeobserver') || msg.includes('undelivered notifications')) {
      return true; // Prevent default error handling
    }
    if (originalOnError) {
      return originalOnError.apply(this, arguments);
    }
    return false;
  };

  // Patch ResizeObserver constructor
  if (window.ResizeObserver) {
    const OriginalResizeObserver = window.ResizeObserver;
    window.ResizeObserver = function(callback) {
      return new OriginalResizeObserver(function(entries, observer) {
        try {
          callback(entries, observer);
        } catch (error) {
          // Silently ignore ResizeObserver errors
          if (!error.message || !error.message.includes('ResizeObserver loop')) {
            throw error;
          }
        }
      });
    };
  }

})();