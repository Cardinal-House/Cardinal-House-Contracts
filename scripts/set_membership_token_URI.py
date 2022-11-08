from brownie import network, config, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pinatapy import PinataPy
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

MEMBERSHIP_NFT_IMAGE_PATH = "MembershipNFT.jpg"

pinata = PinataPy(os.environ["PinataApiKey"], os.environ["PinataSecretApiKey"])

def set_membership_token_URI(cardinalNFTAddress=None, membershipNFTImagePath=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS

    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    if not membershipNFTImagePath:
        membershipNFTImagePath = MEMBERSHIP_NFT_IMAGE_PATH

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFT = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    print(f"Account Matic balance is currently: {account.balance()}")

    response = pinata.pin_file_to_ipfs(membershipNFTImagePath)

    currImageURL = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

    currTokenURI = {
        "NFTName": "Cardinal Crew Membership",
        "NFTDescription": "This NFT represents a Cardinal Crew Membership which is a monthly subscription that gives you access to exclusive content in Cardinal House!",
        "image": currImageURL
    }

    response = pinata.pin_json_to_ipfs(currTokenURI)

    newTokenURI = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"
    print(newTokenURI)

    ''' Old way of doing things with Infura
    with open(membershipNFTImagePath, "rb") as imageFile:
        files = {'file': imageFile}
        response = requests.post('https://infura-ipfs.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
        imageHash = response.json()["Hash"]
        
        imageURL = f"https://infura-ipfs.io/ipfs/{imageHash}"

    membershipNFTJson = {
        "NFTName": "Cardinal Crew Membership",
        "NFTDescription": "This NFT represents a Cardinal Crew Membership which is a monthly subscription that gives you access to exclusive content in Cardinal House!",
        "image": imageURL
    }

    files = {'file': str(membershipNFTJson).replace("\'", "\"")}
    response = requests.post('https://infura-ipfs.io:5001/api/v0/add', files=files, auth=(projectId, projectSecret))
    tokenURIHash = response.json()["Hash"]
    newTokenURI = f"https://infura-ipfs.io/ipfs/{tokenURIHash}"
    '''

    cardinalNFT.updateMembershipTokenURI(newTokenURI, {"from": account})

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    set_membership_token_URI()