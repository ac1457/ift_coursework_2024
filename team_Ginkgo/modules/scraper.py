import psycopg2
from googleapiclient.discovery import build
from config import DB_CONFIG, GOOGLE_API_KEY, GOOGLE_CX
from concurrent.futures import ThreadPoolExecutor
import time
import random

# Get database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# Google API search PDF reports (with retry mechanism)
def google_search_pdf(company_name, year):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    query = f"{company_name} CSR report {year} filetype:pdf"

    attempts = 0  # Record attempt count
    while attempts < 3:  # Maximum 3 attempts
        try:
            sleep_time = random.uniform(1, 3)  # Random wait 1-3 seconds
            time.sleep(sleep_time)

            res = service.cse().list(q=query, cx=GOOGLE_CX).execute()
            pdf_links = [item['link'] for item in res.get('items', []) if item['link'].endswith('.pdf')]

            if pdf_links:
                return pdf_links[0]  # Successfully found PDF, return immediately
        except Exception as e:
            print(f"Attempt {attempts+1} failed: {company_name} {year} - {e}")

        attempts += 1  # Increase attempt count

    print(f"{company_name} {year} failed after 3 attempts")
    return None

# Get companies to scrape
def get_companies_to_scrape():
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT symbol, company_name, report_year 
        FROM Ginkgo.csr_reports  -- Query Full List table
        WHERE report_url IS NULL;
    """)
    companies = cursor.fetchall()

    cursor.close()
    conn.close()
    return companies  # [(symbol, company_name, report_year), ...]

# Multithreaded execution of scraping & database update
def process_company_data(company_data):
    symbol, company_name, report_year = company_data
    pdf_url = google_search_pdf(company_name, report_year)

    if pdf_url:
        conn = get_db_connection()  # Each thread independently gets database connection
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Ginkgo.csr_reports 
                    SET report_url = %s 
                    WHERE symbol = %s AND report_year = %s;
                """, (pdf_url, symbol, report_year))
                conn.commit()
                print(f"Update successful: {company_name} {report_year}: {pdf_url}")
            except Exception as e:
                print(f"Database update failed: {company_name} {report_year} - {e}")
            finally:
                cursor.close()
                conn.close()
    else:
        print(f"Failed after 3 attempts: {company_name} {report_year}")

# Main function: Multithreaded execution of scraping
def multithread_update_csr_reports():
    start_time = time.time()  # Timing
    companies = get_companies_to_scrape()

    if not companies:
        print("No data to scrape, check if the database is fully updated!")
        return

    max_threads = 10  # Number of threads, adjustable
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(process_company_data, companies)

    end_time = time.time()
    print(f"Multithreaded scraping completed! Time taken: {end_time - start_time:.2f} seconds")

# Run
if __name__ == "__main__":
   multithread_update_csr_reports()
