from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(3500000, "ether")

def test_integration():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    cardinalToken, _, _ = deploy_cardinal_house(account3.address, account4.address, account5.address, account5.address, account5.address)
    uniswapPair = cardinalToken.uniswapPair()
    account5CardinalBalance = cardinalToken.balanceOf(account5.address)
    cardinalToken.transfer(uniswapPair, account5CardinalBalance / 2, {"from": account5})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Send CRNL tokens from account3 to account
    tokensSent = 10000000000
    initialAccountBalanceBNB = account.balance()
    cardinalToken.transfer(account.address, tokensSent, {"from": account5})

    # Transfer some of the Cardinal Tokens to account2 when account is not included in fees.
    cardinalToken.excludeUserFromFees(account.address, {"from": account})
    cardinalToken.transfer(account2.address, tokensSent / 4, {"from": account})

    # Asserts that both accounts now have the correct amount of Cardinal Tokens.
    assert cardinalToken.balanceOf(account.address) == tokensSent * 3 / 4
    assert cardinalToken.balanceOf(account2.address) == tokensSent / 4

    # Transfer some of the Cardinal Tokens to account2 when account is included in fees.
    memberGiveawayWalletAddress = cardinalToken.memberGiveawayWalletAddress()
    marketingWalletAddress = cardinalToken.marketingWalletAddress()
    developerWalletAddress = cardinalToken.developerWalletAddress()
    cardinalTokenAddress = cardinalToken.getContractAddress()
    memberGiveawayInitialBalance = cardinalToken.balanceOf(memberGiveawayWalletAddress)
    devMarketingInitialBalance = cardinalToken.balanceOf(marketingWalletAddress)
    account1InitialBalance = cardinalToken.balanceOf(account.address)
    account2InitialBalance = cardinalToken.balanceOf(account2.address)

    memberGiveawayFee = cardinalToken.memberGiveawayFeePercent()
    marketingFee = cardinalToken.marketingFeePercent()
    developerFee = cardinalToken.developerFeePercent()

    cardinalToken.includeUsersInFees(account.address, {"from": account})
    cardinalToken.transfer(account2.address, tokensSent / 4, {"from": account})

    # Asserts that all accounts involved in the transaction have the correct amount of CRNL tokens.
    assert cardinalToken.balanceOf(account.address) == account1InitialBalance - tokensSent / 4
    assert cardinalToken.balanceOf(account2.address) == account2InitialBalance + ((tokensSent / 4) * (float(100 - memberGiveawayFee - marketingFee - developerFee) / 100))
    assert cardinalToken.balanceOf(cardinalTokenAddress) == ((tokensSent / 4) * (float(marketingFee + developerFee) / 100))
    assert cardinalToken.balanceOf(memberGiveawayWalletAddress) == ((tokensSent / 4) * (float(memberGiveawayFee) / 100))