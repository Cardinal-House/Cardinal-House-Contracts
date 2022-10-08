from brownie import network, config, NodeRunner
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

CARDINAL_MARKETPLACE_ADDRESS_TEST = "0x7A4d6294435Ed0a7EbFf5D2bB4211af2d18624bE"
CARDINAL_MARKETPLACE_ADDRESS = "0x038F27dec7F9E02f7F0bA6d2e61Bc190258a7F52"
CARDINAL_NFT_ADDRESS_TEST = "0x92259eB95029965d82edf81A996Add27c6b6a54a"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
USDC_ADDRESS_TEST = "0xe6b8a5CF854791412c1f6EFC7CAf629f5Df1c747"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

MAX_NFTS = "20"
DEFAULT_LISTING_FEE = INITIAL_SUPPLY = Web3.toWei(5, "ether")
NFT_PRICE_IN_USDC = INITIAL_SUPPLY = Web3.toWei(100, "ether")

PROD = False

def deploy_node_runner(cardinalMarketplaceAddress=None, cardinalNFTAddress=None, USDCAddress=None, defaultListingFee=None, maxNFTs=None, NFTPriceInUSDC=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalMarketplaceAddress = CARDINAL_MARKETPLACE_ADDRESS
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS
        USDCAddress = USDC_ADDRESS
    elif not cardinalMarketplaceAddress:
        cardinalMarketplaceAddress = CARDINAL_MARKETPLACE_ADDRESS_TEST
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST
        USDCAddress = USDC_ADDRESS_TEST

    if not defaultListingFee:
        defaultListingFee = DEFAULT_LISTING_FEE

    if not maxNFTs:
        maxNFTs = MAX_NFTS

    if not NFTPriceInUSDC:
        NFTPriceInUSDC = NFT_PRICE_IN_USDC

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    nodeRunner = NodeRunner.deploy(
        cardinalMarketplaceAddress,
        cardinalNFTAddress,
        USDCAddress,
        defaultListingFee,
        maxNFTs,
        NFTPriceInUSDC,
        {"from": account}, publish_source=publishSource
    )
    print(f"Node Runner deployed to {nodeRunner.address}")

    return nodeRunner

def main():
    deploy_node_runner()