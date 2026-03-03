import os
import pandas as pd
from csmarapi.CsmarService import CsmarService

def main():
    csmar = CsmarService()
    print("Logging in...")
    csmar.login('2412782@mail.nankai.edu.cn', '21288480Yy')
    print("Logged in successfully.")

    tables_to_download = [
        'SRDI_EntIdentInfo',
        'SRDI_EntInfo',
        'SRDI_EntMainFinIndex',
        'SRDI_EntPatentInfo'
    ]

    output_dir = "csmar_data_export"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for table in tables_to_download:
        print(f"\nProcessing table: {table}")
        try:
            fields_data = csmar.getListFields(table)
            if not fields_data:
                print(f"  Could not get fields for {table}, skipping.")
                continue
            
            columns = [field.get("field") for field in fields_data if field.get("field")]
            
            # Find the total count using queryCount
            # Important: It seems we need a valid condition or "1=1" is not accepted.
            # Tutorial used "Stkcd like'3%'" or similar. Let's try finding the first column name
            # and use it for condition like: `column_name is not null`
            first_col = columns[0]
            condition = f"{first_col} is not null"
            
            count = csmar.queryCount(columns, condition, table)
            print(f"  Total records for {table}: {count}")
            
            # Since some tables might have massive amounts of data, let's limit downloading to first 100k or user needs?
            # User says: "现在将匹配到的数据下载到本地". So we should download all of it.
            if count == 0:
                print(f"  No data found for {table}")
                continue
            
            if count > 200000:
                print("  Data too large, pagination required.")
            
            # Pagination loop
            limit = 200000
            offset = 0
            all_dfs = []
            output_file = os.path.join(output_dir, f"{table}.csv")
            
            # Only do first 2 chunks for now if data is extremely large (to avoid freezing)
            # Actually we should get all.
            while offset < count:
                print(f"  Fetching records {offset} to {offset+limit}...")
                paginated_condition = f"{condition} limit {offset},{limit}"
                df = csmar.query_df(columns, paginated_condition, table)
                
                if df is not None and not df.empty:
                    # Write header only for the first chunk
                    mode = 'w' if offset == 0 else 'a'
                    header = True if offset == 0 else False
                    df.to_csv(output_file, mode=mode, header=header, index=False, encoding="utf-8-sig")
                else:
                    print(f"  No data returned for offset {offset}")
                    break
                
                offset += limit
                
            print(f"  Finished extracting {table} to {output_file}")
            
        except Exception as e:
            print(f"  Error processing {table}: {e}")

if __name__ == "__main__":
    main()
