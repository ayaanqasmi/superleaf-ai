import psycopg2

# Connect to your database
conn = psycopg2.connect(
    dbname="mydb",
    user="postgres",
    password="1234",
    host="localhost",
    port=5433
)

cursor = conn.cursor()

# Read SQL file
with open("setup_rag.sql", "r") as f:
    sql = f.read()

# Execute SQL script
cursor.execute(sql)
conn.commit()

print("✅ RAG vector table and extension set up successfully.")

# Close connection
cursor.close()
conn.close()
