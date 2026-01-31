# Jupyter Notebook-Style Interface with Python/SQL Toggle

## Overview
The AI Interview Platform now features a Jupyter notebook-style interface that allows candidates to write and execute code in individual cells, with support for both Python and SQL.

## Features Implemented

### 1. Notebook Cell Component (`NotebookCell.tsx`)
- **Individual Execution**: Each cell can be run independently with the ▶ Run button or Shift+Enter
- **Execution Counter**: Tracks execution order with `[n]` notation
- **Output Display**: Shows output/errors inline below each cell
- **Language Support**: Python and SQL syntax highlighting via Monaco Editor
- **Dark Theme**: Matches VS Code dark theme for consistency

### 2. Notebook Container (`NotebookContainer.tsx`)
- **Multiple Cells**: Add/delete cells dynamically
- **Language Toggle**: Switch between Python and SQL modes with 🐍/🗄️ buttons
- **Database Schema**: View database structure when in SQL mode
- **Cell Management**: Add cells between existing cells with + Code buttons
- **Auto-language Update**: All cells update when toggling language

### 3. Backend SQL Executor (`sql_executor.py`)
- **SQLite Database**: Pre-populated sample database with customers and orders tables
- **Safe Execution**: Sandboxed environment for SQL queries
- **Formatted Output**: Pretty-printed table results with column headers
- **Schema Info**: Endpoint to retrieve database structure

### 4. Backend API Endpoints
- `POST /api/execute-sql`: Execute SQL queries
- `GET /api/database-schema`: Get database schema information
- `POST /api/execute-python`: Execute Python code (existing)

### 5. Sample Database Schema
```
customers table:
  - customer_id (INTEGER)
  - name (TEXT)
  - email (TEXT)
  - age (INTEGER)
  - city (TEXT)
  - registration_date (TEXT)

orders table:
  - order_id (INTEGER)
  - customer_id (INTEGER)
  - product_name (TEXT)
  - category (TEXT)
  - amount (REAL)
  - order_date (TEXT)
```

## Usage

### Switching Modes
1. Click the 📝 Editor / 📓 Notebook toggle in the top toolbar
2. Editor mode: Single file with terminal output (classic mode)
3. Notebook mode: Multiple cells with inline output (Jupyter-style)

### Language Toggle (Notebook Mode)
1. Click 🐍 Python or 🗄️ SQL to switch languages
2. All cells will update to the new language
3. SQL mode shows a 📊 Schema button to view database structure

### Running Code
- Click ▶ Run button in cell header
- Press Shift+Enter while editing
- Execution counter increments: `[1]`, `[2]`, etc.

### Managing Cells
- **Add Cell**: Click "+ Add Cell" in toolbar (adds at bottom)
- **Insert Cell**: Click "+ Code" between cells
- **Delete Cell**: Click 🗑️ button (must have >1 cell)

## Example Workflows

### Python Analysis
```python
# Cell 1: Import and explore
import pandas as pd
print("Starting analysis...")

# Cell 2: Data manipulation
data = {'name': ['Alice', 'Bob'], 'age': [25, 30]}
df = pd.DataFrame(data)
print(df)

# Cell 3: Results
print(df['age'].mean())
```

### SQL Queries
```sql
-- Cell 1: Basic query
SELECT * FROM customers LIMIT 5;

-- Cell 2: Join analysis
SELECT c.name, COUNT(o.order_id) as total_orders
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.name;

-- Cell 3: Aggregate statistics
SELECT category, SUM(amount) as total_sales
FROM orders
GROUP BY category
ORDER BY total_sales DESC;
```

## Technical Details

### File Structure
```
frontend/src/components/
  ├── NotebookCell.tsx        # Individual cell component
  ├── NotebookContainer.tsx   # Cell management container
  └── CandidateWorkspace.tsx  # Main workspace with mode toggle

backend/
  ├── sql_executor.py         # SQL query execution
  └── main.py                 # API endpoints
```

### State Management
- **NotebookContainer**: Manages cell array, execution counter, language state
- **NotebookCell**: Displays code/output, handles Monaco Editor integration
- **CandidateWorkspace**: Toggles between editor and notebook views

### Execution Flow
1. User writes code in Monaco Editor
2. Clicks Run or presses Shift+Enter
3. NotebookContainer calls appropriate backend endpoint (`/execute-python` or `/execute-sql`)
4. Backend executes code in sandboxed environment
5. Results displayed inline in cell output area

## Benefits
- **Same Problem, Different Languages**: Candidates can solve the same data analysis problem using Python OR SQL
- **No Terminal Needed**: Output appears directly below cells
- **Cell-by-Cell Debugging**: Test small pieces of code incrementally
- **Familiar Interface**: Jupyter-style workflow for data scientists
- **Real Execution**: Both Python and SQL execute on the backend with actual data

## Future Enhancements
- [ ] Markdown cells for documentation
- [ ] Cell output visualization (plots/charts)
- [ ] Cell execution status indicators
- [ ] Keyboard shortcuts (add cell, delete cell)
- [ ] Cell reordering (drag & drop)
- [ ] Export notebook as .ipynb file
