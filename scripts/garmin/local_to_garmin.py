import argparse
import os
import sqlite3
from garmin_client import GarminClient  # Assuming garmin_client.py is the file name of your provided script

def get_uploaded_files(db_conn):
    cursor = db_conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS uploaded_files (file_name TEXT PRIMARY KEY)')
    cursor.execute('SELECT file_name FROM uploaded_files')
    return {row[0] for row in cursor.fetchall()}

def mark_file_as_uploaded(db_conn, file_name):
    cursor = db_conn.cursor()
    cursor.execute('INSERT INTO uploaded_files (file_name) VALUES (?)', (file_name,))
    db_conn.commit()

def main(garmin_email, garmin_password, local_dir):
    if not os.path.exists(local_dir):
        print(f"Directory {local_dir} does not exist.")
        return
    
    db_path = os.path.join(local_dir, 'uploaded_files.db')
    db_conn = sqlite3.connect(db_path)
    
    garmin_client = GarminClient(garmin_email, garmin_password, None)  # Assuming auth_domain is not needed, replace None if needed
    
    uploaded_files = get_uploaded_files(db_conn)
    
    for file_name in os.listdir(local_dir):
        if file_name in uploaded_files:
            print(f"Skipping {file_name}, already uploaded.")
            continue
        
        file_path = os.path.join(local_dir, file_name)
        if os.path.isfile(file_path) and file_name.endswith('.fit'):
            try:
                response = garmin_client.upload_activity(file_path)
                if response.ok:
                    print(f"Successfully uploaded {file_name}.")
                    mark_file_as_uploaded(db_conn, file_name)
                elif response.status_code == 409:
                    print(f"Conflict: {file_name} already exists on Garmin. Marking as uploaded.")
                    mark_file_as_uploaded(db_conn, file_name)  # Mark file as uploaded on conflict
                else:
                    print(f"Failed to upload {file_name}, response: {response.text}")
            except Exception as e:
                print(f"An error occurred while uploading {file_name}: {e}")
    
    db_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("garmin_email", help="Email for Garmin account")
    parser.add_argument("garmin_password", help="Password for Garmin account")
    parser.add_argument("local_dir", help="Directory containing .fit files to upload")
    args = parser.parse_args()
    
    main(args.garmin_email, args.garmin_password, args.local_dir)
