from ceic_api_client.apis.layout_api import LayoutApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration
api_host = https://api.ceicdata.com.cn/v2/
access_token = "ENTER YOUR API KEY HERE"
configuration = Configuration()
configuration.host = api_host
api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=access_token)
layout_api = LayoutApi(api_client=api_client)
layout_tables = layout_api.get_layout_tables("SC36031")