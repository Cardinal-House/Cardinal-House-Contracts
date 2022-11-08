from brownie import network, config, CardinalHouseMarketplace
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

CARDINAL_TOKEN_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
CARDINAL_TOKEN_ADDRESS = "0x6B627cF7D9D2fF72fCa23bb43dA8350f42577CEa"
CARDINAL_NFT_ADDRESS_TEST = "0xEBadD172563627De64f995380820600335027933"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
PROD = True

def deploy_just_cardinal_house_marketplace(cardinalTokenAddress=None, cardinalNFTAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS
    elif not cardinalTokenAddress:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS_TEST
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    cardinalHouseMarketplace = CardinalHouseMarketplace.deploy({"from": account}, publish_source=publishSource)

    if 'return_value' in dir(cardinalHouseMarketplace):
        cardinalHouseMarketplace = cardinalHouseMarketplace.return_value

    print(f"Cardinal House Marketplace deployed to {cardinalHouseMarketplace.address}")

    transaction = cardinalHouseMarketplace.whiteListNFTContract(cardinalNFTAddress, cardinalTokenAddress, False, {"from": account})
    transaction.wait(1)

    print("Successfully set the Cardinal NFT reference for the marketplace.")

    return cardinalHouseMarketplace

def main():
    deploy_just_cardinal_house_marketplace()