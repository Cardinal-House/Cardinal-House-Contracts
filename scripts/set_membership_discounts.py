from brownie import network, config, chain, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from datetime import datetime
from pathlib import Path
from web3 import Web3
import math
import csv
import os

CARDINAL_NFT_ADDRESS_TEST = "0x2B579760ff3B8B899454370e765Bb748B146aCF0"
CARDINAL_NFT_ADDRESS = "0x57381fA9a67f7c3EAD677BD2cCD41fB583c9Ce3c"
PROD = False

membersArr = [
    "0x6eBA8cF0B61265996a8a32A4E9cF458eaD2e1768"
]

discountAmountsArr = [
    1
]

def set_membership_discounts(cardinalNFTAddress=None, members=None, discountAmounts=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS
        members = membersArr
        discountAmounts = discountAmountsArr
    
    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST
    
    if not members:
        members = membersArr
        discountAmounts = discountAmountsArr

    if len(members) != len(discountAmounts):
        print("Member array length isn't equal to the discount amounts array length.")
        return

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFT = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    print(f"Account Matic balance is currently: {account.balance()}")

    if not cardinalNFT.addressIsAdmin(account.address):
        cardinalNFT.setAdminUser(account.address, True, {"from": account})

    for i in range(len(members)):
        currMember = members[i]
        currDiscountAmount = discountAmounts[i]

        cardinalNFT.setMemberDiscount(currMember, currDiscountAmount, {"from": account})


def main():
    set_membership_discounts()