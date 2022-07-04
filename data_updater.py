


import json

from yaml import dump

from helpful_scripts import connect_to_ETH_provider, ask_graphql
from web3 import Web3
import pandas as pd
import time
import requests
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import os

print("Be careful, functions outside of main function and if __name__")
print("Do not import this file")
#input confirm

development = True

if development:
    dataShowedPath = "dataShowed/"
    dataframesPath = "dataframes/"
    datasPath = "datas/"
    abisPath = "ABIS/"
else:
    dataShowedPath = "mysite/dataShowed/"
    dataframesPath = "mysite/dataframes/"
    datasPath = "mysite/datas/"
    abisPath = "ABIS/"

#veJOE
with open(f"{abisPath}ERC20_ABI.json") as file:
    ERC20_ABI = json.load(file)
with open(f"{abisPath}veJoeStakingABI2.json") as file:
    veJoeStakingABI2 = json.load(file)
with open(f"{abisPath}veJoeTokenABI.json") as file:
    veJoeTokenABI = json.load(file)
with open(f"{datasPath}joeHolders.json") as file:
    joeHolders = json.load(file)
with open(f"{datasPath}data.json") as file:
    addresses = json.load(file)

#TVL
with open(f"{datasPath}data.json") as file:
    datas = json.load(file)
with open(f"{abisPath}chainlinkAvaxOracle.json") as file:
    chainlinkAVAXABI = json.load(file)
with open(f"{abisPath}boostedMasterchefABI.json") as file:
    boostedMasterchefABI = json.load(file)
with open(f"{abisPath}JLPABI.json") as file:
    JLPABI = json.load(file)


with open(f"{datasPath}historicalBlocks.json") as file:
    file = json.load(file)
    historicalBlockTimestamps = file['historicalBlockTimestamps']
    historicalBlocks = file['historicalBlocks']


web3 = connect_to_ETH_provider()
#TVL
chainlinkAVAXAddress = web3.toChecksumAddress(datas['contracts']['chainlinkAVAX'])
chainlinkAVAXContract = web3.eth.contract(address=chainlinkAVAXAddress, abi=chainlinkAVAXABI)
masterchefContract = web3.eth.contract(address=web3.toChecksumAddress(datas["contracts"]['boostedMasterchef']), abi=boostedMasterchefABI)

#veJOE
joeAddress = web3.toChecksumAddress(addresses['contracts']['JOEToken'])
veJOEStakingAddress = web3.toChecksumAddress(addresses['contracts']['veJOEStaking'])
veJOEAddress = web3.toChecksumAddress(addresses['contracts']['veJOEToken'])

joeContract = web3.eth.contract(address=joeAddress, abi=ERC20_ABI)
veJOEStakingContract = web3.eth.contract(address=veJOEStakingAddress, abi=veJoeStakingABI2)
veJoeContract = web3.eth.contract(address=veJOEAddress, abi=veJoeTokenABI)


def updateTimestamps(historicalBlockTimestamps):
    timeNow = int(time.time())
    update_interval_hours = 24
    if historicalBlockTimestamps[-1] + update_interval_hours * 3600-1 > timeNow:
        print("historical timestamps are up to date")
        return historicalBlockTimestamps, []
    else:
        timestampRange = range(historicalBlockTimestamps[-1], timeNow, update_interval_hours * 3600)

        newTimestamps = []
        for timestamp in timestampRange[1:]:
            newTimestamps.append(timestamp)

        print(f"adding timestamps: {newTimestamps} to historicalBlockTimestamps")
        historicalBlockTimestamps += newTimestamps

        return historicalBlockTimestamps, newTimestamps


def updateHistoricalBlocks(historicalBlocks, newTimestamps):
    if newTimestamps == []:
        print("historical blocks are up to date")
        return historicalBlocks, []
    newBlocks = []
    for timestamp2 in newTimestamps:
        block = requests.get(f"https://api.snowtrace.io/api?module=block&action=getblocknobytime&timestamp={timestamp2}&closest=after&apikey=YourApiKeyToken")
        #print(block.json()['result'])
        try:
            newBlocks.append(int(block.json()['result']))
        except:
            time.sleep(1)
            print(f"block api call during updateTimestamps went wrong at {timestamp2}, trying again")
            block = requests.get(f"https://api.snowtrace.io/api?module=block&action=getblocknobytime&timestamp={timestamp2}&closest=after&apikey=YourApiKeyToken")
            newBlocks.append(int(block.json()['result']))
        time.sleep(0.2)
    
    print(f"adding: {newBlocks} to historicalBlocks")
    historicalBlocks += newBlocks
    return historicalBlocks, newBlocks

def dumpNewBlocksToJSON(historicalBlockTimestamps, historicalBlocks):
    print('Saving new blocks')
    data = {"historicalBlockTimestamps": historicalBlockTimestamps,
    "historicalBlocks": historicalBlocks}

    with open(f"{datasPath}historicalBlocks.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


#######HISTORICAL TVL 



def pairHistoricalDatas(onlyUpdate):
    print(f"pairHistoricalDatas. Update - {onlyUpdate}")
    if onlyUpdate:
        dfOLD = pd.read_excel(f"{dataframesPath}/pairHistoricalDatas.xlsx").drop("Unnamed: 0", axis=1)
        lastBlock = max(dfOLD['block'])
        lastBlockIndex = historicalBlocks.index(lastBlock)
        if lastBlock == historicalBlocks[-1]:
            print(f"pairHistoricalDatas is up to date")
            return
        print(f"updating pairHistoricalDatas from {historicalBlocks[lastBlockIndex + 1]} to {historicalBlocks[-1]}")
    else:
        lastBlockIndex = -1
        dfOLD = pd.DataFrame([])


    pairHistoricalDatas = []
    for pair in datas["farmData"]:
        JLP = web3.eth.contract(address=web3.toChecksumAddress(datas["farmData"][pair][1]), abi=JLPABI)

        for number, block in enumerate(historicalBlocks[lastBlockIndex + 1:]):
            reserves = JLP.functions.getReserves().call(block_identifier=block)[datas["farmData"][pair][3]]
            total_supply = JLP.functions.totalSupply().call(block_identifier=block)

            record = [block, historicalBlockTimestamps[lastBlockIndex + 1:][number], pair, datas["farmData"][pair][0], reserves, total_supply]
            pairHistoricalDatas.append(record)
            print(f"{len(pairHistoricalDatas)} - {record}")
            #time.sleep(0.2)
    #pprint(pairHistoricalDatas)
    dfpairHistoricalDatasNew = pd.DataFrame(pairHistoricalDatas, columns=['block', 
        'timestamp',
        'pairName', 
        'poolID', 
        'reserves', 
        'totalSupply'])
    
    dfpairHistoricalDatasUpdated = pd.concat([dfOLD, dfpairHistoricalDatasNew], ignore_index=True)
    dfpairHistoricalDatasUpdated.to_excel(f"{dataframesPath}/pairHistoricalDatas.xlsx")
    print(f"finished pairHistoricalDatas")






def masterchefHistoricalProtocolDatas(onlyUpdate):
    print(f"masterchefHistoricalProtocolDatas. Update - {onlyUpdate}")
    if onlyUpdate:
        dfOLD = pd.read_excel(f"{dataframesPath}/masterchefHistoricalProtocolDatas.xlsx").drop("Unnamed: 0", axis=1)
        lastBlock = max(dfOLD['block'])
        lastBlockIndex = historicalBlocks.index(lastBlock)
        if lastBlock == historicalBlocks[-1]:
            print(f"masterchefHistoricalProtocolDatas is up to date")
            return
        print(f"updating masterchefHistoricalProtocolDatas from {historicalBlocks[lastBlockIndex + 1]} to {historicalBlocks[-1]}")
    else:
        lastBlockIndex = -1
        dfOLD = pd.DataFrame([])



    masterchefHistoricalDatasArray = []
    for protocol in datas["actualProtocolAdresses"]:
        for pool in range(13):
            for block in historicalBlocks[lastBlockIndex + 1:]:
                protocolAddress = Web3.toChecksumAddress(datas["actualProtocolAdresses"][protocol])
                amountInMasterchef = masterchefContract.functions.userInfo(pool, protocolAddress).call(block_identifier=block)[0]
                record = [block, protocol, pool, amountInMasterchef]
                masterchefHistoricalDatasArray.append(record)
                print(f"{len(masterchefHistoricalDatasArray)} - {record}")



    dfmasterchefHistoricalPairDatasNew = pd.DataFrame(masterchefHistoricalDatasArray, columns=['block', 'protocolName', 'poolID', 'amount'])
    dfmasterchefHistoricalPairDatasUpdated = pd.concat([dfOLD, dfmasterchefHistoricalPairDatasNew], ignore_index=True)
    dfmasterchefHistoricalPairDatasUpdated.to_excel(f"{dataframesPath}/masterchefHistoricalProtocolDatas.xlsx")


def avaxprices(onlyUpdate):
    print(f"avaxprices. Update - {onlyUpdate}")
    if onlyUpdate:
        dfOLD = pd.read_excel(f"{dataframesPath}/avaxprices.xlsx").drop("Unnamed: 0", axis=1)
        lastBlock = max(dfOLD['block'])
        lastBlockIndex = historicalBlocks.index(lastBlock)
        if lastBlock == historicalBlocks[-1]:
            print(f"avaxprices is up to date")
            return
        print(f"updating avaxprices from {historicalBlocks[lastBlockIndex + 1]} to {historicalBlocks[-1]}")
    else:
        lastBlockIndex = -1
        dfOLD = pd.DataFrame([])

    avaxprices = []
    for block in historicalBlocks[lastBlockIndex + 1:]:
        AVAXPrice = chainlinkAVAXContract.functions.latestAnswer().call(block_identifier=block) * 10 ** (-8)
        avaxprices.append([block, AVAXPrice])
        print([block, AVAXPrice])

    
    dfavaxpricesNEW = pd.DataFrame(avaxprices, columns=['block', 'avaxprice'])
    dfavaxpricesUpdated = pd.concat([dfOLD, dfavaxpricesNEW], ignore_index=True)
    dfavaxpricesUpdated.to_excel(f"{dataframesPath}/avaxprices.xlsx")


def masterchefHistoricalTotalDatas(onlyUpdate):
    print(f"masterchefHistoricalTotalDatas. Update - {onlyUpdate}")
    poolsStarts = {8 : 12919099, 9: 12919099, 10: 12919099, 11: 12919099, 12: 13428854}
    masterchefHistoricalTotalDatas = []

    if onlyUpdate:
        dfOLD = pd.read_excel(f"{dataframesPath}/masterchefHistoricalTotalDatas.xlsx").drop("Unnamed: 0", axis=1)
        lastBlock = max(dfOLD['block'])
        lastBlockIndex = historicalBlocks.index(lastBlock)
        if lastBlock == historicalBlocks[-1]:
            print(f"TVLLockedInBoostedMasterchefTotal is up to date")
            return
        print(f"updating TVLLockedInBoostedMasterchefTotal from {historicalBlocks[lastBlockIndex + 1]} to {historicalBlocks[-1]}")
    else:
        lastBlockIndex = -1
        dfOLD = pd.DataFrame([])

    
    for pool in range(13):
        if pool in poolsStarts.keys() and not onlyUpdate:
            lastBlockIndex = historicalBlocks.index(poolsStarts[pool])


        for block in historicalBlocks[lastBlockIndex + 1:]:
            amountInMasterchef = masterchefContract.functions.poolInfo(pool).call(block_identifier=block)[8]

            record = [block, 'all users', pool, amountInMasterchef]
            masterchefHistoricalTotalDatas.append(record)
            print(f"{len(masterchefHistoricalTotalDatas)} - {record}")
    dfmasterchefHistoricalPairDatasNEW = pd.DataFrame(masterchefHistoricalTotalDatas, columns=['block', 'protocolName', 'poolID', 'amount'])
    dfmasterchefHistoricalPairDatasUpdated = pd.concat([dfOLD, dfmasterchefHistoricalPairDatasNEW], ignore_index=True)    
    dfmasterchefHistoricalPairDatasUpdated.to_excel(f"{dataframesPath}/masterchefHistoricalTotalDatas.xlsx")

def mergeDataFromAll():
    pairHistoricalDatas = pd.read_excel(f"{dataframesPath}/pairHistoricalDatas.xlsx").drop("Unnamed: 0", axis=1)
    historicalPoolBalancesProtocols = pd.read_excel(f"{dataframesPath}/masterchefHistoricalProtocolDatas.xlsx").drop("Unnamed: 0", axis=1)
    historicalPoolBalancesMasterchef = pd.read_excel(f"{dataframesPath}/masterchefHistoricalTotalDatas.xlsx").drop("Unnamed: 0", axis=1)
    avaxprice = pd.read_excel(f"{dataframesPath}/avaxprices.xlsx").drop("Unnamed: 0", axis=1)

    historicalPoolBalancesAll = pd.concat([historicalPoolBalancesProtocols, historicalPoolBalancesMasterchef])
    df1 = historicalPoolBalancesAll.merge(pairHistoricalDatas, how='left', on=['block', 'poolID'])
    mergedPoolPairs = df1.merge(avaxprice, how='left', on='block')
    mergedPoolPairs['date'] = pd.to_datetime(mergedPoolPairs['timestamp'], unit='s')
    mergedPoolPairs['pool TVL'] = np.where(mergedPoolPairs['pairName'].str.contains('AVAX'), mergedPoolPairs['reserves'] * mergedPoolPairs['avaxprice'] * 2 * 10 ** (-18), mergedPoolPairs['reserves'] * 1 * 2 * 10 ** (-6))
    mergedPoolPairs['protocol TVL'] = mergedPoolPairs['pool TVL'] * mergedPoolPairs['amount'] / mergedPoolPairs['totalSupply']
    df_tvl_sum = mergedPoolPairs.groupby(by=['protocolName', 'block', 'date', 'timestamp'], axis=0).sum()['protocol TVL'].reset_index()
    df_tvl_sum['pairName'] = 'all pools'

    finalMerged = pd.concat([mergedPoolPairs, df_tvl_sum]).sort_values(by='block', axis=0, ascending=True, inplace=False)
    finalMerged = finalMerged.reset_index().drop('index', axis=1)
    print(f"length of finalMerged = {len(finalMerged)}")
    finalMerged.to_excel(f"{dataShowedPath}historicalTVL.xlsx")
    print(f"Data ready to load to app")


def historicalvejoe(onlyUpdate):
    if onlyUpdate:
        dfOLD = pd.read_excel(f"{dataShowedPath}historicalvejoe.xlsx").drop("Unnamed: 0", axis=1)
        lastBlock = max(dfOLD['block'])
        lastBlockIndex = historicalBlocks.index(lastBlock)
        if lastBlock == historicalBlocks[-1]:
            print(f"historicalvejoe is up to date")
            return
        print(f"updating historicalvejoe from {historicalBlocks[lastBlockIndex + 1]} to {historicalBlocks[-1]}")
    else:
        lastBlockIndex = -1
        dfOLD = pd.DataFrame([])

    #blocks = range(firstBlock, 13_500_000, 100_000)
    allveJOEHistoricalBalances = []
    for protocol in addresses['actualProtocolAdresses']:
        address = web3.toChecksumAddress(addresses['actualProtocolAdresses'][protocol])
        for number, block in enumerate(historicalBlocks[lastBlockIndex + 1:]):
            vejoeTotalSupply = veJoeContract.functions.totalSupply().call(block_identifier=block)
            singleveJOEBalance = veJoeContract.functions.balanceOf(address).call(block_identifier=block)
            record = [
                block,
                historicalBlockTimestamps[lastBlockIndex + 1:][number], 
                datetime.fromtimestamp(historicalBlockTimestamps[lastBlockIndex + 1:][number]),
                protocol, 
                address, 
                singleveJOEBalance * 10 ** (-18), 
                vejoeTotalSupply * 10 ** (-18), 
                100 * singleveJOEBalance / vejoeTotalSupply]
            allveJOEHistoricalBalances.append(record)
            print(f"{len(allveJOEHistoricalBalances)} - {record}")

    dfNEW = pd.DataFrame(allveJOEHistoricalBalances, columns=[
        'block', 
        'timestamp',
        'date', 
        'protocolName', 
        'address', 
        'veJoeBalance', 
        'vejoeTotalSupply', 
        '% of veJOE supply'])

    dfupdated = pd.concat([dfOLD, dfNEW], ignore_index=True)
    dfupdated.to_excel(f"{dataShowedPath}/historicalvejoe.xlsx")
    print(f"finished historicalvejoe")

######DATA FRESH


def joeBalances():
    print("Fetching fresh JOE balances")
    circulatingJOESupply = requests.get(f"https://api.traderjoexyz.com/supply/circulating").json()

    allJOEBalances = []
    cumulativeJEOBalance = 0
    cumulativePercentOfJOE = 0

    for i in range(len(joeHolders)):
        address = Web3.toChecksumAddress(joeHolders[i]['address'])
        singleJOEBalance = joeContract.functions.balanceOf(address).call()
        percentOfJOE = round(singleJOEBalance/circulatingJOESupply * 100, 2)
        allJOEBalances.append({
            "name": joeHolders[i]['name'], 
            "balance": singleJOEBalance * 10 ** (-18), 
            "% of JOE": percentOfJOE
            })
        
        cumulativeJEOBalance += singleJOEBalance
        cumulativePercentOfJOE += percentOfJOE

    allJOEBalances.append({
        "name": "Others", 
        "balance": (circulatingJOESupply - cumulativeJEOBalance) * 10 ** (-18), 
        "% of JOE": round(100 - cumulativePercentOfJOE, 2)
        })

    df = pd.DataFrame(allJOEBalances)

    df.to_excel(f"{dataShowedPath}/joeHolders.xlsx")


def TVLFresh():
    print("formatting fetched data for TVL Fresh")

    allfarmTVLBalances = fetchProtocolsTVLs(datas)
    dfProtocolTVLs = pd.DataFrame()
    for i in range(len(allfarmTVLBalances)):
        dfProtocolTVLs = pd.concat([dfProtocolTVLs, pd.DataFrame(allfarmTVLBalances[i])], ignore_index=True)

    dfStrippedPools = pd.json_normalize(dfProtocolTVLs['pool'])
    dfProtocolTVLs = dfProtocolTVLs.drop('pool', axis=1).join(dfStrippedPools)
    #   print("dfProtocolTVLs")
    #   print(dfProtocolTVLs)
    allBoostedFarms = fetchAllFarmTVLs(datas)
    df_allBoostedFarms = pd.DataFrame(allBoostedFarms)
    #print("df_allBoostedFarms")
    #print(df_allBoostedFarms)
    df_allBoostedFarms.rename(columns={"id": "pairAddress", "name": "pairName"}, inplace=True)
    dfProtocolTVLs.rename(columns={"pair": "pairAddress"}, inplace=True)

    
    dfJoinedProtocolsAndTotalTVLs = dfProtocolTVLs.merge(df_allBoostedFarms, on="pairAddress")
    #print(dfJoinedProtocolsAndTotalTVLs)
    dfJoinedProtocolsAndTotalTVLs.loc[dfJoinedProtocolsAndTotalTVLs['pairName'] == 'USDC.e-USDC', 'pairName'] = 'USDC-USDC.e'

    dfJoinedProtocolsAndTotalTVLs.to_csv(f"{dataframesPath}TVLFresh.csv")


def fetchProtocolsTVLs(datas):
    print("Fetching protocol TVLs")
    protocolAddresses = datas['actualProtocolAdresses']
    graphMasterchefUrl = "https://api.thegraph.com/subgraphs/name/traderjoe-xyz/boosted-master-chef"
    allfarmTVLBalances = []

    for protocol in protocolAddresses:
        protocolAdress = protocolAddresses[protocol]

        masterchefQuery = """{{
            users(where: {{address: "{}"}}) {{
            address
            amount
            pool{{pair balance}}
            poolId
            veJoeStaked
            factor
            }}
        }}""".format(protocolAdress)

        masterchefAPIResponse = ask_graphql(masterchefQuery, graphMasterchefUrl)['data']['users']
        allfarmTVLBalances.append(masterchefAPIResponse)

    #pprint(allfarmTVLBalances)
    return allfarmTVLBalances


def fetchAllFarmTVLs(datas):
    print("fetching farm TVLs")
    pairAddresses = datas['boostedFarmsAddresses']
    allFarms = []
    graphexchangeUrl = "https://api.thegraph.com/subgraphs/name/traderjoe-xyz/exchange"
    for pairID in pairAddresses:
        farmAddress = pairAddresses[pairID]

        allFarmsTVLQuery = """{{
            pairs(where: {{id: "{}"}})
        {{
            id
            name
            totalSupply
            reserveUSD
        }}
        }}""".format(farmAddress)
        exchangeAPIResponse = ask_graphql(allFarmsTVLQuery, graphexchangeUrl)['data']['pairs'][0]
        allFarms.append(exchangeAPIResponse)
    return allFarms

def veJOEBalances():
    print("Getting fresh veJOE balances")
    graphVejoeUrl = "https://api.thegraph.com/subgraphs/name/traderjoe-xyz/vejoe"

    protocolAddresses = datas["actualProtocolAdresses"]
    allveJOEBalances = []

    for protocolName in protocolAddresses:
        veJOEHolderAdress = protocolAddresses[protocolName]
        veJOEQueryByAddress = """{{
            users(where: {{id: "{}"}}) {{
            id
            joeStaked
            joeStakedUSD
            totalVeJoeMinted
            veJoeBalance
            }}
        }}
        """.format(veJOEHolderAdress)

        singleveJOEBalances = ask_graphql(veJOEQueryByAddress, graphVejoeUrl)['data']['users'][0]
        singleveJOEBalances['protocolName'] = protocolName

        #print(protocolName)
        #pprint(singleveJOEBalances['data']['users'])
        allveJOEBalances.append(singleveJOEBalances)


    totalveJOEQuery = """{
    veJoes {
        id
        joeStaked
        joeStakedUSD
        totalVeJoeMinted
        totalVeJoeBurned
    }
    }"""

    totalJoes = ask_graphql(totalveJOEQuery, graphVejoeUrl)['data']['veJoes'][0]
    totalveJOEbalance = float(totalJoes['totalVeJoeMinted']) - float(totalJoes['totalVeJoeBurned'])

    df_vejoes = pd.DataFrame(allveJOEBalances)
    df_vejoes = df_vejoes.astype({"joeStaked": float, "joeStakedUSD": float, "totalVeJoeMinted": float, "veJoeBalance": float})

    df_vejoes['% JOE staked in veJOE'] =  round(100 * df_vejoes['joeStaked'] / float(totalJoes['joeStaked']),2)
    df_vejoes['% veJOE'] =  round(100 * df_vejoes['veJoeBalance'] / totalveJOEbalance, 2)

    df_total = pd.DataFrame([['others', totalJoes['joeStaked'], totalJoes['joeStakedUSD'], totalJoes['totalVeJoeMinted'], totalveJOEbalance, 'others', 100, 100]], columns=df_vejoes.columns)
    df_total = df_total.astype({"joeStaked": float, "joeStakedUSD": float, "totalVeJoeMinted": float, "veJoeBalance": float})

    dfOthers = df_total.drop(['protocolName', 'id'], axis=1) - df_vejoes.drop(['protocolName', 'id'], axis=1).sum(axis=0)
    dfOthers[['id', 'protocolName']] = ['others', 'others']

    df_vejoes = pd.concat([df_vejoes, dfOthers], ignore_index=True)

    df_vejoes.to_csv(f"{dataframesPath}veJOEBalances.csv")


def mergeFreshData():
    block = web3.eth.get_block('latest').number
    df_TVL_fresh = pd.read_csv(f'{dataframesPath}TVLFresh.csv')
    #TVL in masterchef
    df_TVL_fresh['TVL in masterchef'] = \
                df_TVL_fresh['reserveUSD']  \
                * (df_TVL_fresh['balance'].astype(float) * 10 ** (-18)) \
                / df_TVL_fresh['totalSupply'].astype(float)
    #% of farm in protocol
    df_TVL_fresh['% of masterchef'] = round(
                    100*df_TVL_fresh['amount'].astype(float) / df_TVL_fresh['balance'].astype(float), 4)
    #protocol TVL
    df_TVL_fresh['protocol TVL'] = df_TVL_fresh['TVL in masterchef'] * df_TVL_fresh['% of masterchef'] / 100
    df_TVL_fresh.drop("Unnamed: 0", axis=1, inplace=True)

    dfveJOEBalances = pd.read_csv(f'{dataframesPath}veJOEBalances.csv')
    dfveJOEBalances.rename(columns={"id": "address"}, inplace=True)
    dfveJOEBalances.drop("Unnamed: 0", axis=1, inplace=True)
    dfMergedTVLveJOE = df_TVL_fresh.merge(dfveJOEBalances, on="address")

    dftotal = dfMergedTVLveJOE.groupby('poolId')['protocol TVL'].sum().reset_index()
    dftotal['% veJOE'] = 100 - dfMergedTVLveJOE.groupby('poolId')['% veJOE'].sum()
    dftotal['% JOE staked in veJOE'] = 100 - dfMergedTVLveJOE.groupby('poolId')['% JOE staked in veJOE'].sum()

    dftotal['protocolName'] = 'others'

    dfTVLinMasterchef = pd.concat(
        [
        dfMergedTVLveJOE['TVL in masterchef'], 
        dfMergedTVLveJOE['pairAddress'], 
        dfMergedTVLveJOE['poolId'] , 
        dfMergedTVLveJOE['pairName']
        ], axis=1).drop_duplicates()

    dfTVLinMasterchef.set_index('poolId', inplace=True)
    dftotal.set_index('poolId', inplace=True)
    dftotal = dftotal.join(dfTVLinMasterchef)
    dftotal['protocol TVL'] = dftotal['TVL in masterchef'] - dftotal['protocol TVL']
    #dftotal.drop('protocol TVL', axis=1, inplace=True)
    dftotal = dfveJOEBalances.loc[dfveJOEBalances['address'] == 'others'].set_index(
        'protocolName').join(dftotal.set_index('protocolName'), on='protocolName', lsuffix='a')
        
    dftotal.drop(['% JOE staked in veJOEa', '% veJOEa'], axis=1, inplace=True)
    dftotal['protocolName'] = 'others'
    dfTVLinMasterchef['protocolName'] = 'all users'
    dfTVLinMasterchef.rename(columns={'TVL in masterchef': 'protocol TVL'}, inplace=True)


    df_ready = pd.concat([dftotal, dfMergedTVLveJOE, dfTVLinMasterchef], ignore_index=True)

    block = web3.eth.get_block('latest')
    blockNumber = block.number
    blockTimestamp = block.timestamp

    df_ready['block'] = blockNumber
    df_ready['timestamp'] = block.timestamp
    df_ready['date'] = pd.to_datetime(df_ready['timestamp'], unit='s')
    df_ready['amount'].astype(float)
    df_ready.rename(columns={'poolId': 'poolID', 'reserveUSD': 'pool TVL'}, inplace=True)
    df_ready.to_excel(f"{dataShowedPath}/ready.xlsx")
    #df_ready.to_csv(f"{dataShowedPath}/ready.csv")

    print("Fresh data merged")
    print(df_ready)


def reloadWebApp():
    load_dotenv()

    username = os.getenv("USERNAME")
    api_token = os.getenv("API_TOKEN")
    domain_name = "vejoedashboard.pythonanywhere.com/"

    response = requests.post(
        'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{domain_name}/reload/'.format(
            username=username, domain_name=domain_name
        ),
        headers={'Authorization': 'Token {token}'.format(token=api_token)}
    )
    if response.status_code == 200:
        print('reloaded OK')
    else:
        print('Got unexpected status code {}: {!r}'.format(response.status_code, response.content))




historicalBlockTimestamps, newTimestamps = updateTimestamps(historicalBlockTimestamps)
historicalBlocks, newBlocks = updateHistoricalBlocks(historicalBlocks, newTimestamps)

dumpNewBlocksToJSON(historicalBlockTimestamps, historicalBlocks)

def main():
    timeStart = time.time()
    print(f"start time: {timeStart}")
    print("Updating data - HISTORICAL TVL")
    #populating data
    pairHistoricalDatas(onlyUpdate=True)
    masterchefHistoricalProtocolDatas(onlyUpdate=True)
    avaxprices(onlyUpdate=True)
    masterchefHistoricalTotalDatas(onlyUpdate=True)
    historicalvejoe(onlyUpdate=True)
    mergeDataFromAll()
    print(f"Historical data merged and updated after {time.time() - timeStart}s")

    print("Getting fresh data:")
    joeBalances()
    TVLFresh()
    veJOEBalances()
    print("Finished fetching, merging")
    mergeFreshData()
    print(f"Fresh data merged and updated after {time.time() - timeStart}s")

    # if not development:
    #     reloadingStart = time.time()

    #     reloadWebApp()
    #     print(f"reloading ended after {time.time() - reloadingStart}")




if __name__ == '__main__':
    main()
