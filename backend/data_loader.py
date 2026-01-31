"""Python data loader for interview environment"""
import pandas as pd
import io

def get_sample_dataframe():
    """Get the sample customer data as a pandas DataFrame"""
    
    # Customer data (same as SQL database)
    customers_data = """customer_id,name,email,age,city,registration_date
1,Alice Johnson,alice@email.com,28,New York,2024-01-15
2,Bob Smith,bob@email.com,34,Los Angeles,2024-02-20
3,Carol White,carol@email.com,45,Chicago,2024-01-10
4,David Brown,david@email.com,29,Houston,2024-03-05
5,Eve Davis,eve@email.com,52,Phoenix,2024-02-28"""
    
    customers_df = pd.read_csv(io.StringIO(customers_data))
    
    # Orders data
    orders_data = """order_id,customer_id,product_name,category,amount,order_date
1,1,Laptop,Electronics,1200.00,2024-03-01
2,1,Mouse,Electronics,25.00,2024-03-01
3,2,Desk Chair,Furniture,350.00,2024-03-15
4,3,Monitor,Electronics,400.00,2024-03-10
5,3,Keyboard,Electronics,75.00,2024-03-10
6,4,Headphones,Electronics,150.00,2024-03-20
7,5,Desk,Furniture,500.00,2024-03-25"""
    
    orders_df = pd.read_csv(io.StringIO(orders_data))
    
    return customers_df, orders_df

# Export data loading code as string for execution
SAMPLE_DATA_CODE = '''import pandas as pd
import io

# Load sample customer data
customers_data = """customer_id,name,email,age,city,registration_date
1,Alice Johnson,alice@email.com,28,New York,2024-01-15
2,Bob Smith,bob@email.com,34,Los Angeles,2024-02-20
3,Carol White,carol@email.com,45,Chicago,2024-01-10
4,David Brown,david@email.com,29,Houston,2024-03-05
5,Eve Davis,eve@email.com,52,Phoenix,2024-02-28"""

customers = pd.read_csv(io.StringIO(customers_data))

# Load sample orders data
orders_data = """order_id,customer_id,product_name,category,amount,order_date
1,1,Laptop,Electronics,1200.00,2024-03-01
2,1,Mouse,Electronics,25.00,2024-03-01
3,2,Desk Chair,Furniture,350.00,2024-03-15
4,3,Monitor,Electronics,400.00,2024-03-10
5,3,Keyboard,Electronics,75.00,2024-03-10
6,4,Headphones,Electronics,150.00,2024-03-20
7,5,Desk,Furniture,500.00,2024-03-25"""

orders = pd.read_csv(io.StringIO(orders_data))

# Display data info
print("📊 Sample Data Loaded!")
print(f"\\nCustomers: {len(customers)} rows")
print(f"Orders: {len(orders)} rows")
print("\\nUse 'customers' and 'orders' DataFrames for analysis")
'''
