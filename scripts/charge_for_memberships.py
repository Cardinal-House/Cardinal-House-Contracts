from brownie import network, config, chain, CardinalToken, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import math
import csv

CARDINAL_TOKEN_ADDRESS_TEST = ""
CARDINAL_TOKEN_ADDRESS = ""
CARDINAL_NFT_ADDRESS_TEST = ""
CARDINAL_NFT_ADDRESS = ""
CARDINAL_HOUSE_MARKETPLACE_ADDRESS_TEST = ""
CARDINAL_HOUSE_MARKETPLACE_ADDRESS = ""
PROD = False

MEMBERSHIP_SECONDS_TILL_RECHARGE = 2592000

def charge_for_memberships(cardinalTokenAddress=None, cardinalNFTAddress=None, cardinalHouseMarketplaceAddress=None, membershipSecondsTillRecharge=MEMBERSHIP_SECONDS_TILL_RECHARGE):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalTokenAddress = CARDINAL_NFT_ADDRESS
        cardinalNFTAddress = CHAIN_ESTATE_V2_TOKEN_ADDRESS
        cardinalHouseMarketplaceAddress = CARDINAL_HOUSE_MARKETPLACE_ADDRESS

    if not cardinalTokenAddress:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS_TEST
    
    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST
    
    if not cardinalHouseMarketplaceAddress:
        cardinalHouseMarketplaceAddress = CARDINAL_HOUSE_MARKETPLACE_ADDRESS_TEST

    cardinalTokenABI = CardinalToken.abi
    cardinalToken = Contract.from_abi("CardinalToken", cardinalTokenAddress, cardinalTokenABI)

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFT = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    print(f"Account Matic balance is currently: {account.balance()}")

    # Get a list of all membership NFTs (not Original Cardinal NFTs though since those owners aren't charged for memberships).
    membershipNFTIds = cardinalNFT.getMembershipTokenIds()

    # For each membership NFT, if not charged for 30 days, charge for the NFT if the owner hasn't already been charged,
    # the owner isn't the Cardinal House deployer address, and the owner isn't the Cardinal House marketplace address
    chargedMembers = []
    chargedNFTIds = []
    lostMembers = []
    burntNFTs = []
    for membershipNFTId in membershipNFTIds:
        NFTOwner = cardinalNFT.ownerOf(membershipNFTId)
        
        if NFTOwner not in chargedMembers and NFTOwner != account.address and NFTOwner != cardinalHouseMarketplaceAddress:
            epoch_time = chain.time()
            membershipLastPaidTimestamp = cardinalNFT.membershipNFTToLastPaid(membershipNFTId)

            if epoch_time - membershipLastPaidTimestamp >= membershipSecondsTillRecharge:
                chargeResult = cardinalNFT.chargeMemberForMembership(NFTOwner, membershipNFTId, epoch_time, {"from": account})

                if chargeResult.return_value == 0:
                    chargedMembers.append(NFTOwner)
                elif not cardinalNFT.addressIsMember(NFTOwner):
                    lostMembers.append(NFTOwner)

                if cardinalNFT.ownerOf(membershipNFTId) == NFTOwner:
                    chargedNFTIds.append(membershipNFTId)
                else:
                    burntNFTs.append(membershipNFTId)

    # Any final checks?

    print(f"Account Matic balance is now currently: {account.balance()}")

    return chargedMembers, chargedNFTIds, lostMembers, burntNFTs

def main():
    charge_for_memberships()