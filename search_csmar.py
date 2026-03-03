import sys
from csmarapi.CsmarService import CsmarService

def main():
    csmar = CsmarService()
    print("Logging in...")
    csmar.login('2412782@mail.nankai.edu.cn', '21288480Yy')
    print("Logged in successfully.")
    
    keywords = ["专精特新", "小巨人", "引导", "基金", "专利", "创新", "投资"]
    
    # Keep track of matches
    matches = []
    
    print("Fetching databases...")
    print("Fetching databases...")
    with open("csmar_search_results.txt", "w", encoding="utf-8") as f:
        try:
            databases = csmar.getListDbs()
            f.write(f"Total databases: {len(databases)}\n")
            
            for db in databases:
                db_name = db.get("databaseName", "")
                
                # Fetch tables for this db
                try:
                    tables = csmar.getListTables(db_name)
                except Exception as e:
                    f.write(f"\nError fetching tables for DB {db_name}: {e}\n")
                    continue
                
                # Search keywords in db_name
                db_match = any(k in db_name for k in keywords)
                
                f.write(f"\n=== DB: {db_name} ===\n")
                if db_match:
                    f.write(f"  [MATCHED DB KEYWORD]\n")
                
                if not tables:
                    f.write(f"  [No Tables Found or Returned None]\n")
                    continue
                    
                for table in tables:
                    table_name = table.get("tableName", "")
                    table_title = table.get("tableTitle", "") # Guessing the keys based on common API patterns, could also be 'title' or 'desc'. 
                    # Let's just convert table dict to string and search
                    table_str = str(table)
                    table_match = any(k in table_str for k in keywords)
                    
                    if db_match or table_match:
                        f.write(f"  Table: {table}\n")
                        # For matched DBs or matched Tables, let's fetch fields
                        try:
                            # table name is usually the key to get fields, e.g. 'FS_Combas'
                            table_id = table.get("table") 
                            if not table_id:
                                continue
                            fields = csmar.getListFields(table_id)
                            # log fields that match
                            if not fields:
                                continue
                            matching_fields = []
                            all_fields = []
                            for field in fields:
                                field_str = str(field)
                                all_fields.append(field_str)
                                if any(k in field_str for k in keywords):
                                    matching_fields.append(field_str)
                            
                            if matching_fields:
                                f.write(f"    Matching Fields:\n")
                                for mf in matching_fields:
                                    f.write(f"      - {mf}\n")
                        except Exception as e:
                            f.write(f"    Error fetching fields for table {table}: {e}\n")
                            
        except Exception as e:
            print("Error:", e)
        
if __name__ == "__main__":
    main()
