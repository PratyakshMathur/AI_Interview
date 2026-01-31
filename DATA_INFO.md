# Sample Data Location & Information

## 📊 Data Sources

### Python Data (In-Memory)
The Python notebooks load data **in-memory** from CSV strings. The data is not stored in files.

**Location:** Embedded in the first cell code
**Files:** `/Users/pratyaksh/UTA/AI_Interview_v1/backend/data_loader.py`

**DataFrames:**
1. **customers** - 5 customers with demographics
2. **orders** - 7 purchase transactions

### SQL Data (SQLite Database)
The SQL data is stored in a SQLite database file.

**Location:** `/Users/pratyaksh/UTA/AI_Interview_v1/backend/ai_interview.db`  
**Temporary Sample DB:** `/tmp/interview_sample.db`

**Tables:**
1. **customers** - Same 5 customers as Python data
2. **orders** - Same 7 orders as Python data

## 🔄 Data Synchronization

Both Python and SQL use **identical sample data** so candidates can solve the same problem using either language.

### Sample Data:

**Customers:**
- Alice Johnson (28, New York)
- Bob Smith (34, Los Angeles)
- Carol White (45, Chicago)
- David Brown (29, Houston)
- Eve Davis (52, Phoenix)

**Orders:**
- Electronics: Laptop ($1200), Mouse ($25), Monitor ($400), Keyboard ($75), Headphones ($150)
- Furniture: Desk Chair ($350), Desk ($500)

## 📝 How It Works

### Python Mode:
1. First cell contains data loading code
2. Creates `customers` and `orders` DataFrames
3. Data is loaded from CSV strings using `pd.read_csv(io.StringIO())`
4. Click "📊 Data Info" button to see structure

### SQL Mode:
1. Data is pre-loaded in SQLite database (`/tmp/interview_sample.db`)
2. Query using `SELECT * FROM customers` or `SELECT * FROM orders`
3. Click "📊 Schema" button to see table structure
4. Database created automatically by `sql_executor.py`

## 🗑️ Clearing Data

To reset all data:
```bash
./clean_db.sh --clear-data   # Clear session data only
./clean_db.sh --reset        # Reset entire database
```

**Note:** The sample data (customers/orders) is **recreated automatically** on each backend start. Only interview session data is cleared.
