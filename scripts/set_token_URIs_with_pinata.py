from brownie import network, config, chain, CardinalNFT
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

CARDINAL_NFT_ADDRESS_TEST = "0x92259eB95029965d82edf81A996Add27c6b6a54a"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
PROD = False
FETCH = False

currentNFTs = [
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmP74mdW6G7LAcBWk3gc7ZW8XYdS52H9XT7GHkLvRZPxb2', 'owner': '0x9Ae29376c8fF59bC8B5217D0cbd3a67Ee48B7465', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmQiig1aveDAhiRxjXZkwteVeUGyGCyNaFpjfzikPGeWaz', 'owner': '0x18Dbdf44c87081c3D6952Dd4B5298C528d3B2e05', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmSdaxGHpdMp6T3RMYJ3326ATRswJPA8kbQmpDqDniXJQ7', 'owner': '0xA30305e3300fAeFcF76cf921fEa11D0A73745fbC', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmNrbELZvMuqy6QCaM1ocxDoizVDt82bTWbXEoa7dFBXUU', 'owner': '0xD9c45dc237886Cb2C0a3F960305D4f866225842f', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmbDFfXPTEbxWPoVu4de54f7tnP76WcMXdT35pwkdDFy1F', 'owner': '0x1318F75B4be4bfE6321FF6cf0e4A4f8cEaE9e7cE', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZYVxF9cM6SgrQEkpudfATufnonQhtix6vCtgfiBo8ZZD', 'owner': '0x402dB56D67b91553E5b09Df60d10881fAa8d4cE5', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmU16ERgJChkMjneSeqFwheCtxrDmsnVrhwBT5vXVo7H9E', 'owner': '0x3451382dadAe3F7c1D46070738D0072376803483', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmWeeymu2XRCZ6gsBqMCcLxfAj6A94n8Hmvzba4voKd8LD', 'owner': '0x43Ca5320BAbF6B2f2328a6dE5C1d97C794d41aBd', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmcY3cE96USMZu7V7r2VdyorrrH3DXqsz96TN1eRmTDMBv', 'owner': '0x377AC2A3adA0952e54F538e51865DfC5FABcAEd7', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/Qmf1bGuKdiM5mYyVzg4NFh3QwyaR7Ywep7hziqEs8VDrju', 'owner': '0xF99220eBC04de3488E4d3BC1b104e83A75bB137a', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmRAdhXBk1pQVtUA8x3sjxwxxhoadQbbhr7FUyRiAFGzuH', 'owner': '0xb4592B2b0D7cE176213f8f9d13e93DB38aB4773b', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmYRRaUvmjbE9driFuMrwEQvc3JyYC15NtAqFyCMiKdon3', 'owner': '0x44da6d127FB9c5536C4e8f38cC9229576cf50326', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmeC9yYaENezAg17m9FhqPsScDnJaVeZs3cy3DV6Xqu9bs', 'owner': '0x563E8425fB2aA879BbE29805745833c13cf4Bd8A', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmRKrogseVEQFdVHWyNzfiqVvsJS8ddZaUrQ2WFuFDAbWh', 'owner': '0x99b005DA72C0b668A11F2C5aB6b8F55b00C99b38', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmTgePttY1J1HsoSgRzRvZbBkVX15TQNHp9MEx65siYtpX', 'owner': '0xC341e0fD548298dE89b38fe31F2AC63457105451', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmVYmuf68NvgSLe3n2SQLxgxGjduEPFQAGiJtja2dpVSFh', 'owner': '0xf817C2040D5468dE61E522D747B775B5942e8cb9', 'typeId': 3},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZbQQadf9aqSyV8RDyTwxyS7wzGovJghJp98asVFqq3EE', 'owner': '0x18Dbdf44c87081c3D6952Dd4B5298C528d3B2e05', 'typeId': 3},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmNqxWiEZ1fo5VpNnFF6KBSEK5AfCfLRdCMbEG2pVBnTbU', 'owner': '0x2Fd71aA5e1906741b22eD561D04cB1a2a5Aca72a', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmNzEmvcYvtJG3jx9gGHpZKKyGG6YyH8pvNSBvaehFiPqh', 'owner': '0xA5aE0A84D79217aA9E0a61fE1983AE1fe3419D1D', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZjCttQmSUveS3F9aANjs1QJ9sqjXhdddCqwFHiA3yiRX', 'owner': '0x4c90e8efEf279a59C380b811003Bb6CcE96453e7', 'typeId': 1},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0x75D0E59e954AC655e20eC8419fDa6415a7F7d0b2', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0x524Fc248Ed5F73Eaf77B4e8d46a9ADfFF1D10144', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0xAbeb50481A7b97c76567461946BC5c2A6F4Eba48', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0x6eBA8cF0B61265996a8a32A4E9cF458eaD2e1768', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0xbe19A2f7f7491E95d6F4F3d6051535D8F81D7501', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0xD17f7a98e933CCEd260D77F8bC0E0Ac56fcdDE3b', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0xd036d87001815e4C0412648A42547a91C859de41', 'typeId': 2},
    {'tokenURI': 'https://infura-ipfs.io/ipfs/QmZ6wbg8NH3tkpVsnftr5cshAgptpXSKCSxd9DQNHovAfk', 'owner': '0x089da352d9b9C929F2e41bd85769faFc31B67376', 'typeId': 2}
]

images = [
    "Original Cardinal NFT 1.png",
    "Original Cardinal NFT 2.png",
    "Original Cardinal NFT 3.png",
    "Original Cardinal NFT 4.png",
    "Original Cardinal NFT 5.png",
    "Original Cardinal NFT 6.jpg",
    "Original Cardinal NFT 7.png",
    "Original Cardinal NFT 8.png",
    "Original Cardinal NFT 9.png",
    "Original Cardinal NFT 10.png",
    "Original Cardinal NFT 11.png",
    "Original Cardinal NFT 12.png",
    "Original Cardinal NFT 13.png",
    "Original Cardinal NFT 14.png",
    "Original Cardinal NFT 15.png",
    "OmniVerseAudit.png",
    "OmniVerseAudit.png",
    "Original Cardinal NFT 16.png",
    "Original Cardinal NFT 17.png",
    "Original Cardinal NFT 18.png",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

NFTNames = [
    "Original Cardinal NFT #1",
    "Original Cardinal NFT #2",
    "Original Cardinal NFT #3",
    "Original Cardinal NFT #4",
    "Original Cardinal NFT #5",
    "Original Cardinal NFT #6",
    "Original Cardinal NFT #7",
    "Original Cardinal NFT #8",
    "Original Cardinal NFT #9",
    "Original Cardinal NFT #10",
    "Original Cardinal NFT #11",
    "Original Cardinal NFT #12",
    "Original Cardinal NFT #13",
    "Original Cardinal NFT #14",
    "Original Cardinal NFT #15",
    "Cardinal House Audit of OmniVerse",
    "Cardinal House Audit #1: OmniVerse",
    "Original Cardinal NFT #16",
    "Original Cardinal NFT #17",
    "Original Cardinal NFT #18",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]

NFTDescriptions = [
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT represents a completed Cardinal House audit of the OmniVerse smart contracts! The OmniVerse smart contracts had a low risk severity, which means they passed the audit with flying colors.",
    "This NFT represents a completed Cardinal House audit of the OmniVerse smart contracts! The OmniVerse smart contracts had a low risk severity, which means they passed the audit with flying colors.",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "This NFT grants you a lifetime Cardinal Crew Membership and was awarded to you for being an upstanding member of the early Cardinal House community!",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    ""
]


pinata = PinataPy(os.environ["PinataApiKey"], os.environ["PinataSecretApiKey"])

def set_token_URIs_with_pinata(cardinalNFTAddress=None, currentNFTs=currentNFTs, NFTNames=NFTNames, NFTDescriptions=NFTDescriptions):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS

    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    if len(currentNFTs) != len(NFTNames):
        print("NFT array length doesn't match the NFT names array length.")
        return

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFTContract = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    if FETCH:
        fetchList = []
        for i in range(1, cardinalNFTContract._tokenIds() + 1):
            currNFTTokenURI = cardinalNFTContract.tokenURI(i)
            currOwner = cardinalNFTContract.ownerOf(i)
            currTypeId = cardinalNFTContract.tokenIdToTypeId(i)

            currFetchItem = {"tokenURI": currNFTTokenURI, "owner": currOwner, "typeId": currTypeId}
            fetchList.append(currFetchItem)

        print(fetchList)

        return fetchList

    print(f"Account Matic balance is currently: {account.balance()}")

    cardinalMembershipTokenURI = cardinalNFTContract.membershipTokenURI()

    for i in range(len(currentNFTs)):
        currTypeId = currentNFTs[i]["typeId"]
        currImage = images[i]
        currNFTName = NFTNames[i]
        currNFTDescription = NFTDescriptions[i]
        currImageURL = ""

        if currTypeId == int(cardinalNFTContract.membershipTypeId()):
            print(f"Setting membership token URI for id: {i + 1}")
            cardinalNFTContract.setTokenURI(i + 1, cardinalMembershipTokenURI, {"from": account})
        else:
            print(f"Setting token URI for id: {i + 1}")
            response = pinata.pin_file_to_ipfs(currImage)

            currImageURL = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

            currTokenURI = {
                "NFTName": currNFTName,
                "NFTDescription": currNFTDescription,
                "image": currImageURL
            }

            response = pinata.pin_json_to_ipfs(currTokenURI)

            newTokenURI = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"
            print(newTokenURI)

            cardinalNFTContract.setTokenURI(i + 1, newTokenURI, {"from": account})

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    set_token_URIs_with_pinata()