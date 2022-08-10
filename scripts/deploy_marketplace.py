from brownie import network, config, CardinalNFT, CardinalHouseMarketplace, CardinalHousePreSale
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

CARDINAL_TOKEN_ADDRESS_TEST = "0xBdf546E64EA72497687f56462adb8cAff1ca1655"
CARDINAL_TOKEN_ADDRESS = "0xf5b618c106ABd01beAc194343B2768b903aF5acA"
CARDINAL_PRESALE_ADDRESS_TEST = "0x8D3a989b9f8D8Ee2CB7F1caBD2b42411946e4931"
CARDINAL_PRESALE_ADDRESS = "0xda482c6bd9d71D1674c9C1F2e70CA08eD164A78a"
PROD = False

def deploy_cardinal_house_marketplace(cardinalTokenAddress=None, cardinalPreSaleAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS
        cardinalPreSaleAddress = CARDINAL_PRESALE_ADDRESS
    elif not cardinalTokenAddress:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS_TEST
        cardinalPreSaleAddress = CARDINAL_PRESALE_ADDRESS_TEST

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    cardinalHouseMarketplace = CardinalHouseMarketplace.deploy(cardinalTokenAddress, {"from": account}, publish_source=publishSource)
    print(f"Cardinal House Marketplace deployed to {cardinalHouseMarketplace.address}")

    cardinalNFT = CardinalNFT.deploy(cardinalHouseMarketplace.address, cardinalTokenAddress, {"from": account}, publish_source=publishSource)
    print(f"Cardinal NFT deployed to {cardinalNFT.address}")

    transaction = cardinalHouseMarketplace.setCardinalNFT(cardinalNFT.address, {"from": account})
    transaction.wait(1)

    print("Successfully set the Cardinal NFT reference for the marketplace.")

    cardinalPreSaleABI = CardinalHousePreSale.abi
    cardinalHousePreSaleContract = Contract.from_abi("CardinalPreSale", cardinalPreSaleAddress, cardinalPreSaleABI)
    transaction = cardinalHousePreSaleContract.setCardinalNFT(cardinalNFT.address, {"from": account})
    transaction.wait(1)

    print("Successfully set the Cardinal NFT reference for the Cardinal House presale.")

    return cardinalHouseMarketplace, cardinalNFT

def main():
    deploy_cardinal_house_marketplace()