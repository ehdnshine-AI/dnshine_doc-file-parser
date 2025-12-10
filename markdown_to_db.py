import psycopg2
from db_config import DB_CONFIG

# Function to create table markdown_table

def create_markdown_table():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"]
        )
        cur = conn.cursor()
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS markdown_table (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL
            );
        '''
        cur.execute(create_table_query)
        conn.commit()
        cur.close()
        print("Table markdown_table created successfully.")
    except Exception as error:
        print(f"Error creating table: {error}")
    finally:
        if conn:
            conn.close()

# Function to insert markdown content into markdown_table

def insert_markdown_content(content):
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"]
        )
        cur = conn.cursor()
        insert_query = "INSERT INTO markdown_table (content) VALUES (%s)"
        cur.execute(insert_query, (content,))
        conn.commit()
        cur.close()
        print("Markdown content inserted successfully.")
    except Exception as error:
        print(f"Error inserting markdown content: {error}")
    finally:
        if conn:
            conn.close()

# Example usage
if __name__ == "__main__":
    create_markdown_table()
    example_markdown = "# This is a markdown header\nHere is some markdown content."
    insert_markdown_content(example_markdown)
