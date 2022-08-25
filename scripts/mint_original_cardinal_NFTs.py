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

CARDINAL_NFT_ADDRESS_TEST = "0x92259eB95029965d82edf81A996Add27c6b6a54a"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
PROD = True

mintToAddresses = [
    "0x9Ae29376c8fF59bC8B5217D0cbd3a67Ee48B7465",
    "0xF011f357da24cad5Bb0897C2D652225937aBC4D7 ",
    "0xA30305e3300fAeFcF76cf921fEa11D0A73745fbC ",
    "0xD9c45dc237886Cb2C0a3F960305D4f866225842f ",
    "0x1318F75B4be4bfE6321FF6cf0e4A4f8cEaE9e7cE ",
    "0x402dB56D67b91553E5b09Df60d10881fAa8d4cE5 ",
    "0x3451382dadAe3F7c1D46070738D0072376803483 ",
    "0x43Ca5320BAbF6B2f2328a6dE5C1d97C794d41aBd ",
    "0x377AC2A3adA0952e54F538e51865DfC5FABcAEd7",
    "0xF99220eBC04de3488E4d3BC1b104e83A75bB137a",
    "0xb4592B2b0D7cE176213f8f9d13e93DB38aB4773b",
    "0x44da6d127FB9c5536C4e8f38cC9229576cf50326",
    "0x563E8425fB2aA879BbE29805745833c13cf4Bd8A",
    "0x99b005da72c0b668a11f2c5ab6b8f55b00c99b38",
    "0xc341e0fd548298de89b38fe31f2ac63457105451"
]
images = [
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 1.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 2.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 3.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 4.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 5.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 6.jpg",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 7.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 8.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 9.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 10.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 11.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 12.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 13.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 14.png",
    "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 15.png",
]

tokenIds = [
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    # "8",
    # "9",
    # "10",
    # "11",
    # "12",
    # "13",
    # "14",
    # "15",
    # "16",
    # "17",
    #"18",
    # "19",
    # "20"
]

startOCNum = 1

projectId = os.environ["InfuraCardinalHouseProjectId"]
projectSecret = os.environ["InfuraCardinalHouseProjectSecret"]

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
            response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
            imageHash = response.json()["Hash"]
            
            currImageURL = f"https://ipfs.infura.io/ipfs/{imageHash}"

        currTokenURI = {
            "NFTName": f"Original Cardinal NFT #{currOCNum}",
            "NFTDescription": "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
            "image": currImageURL
        }

        files = {'file': str(currTokenURI).replace("\'", "\"")}
        response = requests.post('https://ipfs.infura.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
        tokenURIHash = response.json()["Hash"]
        newTokenURI = f"https://ipfs.infura.io/ipfs/{tokenURIHash}"

        epoch_time = chain.time()
        cardinalNFTContract.createToken(newTokenURI, cardinalNFTContract.originalCardinalTypeId(), 0, epoch_time, {"from": account})
        cardinalNFTContract.transferFrom(account.address, currAddress, tokenIds[i], {"from": account})
        
        currOCNum += 1

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    mint_original_cardinal_NFTs()