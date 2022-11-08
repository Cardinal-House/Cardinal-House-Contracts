from brownie import network, config, chain, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import requests
import math
import json
import csv
import os

CARDINAL_NFT_ADDRESS_TEST = "0x2B579760ff3B8B899454370e765Bb748B146aCF0"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
PROD = False

mintToAddresses = [
    "0xf817C2040D5468dE61E522D747B775B5942e8cb9",
    "0x18Dbdf44c87081c3D6952Dd4B5298C528d3B2e05",
]
images = [
    "D:\\Cardinal House Art\\Service NFTs\\OmniVerseAudit.png",
    "D:\\Cardinal House Art\\Service NFTs\\OmniVerseAudit.png",
]

tokenIds = [
    "16",
    "17",
]

tokenNames = [
    "Cardinal House Audit of OmniVerse",
    "Cardinal House Audit #1: OmniVerse",
]

tokenDescriptions = [
    "This NFT represents a completed Cardinal House audit of the OmniVerse smart contracts! The OmniVerse smart contracts had a low risk severity, which means they passed the audit with flying colors.",
    "This NFT represents a completed Cardinal House audit of the OmniVerse smart contracts! The OmniVerse smart contracts had a low risk severity, which means they passed the audit with flying colors.",
]

projectId = os.environ["InfuraCardinalHouseProjectId"]
projectSecret = os.environ["InfuraCardinalHouseProjectSecret"]

def mint_service_NFTs(cardinalNFTAddress=None, mintToAddresses=mintToAddresses, images=images, tokenIds=tokenIds, tokenNames=tokenNames, tokenDescriptions=tokenDescriptions):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS

    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    if len(mintToAddresses) != len(images):
        print("Mint to addresses array length doesn't match the images array length.")
        return

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFTContract = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    print(f"Account Matic balance is currently: {account.balance()}")

    for i in range(len(mintToAddresses)):
        currAddress = mintToAddresses[i]
        currImage = images[i]
        currTokenName = tokenNames[i]
        currTokenDescription = tokenDescriptions[i]
        currImageURL = ""

        response = pinata.pin_file_to_ipfs(currImage)

        currImageURL = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

        currTokenURI = {
            "NFTName": currTokenName,
            "NFTDescription": currTokenDescription,
            "image": currImageURL
        }

        response = pinata.pin_json_to_ipfs(currTokenURI)

        newTokenURI = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

        epoch_time = chain.time()
        cardinalNFTContract.createToken(newTokenURI, cardinalNFTContract.serviceTypeId(), 0, epoch_time, {"from": account})

        if account.address != currAddress:
            cardinalNFTContract.transferFrom(account.address, currAddress, tokenIds[i], {"from": account})

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    mint_service_NFTs()