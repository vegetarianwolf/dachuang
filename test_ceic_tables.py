import ceic_api_client
from ceic_api_client.apis.layout_api import LayoutApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration

with open("ceic_token.txt", "r") as f:
    token = f.read().strip()

configuration = Configuration()
configuration.host = "https://api.ceicdata.com.cn/v2/" 
api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=token)
layout_api = LayoutApi(api_client=api_client)

res_tables = layout_api.get_layout_tables("SC36031")
if res_tables.data:
    t = res_tables.data[0]
    print(dir(t))
    print(vars(t))
