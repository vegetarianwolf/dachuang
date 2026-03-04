import ceic_api_client
from ceic_api_client.apis.layout_api import LayoutApi
from ceic_api_client.apis.series_api import SeriesApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration

with open("ceic_token.txt", "r") as f:
    token = f.read().strip()

# Configure API
configuration = Configuration()
configuration.api_key['token'] = token
# Default host is usually 'https://api.ceicdata.com/v2', but let's check what the user provided
configuration.host = "https://api.ceicdata.com.cn/v2" 

# Or use Authorization header
# api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=token)
api_client = ApiClient(configuration=configuration)

layout_api = LayoutApi(api_client=api_client)

try:
    # Let's inspect SC36031
    res = layout_api.get_layout("SC36031")
    print("SC36031 Layout:", res)
    
except Exception as e:
    print(f"Error fetching SC36031: {e}")

try:
    res2 = layout_api.get_layout_series("SC36031")
    print("SC36031 series count:", len(res2.data))
    if res2.data:
        print("First few series:", [s.id for s in res2.data[:5]])
except Exception as e:
    print(f"Error fetching SC36031 series: {e}")

try:
    res3 = layout_api.get_layout_series("TB36033")
    print("TB36033 series count:", len(res3.data))
    if res3.data:
        print("First few series:", [s.id for s in res3.data[:5]])
except Exception as e:
    print(f"Error fetching TB36033 series: {e}")
