import ceic_api_client
from ceic_api_client.apis.series_api import SeriesApi
from ceic_api_client.api_client import ApiClient
from ceic_api_client.configuration import Configuration

with open("ceic_token.txt", "r") as f:
    token = f.read().strip()

configuration = Configuration()
configuration.host = "https://api.ceicdata.com/v2" 
api_client = ApiClient(configuration=configuration, header_name="Authorization", header_value=token)
series_api = SeriesApi(api_client=api_client)

res = series_api.get_series("301546101")
print(res.to_dict() if hasattr(res, 'to_dict') else res)
