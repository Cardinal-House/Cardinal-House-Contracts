from brownie import network, config, CardinalToken, interface
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account
from pathlib import Path
from web3 import Web3
import math
import csv

CARDINAL_TOKEN_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
CARDINAL_TOKEN_ADDRESS = "0x6B627cF7D9D2fF72fCa23bb43dA8350f42577CEa"
USDC_ADDRESS_TEST_REAL = "0xe6b8a5CF854791412c1f6EFC7CAf629f5Df1c747"
USDC_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

PROD = True
SET_BALANCES = False
CARDINAL_TO_USDC = 36640

def refund_USDC_to_CRNL_holders(cardinalTokenAddress=None, usdcAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS
        usdcAddress = USDC_ADDRESS

    if not cardinalTokenAddress:
        cardinalTokenAddress = CARDINAL_TOKEN_ADDRESS_TEST

    if not usdcAddress:
        usdcAddress = USDC_ADDRESS_TEST

    cardinalTokenABI = CardinalToken.abi
    cardinalToken = Contract.from_abi("CardinalToken", cardinalTokenAddress, cardinalTokenABI)
    USDC = interface.IERC20(usdcAddress)

    print(f"Account Matic balance is currently: {account.balance()}")

    accounts = []
    balances = []
    CRNLbalance = 0

    filePath = Path(__file__).parent.parent
    with open(f'{filePath}/holder-data/CRNLHolders.csv', 'r') as holderDataFile:
        holderData = csv.reader(holderDataFile, delimiter=',')

        for holder in holderData:
            if holder[0] != "HolderAddress":
                accounts.append(holder[0])
                if Web3.toWei(holder[1], "ether") > Web3.toWei("1", "ether"):
                    balances.append(int(float(holder[1]) * CARDINAL_TO_USDC))
                else:
                    balances.append(int(float(holder[1]) * CARDINAL_TO_USDC))

                CRNLbalance += int(float(holder[1]))

    assert len(accounts) == len(balances)
    print(f"Number of holders: {len(accounts)}")
    
    if SET_BALANCES:
        for i in range(len(accounts)):
            USDC.transfer(accounts[i], balances[i], {"from": account})
    else:
        print(accounts)
        print(balances)
        print(len(accounts))
        print(len(balances))
        print(f"Sum of all account balances is: {sum(balances)}")
        print(f"Sum of all CRNL is: {CRNLbalance}")

    print(f"Account Matic balance is currently: {account.balance()}")

def main():
    refund_USDC_to_CRNL_holders()