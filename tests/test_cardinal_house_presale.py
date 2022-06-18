from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from brownie import network, accounts, exceptions
import pytest

def test_user_can_purchase_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    initialPreSaleBalance = cardinalToken.balanceOf(cardinalHousePreSale.address)
    initialAccountBalance = cardinalToken.balanceOf(account.address)
    initialAccountBalanceMatic = account.balance()

    # Act
    MaticSent = 5
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})

    # Assert
    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate()
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

    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate()
    purchaseCap = 10
    cardinalHousePreSale.changeCardinalTokenPurchaseCap(purchaseCap, {"from": account})

    # Act/Assert
    MaticSent = 5
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})
    assert "You cannot purchase this many Cardinal Tokens, that would put you past your presale cap." in str(ex.value)

def test_user_cant_purchase_above_purchase_cap_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()

    MaticToCRNLRate = cardinalHousePreSale.MaticToCRNLRate()
    MaticSent = 5
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
    initialPreSaleBalance = cardinalToken.balanceOf(cardinalHousePreSale.address)
    initialAccountBalance = cardinalToken.balanceOf(account.address)
    initialAccountBalanceMatic = account.balance()

    # Act
    MaticSent = 2
    initialConversionRate = cardinalHousePreSale.MaticToCRNLRate()
    newConversionRate = 75000
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})
    cardinalHousePreSale.changeMaticToCardinalTokenRate(75000, {"from": account})
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})

    # Assert
    MaticToCNRLRate = cardinalHousePreSale.MaticToCRNLRate()
    assert MaticToCNRLRate == newConversionRate
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

    initialPreSaleBalance = cardinalToken.balanceOf(cardinalHousePreSale.address)
    initialAccount2Balance = cardinalToken.balanceOf(account2.address)
    initialAccountBalanceMatic = account.balance()
    initialAccount2BalanceMatic = account2.balance()
    
    # Act
    MaticSent = 10
    cardinalHousePreSale.purchaseCardinalTokens({"from": account2, "value": MaticSent})

    # Assert
    MaticToCNRLRate = cardinalHousePreSale.MaticToCRNLRate()
    assert cardinalToken.balanceOf(account2.address) == initialAccount2Balance + MaticToCNRLRate * MaticSent
    assert cardinalToken.balanceOf(cardinalHousePreSale.address) == initialPreSaleBalance - MaticToCNRLRate * MaticSent
    assert account2.balance() == initialAccount2BalanceMatic - MaticSent
    assert cardinalHousePreSale.balance() == MaticSent

    # Act 2
    maticWithdraw = 8
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

    # Act
    MaticSent = 5
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
    MaticSent = 8
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHousePreSale.purchaseCardinalTokens({"from": account, "value": MaticSent})

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePreSale.withdrawMatic(MaticSent / 2, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)