from brownie import network, config, CardinalNFT
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

images = [
    "C:\\Users\\colem\\Cardinal House\\Cardinal House Art\\Service NFTs\\OmniVerseAudit.png",
    "C:\\Users\\colem\\Cardinal House\\Cardinal House Art\\Service NFTs\\OmniVerseAudit.png",
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

imageToURL = {}

projectId = os.environ["InfuraCardinalHouseProjectId"]
projectSecret = os.environ["InfuraCardinalHouseProjectSecret"]

def update_NFT_token_URIs(cardinalNFTAddress=None, tokenIds=tokenIds, images=images, tokenNames=tokenNames, tokenDescriptions=tokenDescriptions):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS

    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    if len(tokenIds) != len(images):
        print("Token ID array length doesn't match the images array length.")
        return

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFT = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    if cardinalNFT._tokenIds() < max(tokenIds):
        print("There are token IDs in the token ID array that aren't in the NFT contract.")

    print(f"Account Matic balance is currently: {account.balance()}")

    for i in range(len(tokenIds)):
        currTokenId = tokenIds[i]
        currImage = images[i]

        currTokenURI = cardinalNFT.tokenURI(currTokenId)
        response = requests.get(currTokenURI)
        NFTTokenURI = json.loads(str(response.content).replace("\'", "\"")[2:-1])

        imageURL = ""
        if currImage in imageToURL.keys():
            imageURL = imageToURL[currImage]
        else:
            with open(currImage, "rb") as imageFile:
                files = {'file': imageFile}
                response = requests.post('https://infura-ipfs.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
                imageHash = response.json()["Hash"]
                
                imageURL = f"https://infura-ipfs.io/ipfs/{imageHash}"
                imageToURL[currImage] = imageURL

        NFTTokenURI["image"] = imageURL

        files = {'file': str(NFTTokenURI).replace("\'", "\"")}
        response = requests.post('https://infura-ipfs.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
        tokenURIHash = response.json()["Hash"]
        newTokenURI = f"https://infura-ipfs.io/ipfs/{tokenURIHash}"

        print(newTokenURI)

        cardinalNFT.setTokenURI(currTokenId, newTokenURI, {"from": account})

    '''
    for currTokenId in range(1, cardinalNFT._tokenIds() + 1):
        currTokenURI = cardinalNFT.tokenURI(currTokenId)
        currTokenURI = currTokenURI.replace("ipfs.infura.io", "infura-ipfs.io")

        response = requests.get(currTokenURI)
        NFTTokenURI = json.loads(str(response.content).replace("\'", "\"")[2:-1])

        NFTTokenURI["image"] = NFTTokenURI["image"].replace("ipfs.infura.io", "infura-ipfs.io")

        files = {'file': str(NFTTokenURI).replace("\'", "\"")}
        response = requests.post('https://infura-ipfs.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
        tokenURIHash = response.json()["Hash"]
        newTokenURI = f"https://infura-ipfs.io/ipfs/{tokenURIHash}"

        print(newTokenURI)

        cardinalNFT.setTokenURI(currTokenId, newTokenURI, {"from": account})
    '''

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    update_NFT_token_URIs()