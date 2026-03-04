import os
import shutil
from csmarapi.CsmarService import CsmarService

def main():
    csmar = CsmarService()
    print("Logging in...")
    csmar.login('2412782@mail.nankai.edu.cn', '21288480Yy')
    print("Logged in successfully.")

    # We will pick up just SRDI_EntInfo and SRDI_EntPatentInfo.
    tables_to_download = [
        'SRDI_EntInfo',
        'SRDI_EntPatentInfo'
    ]

    for table in tables_to_download:
        print(f"\nProcessing table via Pack Ext: {table}")
        try:
            fields_data = csmar.getListFields(table)
            if not fields_data:
                print(f"  Could not get fields for {table}, skipping.")
                continue
            
            columns = [field.get("field") for field in fields_data if field.get("field")]
            
            condition = "1=1"
            
            # This method automatically saves to c:\csmardata\zip\{signCode}.zip
            print(f"  Requesting Pack Result for {table}...")
            # We must use "1=1" or condition as empty if no filter
            csmar.getPackResultExt(columns, "", table)
            
            # After getting it, the file should be in c:\\csmardata\\zip\\
            # Let's read the signCode from token file or we can just find it
            # The API saves `signCode.txt` in current dir
            signCode = None
            if os.path.exists("signCode.txt"):
                with open("signCode.txt", "r") as f:
                    signCode = f.read().strip()
            
            if signCode:
                zip_path = f"c:\\csmardata\\zip\\{signCode}.zip"
                if os.path.exists(zip_path):
                    print(f"  Found downloaded zip: {zip_path}. Unzipping...")
                    csmar.unzipSingle(zip_path)
                    
                    unzip_dir = f"c:\\csmardata\\{signCode}"
                    print(f"  Checking unzipped contents in {unzip_dir}...")
                    
                    # Usually it unzips to a CSV file named after the table
                    # Let's copy it to our workspace
                    dest_dir = "csmar_data_export"
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    if os.path.exists(unzip_dir):
                        for file in os.listdir(unzip_dir):
                            if file.endswith('.csv'):
                                src_file = os.path.join(unzip_dir, file)
                                dest_file = os.path.join(dest_dir, f"{table}_packed.csv")
                                shutil.copy2(src_file, dest_file)
                                print(f"  Moved fully packed data to {dest_file}")
                else:
                    print(f"  Failed: Expected zip file not found at {zip_path}")
            else:
                print(f"  Failed to retrieve signCode.")
                
        except Exception as e:
            print(f"  Error processing {table}: {e}")

if __name__ == "__main__":
    main()
