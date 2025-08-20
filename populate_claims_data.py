import pandas as pd
from sqlalchemy.orm import Session
from database import get_db, create_tables, ClaimsList, ClaimsDetail
from datetime import datetime
import os

def populate_claims_data():
    """Populate the claims tables with data from CSV files"""
    
    create_tables()
    
    claims_list_df = pd.read_csv('/home/ubuntu/attachments/3f2b4685-d503-4d29-a1c8-fd1ef23efab9/claim_list_data.csv')
    claims_detail_df = pd.read_csv('/home/ubuntu/attachments/6f16af9c-4da0-42bc-9542-a63111f3529e/claim_detail_data.csv')
    
    db = next(get_db())
    
    try:
        db.query(ClaimsDetail).delete()
        db.query(ClaimsList).delete()
        db.commit()
        
        print("Populating Claims List table...")
        
        for _, row in claims_list_df.iterrows():
            claim = ClaimsList(
                id=int(row['id']),
                patient_name=str(row['patient_name']),
                billed_amount=float(row['billed_amount']),
                paid_amount=float(row['paid_amount']),
                status=str(row['status']),
                insurer_name=str(row['insurer_name']),
                discharge_date=datetime.strptime(row['discharge_date'], '%Y-%m-%d').date()
            )
            db.add(claim)
        
        db.commit()
        print(f"Successfully inserted {len(claims_list_df)} records into Claims List table")
        
        print("Populating Claims Detail table...")
        
        for _, row in claims_detail_df.iterrows():
            detail = ClaimsDetail(
                id=int(row['id']),
                claim_id=int(row['claim_id']),
                denial_reason=str(row['denial_reason']) if pd.notna(row['denial_reason']) and row['denial_reason'] != 'N/A' else None,
                cpt_codes=str(row['cpt_codes']) if pd.notna(row['cpt_codes']) else None
            )
            db.add(detail)
        
        db.commit()
        print(f"Successfully inserted {len(claims_detail_df)} records into Claims Detail table")
        
        claims_count = db.query(ClaimsList).count()
        details_count = db.query(ClaimsDetail).count()
        
        print(f"\nData verification:")
        print(f"Claims List records: {claims_count}")
        print(f"Claims Detail records: {details_count}")
        
        print(f"\nSample Claims List data:")
        sample_claims = db.query(ClaimsList).limit(3).all()
        for claim in sample_claims:
            print(f"ID: {claim.id}, Patient: {claim.patient_name}, Status: {claim.status}, Billed: ${claim.billed_amount}")
        
        print(f"\nSample Claims Detail data:")
        sample_details = db.query(ClaimsDetail).limit(3).all()
        for detail in sample_details:
            print(f"ID: {detail.id}, Claim ID: {detail.claim_id}, Denial Reason: {detail.denial_reason}, CPT Codes: {detail.cpt_codes}")
        
    except Exception as e:
        print(f"Error populating data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_claims_data()
