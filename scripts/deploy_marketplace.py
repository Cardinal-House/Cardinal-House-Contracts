from brownie import network, config, CardinalNFT, CardinalHouseMarketplace
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

CARDINAL_TOKEN_ADDRESS_TEST = "0x42b3be0E4769D5715b7D5a8D8D765C2E9D2aeD9D"
CARDINAL_TOKEN_ADDRESS = "0x31832D10f68D3112d847Bd924331F3d182d268C4"
PROD = False

def deploy_cardinal_house_marketplace(cardinalTokenAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS
    elif not cardinalTokenAddress:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS_TEST

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    cardinalHouseMarketplace = CardinalHouseMarketplace.deploy(cardinalTokenAddress, {"from": account}, publish_source=publishSource)
    print(f"Cardinal House Marketplace deployed to {cardinalHouseMarketplace.address}")

    cardinalNFT = CardinalNFT.deploy(cardinalHouseMarketplace.address, cardinalTokenAddress, {"from": account}, publish_source=publishSource)
    print(f"Cardinal NFT deployed to {cardinalNFT.address}")

    transaction = cardinalHouseMarketplace.setCardinalNFT(cardinalNFT.address, {"from": account})
    transaction.wait(1)
    print("Successfully set the Cardinal NFT reference for the marketplace.")

    return cardinalHouseMarketplace, cardinalNFT

def main():
    deploy_cardinal_house_marketplace()