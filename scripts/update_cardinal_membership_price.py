from brownie import network, config, chain, CardinalToken, CardinalNFT
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from datetime import datetime
from pathlib import Path
from web3 import Web3
import requests
import json
import math
import csv
import os

CARDINAL_TOKEN_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
CARDINAL_TOKEN_ADDRESS = "0x6B627cF7D9D2fF72fCa23bb43dA8350f42577CEa"
CARDINAL_NFT_ADDRESS_TEST = "0x2B579760ff3B8B899454370e765Bb748B146aCF0"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
PAIR_ADDRESS = "0x98f533175f057f681cd2e29e882ccab75664d7b9"
PAIR_ADDRESS_TEST = ""
AGGREGATOR_ADDRESS = "0xAB594600376Ec9fD91F8e885dADF0CE036862dE0"
AGGREGATOR_ADDRESS_TEST = ""

aggregatorV3InterfaceABI = [{ "inputs": [], "name": "decimals", "outputs": [{ "internalType": "uint8", "name": "", "type": "uint8" }], "stateMutability": "view", "type": "function" }, { "inputs": [], "name": "description", "outputs": [{ "internalType": "string", "name": "", "type": "string" }], "stateMutability": "view", "type": "function" }, { "inputs": [{ "internalType": "uint80", "name": "_roundId", "type": "uint80" }], "name": "getRoundData", "outputs": [{ "internalType": "uint80", "name": "roundId", "type": "uint80" }, { "internalType": "int256", "name": "answer", "type": "int256" }, { "internalType": "uint256", "name": "startedAt", "type": "uint256" }, { "internalType": "uint256", "name": "updatedAt", "type": "uint256" }, { "internalType": "uint80", "name": "answeredInRound", "type": "uint80" }], "stateMutability": "view", "type": "function" }, { "inputs": [], "name": "latestRoundData", "outputs": [{ "internalType": "uint80", "name": "roundId", "type": "uint80" }, { "internalType": "int256", "name": "answer", "type": "int256" }, { "internalType": "uint256", "name": "startedAt", "type": "uint256" }, { "internalType": "uint256", "name": "updatedAt", "type": "uint256" }, { "internalType": "uint80", "name": "answeredInRound", "type": "uint80" }], "stateMutability": "view", "type": "function" }, { "inputs": [], "name": "version", "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }], "stateMutability": "view", "type": "function" }]

PROD = True
MEMBERSHIP_PRICE_IN_USD = 25

def update_cardinal_membership_price(cardinalTokenAddress=None, cardinalNFTAddress=None, pairAddress=None, aggregatorAddress=None, membershipPriceInUSD=MEMBERSHIP_PRICE_IN_USD):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS
        pairAddress = PAIR_ADDRESS
        aggregatorAddress = AGGREGATOR_ADDRESS

    if not cardinalTokenAddress:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS_TEST
    
    if not cardinalNFTAddress:
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST

    if not pairAddress:
        pairAddress = PAIR_ADDRESS_TEST

    if not aggregatorAddress:
        aggregatorAddress = AGGREGATOR_ADDRESS_TEST

    if not os.path.exists("logs"):
        os.mkdir("logs")

    currDate = datetime.now()
    currDateStr = datetime.strftime(currDate, "%Y-%m-%d")
    if not os.path.exists(f"logs/{currDateStr}"):
        os.mkdir(f"logs/{currDateStr}")

    cardinalTokenABI = CardinalToken.abi
    cardinalToken = Contract.from_abi("CardinalToken", cardinalTokenAddress, cardinalTokenABI)

    cardinalNFTABI = CardinalNFT.abi
    cardinalNFT = Contract.from_abi("CardinalNFT", cardinalNFTAddress, cardinalNFTABI)

    maticAggregator = Contract.from_abi("MaticAggregator", aggregatorAddress, aggregatorV3InterfaceABI)

    print(f"Account Matic balance is currently: {account.balance()}")
    print(f"Current Cardinal Crew Membership price is: {Web3.fromWei(cardinalNFT.membershipPriceInCardinalTokens(), 'ether')}")

    maticPriceInUSD = float(maticAggregator.latestRoundData()[1]) / 100000000.0
    print(f"Matic price in USD: ${maticPriceInUSD}")

    response = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/polygon/{pairAddress}")
    CRNLToUSD = json.loads(response.content)["pairs"][0]["priceUsd"]
    print(f"Cardinal Token price in USD: ${CRNLToUSD}")

    newCardinalMembershipPrice = Web3.toWei(float(membershipPriceInUSD) / float(CRNLToUSD), 'ether')
    print(f"New Cardinal Crew Membership Price in Cardinal Tokens is: {Web3.fromWei(newCardinalMembershipPrice, 'ether')}")

    cardinalNFT.updateMembershipPrice(newCardinalMembershipPrice, {"from": account})

    print(f"Account Matic balance is now currently: {account.balance()}")

    with open(f"logs/{currDateStr}/cardinalMembershipPriceChanges.txt", 'a') as priceChangeFile:
        priceChangeFile.write(f"{currDate.strftime('%Y-%m-%d, %H:%M:%S')}  -  updated price to {newCardinalMembershipPrice}\n")

    return newCardinalMembershipPrice

def main():
    update_cardinal_membership_price()