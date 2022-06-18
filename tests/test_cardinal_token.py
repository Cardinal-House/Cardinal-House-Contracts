from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(3500000, "ether")

def test_can_transfer_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, 10000, {"from": account})
    cardinalToken.transfer(account.address, 2000, {"from": account2})

    # Assert
    account2Balance = cardinalToken.balanceOf(account2.address)
    assert account2Balance == 8000
    waitForTransactionsToComplete()

def test_transaction_fees_work():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    cardinalToken, _, _ = deploy_cardinal_house(account3.address, account4.address, account5.address, account.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Account 3 is the giveaway wallet
    memberGiveawayWalletAddress = cardinalToken.memberGiveawayWalletAddress()
    # Account 4 is the marketing wallet
    marketingWalletAddress = cardinalToken.marketingWalletAddress()
    # Account 5 is the developer wallet
    developerWalletAddress = cardinalToken.developerWalletAddress()
    cardinalTokenAddress = cardinalToken.getContractAddress()

    memberGiveawayFee = cardinalToken.memberGiveawayFeePercent()
    marketingFee = cardinalToken.marketingFeePercent()
    developerFee = cardinalToken.developerFeePercent()

    # Act
    # Account deployed the smart contract and thus was excluded from fees by default, so needs to be added.
    cardinalToken.includeUsersInFees(account.address, {"from": account})

    # Send tokens from account5 to account
    tokensSent = 10000
    cardinalToken.transfer(account.address, tokensSent, {"from": account5})

    # Transfer some tokens to account2
    transferAmount = 100
    cardinalToken.transfer(account2.address, transferAmount, {"from": account})

    # Assert
    assert cardinalToken.balanceOf(account.address) == tokensSent - transferAmount
    assert cardinalToken.balanceOf(account2.address) == transferAmount * ((100 - memberGiveawayFee - marketingFee - developerFee) / 100)

    memberGiveawayFeeAmount = transferAmount * (memberGiveawayFee / 100)
    marketingFeeAmount = transferAmount * (marketingFee / 100)
    developerFeeAmount = transferAmount * (developerFee / 100)
    assert cardinalToken.balanceOf(cardinalTokenAddress) == marketingFeeAmount + developerFeeAmount
    assert cardinalToken.balanceOf(account3.address) == memberGiveawayFeeAmount

def test_owner_can_exclude_users_from_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act
    cardinalToken.excludeUserFromFees(account2.address, {"from": account})

    # Assert
    assert cardinalToken.excludedFromFees(account2.address)

def test_only_owner_can_exclude_users_from_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    cardinalToken, _, _ = deploy_cardinal_house()

    # Act/Assert
    nonOwner = accounts.add()
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.excludeUserFromFees(nonOwner.address, {"from": nonOwner})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_include_users_into_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act
    cardinalToken.includeUsersInFees(account2.address, {"from": account})

    # Assert
    assert not cardinalToken.excludedFromFees(account2.address)

def test_only_owner_can_include_users_from_fees():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    cardinalToken, _, _ = deploy_cardinal_house()

    # Act/Assert
    nonOwner = accounts.add()
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.includeUsersInFees(nonOwner.address, {"from": nonOwner})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_transaction_fee_works_on_transfer_from():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    cardinalToken, _, _ = deploy_cardinal_house(account3.address, account4.address, account5.address, account.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Account 3 is the giveaway wallet
    memberGiveawayWalletAddress = cardinalToken.memberGiveawayWalletAddress()
    # Account 4 is the marketing wallet
    marketingWalletAddress = cardinalToken.marketingWalletAddress()
    # Account 5 is the developer wallet
    developerWalletAddress = cardinalToken.developerWalletAddress()
    cardinalTokenAddress = cardinalToken.getContractAddress()

    memberGiveawayInitialBalance = cardinalToken.balanceOf(memberGiveawayWalletAddress)
    marketingInitialBalance = cardinalToken.balanceOf(marketingWalletAddress)
    developerInitialBalance = cardinalToken.balanceOf(developerWalletAddress)

    memberGiveawayFee = cardinalToken.memberGiveawayFeePercent()
    marketingFee = cardinalToken.marketingFeePercent()
    developerFee = cardinalToken.developerFeePercent()

    # Act
    tokenAmount = 1000000
    initialAccountBalance = cardinalToken.balanceOf(account.address)
    initialAccount2Balance = cardinalToken.balanceOf(account2.address)
    cardinalToken.transfer(account.address, tokenAmount, {"from": account5})
    cardinalToken.transfer(account2.address, tokenAmount, {"from": account5})

    assert cardinalToken.balanceOf(account.address) == initialAccountBalance + tokenAmount
    assert cardinalToken.balanceOf(account2.address) == initialAccount2Balance + tokenAmount

    # Approve account 1 to spend account 2's tokens and then spend them with the transferFrom function.
    initialAccount2Balance = cardinalToken.balanceOf(account2.address)
    initialAccount4Balance = cardinalToken.balanceOf(account4.address)
    cardinalToken.includeUsersInFees(account.address, {"from": account})
    cardinalToken.includeUsersInFees(account2.address, {"from": account})
    cardinalToken.includeUsersInFees(account4.address, {"from": account})
    cardinalToken.approve(account.address, tokenAmount, {"from": account2})
    cardinalToken.transferFrom(account2.address, account4.address, tokenAmount, {"from": account})

    # Assert
    assert cardinalToken.balanceOf(account4.address) == initialAccount4Balance + tokenAmount * ((100 - memberGiveawayFee - marketingFee - developerFee) / 100)
    assert cardinalToken.balanceOf(account2.address) == initialAccount2Balance - tokenAmount

    memberGiveawayFeeAmount = tokenAmount * (memberGiveawayFee / 100)
    marketingFeeAmount = tokenAmount * (marketingFee / 100)
    developerFeeAmount = tokenAmount * (developerFee / 100)
    assert cardinalToken.balanceOf(cardinalTokenAddress) == marketingFeeAmount + developerFeeAmount
    assert cardinalToken.balanceOf(account3.address) == memberGiveawayFeeAmount

def test_owner_cant_update_fees_past_limit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    cardinalToken, _, _ = deploy_cardinal_house()

    memberGiveawayFeeLimit = 5
    marketingFeeLimit = 5
    developerFeeLimit = 5

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.updateMemberGiveawayTransactionFee(memberGiveawayFeeLimit + 1, {"from": account})
    assert "The member giveaway transaction fee can't be more than 5%." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.updateMarketingTransactionFee(marketingFeeLimit + 1, {"from": account})
    assert "The marketing transaction fee can't be more than 5%." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.updateDeveloperTransactionFee(developerFeeLimit + 1, {"from": account})
    assert "The developer transaction fee can't be more than 5%." in str(ex.value)

def test_owner_can_update_fees_within_limit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()
    cardinalToken.setContractTokenDivisor(1, {"from": account})
    cardinalTokenAddress = cardinalToken.getContractAddress()

    memberGiveawayFeeLimit = 5
    marketingFeeLimit = 5
    developerFeeLimit = 5

    # Act
    cardinalToken.updateMemberGiveawayTransactionFee(memberGiveawayFeeLimit, {"from": account})
    cardinalToken.updateMarketingTransactionFee(marketingFeeLimit, {"from": account})
    cardinalToken.updateDeveloperTransactionFee(developerFeeLimit, {"from": account})

    # Assert
    memberGiveawayFee = cardinalToken.memberGiveawayFeePercent()
    marketingFee = cardinalToken.marketingFeePercent()
    developerFee = cardinalToken.developerFeePercent() 

    assert memberGiveawayFee == memberGiveawayFeeLimit
    assert marketingFee == marketingFeeLimit
    assert developerFee == developerFeeLimit

def test_transaction_fees_work_after_fee_update():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)
    cardinalToken, _, _ = deploy_cardinal_house(account3.address, account4.address, account5.address, account.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Account 3 is the giveaway wallet
    memberGiveawayWalletAddress = cardinalToken.memberGiveawayWalletAddress()
    # Account 4 is the marketing wallet
    marketingWalletAddress = cardinalToken.marketingWalletAddress()
    # Account 5 is the developer wallet
    developerWalletAddress = cardinalToken.developerWalletAddress()
    cardinalTokenAddress = cardinalToken.getContractAddress()

    memberGiveawayFeeLimit = 5
    marketingFeeLimit = 5
    developerFeeLimit = 5

    # Act
    cardinalToken.updateMemberGiveawayTransactionFee(memberGiveawayFeeLimit, {"from": account})
    cardinalToken.updateMarketingTransactionFee(marketingFeeLimit, {"from": account})
    cardinalToken.updateDeveloperTransactionFee(developerFeeLimit, {"from": account})

    # Account deployed the smart contract and thus was excluded from fees by default, so needs to be added.
    cardinalToken.includeUsersInFees(account.address, {"from": account})

    # Send tokens from account5 to account
    tokensSent = 10000
    cardinalToken.transfer(account.address, tokensSent, {"from": account5})

    # Transfer some tokens to account2
    transferAmount = 100
    cardinalToken.transfer(account2.address, transferAmount, {"from": account})

    # Assert
    assert cardinalToken.balanceOf(account.address) == tokensSent - transferAmount
    assert cardinalToken.balanceOf(account2.address) == transferAmount * ((100 - memberGiveawayFeeLimit - marketingFeeLimit - developerFeeLimit) / 100)

    memberGiveawayFeeAmount = transferAmount * (memberGiveawayFeeLimit / 100)
    marketingFeeAmount = transferAmount * (marketingFeeLimit / 100)
    developerFeeAmount = transferAmount * (developerFeeLimit / 100)
    assert cardinalToken.balanceOf(cardinalTokenAddress) == marketingFeeAmount + developerFeeAmount
    assert cardinalToken.balanceOf(account3.address) == memberGiveawayFeeAmount

def test_blacklist_stops_trading():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act/Assert
    tokenAmount = 7500000
    tokenAmount2 = 1000000
    initialAccountCRNLBalance = cardinalToken.balanceOf(account.address)
    initialAccount2CRNLBalance = cardinalToken.balanceOf(account2.address)
    cardinalToken.transfer(account2.address, tokenAmount, {"from": account})
    cardinalToken.transfer(account.address, tokenAmount2, {"from": account2})

    assert cardinalToken.balanceOf(account.address) == initialAccountCRNLBalance - tokenAmount + tokenAmount2
    assert cardinalToken.balanceOf(account2.address) == initialAccount2CRNLBalance + tokenAmount - tokenAmount2

    # Blacklist account 2 and make sure they can't transfer or transferFrom
    cardinalToken.updateBlackList(account2.address, True, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.transfer(account2.address, tokenAmount, {"from": account})
    assert "The address you are trying to send Cardinal Tokens to has been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.transfer(account.address, tokenAmount2, {"from": account2})
    assert "You have been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team." in str(ex.value)

    cardinalToken.approve(account.address, 1000000000, {"from": account2})
    cardinalToken.approve(account3.address, 1000000000, {"from": account2})
    cardinalToken.approve(account2.address, 1000000000, {"from": account})
    cardinalToken.approve(account3.address, 1000000000, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.transferFrom(account.address, account3.address, tokenAmount, {"from": account2})
    assert "You have been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.transferFrom(account2.address, account3.address, tokenAmount, {"from": account})
    assert "The address you're trying to spend the Cardinal Tokens from has been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.transferFrom(account.address, account2.address, tokenAmount, {"from": account3})
    assert "The address you are trying to send Cardinal Tokens to has been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team." in str(ex.value)

    # Unblacklist account 2 and make sure they can trade again
    cardinalToken.updateBlackList(account2.address, False, {"from": account})

    initialAccountCRNLBalance = cardinalToken.balanceOf(account.address)
    initialAccount2CRNLBalance = cardinalToken.balanceOf(account2.address)
    cardinalToken.transfer(account2.address, tokenAmount, {"from": account})
    cardinalToken.transfer(account.address, tokenAmount2, {"from": account2})

    assert cardinalToken.balanceOf(account.address) == initialAccountCRNLBalance - tokenAmount + tokenAmount2
    assert cardinalToken.balanceOf(account2.address) == initialAccount2CRNLBalance + tokenAmount - tokenAmount2

    initialAccountCRNLBalance = cardinalToken.balanceOf(account.address)
    initialAccount2CRNLBalance = cardinalToken.balanceOf(account2.address)
    cardinalToken.transferFrom(account.address, account2.address, tokenAmount, {"from": account3})
    cardinalToken.transferFrom(account2.address, account.address, tokenAmount2, {"from": account3})

    assert cardinalToken.balanceOf(account.address) == initialAccountCRNLBalance - tokenAmount + tokenAmount2
    assert cardinalToken.balanceOf(account2.address) == initialAccount2CRNLBalance + tokenAmount - tokenAmount2

def test_only_owner_can_add_minters():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.updateMinter(account.address, True, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)    

def test_only_minters_can_mint_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.mint(account2.address, 1000000, {"from": account})
    assert "You are not authorized to mint Cardinal Tokens." in str(ex.value)

def test_only_minters_can_burn_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalToken.burn(account2.address, 1000000, {"from": account})
    assert "You are not authorized to burn Cardinal Tokens." in str(ex.value)

def test_minters_can_mint_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act
    tokenMintAmount = 3500000
    initialTokenSupply = cardinalToken.totalSupply()
    initialAccount2CRNLBalance = cardinalToken.balanceOf(account2.address)
    cardinalToken.updateMinter(account.address, True, {"from": account})
    cardinalToken.mint(account2.address, tokenMintAmount, {"from": account})

    # Assert
    assert cardinalToken.balanceOf(account2.address) == initialAccount2CRNLBalance + tokenMintAmount
    assert cardinalToken.totalSupply() == initialTokenSupply + tokenMintAmount

def test_minters_can_burn_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, _, _ = deploy_cardinal_house()

    # Act
    tokenBurnAmount = 1000000
    initialTokenSupply = cardinalToken.totalSupply()
    initialAccountCRNLBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.updateMinter(account.address, True, {"from": account})
    cardinalToken.burn(account.address, tokenBurnAmount, {"from": account})

    # Assert
    assert cardinalToken.balanceOf(account.address) == initialAccountCRNLBalance - tokenBurnAmount
    assert cardinalToken.totalSupply() == initialTokenSupply - tokenBurnAmount
