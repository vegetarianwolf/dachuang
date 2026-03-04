import ceic_api_client
from ceic_api_client.apis.layout_api import LayoutApi
from ceic_api_client.apis.series_api import SeriesApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration

with open("ceic_token.txt", "r") as f:
    token = f.read().strip()

configuration = Configuration()
configuration.host = "https://api.ceicdata.com.cn/v2/" 
api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=token)
layout_api = LayoutApi(api_client=api_client)
series_api = SeriesApi(api_client=api_client)

res_tables = layout_api.get_layout_tables("SC36031")
if res_tables.data:
    t = res_tables.data[0]
    table_id = t.metadata.id
    print(f"Table ID: {table_id}")
    res_series = layout_api.get_layout_series(table_id)
    if res_series.data:
        s = res_series.data[0]
        s_id = s.metadata.id
        print(f"Series ID: {s_id}")
        # Fetch the series data
        res_data = series_api.get_series_time_points(s_id)
        print(f"res_data type: {type(res_data)}")
        if hasattr(res_data, 'data'):
            print(f"res_data.data exists (length {len(res_data.data)})")
            if res_data.data:
                series_obj = res_data.data[0]
                if hasattr(series_obj, 'time_points') and series_obj.time_points:
                    print(f"First data point: {series_obj.time_points[0].date} - {series_obj.time_points[0].value}")
                    print(f"Number of points: {len(series_obj.time_points)}")
                elif hasattr(series_obj, 'data') and series_obj.data:
                    print(f"First data point: {series_obj.data[0].date} - {series_obj.data[0].value}")
                    print(f"Number of points: {len(series_obj.data)}")
                else:
                    print("No time_points or data attribute found in series_obj. Attributes:")
                    print(dir(series_obj))
        else:
            print("No data attribute in res_data. Attributes:")
            print(dir(res_data))
