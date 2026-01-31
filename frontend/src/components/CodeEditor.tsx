import React, { useRef, useCallback, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { eventTracker } from '../services/eventTracker';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: string;
  onRun?: () => void;
  readOnly?: boolean;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language,
  onRun,
  readOnly = false
}) => {
  const editorRef = useRef<any>(null);
  const lastValueRef = useRef(value);
  const editTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      if (onRun) {
        onRun();
      }
    });

    // Configure editor options
    editor.updateOptions({
      fontSize: 14,
      fontFamily: 'Fira Code, Monaco, Menlo, monospace',
      fontLigatures: true,
      lineNumbers: 'on',
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      wordWrap: 'bounded',
      automaticLayout: true,
      tabSize: 2,
      insertSpaces: true,
      renderWhitespace: 'selection',
      bracketPairColorization: { enabled: true }
    });
  };

  const handleChange = useCallback((newValue: string = '') => {
    onChange(newValue);
    
    // Track code edit with debouncing
    if (editTimeoutRef.current) {
      clearTimeout(editTimeoutRef.current);
    }
    
    editTimeoutRef.current = setTimeout(() => {
      // Only track if there was a meaningful change
      if (newValue !== lastValueRef.current && 
          Math.abs(newValue.length - lastValueRef.current.length) > 0) {
        eventTracker.trackCodeEdit(newValue, language);
        lastValueRef.current = newValue;
      }
    }, 1000); // Debounce for 1 second
  }, [onChange, language]);

  useEffect(() => {
    return () => {
      if (editTimeoutRef.current) {
        clearTimeout(editTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="h-full w-full bg-gray-50 rounded-lg overflow-hidden border">
      <div className="bg-gray-100 px-4 py-2 border-b flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-sm font-medium text-gray-700">
            {language.charAt(0).toUpperCase() + language.slice(1)} Editor
          </span>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-red-400 rounded-full"></div>
            <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          </div>
        </div>
        {onRun && (
          <button
            onClick={onRun}
            className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 transition-colors"
          >
            Run (⌘+Enter)
          </button>
        )}
      </div>
      
      <div className="h-full">
        <Editor
          height="100%"
          language={language}
          value={value}
          onChange={handleChange}
          onMount={handleEditorDidMount}
          options={{
            readOnly,
            theme: 'vs',
            padding: { top: 16, bottom: 16 }
          }}
          loading={
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          }
        />
      </div>
    </div>
  );
};

export default CodeEditor;