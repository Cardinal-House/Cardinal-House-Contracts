from brownie import network, config, chain, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pinatapy import PinataPy
from pathlib import Path
from web3 import Web3
import requests
import math
import time
import json
import csv
import os

CARDINAL_NFT_ADDRESS_TEST = "0x92259eB95029965d82edf81A996Add27c6b6a54a"
CARDINAL_NFT_ADDRESS = "0x57381fA9a67f7c3EAD677BD2cCD41fB583c9Ce3c"
PROD = True

mintToAddresses = [
    # "0x9Ae29376c8fF59bC8B5217D0cbd3a67Ee48B7465",
    # "0xF011f357da24cad5Bb0897C2D652225937aBC4D7",
    # "0xA30305e3300fAeFcF76cf921fEa11D0A73745fbC",
    # "0xD9c45dc237886Cb2C0a3F960305D4f866225842f",
    # "0x1318F75B4be4bfE6321FF6cf0e4A4f8cEaE9e7cE",
    # "0x402dB56D67b91553E5b09Df60d10881fAa8d4cE5",
    # "0x3451382dadAe3F7c1D46070738D0072376803483",
    # "0x43Ca5320BAbF6B2f2328a6dE5C1d97C794d41aBd",
    # "0x377AC2A3adA0952e54F538e51865DfC5FABcAEd7",
    # "0xF99220eBC04de3488E4d3BC1b104e83A75bB137a",
    # "0xb4592B2b0D7cE176213f8f9d13e93DB38aB4773b",
    # "0x44da6d127FB9c5536C4e8f38cC9229576cf50326",
    # "0x563E8425fB2aA879BbE29805745833c13cf4Bd8A",
    # "0x99b005da72c0b668a11f2c5ab6b8f55b00c99b38",
    # "0xc341e0fd548298de89b38fe31f2ac63457105451",
    # "0x2fd71aa5e1906741b22ed561d04cb1a2a5aca72a",
    # "0xa5ae0a84d79217aa9e0a61fe1983ae1fe3419d1d",
    # "0x4c90e8efef279a59c380b811003bb6cce96453e7",
    # "0x6E4D81B632Ee459Af61fb82e73D4e87Ff6dE70Cb",
    # "0x75D0E59e954AC655e20eC8419fDa6415a7F7d0b2",
    # "0x1270781F79133e7d1EB6928aca40cD949af27dA8",
    # "0x88Be8ed5D9d48C6A8024bC4eeB08258edFE42cd9",
    # "0xAbeb50481A7b97c76567461946BC5c2A6F4Eba48",
    # "0x20d9849D9A5924d86dDc379Bc29Bb5f2B5286892",
    # "0x160Cf6551ee3d910f673AF762D5a2f1bd4855be1",
    # "0xc7ED085dd3Ba4E69B0904C8d0C57E91b47E9bB81",
    # "0x8903FdDa42120CE6cE5EE158ED2cd085aB5c7eC0",
    # "0xa31539145CBf7F5aA7B4e72FaC3C520a86Cec00E",
    # "0x701C139a3513E73Dd75bd97B4e2737Cf842B40a4",
    # "0xB824a716E5b8B6Cc28B15aaF04d424D50Aa75C99",
    # "0xe0FF396Ae31Dc24848957bca282Bd07c01119B89",
    # "0x1c343ED0e03Fc5fB9a0804214E614963E6D2Ff00",
    # "0x9884705F4E825a2174C115280c4d147379d5C33D",
    # "0xf2A8E743F71E705edA3524e7812E7Eb9c8A2C78B",
    # "0x000469f3f9cf8F58c2f1796f94a58CDDeaE8dc2E",
    # "0xf65C572C797dcEc550c656F4dfb458f34EFB255A",
    # "0x0D61F83C20A9daF284aC3e576074Ae18D64F1404",
    # "0x160Cf6551ee3d910f673AF762D5a2f1bd4855be1",
    # "0xda53FBA9E7d5ec325808a43615280c5886a0b47E",
    # "0xf1bF108E81DD7257D491a6cd2575156B8afe25cB",
    # "0x219E5dCb3a20FA6B9653fE8534544CEF342132eC",
    # "0x534ec10913f40a271cD46644a6bB54a0152916c6",
    # "0xC31cA0dFc4537d4c214c3aE94a14442D50729401",
    "0xF7a403828e313BD786462afeBB9568F0fDaB07ba",
    "0x6E85929Cb0E92269E5ff5fd6a6cd3F378C41b316"
]
images = [
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 1.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 2.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 3.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 4.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 5.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 6.jpg",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 7.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 8.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 9.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 10.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 11.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 12.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 13.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 14.png",
    # "D:\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 15.png",
    # "C:\\Users\\colem\\Cardinal House\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 16.png",
    # "C:\\Users\\colem\\Cardinal House\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 17.png",
    # "C:\\Users\\colem\\Cardinal House\\Cardinal House Art\\Original Cardinal NFTs\\Original Cardinal NFT 18.png",
    # "Original Cardinal NFT 19.png",
    # "Original Cardinal NFT 20.png",
    # "Original Cardinal NFT 21.png",
    # "Original Cardinal NFT 22.png",
    # "Original Cardinal NFT 23.png",
    # "Original Cardinal NFT 24.png",
    # "Original Cardinal NFT 25.png",
    # "Original Cardinal NFT 26.png",
    # "Original Cardinal NFT 27.png",
    # "Original Cardinal NFT 28.png",
    # "Original Cardinal NFT 29.png",
    # "Original Cardinal NFT 30.png",
    # "Original Cardinal NFT 31.png",
    # "Original Cardinal NFT 32.png",
    # "Original Cardinal NFT 33.png",
    # "Original Cardinal NFT 34.png",
    # "Original Cardinal NFT 35.png",
    # "Original Cardinal NFT 36.png",
    # "Original Cardinal NFT 37.png",
    # "Original Cardinal NFT 38.png",
    # "Original Cardinal NFT 39.png",
    # "Original Cardinal NFT 40.png",
    # "Original Cardinal NFT 41.png",
    # "Original Cardinal NFT 42.png",
    # "Original Cardinal NFT 43.png",
    "Original Cardinal NFT 44.png",
    "Original Cardinal NFT 45.png"
]

tokenIds = [
    # "1",
    # "2",
    # "3",
    # "4",
    # "5",
    # "6",
    # "7",
    # "8",
    # "9",
    # "10",
    # "11",
    # "12",
    # "13",
    # "14",
    # "15",
    # "18",
    # "19",
    # "20",
    # "30",
    # "31",
    # "32",
    # "33",
    # "35",
    # "36",
    # "37",
    # "38",
    # "39",
    # "40",
    # "41",
    # "42",
    # "43",
    # "44",
    # "45",
    # "46",
    # "49",
    # "48",
    # "49",
    # "50",
    # "51",
    # "52",
    # "53",
    # "54",
    # "55",
    "56",
    "57"
]

startOCNum = 44

pinata = PinataPy(os.environ["PinataApiKey"], os.environ["PinataSecretApiKey"])

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

        response = pinata.pin_file_to_ipfs(currImage)

        currImageURL = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

        currTokenURI = {
            "NFTName": f"Original Cardinal NFT #{currOCNum}",
            "NFTDescription": "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
            "image": currImageURL
        }

        response = pinata.pin_json_to_ipfs(currTokenURI)

        newTokenURI = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

        epoch_time = chain.time()
        if int(tokenIds[i]) != 56:
            createTokenTransaction = cardinalNFTContract.createToken(newTokenURI, cardinalNFTContract.originalCardinalTypeId(), 0, epoch_time, {"from": account})
            createTokenTransaction.wait(1)
        
        time.sleep(10)

        cardinalNFTContract.transferFrom(account.address, currAddress, int(tokenIds[i]), {"from": account})
        
        currOCNum += 1

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    mint_original_cardinal_NFTs()