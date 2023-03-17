from brownie import network, config, chain, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from datetime import datetime
from pathlib import Path
from web3 import Web3
import time
import math
import csv
import os

CARDINAL_NFT_ADDRESS_TEST = "0x2B579760ff3B8B899454370e765Bb748B146aCF0"
CARDINAL_NFT_ADDRESS = "0x57381fA9a67f7c3EAD677BD2cCD41fB583c9Ce3c"
CARDINAL_HOUSE_MARKETPLACE_ADDRESS_TEST = "0xFa246fCF66056BFa737027ef24c8410248eD9041"
CARDINAL_HOUSE_MARKETPLACE_ADDRESS = "0x87dD7CC57E95cb288274319EbD33ED0fA640CBEf"
PROD = True

MEMBERSHIP_SECONDS_TILL_RECHARGE = 2592000

def charge_for_memberships(cardinalNFTAddress=None, cardinalHouseMarketplaceAddress=None, membershipSecondsTillRecharge=MEMBERSHIP_SECONDS_TILL_RECHARGE):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS
        cardinalHouseMarketplaceAddress = CARDINAL_HOUSE_MARKETPLACE_ADDRESS
    
    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST
    
    if not cardinalHouseMarketplaceAddress:
        cardinalHouseMarketplaceAddress = CARDINAL_HOUSE_MARKETPLACE_ADDRESS_TEST

    if not os.path.exists("logs"):
        os.mkdir("logs")

    currDate = datetime.now()
    currDateStr = datetime.strftime(currDate, "%Y-%m-%d")
    if not os.path.exists(f"logs/{currDateStr}"):
        os.mkdir(f"logs/{currDateStr}")

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
                completed = False

                while not completed:
                    time.sleep(3)
                    try:
                        chargeResult = cardinalNFT.chargeMemberForMembership.call(NFTOwner, membershipNFTId, epoch_time, {"from": account})
                        chargeResultTx = cardinalNFT.chargeMemberForMembership(NFTOwner, membershipNFTId, epoch_time, {"from": account})
                        chargeResultTx.wait(1)

                        if chargeResult == 0:
                            chargedMembers.append(NFTOwner)
                        elif not cardinalNFT.addressIsMember(NFTOwner):
                            lostMembers.append(NFTOwner)

                        if cardinalNFT.ownerOf(membershipNFTId) == NFTOwner:
                            chargedNFTIds.append(membershipNFTId)
                        else:
                            burntNFTs.append(membershipNFTId)   

                        completed = True                 
                    except:
                        completed = False

    # Any final checks?

    print(f"Account Matic balance is now currently: {account.balance()}")

    with open(f"logs/{currDateStr}/membershipCharges.txt", 'a') as membershipChargesFile:
        membershipChargesFile.writelines([
            f"{currDate.strftime('%Y-%m-%d, %H:%M:%S')}:\n",
            f"Charged Members: {chargedMembers}\n",
            f"Charged NFT IDs: {chargedNFTIds}\n",
            f"Lost members: {lostMembers}\n",
            f"Burnt NFT IDs: {burntNFTs}\n\n\n"
        ])

    return chargedMembers, chargedNFTIds, lostMembers, burntNFTs

def main():
    charge_for_memberships()