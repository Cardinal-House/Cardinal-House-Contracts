from brownie import network, config, chain, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import requests

CARDINAL_NFT_ADDRESS_TEST = "0x92259eB95029965d82edf81A996Add27c6b6a54a"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
PROD = True

MEMBER_ADDRESSES = [
    # "0x20d9849D9A5924d86dDc379Bc29Bb5f2B5286892",
    # "0x43Ca5320BAbF6B2f2328a6dE5C1d97C794d41aBd",
    # "0xFC110131F24c3cD7094FAf9E51635a22Be30D8A0",
    # "0x75D0E59e954AC655e20eC8419fDa6415a7F7d0b2",
    # "0x2F6F40da6DBA834D6Ab6f62a93bC606733737Fd5",
    # "0x88Be8ed5D9d48C6A8024bC4eeB08258edFE42cd9",
    # "0xAbeb50481A7b97c76567461946BC5c2A6F4Eba48",
    # "0x6E4D81B632Ee459Af61fb82e73D4e87Ff6dE70Cb",
    # "0x1270781F79133e7d1EB6928aca40cD949af27dA8",
    # "0x2425756033EF4F7315107d7CbeAdD65aAB26FC7d",
    # "0x049CC7022a82015C408C69407Fe833897A687B25",
    # "0x3451382dadAe3F7c1D46070738D0072376803483",
    # "0x6e39e0646ae69a9deef51d5b11a1dd2aaa16f56b",
    # "0x02E65F52f46373a60e8f87c16e496111f4F47EF6",
    # "0xF99220eBC04de3488E4d3BC1b104e83A75bB137a",
    # "0xF3FccD931781c663BC05b067861d8a005d6467a1",
    # "0xeB0E8aeC5De2312788aEb352d3c4Baf105B26E8c",
    # "0x377AC2A3adA0952e54F538e51865DfC5FABcAEd7",
    # "0xc341e0fd548298de89b38fe31f2ac63457105451",
    # "0xBf093b713E2547f1641520f5c1627D23e5664B6F",
    # "0xA5aE0A84D79217aA9E0a61fE1983AE1fe3419D1D",
    # "0xbe19A2f7f7491E95d6F4F3d6051535D8F81D7501",
    # "0x402dB56D67b91553E5b09Df60d10881fAa8d4cE5",
    # "0x9Ae29376c8fF59bC8B5217D0cbd3a67Ee48B7465",
    # "0xa1090738b0Af70A60a62a19De9aAE0D9639EAf64",
    # "0x8963e2D4982a89824c08741270244AF0AcAc5C2E",
    # "0x6155b60ECe82575235C03a65d288edE30008dA9A",
    # "0x906604cE1374b47b0986Cf2081e645c0ffddA1EC",
    # "0x93893f7e609888801ea67A586fC40fdB06F8b700",
    # "0x1318F75B4be4bfE6321FF6cf0e4A4f8cEaE9e7cE",
    # "0xD9c45dc237886Cb2C0a3F960305D4f866225842f",
    # "0x7B726662589f916A9A2fd393A58136ED9ca05bd0",
    # "0xF011f357da24cad5Bb0897C2D652225937aBC4D7",
    # "0xc1bA44b87ef5f0397f98AAd49e702e356C3A3b7E",
    # "0x000469f3f9cf8F58c2f1796f94a58CDDeaE8dc2E"
    # "0x303e818689FFF838e8c6867635c473c4AB89867F",
    "0xBA4Ddf6F81dC6Ee5626d8982Ab22dC22e2C24ddC"
]

def add_cardinal_crew_members(cardinalNFTAddress=None, memberAddresses=MEMBER_ADDRESSES):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS

    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFTContract = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    print(f"Account Matic balance is currently: {account.balance()}")

    for member in memberAddresses:
        print(member)
        cardinalNFTContract.addMember(member, {"from": account})

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    add_cardinal_crew_members()