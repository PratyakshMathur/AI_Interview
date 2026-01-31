import React, { useRef } from 'react';
import Editor from '@monaco-editor/react';

interface NotebookCellProps {
  code: string;
  language: 'python' | 'sql';
  output: string;
  error: string;
  executionCount: number | null;
  onCodeChange: (code: string) => void;
  onExecute: () => void;
  onDelete: () => void;
  canDelete: boolean;
}

const NotebookCell: React.FC<NotebookCellProps> = ({
  code,
  language,
  output,
  error,
  executionCount,
  onCodeChange,
  onExecute,
  onDelete,
  canDelete
}) => {
  const editorRef = useRef<any>(null);

  const handleEditorMount = (editor: any) => {
    editorRef.current = editor;
    
    // Add Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux) to run cell
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      onExecute();
    });
    
    // Shift+Enter should insert a new line (default behavior)
    // No need to override, Monaco handles this by default
  };

  const handleCodeChange = (value: string | undefined) => {
    onCodeChange(value || '');
  };

  return (
    <div style={{
      border: '1px solid #3e3e42',
      borderRadius: '4px',
      background: '#1e1e1e',
      marginBottom: '8px',
    }}>
      {/* Cell Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '4px 12px',
        background: '#2d2d30',
        borderBottom: '1px solid #3e3e42',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontFamily: 'monospace',
            fontSize: '12px',
            color: '#858585',
            minWidth: '40px',
          }}>
            [{executionCount !== null ? executionCount : ' '}]
          </span>
          <span style={{
            fontSize: '11px',
            padding: '2px 6px',
            borderRadius: '3px',
            background: language === 'python' ? '#1e5a8e' : '#2d5f3f',
            color: '#ffffff',
            fontWeight: 500,
          }}>
            {language.toUpperCase()}
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={onExecute}
            style={{
              padding: '3px 10px',
              fontSize: '12px',
              background: '#0e639c',
              border: 'none',
              borderRadius: '3px',
              color: 'white',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            ▶ Run
          </button>
          
          {canDelete && (
            <button
              onClick={onDelete}
              style={{
                padding: '3px 8px',
                fontSize: '12px',
                background: 'transparent',
                border: '1px solid #3e3e42',
                borderRadius: '3px',
                color: '#cccccc',
                cursor: 'pointer',
              }}
            >
              🗑️
            </button>
          )}
        </div>
      </div>

      {/* Code Editor */}
      <div>
        <Editor
          height="150px"
          language={language}
          value={code}
          onChange={handleCodeChange}
          onMount={handleEditorMount}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            automaticLayout: true,
            tabSize: 2,
            padding: { top: 8, bottom: 8 },
          }}
        />
      </div>

      {/* Output Area */}
      {(output || error) && (
        <div style={{
          padding: '12px',
          background: '#252526',
          borderTop: '1px solid #3e3e42',
          fontFamily: 'monospace',
          fontSize: '12px',
        }}>
          {output && (
            <pre style={{
              margin: 0,
              color: '#cccccc',
              whiteSpace: 'pre-wrap',
            }}>
              {output}
            </pre>
          )}
          {error && (
            <pre style={{
              margin: 0,
              color: '#f48771',
              whiteSpace: 'pre-wrap',
            }}>
              {error}
            </pre>
          )}
        </div>
      )}
      
      {/* Help Text */}
      <div style={{
        padding: '4px 12px',
        fontSize: '11px',
        color: '#858585',
        background: '#252526',
        borderTop: '1px solid #3e3e42',
      }}>
        Press <kbd style={{
          padding: '2px 4px',
          background: '#3e3e42',
          border: '1px solid #454545',
          borderRadius: '3px',
          fontSize: '10px',
        }}>Cmd</kbd> + <kbd style={{
          padding: '2px 4px',
          background: '#3e3e42',
          border: '1px solid #454545',
          borderRadius: '3px',
          fontSize: '10px',
        }}>Enter</kbd> to run • <kbd style={{
          padding: '2px 4px',
          background: '#3e3e42',
          border: '1px solid #454545',
          borderRadius: '3px',
          fontSize: '10px',
        }}>Shift</kbd> + <kbd style={{
          padding: '2px 4px',
          background: '#3e3e42',
          border: '1px solid #454545',
          borderRadius: '3px',
          fontSize: '10px',
        }}>Enter</kbd> for new line
      </div>
    </div>
  );
};

declare const monaco: any;

export default NotebookCell;
