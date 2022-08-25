from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from scripts.deploy_marketplace import deploy_cardinal_house_marketplace
from brownie import network, accounts, exceptions
import pytest

def test_user_can_purchase_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    initialPreSaleBalance = cardinalToken.balanceOf(cardinalHousePreSale.address)
    initialAccountBalance = cardinalToken.balanceOf(account.address)
    initialAccountBalanceMatic = account.balance()

    # Act
    MaticSent = 5000
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})

    # Assert
    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000
    assert cardinalToken.balanceOf(account.address) == initialAccountBalance + MaticToCRNLRate * MaticSent
    assert cardinalHousePreSale.getContractTokens() == initialPreSaleBalance - MaticToCRNLRate * MaticSent
    assert account.balance() == initialAccountBalanceMatic - MaticSent
    assert cardinalHousePreSale.getContractMatic() == MaticSent

def test_owner_can_change_purchase_cap():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    # Act
    initialPurchaseCap = cardinalHousePreSale.purchaseCap()
    purchaseCap = initialPurchaseCap / 2
    cardinalHousePreSale.changeCardinalTokenPurchaseCap(purchaseCap, {"from": account})

    # Assert
    assert cardinalHousePreSale.purchaseCap() == purchaseCap

def test_user_cant_purchase_above_purchase_cap():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000
    purchaseCap = 10000
    cardinalHousePreSale.changeCardinalTokenPurchaseCap(purchaseCap, {"from": account})

    # Act/Assert
    MaticSent = 5000
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})
    assert "You cannot purchase this many Cardinal Tokens, that would put you past your presale cap." in str(ex.value)

def test_user_cant_purchase_above_purchase_cap_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000
    MaticSent = 5000
    purchaseCap = MaticSent * 2 * MaticToCRNLRate
    cardinalHousePreSale.changeCardinalTokenPurchaseCap(purchaseCap, {"from": account})

    # Act/Assert
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})
    accountPurchaseAmount = cardinalHousePreSale.addressToAmountPurchased(account.address)
    assert accountPurchaseAmount == purchaseCap / 2

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent + 1})
    assert "You cannot purchase this many Cardinal Tokens, that would put you past your presale cap." in str(ex.value)

def test_only_owner_can_change_purchase_cap():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.changeCardinalTokenPurchaseCap(10, {"from": account2})
    assert "revert: Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_change_matic_conversion_rate():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    initialPreSaleBalance = cardinalToken.balanceOf(cardinalHousePreSale.address)
    initialAccountBalance = cardinalToken.balanceOf(account.address)
    initialAccountBalanceMatic = account.balance()

    # Act
    MaticSent = 2000
    initialConversionRate = cardinalHousePreSale.MaticToCRNLRate() / 1000
    newConversionRate = 75000
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})
    cardinalHousePreSale.changeMaticToCardinalTokenRate(75000, {"from": account})
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})

    # Assert
    MaticToCNRLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000
    assert MaticToCNRLRate == newConversionRate / 1000
    assert cardinalToken.balanceOf(account.address) == initialAccountBalance + (initialConversionRate + MaticToCNRLRate) * MaticSent
    assert cardinalHousePreSale.getContractTokens() == initialPreSaleBalance - (initialConversionRate + MaticToCNRLRate) * MaticSent
    assert account.balance() == initialAccountBalanceMatic - MaticSent * 2
    assert cardinalHousePreSale.getContractMatic() == MaticSent * 2

def test_only_owner_can_change_matic_conversion_rate():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.changeMaticToCardinalTokenRate(75000, {"from": account})
    assert "revert: Ownable: caller is not the owner" in str(ex.value)

def test_owner_can_withdraw_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    initialPreSaleBalance = cardinalToken.balanceOf(cardinalHousePreSale.address)
    initialAccount2Balance = cardinalToken.balanceOf(account2.address)
    initialAccountBalanceMatic = account.balance()
    initialAccount2BalanceMatic = account2.balance()
    
    # Act
    MaticSent = 10000
    cardinalHousePreSale.purchaseCardinalTokens({"from": account2, "value": MaticSent})

    # Assert
    MaticToCNRLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000
    assert cardinalToken.balanceOf(account2.address) == initialAccount2Balance + MaticToCNRLRate * MaticSent
    assert cardinalToken.balanceOf(cardinalHousePreSale.address) == initialPreSaleBalance - MaticToCNRLRate * MaticSent
    assert account2.balance() == initialAccount2BalanceMatic - MaticSent
    assert cardinalHousePreSale.balance() == MaticSent

    # Act 2
    maticWithdraw = 8000
    presaleMaticBalance = cardinalHousePreSale.balance()
    cardinalHousePreSale.withdrawMatic(maticWithdraw, {"from": account})

    # Assert 2
    assert account.balance() == initialAccountBalanceMatic + maticWithdraw
    assert cardinalHousePreSale.balance() == presaleMaticBalance - maticWithdraw
    
def test_owner_cant_over_withdraw():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)

    # Act
    MaticSent = 50000
    maticWithdraw = MaticSent * 2
    cardinalHousePreSale.purchaseCardinalTokens({"from": account2, "value": MaticSent})

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.withdrawMatic(maticWithdraw, {"from": account})
    assert "revert: Failed to send Matic" in str(ex.value)

def test_only_owner_can_withdraw_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
    
    account = retrieve_account()
    account2 = retrieve_account(2)

    # Act
    MaticSent = 800000
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.withdrawMatic(MaticSent / 2, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_member_discount():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    NFTMembershipPrice = 5000
    cardinalNFT.updateMembershipPrice(NFTMembershipPrice, {"from": account})

    # Give some tokens to the accounts to purchase membership NFTs.
    accountTokenAmount = 1000000000
    cardinalToken.transfer(account2.address, 1000000000, {"from": account})
    cardinalToken.transfer(account3.address, 1000000000, {"from": account})
    cardinalToken.transfer(account4.address, 1000000000, {"from": account})

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFTs.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account2})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account3})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account4})

    # Have account2 purchase a membership NFT
    cardinalNFT.mintMembershipNFT({"from": account2})
    
    # Manually make account3 a member
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account3.address, {"from": account})
    
    # Act
    # Have acount2 and account3 purchase Cardinal Tokens from the presale and make sure the discount applies
    MaticSent = 10000
    account2InitialCRNLBalance = cardinalToken.balanceOf(account2.address)
    account3InitialCRNLBalance = cardinalToken.balanceOf(account3.address)
    account4InitialCRNLBalance = cardinalToken.balanceOf(account4.address)
    cardinalHousePreSale.purchaseCardinalTokens({"from": account2, "value": MaticSent})
    cardinalHousePreSale.purchaseCardinalTokens({"from": account3, "value": MaticSent})
    cardinalHousePreSale.purchaseCardinalTokens({"from": account4, "value": MaticSent})

    memberPreSaleDiscount = cardinalHousePreSale.memberDiscountAmount()
    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000

    # Assert
    assert cardinalToken.balanceOf(account2.address) == account2InitialCRNLBalance + MaticSent * MaticToCRNLRate * memberPreSaleDiscount / 100
    assert cardinalToken.balanceOf(account3.address) == account3InitialCRNLBalance + MaticSent * MaticToCRNLRate * memberPreSaleDiscount / 100
    assert cardinalToken.balanceOf(account4.address) == account3InitialCRNLBalance + MaticSent * MaticToCRNLRate

def test_only_members_can_purchase_when_flag_set():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
        
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    NFTMembershipPrice = 5000
    cardinalNFT.updateMembershipPrice(NFTMembershipPrice, {"from": account})

    # Non owner can't set the onlyMembers flag.
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.changeOnlyMembers(True, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Set the onlyMembers flag to true so only members can purchase Cardinal Tokens from the presale.
    cardinalHousePreSale.changeOnlyMembers(True, {"from": account})

    # Give some tokens to the accounts to purchase membership NFTs.
    accountTokenAmount = 1000000000
    cardinalToken.transfer(account2.address, 1000000000, {"from": account})
    cardinalToken.transfer(account3.address, 1000000000, {"from": account})
    cardinalToken.transfer(account4.address, 1000000000, {"from": account})

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFTs.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account2})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account3})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account4})

    # Have account2 purchase a membership NFT
    cardinalNFT.mintMembershipNFT({"from": account2})
    
    # Manually make account3 a member
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account3.address, {"from": account})
    
    # Act
    # Have acount2 and account3 purchase Cardinal Tokens from the presale and make sure the discount applies
    MaticSent = 10000
    account2InitialCRNLBalance = cardinalToken.balanceOf(account2.address)
    account3InitialCRNLBalance = cardinalToken.balanceOf(account3.address)
    account4InitialCRNLBalance = cardinalToken.balanceOf(account4.address)
    cardinalHousePreSale.purchaseCardinalTokens({"from": account2, "value": MaticSent})
    cardinalHousePreSale.purchaseCardinalTokens({"from": account3, "value": MaticSent})

    # Account 4 isn't a member so shouldn't be able to purchase Cardinal Tokens from presale since the onlyMembers flag is set to true
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.purchaseCardinalTokens({"from": account4, "value": MaticSent})
    assert "Only members can participate in the presale for the first 24 hours." in str(ex.value)

    memberPreSaleDiscount = cardinalHousePreSale.memberDiscountAmount()
    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate() / 1000

    # Assert
    assert cardinalToken.balanceOf(account2.address) == account2InitialCRNLBalance + MaticSent * MaticToCRNLRate * memberPreSaleDiscount / 100
    assert cardinalToken.balanceOf(account3.address) == account3InitialCRNLBalance + MaticSent * MaticToCRNLRate * memberPreSaleDiscount / 100

    # Set onlyMembers flag to false so account 4 can participate in the presale.
    cardinalHousePreSale.changeOnlyMembers(False, {"from": account})
    cardinalHousePreSale.purchaseCardinalTokens({"from": account4, "value": MaticSent})

    assert cardinalToken.balanceOf(account4.address) == account3InitialCRNLBalance + MaticSent * MaticToCRNLRate