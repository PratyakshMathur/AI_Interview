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
}

interface NotebookContainerProps {
  language: 'python' | 'sql';
  onLanguageChange: (language: 'python' | 'sql') => void;
  sessionId: string;
}

const NotebookContainer: React.FC<NotebookContainerProps> = ({ language, onLanguageChange, sessionId }) => {
  const [cells, setCells] = useState<Cell[]>([
    {
      id: '1',
      code: language === 'python' 
        ? '# Load sample data\nimport pandas as pd\nimport io\n\n# Sample customer data\ncustomers_data = """customer_id,name,email,age,city,registration_date\n1,Alice Johnson,alice@email.com,28,New York,2024-01-15\n2,Bob Smith,bob@email.com,34,Los Angeles,2024-02-20\n3,Carol White,carol@email.com,45,Chicago,2024-01-10\n4,David Brown,david@email.com,29,Houston,2024-03-05\n5,Eve Davis,eve@email.com,52,Phoenix,2024-02-28"""\n\ncustomers = pd.read_csv(io.StringIO(customers_data))\n\n# Sample orders data\norders_data = """order_id,customer_id,product_name,category,amount,order_date\n1,1,Laptop,Electronics,1200.00,2024-03-01\n2,1,Mouse,Electronics,25.00,2024-03-01\n3,2,Desk Chair,Furniture,350.00,2024-03-15\n4,3,Monitor,Electronics,400.00,2024-03-10\n5,3,Keyboard,Electronics,75.00,2024-03-10\n6,4,Headphones,Electronics,150.00,2024-03-20\n7,5,Desk,Furniture,500.00,2024-03-25"""\n\norders = pd.read_csv(io.StringIO(orders_data))\n\nprint("📊 Data loaded successfully!")\nprint(f"Customers: {len(customers)} rows, {len(customers.columns)} columns")\nprint(f"Orders: {len(orders)} rows, {len(orders.columns)} columns")'
        : '-- Write your SQL query here\nSELECT * FROM customers LIMIT 5;',
      language,
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
    eventTracker.initialize(sessionId);
    return () => {
      eventTracker.cleanup();
    };
  }, [sessionId]);

  // Fetch schema info when switching to SQL
  React.useEffect(() => {
    if (language === 'sql' && !schemaInfo) {
      fetchSchema();
    }
    if (language === 'python' && !dataInfo) {
      fetchDataInfo();
    }
  }, [language]);

  const fetchSchema = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/database-schema');
      setSchemaInfo(response.data.schema);
    } catch (error) {
      console.error('Error fetching schema:', error);
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

  const handleLanguageToggle = () => {
    const newLanguage = language === 'python' ? 'sql' : 'python';
    onLanguageChange(newLanguage);
    
    // Update ALL cells to the new language - no mixing allowed
    setCells(prevCells => prevCells.map((cell, index) => ({
      ...cell,
      language: newLanguage,
      // Only reset code for the first cell to have starter template
      code: index === 0 
        ? (newLanguage === 'python' 
          ? '# Load sample data\nimport pandas as pd\nimport io\n\n# Sample customer data\ncustomers_data = """customer_id,name,email,age,city,registration_date\n1,Alice Johnson,alice@email.com,28,New York,2024-01-15\n2,Bob Smith,bob@email.com,34,Los Angeles,2024-02-20\n3,Carol White,carol@email.com,45,Chicago,2024-01-10\n4,David Brown,david@email.com,29,Houston,2024-03-05\n5,Eve Davis,eve@email.com,52,Phoenix,2024-02-28"""\n\ncustomers = pd.read_csv(io.StringIO(customers_data))\n\n# Sample orders data\norders_data = """order_id,customer_id,product_name,category,amount,order_date\n1,1,Laptop,Electronics,1200.00,2024-03-01\n2,1,Mouse,Electronics,25.00,2024-03-01\n3,2,Desk Chair,Furniture,350.00,2024-03-15\n4,3,Monitor,Electronics,400.00,2024-03-10\n5,3,Keyboard,Electronics,75.00,2024-03-10\n6,4,Headphones,Electronics,150.00,2024-03-20\n7,5,Desk,Furniture,500.00,2024-03-25"""\n\norders = pd.read_csv(io.StringIO(orders_data))\n\nprint("📊 Data loaded successfully!")\nprint(f"Customers: {len(customers)} rows, {len(customers.columns)} columns")\nprint(f"Orders: {len(orders)} rows, {len(orders.columns)} columns")'
          : '-- Write your SQL query here\nSELECT * FROM customers LIMIT 5;')
        : cell.code,  // Keep existing code for other cells
      output: '',
      error: '',
      executionCount: null,
    })));
  };

  const addCell = (afterId?: string) => {
    const newCell: Cell = {
      id: Date.now().toString(),
      code: language === 'python' 
        ? '# Python code\nimport pandas as pd\n\n' 
        : '-- SQL query\nSELECT * FROM customers LIMIT 5;',
      language,  // Use current global language for new cells
      output: '',
      error: '',
      executionCount: null,
    };

    if (afterId) {
      const index = cells.findIndex(c => c.id === afterId);
      const newCells = [...cells];
      newCells.splice(index + 1, 0, newCell);
      setCells(newCells);
    } else {
      setCells([...cells, newCell]);
    }
  };

  const deleteCell = (id: string) => {
    if (cells.length > 1) {
      setCells(cells.filter(c => c.id !== id));
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
        ? { ...c, executionCount, output: 'Executing...', error: '' } 
        : c
    ));

    try {
      // Use the cell's language, not the global language state
      const endpoint = cell.language === 'python' 
        ? 'http://localhost:8000/api/execute-python'
        : 'http://localhost:8000/api/execute-sql';

      const response = await axios.post(endpoint, {
        code: cell.code,
        language: cell.language,  // Use cell's language
      });

      setCells(cells.map(c =>
        c.id === id
          ? {
              ...c,
              output: response.data.output,
              error: response.data.error,
              executionCount,
            }
          : c
      ));
      
      // Track successful execution
      eventTracker.trackRunResult(true, response.data.output);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message;
      setCells(cells.map(c =>
        c.id === id
          ? {
              ...c,
              output: '',
              error: errorMessage,
              executionCount,
            }
          : c
      ));
      
      // Track execution error
      eventTracker.trackError(errorMessage, { code_snippet: cell.code });
      eventTracker.trackRunResult(false, undefined, errorMessage);
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
            📓 Notebook
          </span>
          
          {/* Language Toggle */}
          <div style={{ display: 'flex', background: '#1e1e1e', borderRadius: '4px', overflow: 'hidden' }}>
            <button
              onClick={handleLanguageToggle}
              style={{
                padding: '4px 12px',
                background: language === 'python' ? '#0e639c' : 'transparent',
                border: 'none',
                color: '#cccccc',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              🐍 Python
            </button>
            <button
              onClick={handleLanguageToggle}
              style={{
                padding: '4px 12px',
                background: language === 'sql' ? '#0e639c' : 'transparent',
                border: 'none',
                color: '#cccccc',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              🗄️ SQL
            </button>
          </div>

          {language === 'sql' && schemaInfo && (
            <button
              onClick={() => alert(schemaInfo)}
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

          {language === 'python' && dataInfo && (
            <button
              onClick={() => alert(dataInfo)}
              style={{
                padding: '4px 12px',
                background: '#3e3e42',
                border: '1px solid #454545',
                borderRadius: '4px',
                color: '#cccccc',
                cursor: 'pointer',
                fontSize: '12px',
              }}
              title="View data information"
            >
              📊 Data Info
            </button>
          )}
        </div>

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
              canDelete={cells.length > 1}
            />
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
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotebookContainer;
