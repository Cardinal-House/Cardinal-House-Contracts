from brownie import network, config, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import requests
import math
import json
import csv

CARDINAL_NFT_ADDRESS_TEST = "0x92259eB95029965d82edf81A996Add27c6b6a54a"
CARDINAL_NFT_ADDRESS = "0x7D9E6AadBb79E83f327369F379d9b26CC4a4452b"
PROD = True

mintToAddresses = [
    "0x18Dbdf44c87081c3D6952Dd4B5298C528d3B2e05",
]
images = [
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Chess Silver Trophy.png",
]

startOCNum = 1

def mint_original_cardinal_NFTs(cardinalNFTAddress=None, mintToAddresses=mintToAddresses, images=images, startOCNum=startOCNum):
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

    currOCNum = startOCNum

    for i in range(len(mintToAddresses)):
        currAddress = mintToAddresses[i]
        currImage = images[i]
        currImageURL = ""

        with open(currImage, "rb") as imageFile:
            files = {'file': imageFile}
            response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files)
            imageHash = response.json()["Hash"]
            
            currImageURL = f"https://ipfs.infura.io/ipfs/{imageHash}"

        currTokenURI = {
            "NFTName": f"Original Cardinal NFT #{currOCNum}",
            "NFTDescription": "This NFT grants you a lifetime Cardinal Crew membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
            "image": currImageURL
        }

        files = {'file': str(currTokenURI).replace("\'", "\"")}
        response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files)
        tokenURIHash = response.json()["Hash"]
        newTokenURI = f"https://ipfs.infura.io/ipfs/{tokenURIHash}"

        cardinalNFTContract.createToken(newTokenURI, cardinalNFTContract.originalCardinalTypeId(), 0, {"from": account})
        
        currOCNum += 1

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    mint_original_cardinal_NFTs()