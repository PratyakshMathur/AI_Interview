"""SQL query execution service"""
import sqlite3
import tempfile
import os
from typing import Tuple, List, Dict, Any

class SQLExecutor:
    """Execute SQL queries in a sandboxed SQLite environment"""
    
    def __init__(self):
        # Create a sample database for practice
        self.db_path = self._create_sample_database()
    
    def _create_sample_database(self) -> str:
        """Create a sample customer database for SQL practice"""
        db_path = os.path.join(tempfile.gettempdir(), 'interview_sample.db')
        
        # Remove existing database
        if os.path.exists(db_path):
            os.remove(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create sample tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER,
                city TEXT,
                registration_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                product_name TEXT,
                category TEXT,
                amount REAL,
                order_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        # Insert sample data
        customers_data = [
            (1, 'Alice Johnson', 'alice@email.com', 28, 'New York', '2024-01-15'),
            (2, 'Bob Smith', 'bob@email.com', 34, 'Los Angeles', '2024-02-20'),
            (3, 'Carol White', 'carol@email.com', 45, 'Chicago', '2024-01-10'),
            (4, 'David Brown', 'david@email.com', 29, 'Houston', '2024-03-05'),
            (5, 'Eve Davis', 'eve@email.com', 52, 'Phoenix', '2024-02-28'),
        ]
        
        cursor.executemany(
            'INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)',
            customers_data
        )
        
        orders_data = [
            (1, 1, 'Laptop', 'Electronics', 1200.00, '2024-03-01'),
            (2, 1, 'Mouse', 'Electronics', 25.00, '2024-03-01'),
            (3, 2, 'Desk Chair', 'Furniture', 350.00, '2024-03-15'),
            (4, 3, 'Monitor', 'Electronics', 400.00, '2024-03-10'),
            (5, 3, 'Keyboard', 'Electronics', 75.00, '2024-03-10'),
            (6, 4, 'Headphones', 'Electronics', 150.00, '2024-03-20'),
            (7, 5, 'Desk', 'Furniture', 500.00, '2024-03-25'),
        ]
        
        cursor.executemany(
            'INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)',
            orders_data
        )
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def execute_query(self, query: str) -> Tuple[bool, str, str]:
        """
        Execute SQL query and return results
        
        Returns:
            Tuple of (success, output, error)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query)
            
            # Check if it's a SELECT query by checking if there are results
            if cursor.description is not None:
                # This is a SELECT query (has columns)
                results = cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
                
                # Format output as table
                output = self._format_table(column_names, results)
                conn.close()
                return True, output, ""
            else:
                # For INSERT, UPDATE, DELETE queries
                conn.commit()
                affected_rows = cursor.rowcount
                conn.close()
                return True, f"Query executed successfully. {affected_rows} row(s) affected.", ""
                
        except sqlite3.Error as e:
            return False, "", f"SQL Error: {str(e)}"
        except Exception as e:
            return False, "", f"Error: {str(e)}"
    
    def _format_table(self, columns: List[str], rows: List[Tuple]) -> str:
        """Format query results as a readable table"""
        if not rows:
            return "Query returned no results."
        
        # Calculate column widths
        col_widths = [len(col) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        
        # Create header
        header = " | ".join(col.ljust(col_widths[i]) for i, col in enumerate(columns))
        separator = "-+-".join("-" * width for width in col_widths)
        
        # Create rows
        formatted_rows = []
        for row in rows:
            formatted_row = " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
            formatted_rows.append(formatted_row)
        
        # Combine everything
        output = f"{header}\n{separator}\n" + "\n".join(formatted_rows)
        output += f"\n\n({len(rows)} row(s) returned)"
        
        return output
    
    def get_schema_info(self) -> str:
        """Get database schema information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema_info = "📊 Database Schema:\n\n"
        
        for table in tables:
            table_name = table[0]
            schema_info += f"Table: {table_name}\n"
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name, col_type = col[1], col[2]
                schema_info += f"  - {col_name} ({col_type})\n"
            
            schema_info += "\n"
        
        conn.close()
        return schema_info
