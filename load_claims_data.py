import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def load_claims_data():
    """Load claims data directly into PostgreSQL tables"""
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/pdf_chat_db")
    engine = create_engine(DATABASE_URL)
    
    claims_list_df = pd.read_csv('/home/ubuntu/attachments/3f2b4685-d503-4d29-a1c8-fd1ef23efab9/claim_list_data.csv', sep='|')
    claims_detail_df = pd.read_csv('/home/ubuntu/attachments/6f16af9c-4da0-42bc-9542-a63111f3529e/claim_detail_data.csv', 
                                   sep='|', on_bad_lines='skip', engine='python')
    
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM claims_detail"))
            conn.execute(text("DELETE FROM claims_list"))
            conn.commit()
            
            print("Loading Claims List data...")
            print(f"Columns in claims_list_df: {list(claims_list_df.columns)}")
            
            for _, row in claims_list_df.iterrows():
                conn.execute(text("""
                    INSERT INTO claims_list (id, patient_name, billed_amount, paid_amount, status, insurer_name, discharge_date)
                    VALUES (:id, :patient_name, :billed_amount, :paid_amount, :status, :insurer_name, :discharge_date)
                """), {
                    'id': int(row['id']),
                    'patient_name': str(row['patient_name']),
                    'billed_amount': float(row['billed_amount']),
                    'paid_amount': float(row['paid_amount']),
                    'status': str(row['status']),
                    'insurer_name': str(row['insurer_name']),
                    'discharge_date': datetime.strptime(row['discharge_date'], '%Y-%m-%d').date()
                })
            
            print(f"Successfully inserted {len(claims_list_df)} records into claims_list table")
            
            print("Loading Claims Detail data...")
            print(f"Columns in claims_detail_df: {list(claims_detail_df.columns)}")
            
            for _, row in claims_detail_df.iterrows():
                conn.execute(text("""
                    INSERT INTO claims_detail (id, claim_id, denial_reason, cpt_codes)
                    VALUES (:id, :claim_id, :denial_reason, :cpt_codes)
                """), {
                    'id': int(row['id']),
                    'claim_id': int(row['claim_id']),
                    'denial_reason': str(row['denial_reason']) if pd.notna(row['denial_reason']) and row['denial_reason'] != 'N/A' else None,
                    'cpt_codes': str(row['cpt_codes']) if pd.notna(row['cpt_codes']) else None
                })
            
            conn.commit()
            print(f"Successfully inserted {len(claims_detail_df)} records into claims_detail table")
            
            result = conn.execute(text("SELECT COUNT(*) FROM claims_list")).fetchone()
            claims_count = result[0]
            result = conn.execute(text("SELECT COUNT(*) FROM claims_detail")).fetchone()
            details_count = result[0]
            
            print(f"\nData verification:")
            print(f"Claims List records: {claims_count}")
            print(f"Claims Detail records: {details_count}")
            
            print(f"\nSample Claims List data:")
            sample_claims = conn.execute(text("SELECT id, patient_name, status, billed_amount FROM claims_list LIMIT 3")).fetchall()
            for claim in sample_claims:
                print(f"ID: {claim[0]}, Patient: {claim[1]}, Status: {claim[2]}, Billed: ${claim[3]}")
            
            print(f"\nSample Claims Detail data:")
            sample_details = conn.execute(text("SELECT id, claim_id, denial_reason, cpt_codes FROM claims_detail LIMIT 3")).fetchall()
            for detail in sample_details:
                print(f"ID: {detail[0]}, Claim ID: {detail[1]}, Denial Reason: {detail[2]}, CPT Codes: {detail[3]}")
            
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise

if __name__ == "__main__":
    load_claims_data()
