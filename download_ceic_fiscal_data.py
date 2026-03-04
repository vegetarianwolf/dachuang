import ceic_api_client
from ceic_api_client.apis.layout_api import LayoutApi
from ceic_api_client.apis.series_api import SeriesApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration
import pandas as pd
import time

def download_layout_data(layout_id, output_filename, token):
    print(f"Starting download for Layout: {layout_id}")
    configuration = Configuration()
    configuration.host = "https://api.ceicdata.com.cn/v2/" 
    api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=token)
    
    layout_api = LayoutApi(api_client=api_client)
    series_api = SeriesApi(api_client=api_client)

    try:
        res_tables = layout_api.get_layout_tables(layout_id)
    except Exception as e:
        print(f"Failed to fetch layout {layout_id}: {e}")
        return

    if not res_tables.data:
        print(f"No tables found for layout {layout_id}")
        return

    all_data = []

    for t in res_tables.data:
        table_id = t.metadata.id
        print(f"Fetching series list for table: {table_id} ({t.metadata.name})")
        try:
            res_series = layout_api.get_layout_series(table_id)
        except Exception as e:
            print(f"Failed to fetch series for table {table_id}: {e}")
            continue
            
        if not res_series.data:
            continue

        # Extract series IDs
        series_ids = [s.metadata.id for s in res_series.data]
        
        # Batch query series time points (API usually supports multiple IDs separated by commas, but here we query safely)
        # To avoid URL too long, we process in chunks of 50
        chunk_size = 50
        for i in range(0, len(series_ids), chunk_size):
            chunk = series_ids[i:i+chunk_size]
            chunk_str = ",".join(str(sid) for sid in chunk)
            
            try:
                res_data = series_api.get_series_time_points(chunk_str)
            except Exception as e:
                print(f"Error fetching data for chunk {chunk_str[:30]}...: {e}")
                continue
                
            if hasattr(res_data, 'data') and res_data.data:
                for s_obj in res_data.data:
                    s_id = s_obj.metadata.id
                    s_name = s_obj.metadata.name
                    if hasattr(s_obj, 'time_points') and s_obj.time_points:
                        for pt in s_obj.time_points:
                            all_data.append({
                                'Table_ID': table_id,
                                'Table_Name': t.metadata.name,
                                'Series_ID': s_id,
                                'Series_Name': s_name,
                                'Date': pt.date,
                                'Value': pt.value
                            })
            
            time.sleep(0.5) # simple rate limit pause
            
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"Successfully saved {len(all_data)} records to {output_filename}")
    else:
        print(f"No data points could be downloaded for {layout_id}. Check your subscription.")

if __name__ == "__main__":
    with open("ceic_token.txt", "r") as f:
        token = f.read().strip()
        
    download_layout_data("SC36031", "地级市财政支出_SC36031.csv", token)
    download_layout_data("TB36033", "地级市财政收入_TB36033.csv", token)
