import requests
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
from pprint import pprint

def ask_graphql(query, graphURL):

    request = requests.post(graphURL,
                            json={'query': query})
    if request.status_code == 200:
        return request.json()
    else:
        time.sleep(0.1)
        request = requests.post(graphURL,
                                json={'query': query})
        if request.status_code == 200:
            return request.json()
        
        #TODO do przetestowania kiedyś
        else:
            print(f"query {query} to {graphURL} failed")
        

def connect_to_ETH_provider():
    # avalanche_url = 'https://api.avax.network/ext/bc/C/rpc' #mainnet
    avalanche_url = 'https://api.avax.network/ext/bc/C/rpc'  # mainnet
    web3 = Web3(Web3.HTTPProvider(avalanche_url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    assert web3.isConnected() == True, "web3 not connected"

    return web3