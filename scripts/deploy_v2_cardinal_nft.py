from brownie import network, config, chain, CardinalNFT, CardinalHouseMarketplace
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from pathlib import Path
from web3 import Web3
import time

USDC_ADDRESS_TEST_REAL = "0xe6b8a5CF854791412c1f6EFC7CAf629f5Df1c747"
USDC_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
CARDINAL_MARKETPLACE_ADDRESS_TEST = "0xe8d93aB8ABC90495FDd5Bd797D8C8b2EBc63b43D"
CARDINAL_MARKETPLACE_ADDRESS = "0x16fA58F4CcDDcdD0a72fb71EAeDe896c2C4E77B0"
CARDINAL_NFT_OLD_ADDRESS_TEST = "0xEBadD172563627De64f995380820600335027933"
CARDINAL_NFT_OLD_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"

PROD = True

def deploy_v2_cardinal_nft(cardinalNFTOldAddress=None, cardinalHouseMarketplaceAddress=None, usdcAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTOldAddress = CARDINAL_NFT_OLD_ADDRESS
        cardinalHouseMarketplaceAddress = CARDINAL_MARKETPLACE_ADDRESS
        usdcAddress = USDC_ADDRESS

    if not cardinalNFTOldAddress:
        cardinalNFTOldAddress = CARDINAL_NFT_OLD_ADDRESS_TEST

    if not cardinalHouseMarketplaceAddress:
        cardinalHouseMarketplaceAddress = CARDINAL_MARKETPLACE_ADDRESS_TEST

    if not usdcAddress:
        usdcAddress = USDC_ADDRESS_TEST

    cardinalHouseMarketplaceABI = CardinalHouseMarketplace.abi
    cardinalHouseMarketplace = Contract.from_abi("CardinalHouseMarketplace", cardinalHouseMarketplaceAddress, cardinalHouseMarketplaceABI)

    cardinalNFTOldABI = CardinalNFT.abi
    cardinalNFTOld = Contract.from_abi("CardinalNFT", cardinalNFTOldAddress, cardinalNFTOldABI)

    print(f"Account Matic balance is currently: {account.balance()}")

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    cardinalNFT = CardinalNFT.deploy(cardinalHouseMarketplaceAddress, usdcAddress, {"from": account}, publish_source=publishSource)
    print(f"Cardinal NFT deployed to {cardinalNFT.address}")

    transaction = cardinalHouseMarketplace.whiteListNFTContract(cardinalNFT.address, usdcAddress, False, {"from": account})
    transaction.wait(1)

    print("Successfully set the Cardinal NFT reference for the marketplace.")

    membershipTypeId = cardinalNFTOld.membershipTypeId()
    for i in range(1, cardinalNFTOld._tokenIds() + 1):
        if cardinalNFTOld.tokenIdToTypeId(i) != membershipTypeId:
            cardinalNFT.createToken(cardinalNFTOld.tokenURI(i), cardinalNFTOld.tokenIdToTypeId(i), cardinalNFTOld.tokenIdToListingFee(i), chain.time(), {"from": account})
            time.sleep(3)
            newTokenId = cardinalNFT._tokenIds()
            cardinalNFT.transferFrom(account.address, cardinalNFTOld.ownerOf(i), newTokenId, {"from": account})

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    deploy_v2_cardinal_nft()