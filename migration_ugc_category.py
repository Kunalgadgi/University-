"""
Manual migration to add ugc_category field to AdmissionApplication model
"""
import sqlite3
import os

def add_ugc_category_column():
    # Path to the database
    db_path = os.path.join(os.path.dirname(__file__), 'master_control_project', 'db.sqlite3')
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Available tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Look for admission application table
        admission_table = None
        for table in tables:
            if 'admission' in table[0].lower() and 'application' in table[0].lower():
                admission_table = table[0]
                break
        
        if not admission_table:
            print("❌ No admission application table found!")
            return False
            
        print(f"✅ Found admission table: {admission_table}")
        
        # Check if ugc_category column already exists
        cursor.execute(f"PRAGMA table_info({admission_table});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Current columns: {column_names}")
        
        if 'ugc_category' in column_names:
            print("✅ ugc_category column already exists!")
            return True
        
        # Add the ugc_category column
        cursor.execute(f'''
            ALTER TABLE {admission_table} 
            ADD COLUMN ugc_category VARCHAR(50) DEFAULT ''
        ''')
        
        conn.commit()
        print("✅ ugc_category column added successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_ugc_category_column()
