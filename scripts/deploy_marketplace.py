from brownie import network, config, CardinalNFT, CardinalHouseMarketplace, CardinalHousePreSale
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

CARDINAL_TOKEN_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
CARDINAL_TOKEN_ADDRESS = "0x6B627cF7D9D2fF72fCa23bb43dA8350f42577CEa"
CARDINAL_PRESALE_ADDRESS_TEST = "0xF988d17B4CB8c9eCB83aC8C257885F66464Fb9e5"
CARDINAL_PRESALE_ADDRESS = "0xdEe16fAFc83D2c351D5A43577cFCBC6473F9b6bA"
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

    cardinalHouseMarketplace = CardinalHouseMarketplace.deploy({"from": account}, publish_source=publishSource)
    print(f"Cardinal House Marketplace deployed to {cardinalHouseMarketplace.address}")

    cardinalNFT = CardinalNFT.deploy(cardinalHouseMarketplace.address, cardinalTokenAddress, {"from": account}, publish_source=publishSource)
    print(f"Cardinal NFT deployed to {cardinalNFT.address}")

    transaction = cardinalHouseMarketplace.whiteListNFTContract(cardinalNFT.address, cardinalTokenAddress, False, {"from": account})
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