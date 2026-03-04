import ceic_api_client
from ceic_api_client.apis.layout_api import LayoutApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration

with open("ceic_token.txt", "r") as f:
    token = f.read().strip()

# Configure API for China endpoint as user requested
configuration = Configuration()
configuration.host = "https://api.ceicdata.com.cn/v2/" 

api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=token)
layout_api = LayoutApi(api_client=api_client)

try:
    print("Testing SC36031...")
    res2 = layout_api.get_layout_series("SC36031")
    print("SC36031 series count:", len(res2.data))
    if res2.data:
        print("First few series:", [s.id for s in res2.data[:5]])
except Exception as e:
    print(f"Error fetching SC36031 series: {e}")
    if hasattr(e, 'body'):
        print(e.body)

try:
    print("Testing layout tables for SC36031...")
    res_tables = layout_api.get_layout_tables("SC36031")
    print("Tables count:", len(res_tables.data))
except Exception as e:
    print(f"Error fetching SC36031 tables: {e}")
    if hasattr(e, 'body'):
        print(e.body)
