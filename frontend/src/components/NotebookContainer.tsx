import React, { useState, useEffect } from 'react';
import NotebookCell from './NotebookCell';
import axios from 'axios';
import { eventTracker } from '../services/eventTracker';

interface Cell {
  id: string;
  code: string;
  language: 'python' | 'sql';
  output: string;
  error: string;
  executionCount: number | null;
  rows?: Array<Record<string, any>>;
  columnNames?: string[];
  hasChart?: boolean;
  chartConfig?: {
    chartType: string;
    xAxis: string;
    yAxis: string;
  };
}

interface NotebookContainerProps {
  sessionId: string;
  readonly?: boolean;
}

const NotebookContainer: React.FC<NotebookContainerProps> = ({ sessionId, readonly = false }) => {
  const [cells, setCells] = useState<Cell[]>([
    {
      id: '1',
      code: '-- Write your SQL query here\nSELECT * FROM customers LIMIT 5;',
      language: 'sql',
      output: '',
      error: '',
      executionCount: null,
    },
  ]);
  const [globalExecutionCount, setGlobalExecutionCount] = useState(0);
  const [schemaInfo, setSchemaInfo] = useState<string>('');
  const [dataInfo, setDataInfo] = useState<string>('');

  // Initialize event tracker
  React.useEffect(() => {
    if (!readonly) {
      eventTracker.initialize(sessionId);
      return () => {
        eventTracker.cleanup();
      };
    }
  }, [sessionId, readonly]);

  // Load saved notebook in readonly mode
  React.useEffect(() => {
    if (readonly) {
      loadNotebook();
    }
  }, [readonly, sessionId]);

  // Fetch schema info on mount
  React.useEffect(() => {
    if (!schemaInfo) {
      fetchSchema();
    }
  }, []);

  const fetchSchema = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/database-schema');
      setSchemaInfo(response.data.schema);
    } catch (error) {
      console.error('Error fetching schema:', error);
    }
  };

  const loadNotebook = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/notebooks/${sessionId}/load`);
      if (response.data.cells && response.data.cells.length > 0) {
        setCells(response.data.cells);
        // Set globalExecutionCount to highest execution count
        const maxCount = Math.max(...response.data.cells.map((c: Cell) => c.executionCount || 0));
        setGlobalExecutionCount(maxCount);
        console.log('Loaded saved notebook with', response.data.cells.length, 'cells');
      }
    } catch (error) {
      console.error('Error loading notebook:', error);
    }
  };

  const saveNotebook = async () => {
    if (readonly) return; // Don't save in readonly mode
    try {
      await axios.post(`http://localhost:8000/api/notebooks/${sessionId}/save`, {
        session_id: sessionId,
        cells: cells
      });
      console.log('Notebook saved successfully');
    } catch (error) {
      console.error('Error saving notebook:', error);
    }
  };

  const fetchDataInfo = async () => {
    const info = `📊 Sample Data Information:

**Customers DataFrame** (customers)
- 5 rows × 6 columns
- Columns: customer_id, name, email, age, city, registration_date
- Data: Customer information with demographics

**Orders DataFrame** (orders)  
- 7 rows × 6 columns
- Columns: order_id, customer_id, product_name, category, amount, order_date
- Data: Purchase transactions

💡 Use customers.describe() or orders.head() to explore the data
💡 Both DataFrames are pre-loaded in the first cell`;
    
    setDataInfo(info);
  };

  const addCell = (afterId?: string) => {
    const newCell: Cell = {
      id: Date.now().toString(),
      code: '-- SQL query',
      language: 'sql',
      output: '',
      error: '',
      executionCount: null,
    };

    let newCells;
    if (afterId) {
      const index = cells.findIndex(c => c.id === afterId);
      newCells = [...cells];
      newCells.splice(index + 1, 0, newCell);
      setCells(newCells);
    } else {
      newCells = [...cells, newCell];
      setCells(newCells);
    }
    
    // Auto-save after adding cell
    setTimeout(() => saveNotebook(), 100);
  };

  const deleteCell = (id: string) => {
    if (cells.length > 1) {
      setCells(cells.filter(c => c.id !== id));
      // Auto-save after deleting cell
      setTimeout(() => saveNotebook(), 100);
    }
  };

  const updateCellCode = (id: string, code: string) => {
    setCells(cells.map(c => c.id === id ? { ...c, code } : c));
    // Track code edit
    const cell = cells.find(c => c.id === id);
    if (cell) {
      eventTracker.trackCodeEdit(code, cell.language);
    }
  };

  const handleChartToggle = (id: string, show: boolean, chartConfig?: { chartType: string; xAxis: string; yAxis: string }) => {
    setCells(cells.map(c => c.id === id ? { ...c, hasChart: show, chartConfig: chartConfig || c.chartConfig } : c));
    // Auto-save when chart state changes
    setTimeout(() => saveNotebook(), 100);
  };

  const executeCell = async (id: string) => {
    const cell = cells.find(c => c.id === id);
    if (!cell) return;

    // Track code run
    eventTracker.trackCodeRun(cell.code, cell.language);

    // Increment global execution count
    const executionCount = globalExecutionCount + 1;
    setGlobalExecutionCount(executionCount);

    // Update cell with execution count and clear previous output
    setCells(cells.map(c => 
      c.id === id 
        ? { ...c, executionCount, output: 'Executing...', error: '', rows: undefined, columnNames: undefined } 
        : c
    ));

    try {
      // Use the cell's language, not the global language state
      const endpoint = cell.language === 'python' 
        ? 'http://localhost:8000/api/execute-python'
        : 'http://localhost:8000/api/execute-sql';

      const response = await axios.post(endpoint, {
        code: cell.code,
        language: cell.language,
        session_id: sessionId,  // Pass session_id for event logging
      });

      // Track SQL complexity after execution
      if (cell.language === 'sql') {
        eventTracker.trackSQLComplexity(cell.code);
      }

      // For SQL, store rows and column_names from response
      if (cell.language === 'sql' && response.data.rows) {
        setCells(cells.map(c =>
          c.id === id
            ? {
                ...c,
                output: response.data.output,
                error: response.data.error,
                executionCount,
                rows: response.data.rows,
                columnNames: response.data.column_names,
              }
            : c
        ));
      } else {
        // Python or SQL with no results
        setCells(cells.map(c =>
          c.id === id
            ? {
                ...c,
                output: response.data.output,
                error: response.data.error,
                executionCount,
                rows: undefined,
                columnNames: undefined,
              }
            : c
        ));
      }
      
      // Track successful execution
      eventTracker.trackRunResult(true, response.data.output);
      
      // Save notebook state
      await saveNotebook();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message;
      setCells(cells.map(c =>
        c.id === id
          ? {
              ...c,
              output: '',
              error: errorMessage,
              executionCount,
              rows: undefined,
              columnNames: undefined,
            }
          : c
      ));
      
      // Track execution error
      eventTracker.trackError(errorMessage, { code_snippet: cell.code });
      eventTracker.trackRunResult(false, undefined, errorMessage);
      
      // Save notebook state even with errors
      await saveNotebook();
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#1e1e1e' }}>
      {/* Toolbar */}
      <div style={{
        padding: '8px 16px',
        background: '#2d2d30',
        borderBottom: '1px solid #3e3e42',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ color: '#cccccc', fontSize: '14px', fontWeight: 500 }}>
            �️ SQL Notebook
          </span>

          {schemaInfo && (
            <button
              onClick={() => {
                eventTracker.trackSchemaExplored('database_schema');
                alert(schemaInfo);
              }}
              style={{
                padding: '4px 12px',
                background: '#3e3e42',
                border: '1px solid #454545',
                borderRadius: '4px',
                color: '#cccccc',
                cursor: 'pointer',
                fontSize: '12px',
              }}
              title="View database schema"
            >
              📊 Schema
            </button>
          )}
        </div>

        {!readonly && (
          <button
            onClick={() => addCell()}
            style={{
              padding: '4px 12px',
              background: '#0e639c',
              border: 'none',
              borderRadius: '4px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            + Add Cell
          </button>
        )}
      </div>

      {/* Cells Container */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
      }}>
        {cells.map((cell, index) => (
          <div key={cell.id} style={{ marginBottom: '16px' }}>
            <NotebookCell
              code={cell.code}
              language={cell.language}
              output={cell.output}
              error={cell.error}
              executionCount={cell.executionCount}
              onCodeChange={(code) => updateCellCode(cell.id, code)}
              onExecute={() => executeCell(cell.id)}
              onDelete={() => deleteCell(cell.id)}
              canDelete={cells.length > 1 && !readonly}
              rows={cell.rows}
              columnNames={cell.columnNames}
              readonly={readonly}
              hasChart={cell.hasChart}
              chartConfig={cell.chartConfig}
              onChartToggle={(show, config) => handleChartToggle(cell.id, show, config)}
            />
            {!readonly && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                margin: '8px 0',
              }}>
                <button
                  onClick={() => addCell(cell.id)}
                  style={{
                    padding: '2px 8px',
                    background: 'transparent',
                    border: '1px solid #3e3e42',
                    borderRadius: '3px',
                    color: '#858585',
                    cursor: 'pointer',
                    fontSize: '11px',
                    opacity: 0.5,
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '0.5'}
                >
                  + Code
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotebookContainer;
