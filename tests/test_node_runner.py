from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from scripts.deploy_marketplace import deploy_cardinal_house_marketplace
from scripts.deploy_node_runner import deploy_node_runner
from brownie import network, accounts, exceptions
from web3 import Web3
import pytest

LIQUIDITY_SUPPLY = Web3.toWei(3500000, "ether")

def test_user_can_purchase_node_runner_NFT():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    testTokenURI = "Test Token URI"
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)
    cardinalToken.excludeUserFromFees(nodeRunner.address, {"from": account})
    nodeRunner.updateNodeRunnerTokenURI(testTokenURI, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, NFTPrice, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})

    cardinalToken.approve(nodeRunner.address, NFTPrice, {"from": account2})
    nodeRunner.mintNodeRunnerNFT(1, {"from": account2})

    # Assert
    assert nodeRunner.nodeRunnerTokenURI() == testTokenURI
    assert cardinalToken.balanceOf(account2.address) == 0
    assert cardinalToken.balanceOf(nodeRunner.address) == NFTPrice
    assert nodeRunner.maxNFTs() == maxNFTs
    assert nodeRunner.NFTPriceInUSDC() == NFTPrice
    assert nodeRunner.marketplaceAddress() == cardinalHouseMarketplace.address
    assert nodeRunner._tokenIds() == 1
    assert nodeRunner.tokenURI(1) == testTokenURI
    assert nodeRunner.ownerOf(1) == account2.address
    assert nodeRunner.tokenIdToListingFee(1) == listingFee

def test_user_cant_purchase_NFT_unless_member():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act/Assert
    cardinalToken.transfer(account2.address, NFTPrice, {"from": account})
    cardinalToken.approve(nodeRunner.address, NFTPrice, {"from": account2})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        nodeRunner.mintNodeRunnerNFT(1, {"from": account2})
    assert "Only Cardinal Crew Members can participate in Node Runner." in str(ex.value)

def test_user_cant_purchase_NFT_without_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act/Assert
    cardinalToken.transfer(account2.address, NFTPrice - 1, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})
    cardinalToken.approve(nodeRunner.address, NFTPrice, {"from": account2})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        nodeRunner.mintNodeRunnerNFT(1, {"from": account2})
    assert "You don't have enough USDC to pay for the Node Runner NFT." in str(ex.value)

def test_user_cant_purchase_NFT_without_approving_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act/Assert
    cardinalToken.transfer(account2.address, NFTPrice, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})
    cardinalToken.approve(nodeRunner.address, NFTPrice - 1, {"from": account2})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        nodeRunner.mintNodeRunnerNFT(1, {"from": account2})
    assert "You haven't approved this contract to spend enough of your USDC to pay for the Node Runner NFT." in str(ex.value)

def test_user_cant_purchase_NFT_past_limit():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act/Assert
    cardinalToken.transfer(account2.address, NFTPrice, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account.address, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})

    cardinalToken.approve(nodeRunner.address, NFTPrice * maxNFTs, {"from": account})
    for i in range(maxNFTs):
        nodeRunner.mintNodeRunnerNFT(1, {"from": account})

    cardinalToken.approve(nodeRunner.address, NFTPrice, {"from": account2})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        nodeRunner.mintNodeRunnerNFT(1, {"from": account2})
    assert "There aren't enough Node Runner NFTs for this node for you to mint you amount you chose. Another node will be available soon!" in str(ex.value)

def test_owner_can_deposit_matic():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act
    account1NFTCount = 15
    account2NFTCount = 5
    depositAmount = 1000
    cardinalToken.transfer(account2.address, NFTPrice * account2NFTCount, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account.address, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})

    cardinalToken.approve(nodeRunner.address, NFTPrice * account1NFTCount, {"from": account})
    cardinalToken.approve(nodeRunner.address, NFTPrice * account2NFTCount, {"from": account2})

    nodeRunner.mintNodeRunnerNFT(account1NFTCount, {"from": account})
    nodeRunner.mintNodeRunnerNFT(account2NFTCount, {"from": account2})

    nodeRunner.depositNodeRewards({"from": account, "value": depositAmount})

    # Assert
    assert nodeRunner._tokenIds() == account1NFTCount + account2NFTCount
    assert nodeRunner.addressToMaticCanClaim(account.address) == depositAmount * (account1NFTCount / (account1NFTCount + account2NFTCount))
    assert nodeRunner.addressToMaticCanClaim(account2.address) == depositAmount * (account2NFTCount / (account1NFTCount + account2NFTCount))

def test_users_can_withdraw_matic():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act
    account1NFTCount = 15
    account2NFTCount = 5
    depositAmount = 1000
    cardinalToken.transfer(account2.address, NFTPrice * account2NFTCount, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account.address, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})

    cardinalToken.approve(nodeRunner.address, NFTPrice * account1NFTCount, {"from": account})
    cardinalToken.approve(nodeRunner.address, NFTPrice * account2NFTCount, {"from": account2})

    nodeRunner.mintNodeRunnerNFT(account1NFTCount, {"from": account})
    nodeRunner.mintNodeRunnerNFT(account2NFTCount, {"from": account2})

    nodeRunner.depositNodeRewards({"from": account, "value": depositAmount})

    account1InitialBalance = account.balance()
    account2InitialBalance = account2.balance()
    account1CanClaimAmount = nodeRunner.addressToMaticCanClaim(account.address)
    account2CanClaimAmount = nodeRunner.addressToMaticCanClaim(account2.address)

    nodeRunner.claimNodeRewards({"from": account})
    nodeRunner.claimNodeRewards({"from": account2})

    # Assert
    assert account.balance() == account1InitialBalance + account1CanClaimAmount
    assert account2.balance() == account2InitialBalance + account2CanClaimAmount
    assert nodeRunner.addressToMaticCanClaim(account.address) == 0
    assert nodeRunner.addressToMaticCanClaim(account2.address) == 0

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        nodeRunner.claimNodeRewards({"from": account2})
    assert "You don't have any node rewards to claim! If you have an NFT for this node, please wait until the next reward deposit." in str(ex.value)

def test_owner_can_create_NFTs():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)

    # Act
    account1NFTCount = 15
    account2NFTCount = 5
    depositAmount = 1000
    cardinalToken.transfer(account2.address, NFTPrice * account2NFTCount, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account.address, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})

    for i in range(account1NFTCount):
        nodeRunner.createToken("test token URI", {"from": account})
    
    for i in range(account2NFTCount):
        tokenId = nodeRunner.createToken("test token URI", {"from": account}).return_value
        nodeRunner.transferFrom(account.address, account2.address, tokenId, {"from": account})

    nodeRunner.depositNodeRewards({"from": account, "value": depositAmount})

    # Assert
    assert nodeRunner._tokenIds() == account1NFTCount + account2NFTCount
    assert nodeRunner.addressToMaticCanClaim(account.address) == depositAmount * (account1NFTCount / (account1NFTCount + account2NFTCount))
    assert nodeRunner.addressToMaticCanClaim(account2.address) == depositAmount * (account2NFTCount / (account1NFTCount + account2NFTCount))

def test_owner_can_withdraw_node_funds():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    cardinalToken.transfer(uniswapPair, LIQUIDITY_SUPPLY, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    listingFee = 1000
    maxNFTs = 20
    NFTPrice = 10000
    nodeRunner = deploy_node_runner(cardinalHouseMarketplace.address, cardinalNFT.address, cardinalToken.address, listingFee, maxNFTs, NFTPrice)
    cardinalToken.excludeUserFromFees(nodeRunner.address, {"from": account})
    nodeRunner.updateNFTPriceInUSDC(NFTPrice * 2, {"from": account})
    nodeRunner.updateUSDCAddress(cardinalToken.address, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, NFTPrice * 2, {"from": account})
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.addMember(account2.address, {"from": account})

    cardinalToken.approve(nodeRunner.address, NFTPrice * 2, {"from": account2})
    nodeRunner.mintNodeRunnerNFT(1, {"from": account2})

    initialCardinalTokenBalance = cardinalToken.balanceOf(account.address)
    nodeRunner.withdrawNodeFunds({"from": account})

    # Assert
    assert cardinalToken.balanceOf(account.address) == initialCardinalTokenBalance + NFTPrice * 2
