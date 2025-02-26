import psycopg2
from config import DB_CONFIG

def insert_companies():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Design schema and table
    cursor.execute("CREATE SCHEMA IF NOT EXISTS Ginkgo;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ginkgo.csr_reports (
            symbol VARCHAR(50),
            company_name TEXT NOT NULL,
            report_year INT NOT NULL,
            report_url TEXT,    
            minio_path TEXT,
            PRIMARY KEY (symbol, report_year)     
        );
    """)

    conn.commit()
    print("✅ Database setup completed!")

    # Select all companies (column name `security` corresponds to company name)
    cursor.execute("""
        SELECT symbol, security FROM csr_reporting.company_static
        ORDER BY symbol;
    """)
    companies = cursor.fetchall()

    for symbol, security in companies:
        for year in range(2014, 2024):
            cursor.execute("""
                   INSERT INTO Ginkgo.csr_reports (symbol, company_name, report_year)
                   VALUES (%s, %s, %s)
                   ON CONFLICT DO nothing;
               """, (symbol, security, year))

    conn.commit()
    cursor.close()
    conn.close()
    print("Successfully inserted companies into csr_reports")

# Run
if __name__ == "__main__":
   insert_companies()

