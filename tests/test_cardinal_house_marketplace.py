from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from scripts.deploy_marketplace import deploy_cardinal_house_marketplace
from scripts.charge_for_memberships import charge_for_memberships
from brownie import network, accounts, exceptions, chain
from web3 import Web3
import pytest
import time

LIQUIDITY_SUPPLY = Web3.toWei(3500000, "ether")
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def test_membership_discount():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)

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
    cardinalToken.transfer(account5.address, 1000000000, {"from": account})

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFTs.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account2})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account3})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account4})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account5})

    # Even owner can't add discount to member until owner is made admin
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.setMemberDiscount(account2.address, 50, {"from": account})
    assert "Only contract admins can set a membership discount." in str(ex.value)

    # Non owner can't set admin user.
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.setAdminUser(account2.address, True, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Make the owner and account2 an admin.
    cardinalNFT.setAdminUser(account.address, True, {"from": account})
    cardinalNFT.setAdminUser(account2.address, True, {"from": account})

    # Owner and account2 should be able to apply discounts now.
    account2MembershipDiscount = 50
    accountMembershipDiscount = 90
    cardinalNFT.setMemberDiscount(account2.address, account2MembershipDiscount, {"from": account})
    cardinalNFT.setMemberDiscount(account.address, accountMembershipDiscount, {"from": account2})

    assert cardinalNFT.addressToMembershipDiscount(account2.address) == account2MembershipDiscount
    assert cardinalNFT.addressToMembershipDiscount(account.address) == accountMembershipDiscount

    # Owner can revoke admin rights for account2.
    cardinalNFT.setAdminUser(account2.address, False, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.setMemberDiscount(account.address, 50, {"from": account2})
    assert "Only contract admins can set a membership discount." in str(ex.value)

    # Account2 can purchase a membership NFT using the discount set by the owner.
    account2CRNLBalance = cardinalToken.balanceOf(account2.address)
    cardinalNFT.mintMembershipNFT({"from": account2})

    account2MembershipNFTID = 1
    assert cardinalNFT.addressToMembershipDiscount(account2.address) == 0
    assert cardinalNFT._tokenIds() == account2MembershipNFTID
    assert cardinalNFT.tokenIdToTypeId(account2MembershipNFTID) == cardinalNFT.membershipTypeId()
    assert cardinalNFT.ownerOf(account2MembershipNFTID) == account2.address

    cardinalNFTPrice = cardinalNFT.membershipPriceInCardinalTokens()
    
    assert cardinalToken.balanceOf(account2.address) == account2CRNLBalance - (cardinalNFTPrice * account2MembershipDiscount / 100)

    # Set up so that account2 gets charged again for membership NFT
    account2CRNLBalance = cardinalToken.balanceOf(account2.address)
    print(account2CRNLBalance)
    membershipSecondsTillRecharge = 1000
    epoch_time = chain.time()
    cardinalNFT.updateMembershipNFTLastPaid(account2MembershipNFTID, epoch_time - membershipSecondsTillRecharge, {"from": account})

    # Set discount for account2 for recharge
    account2MembershipDiscount = 80
    cardinalNFT.setMemberDiscount(account2.address, account2MembershipDiscount, {"from": account})

    chargedMembers, chargedNFTIds, lostMembers, burntNFTs = charge_for_memberships(cardinalToken.address, cardinalNFT.address, cardinalHouseMarketplace.address, membershipSecondsTillRecharge)

    assert cardinalNFT.addressToMembershipDiscount(account2.address) == 0
    assert cardinalNFT.ownerOf(account2MembershipNFTID) == account2.address
    assert cardinalToken.balanceOf(account2.address) == account2CRNLBalance - (cardinalNFTPrice * account2MembershipDiscount / 100)

def test_charge_for_memberships_script():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)

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
    cardinalToken.transfer(account5.address, 1000000000, {"from": account})

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFTs.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account2})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account3})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account4})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 10, {"from": account5})

    # Mints should be successful now since allowance and balance are good now for account2.
    cardinalNFT.mintMembershipNFT({"from": account2})
    cardinalNFT.mintMembershipNFT({"from": account3})
    cardinalNFT.mintMembershipNFT({"from": account4})
    cardinalNFT.mintMembershipNFT({"from": account5})
    cardinalNFT.mintMembershipNFT({"from": account})
    epoch_time = chain.time()
    firstTokenId = 1
    secondTokenId = 2
    thirdTokenId = 3
    fourthTokenId = 4
    fifthTokenId = 5

    # Set the last paid timestamp for account2, account3, account5, and account'ss membership NFTs so they get charged
    membershipSecondsTillRecharge = 1000
    cardinalNFT.updateMembershipNFTLastPaid(firstTokenId, epoch_time - membershipSecondsTillRecharge, {"from": account})
    cardinalNFT.updateMembershipNFTLastPaid(secondTokenId, epoch_time - 2 * membershipSecondsTillRecharge, {"from": account})
    cardinalNFT.updateMembershipNFTLastPaid(fourthTokenId, epoch_time - 2 * membershipSecondsTillRecharge, {"from": account})
    cardinalNFT.updateMembershipNFTLastPaid(fifthTokenId, epoch_time - 2 * membershipSecondsTillRecharge, {"from": account})

    # Transfer tokens from account5 so the membership NFT for account5 gets burnt.
    cardinalToken.transfer(account.address, cardinalToken.balanceOf(account5.address), {"from": account5})
    initialAccountBalance = cardinalToken.balanceOf(account.address)

    # Call the charge_for_memberships script.
    # Account 1 and Account 4 should have nothing happen with their membership NFTs (Account 1 since the deployer never gets charged).
    # Account 2 and Account 3 should be charged for their membership NFTs.
    # Account 5 should have its membership NFT burnt since it doesn't have the tokens to pay for the charge.
    chargedMembers, chargedNFTIds, lostMembers, burntNFTs = charge_for_memberships(cardinalToken.address, cardinalNFT.address, cardinalHouseMarketplace.address, membershipSecondsTillRecharge)

    # Assert that the arrays returned are correct.
    assert len(chargedMembers) == 2
    assert chargedMembers[0] == account2.address
    assert chargedMembers[1] == account3.address

    assert len(chargedNFTIds) == 2
    assert chargedNFTIds[0] == firstTokenId
    assert chargedNFTIds[1] == secondTokenId

    assert len(lostMembers) == 1
    assert lostMembers[0] == account5.address

    assert len(burntNFTs) == 1
    assert burntNFTs[0] == 4

    # Assert that all of the correct membership NFT transactions took place.
    assert cardinalNFT.ownerOf(firstTokenId) == account2.address
    assert cardinalNFT.ownerOf(secondTokenId) == account3.address
    assert cardinalNFT.ownerOf(thirdTokenId) == account4.address
    assert cardinalNFT.ownerOf(fifthTokenId) == account.address

    # Account 5 should lose the membership NFT.
    assert cardinalNFT.ownerOf(fourthTokenId) != account5.address
    assert cardinalNFT.ownerOf(fourthTokenId) == cardinalNFT.address

    # Account 2 and Accoun t 3 should have less tokens since they were charged for the membership NFTs.
    assert cardinalToken.balanceOf(account2.address) == accountTokenAmount - 2 * NFTMembershipPrice
    assert cardinalToken.balanceOf(account3.address) == accountTokenAmount - 2 * NFTMembershipPrice

    # Account 1 and Account 4 should not have been charged for the membership NFT (besides the initial mint)
    assert abs(cardinalToken.balanceOf(account.address) - initialAccountBalance) < NFTMembershipPrice / 2
    assert cardinalToken.balanceOf(account4.address) == accountTokenAmount - NFTMembershipPrice

    assert cardinalNFT.addressIsMember(account.address) == True
    assert cardinalNFT.addressIsMember(account2.address) == True
    assert cardinalNFT.addressIsMember(account3.address) == True
    assert cardinalNFT.addressIsMember(account4.address) == True
    assert cardinalNFT.addressIsMember(account5.address) == False

def test_users_can_mint_membership_NFTs():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    NFTMembershipPrice = 5000
    cardinalNFT.updateMembershipPrice(NFTMembershipPrice, {"from": account})
    newMembershipTokenURI = "New Membership Token URI"
    cardinalNFT.updateMembershipTokenURI(newMembershipTokenURI, {"from": account})

    assert cardinalNFT.membershipPriceInCardinalTokens() == NFTMembershipPrice
    assert cardinalNFT.membershipTokenURI() == newMembershipTokenURI

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.mintMembershipNFT({"from": account2})
    assert "You don't have enough Cardinal Tokens to pay for the membership NFT." in str(ex.value)

    # Give some tokens to account2.
    cardinalToken.transfer(account2.address, 1000000000, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.mintMembershipNFT({"from": account2})
    assert "You haven't approved this contract to spend enough of your Cardinal Tokens to pay for the membership NFT." in str(ex.value)

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFT.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice, {"from": account2})

    # This mint should be successful now since allowance and balance are good now for account2.
    epoch_time = chain.time()
    cardinalNFT.mintMembershipNFT({"from": account2})
    tokenId = 1

    assert cardinalNFT._tokenIds() == tokenId
    assert cardinalNFT.ownerOf(tokenId) == account2.address
    assert cardinalNFT.tokenIdToTypeId(tokenId) == cardinalNFT.membershipTypeId()
    assert cardinalNFT.addressToMemberNFTCount(account2.address) == tokenId
    assert cardinalNFT.addressIsMember(account2.address) == True
    assert len(cardinalNFT.getMembershipTokenIds()) == tokenId
    assert cardinalNFT.getMembershipTokenIds()[0] == tokenId
    assert cardinalNFT.tokenURI(tokenId) == cardinalNFT.membershipTokenURI()
    assert abs(epoch_time - cardinalNFT.membershipNFTToLastPaid(tokenId)) <= 2

def test_owner_can_create_and_send_membership_NFTs():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    epoch_time = chain.time()
    cardinalNFT.createToken("Test Membership NFT", cardinalNFT.membershipTypeId(), 0, epoch_time, {"from": account})
    tokenId = 1

    # Send the newly created membership NFT to account3 to then send to account2 since the owner account has special behaviors
    cardinalNFT.transferFrom(account.address, account3.address, tokenId, {"from": account})

    assert cardinalNFT._tokenIds() == tokenId
    assert cardinalNFT.ownerOf(tokenId) == account3.address
    assert cardinalNFT.tokenIdToTypeId(tokenId) == cardinalNFT.membershipTypeId()
    assert cardinalNFT.addressToMemberNFTCount(account3.address) == tokenId
    assert cardinalNFT.addressIsMember(account3.address) == True
    assert len(cardinalNFT.getMembershipTokenIds()) == tokenId
    assert cardinalNFT.getMembershipTokenIds()[0] == tokenId
    assert cardinalNFT.tokenURI(tokenId) == "Test Membership NFT"
    assert abs(epoch_time - cardinalNFT.membershipNFTToLastPaid(tokenId)) <= 2

    # Send the newly created membership NFT to account2 from account3
    cardinalNFT.transferFrom(account3.address, account2.address, tokenId, {"from": account3})

    assert cardinalNFT._tokenIds() == tokenId
    assert cardinalNFT.ownerOf(tokenId) == account2.address
    assert cardinalNFT.tokenIdToTypeId(tokenId) == cardinalNFT.membershipTypeId()
    assert cardinalNFT.addressToMemberNFTCount(account2.address) == tokenId
    assert cardinalNFT.addressToMemberNFTCount(account3.address) == 0
    assert cardinalNFT.addressIsMember(account2.address) == True
    assert cardinalNFT.addressIsMember(account3.address) == False
    assert len(cardinalNFT.getMembershipTokenIds()) == tokenId
    assert cardinalNFT.getMembershipTokenIds()[0] == tokenId
    assert cardinalNFT.tokenURI(tokenId) == "Test Membership NFT"

def test_owner_can_charge_for_membership_NFTs():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    NFTMembershipPrice = 5000
    cardinalNFT.updateMembershipPrice(NFTMembershipPrice, {"from": account})
    newMembershipTokenURI = "New Membership Token URI"
    cardinalNFT.updateMembershipTokenURI(newMembershipTokenURI, {"from": account})

    # Give some tokens to each account.
    cardinalToken.transfer(account2.address, 1000000000, {"from": account})
    cardinalToken.transfer(account3.address, 1000000000, {"from": account})
    cardinalToken.transfer(account4.address, 1000000000, {"from": account})
    cardinalToken.transfer(account5.address, 1000000000, {"from": account})

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFTs.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 5, {"from": account2})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 5, {"from": account3})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 5, {"from": account4})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 5, {"from": account5})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice * 2, {"from": account})

    # Mint the NFTs for each account for further testing.
    epoch_time = chain.time()
    account2TokenId = 1
    account3TokenId = 2
    account4TokenId = 3
    account5TokenId = 4
    account1TokenId = 5
    cardinalNFT.mintMembershipNFT({"from": account2})
    cardinalNFT.mintMembershipNFT({"from": account3})
    cardinalNFT.mintMembershipNFT({"from": account4})
    cardinalNFT.mintMembershipNFT({"from": account5})
    cardinalNFT.mintMembershipNFT({"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.chargeMemberForMembership(account.address, 1, epoch_time, {"from": account})
    assert "This address doesn't own the NFT specified." in str(ex.value)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.chargeMemberForMembership(account.address, account1TokenId, epoch_time, {"from": account})
    assert "Can't charge the owner or marketplace for the membership." in str(ex.value)

    # Send the membership NFTs owned by account to the marketplace to make sure the marketplace can't get charged
    cardinalNFT.transferFrom(account.address, cardinalHouseMarketplace.address, account1TokenId, {"from": account})

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.chargeMemberForMembership(cardinalHouseMarketplace.address, account1TokenId, epoch_time, {"from": account})
    assert "Can't charge the owner or marketplace for the membership." in str(ex.value)

    # Mine a few blocks so the membership paid timestamps are different than initial mint time
    chain.mine(10)
    chain.sleep(10)
    chain.mine(10)

    # First test to make sure the membership NFT is burnt if the account with it can't afford it anymore
    cardinalToken.transfer(account.address, cardinalToken.balanceOf(account2.address), {"from": account2})
    account2InitialCRNLBalance = cardinalToken.balanceOf(account2.address)
    epoch_time = chain.time()
    chargeResult = cardinalNFT.chargeMemberForMembership(account2.address, account2TokenId, epoch_time, {"from": account})

    assert chargeResult.return_value == 1
    assert cardinalNFT.ownerOf(account2TokenId) == cardinalNFT.address
    assert cardinalNFT.addressIsMember(account2.address) == False
    assert account2TokenId not in cardinalNFT.getMembershipTokenIds()
    assert cardinalToken.balanceOf(account2.address) == account2InitialCRNLBalance

    # Second test the make sure the membership NFT is burnt if the allowance has run dry for the NFT contract to pull funds for the membership
    account3InitialCRNLBalance = cardinalToken.balanceOf(account3.address)
    cardinalToken.decreaseAllowance(cardinalNFT.address, cardinalToken.allowance(account3.address, cardinalNFT.address), {"from": account3})
    epoch_time = chain.time()
    chargeResult = cardinalNFT.chargeMemberForMembership(account3.address, account3TokenId, epoch_time, {"from": account})

    assert chargeResult.return_value == 1
    assert cardinalNFT.ownerOf(account3TokenId) == cardinalNFT.address
    assert cardinalNFT.addressIsMember(account3.address) == False
    assert account3TokenId not in cardinalNFT.getMembershipTokenIds()
    assert cardinalToken.balanceOf(account3.address) == account3InitialCRNLBalance

    # Third test the make sure funds are pulled for a membership NFT if the payment can actually go through and the NFT isn't burnt
    account4InitialCRNLBalance = cardinalToken.balanceOf(account4.address)
    epoch_time = chain.time()
    chargeResult = cardinalNFT.chargeMemberForMembership(account4.address, account4TokenId, epoch_time, {"from": account})

    assert chargeResult.return_value == 0
    assert cardinalNFT.ownerOf(account4TokenId) == account4.address
    assert cardinalNFT.addressIsMember(account4.address) == True
    assert account4TokenId in cardinalNFT.getMembershipTokenIds()
    assert cardinalToken.balanceOf(account4.address) == account4InitialCRNLBalance - cardinalNFT.membershipPriceInCardinalTokens()
    assert epoch_time == cardinalNFT.membershipNFTToLastPaid(account4TokenId)

    # Withdraw the funds from the NFT contract to the owner address.
    cardinalNFTContractCRNLBalance = cardinalToken.balanceOf(cardinalNFT.address)
    accountCRNLInitialBalance = cardinalToken.balanceOf(account.address)

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.withdrawMembershipNFTFunds({"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

    cardinalNFT.withdrawMembershipNFTFunds({"from": account})

    assert cardinalToken.balanceOf(account.address) == accountCRNLInitialBalance + cardinalNFTContractCRNLBalance
    assert cardinalToken.balanceOf(cardinalNFT.address) == 0

def test_owner_can_burn_membership_NFTs():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    NFTMembershipPrice = 5000
    cardinalNFT.updateMembershipPrice(NFTMembershipPrice, {"from": account})

    # Give some tokens to account2.
    cardinalToken.transfer(account2.address, 1000000000, {"from": account})

    # Approve the Cardinal NFT contract to spend the Cardinal Tokens to mint the membership NFT.
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice, {"from": account})
    cardinalToken.approve(cardinalNFT.address, NFTMembershipPrice, {"from": account2})

    # This mint should be successful now since allowance and balance are good now for account2.
    epoch_time = chain.time()
    cardinalNFT.mintMembershipNFT({"from": account2})
    cardinalNFT.mintMembershipNFT({"from": account})
    firstTokenId = 1
    secondTokenId = 2

    # Burn the NFT and then make sure the properties are updated for the user (i.e. they shouldn't be a member now)
    cardinalNFT.burnMembershiptNFTManually(firstTokenId, {"from": account})

    assert cardinalNFT._tokenIds() == secondTokenId
    assert cardinalNFT.ownerOf(firstTokenId) == cardinalNFT.address
    assert cardinalNFT.tokenIdToTypeId(firstTokenId) == cardinalNFT.membershipTypeId()
    assert cardinalNFT.addressToMemberNFTCount(account2.address) == 0
    assert cardinalNFT.addressIsMember(account2.address) == False
    assert len(cardinalNFT.getMembershipTokenIds()) == 1
    assert cardinalNFT.getMembershipTokenIds()[0] == secondTokenId

def test_cardinal_house_marketplace_whitelisting():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house()
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Give some tokens to each of the accounts.
    cardinalToken.transfer(account2.address, 1000000000, {"from": account})
    cardinalToken.transfer(account3.address, 1000000000, {"from": account})
    cardinalToken.transfer(account4.address, 1000000000, {"from": account})
    cardinalToken.transfer(account5.address, 1000000000, {"from": account})

    # Create Cardinal NFTs
    listingFee = Web3.toWei(0, "ether")
    epoch_time = chain.time()
    cardinalNFT.createToken("CRNL NFT 1", 2, listingFee, epoch_time, {"from": account})
    cardinalNFT.createToken("CRNL NFT 2", 3, listingFee, epoch_time, {"from": account})
    cardinalNFT.createToken("CRNL NFT 3", 4, listingFee, epoch_time, {"from": account})
    cardinalNFT.createToken("CRNL NFT 4", 5, listingFee, epoch_time, {"from": account})
    cardinalNFT.createToken("CRNL NFT 5", 6, listingFee, epoch_time, {"from": account})

    # Whitelist the first NFT to account 2 (token ID = 1) and the second NFT to account 3 (token ID = 2)
    cardinalNFT.addWhiteListToToken(account2.address, 1)
    cardinalNFT.addWhiteListToToken(account3.address, 2)

    # List the NFTs on the marketplace, no listing fee for the owner account (account 1)
    NFTPrice = 2000000
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, 1, NFTPrice, {"from": account})
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, 2, NFTPrice, {"from": account})

    # account 2 can't purchase the NFT for account 3
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice, {"from": account2})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, 2, NFTPrice, {"from": account2})
    assert "This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT." in str(ex.value)

    # account can't purchase the NFT for account 2
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, 1, NFTPrice, {"from": account})
    assert "This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT." in str(ex.value)

    # Purchase the NFT for account 2 that was assigned through the whitelist spot
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, 1, NFTPrice, {"from": account2})
    assert cardinalNFT.ownerOf(1) == account2.address

    # Purchase the NFT for account 3 that was assigned through the whitelist spot
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice, {"from": account3})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, 2, NFTPrice, {"from": account3})
    assert cardinalNFT.ownerOf(2) == account3.address

    # Have account 2 list the NFT it just purchased back on the marketplace
    cardinalNFT.approve(cardinalHouseMarketplace.address, 1, {"from": account2})
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, 1, NFTPrice * 2, {"from": account2, "value": listingFee})

    # Since the whitelist spot only applies when the contract owner is selling
    # the NFT, make sure a different account can now purchase the NFT that account 2 is selling.
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice * 2, {"from": account5})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, 3, NFTPrice * 2, {"from": account5})
    assert cardinalNFT.ownerOf(1) == account5.address

    # Have account 3 list the NFT it just purchased back on the marketplace
    cardinalNFT.approve(cardinalHouseMarketplace.address, 2, {"from": account3})
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, 2, NFTPrice * 5, {"from": account3, "value": listingFee})

    # Since the whitelist spot only applies when the contract owner is selling
    # the NFT, make sure a different account can now purchase the NFT that account  3is selling.
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice * 5, {"from": account})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, 4, NFTPrice * 5, {"from": account})
    assert cardinalNFT.ownerOf(2) == account.address
    
def test_cardinal_house_marketplace():
    # First, get the accounts and deploy the smart contracts.
    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    account4 = retrieve_account(4)
    account5 = retrieve_account(5)

    cardinalToken, cardinalHousePreSale, _ = deploy_cardinal_house(account3.address, account4.address, account5.address, account5.address)
    cardinalHouseMarketplace, cardinalNFT = deploy_cardinal_house_marketplace(cardinalToken.address, cardinalHousePreSale.address)
    uniswapPair = cardinalToken.uniswapPair()
    account5CardinalBalance = cardinalToken.balanceOf(account5.address)
    cardinalToken.transfer(uniswapPair, account5CardinalBalance / 2, {"from": account5})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Owner can create an NFT
    listingFee = Web3.toWei(0.02, "ether")
    epoch_time = chain.time()
    cardinalNFT.createToken("Test Token", 1, listingFee, epoch_time, {"from": account})
    tokenId = cardinalNFT._tokenIds()
    
    tokenOwner = cardinalNFT.ownerOf(tokenId)
    assert tokenOwner == account.address
    assert cardinalNFT.tokenIdToListingFee(tokenId) == listingFee

    # User can fetch all token URIs for all NFTs someone owns
    tokenURIs = cardinalNFT.getUserTokenURIs(account.address)
    # tokenURIs = tokenURIs.return_value
    assert len(tokenURIs) == 1
    assert tokenURIs[0] == "Test Token"

    # Non-owner can't create an NFT
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.createToken("Test Token 2", 2, listingFee, epoch_time, {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Owner can set the listing fee for the marketplace
    defaultListingFee = cardinalHouseMarketplace.getDefaultListingPrice()
    assert defaultListingFee == Web3.toWei(0, "ether")
    newDefaultListingFee = Web3.toWei(0.0001, "ether")
    cardinalHouseMarketplace.setDefaultListingPrice(newDefaultListingFee, {"from": account})

    # Non-owner can't set the listing fee for the marketplace
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.setDefaultListingPrice(newDefaultListingFee, {"from": account3})
    assert "Ownable: caller is not the owner" in str(ex.value)

    # Owner can't create an NFT with an invalid NFT address
    NFTPrice = 1000000
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketItem(ZERO_ADDRESS, tokenId, NFTPrice, {"from": account})
    assert "revert: This isn't a valid Cardinal NFT contract" in str(ex.value)

    # Owner can add the NFT to the marketplace without a fee
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, NFTPrice, {"from": account})

    # Assert the NFT was added to the marketplace properly
    marketplaceNFTs = cardinalHouseMarketplace.fetchMarketItems()
    createdNFT = marketplaceNFTs[0]
    
    assert createdNFT[0] == 1
    assert createdNFT[1] == cardinalNFT.address
    assert createdNFT[2] == 1
    assert createdNFT[3] == account.address
    assert createdNFT[4] == ZERO_ADDRESS
    assert createdNFT[5] == NFTPrice
    assert createdNFT[6] == False
    assert createdNFT[7] == "Test Token"
    assert createdNFT[8] == listingFee

    # User can't purchase the NFT without sending the proper amount
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, tokenId, NFTPrice / 2, {"from": account5})
    assert "revert: Please submit the asking price in order to complete the purchase" in str(ex.value)

    # User can't purchase an NFT from an invalid NFT address
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketSale(ZERO_ADDRESS, tokenId, NFTPrice, {"from": account5})
    assert "revert: This isn't a valid Cardinal NFT contract" in str(ex.value)

    # User can't purchase an NFT without first approving the marketplace to spend their Cardinal Tokens
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, tokenId, NFTPrice, {"from": account5})
    assert "revert: ERC20: insufficient allowance" in str(ex.value)

    # User can purchase the NFT listed on the marketplace
    initialAccountBalance = cardinalToken.balanceOf(account5.address)
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice, {"from": account5})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, tokenId, NFTPrice, {"from": account5})
    assert cardinalToken.balanceOf(account5.address) == initialAccountBalance - NFTPrice

    accountNFTs = cardinalHouseMarketplace.fetchMyNFTs(account5.address)
    assert len(accountNFTs) == 1
    assert accountNFTs[0][3] == account.address
    assert accountNFTs[0][4] == account5.address

    tokenOwner = cardinalNFT.ownerOf(tokenId)
    assert tokenOwner == account5.address

    # User can't list the NFT they just purchased without paying the listing fee
    newNFTPrice = NFTPrice * 2
    cardinalNFT.approve(cardinalHouseMarketplace.address, tokenId, {"from": account5})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, newNFTPrice, {"from": account5})
    assert "revert: Not enough or too much Matic was sent to pay the NFT listing fee." in str(ex.value)

    # User can list the NFT they just purchased if they pay the listing fee
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, newNFTPrice, {"from": account5, "value": listingFee})

    # Assert the NFT was added to the marketplace properly
    marketplaceNFTs = cardinalHouseMarketplace.fetchMarketItems()
    createdNFT = marketplaceNFTs[0]
    
    assert createdNFT[0] == 2
    assert createdNFT[1] == cardinalNFT.address
    assert createdNFT[2] == 1
    assert createdNFT[3] == account5.address
    assert createdNFT[4] == ZERO_ADDRESS
    assert createdNFT[5] == newNFTPrice
    assert createdNFT[6] == False
    assert createdNFT[7] == "Test Token"
    assert createdNFT[8] == listingFee

    # User can purchase the NFT listed on the marketplace by another user (not the owner)
    initialAccount4Balance = cardinalToken.balanceOf(account4.address)
    initialAccount5Balance = cardinalToken.balanceOf(account5.address)
    marketItemId = 2
    ownerInitialBalance = account.balance()

    cardinalToken.approve(cardinalHouseMarketplace.address, newNFTPrice, {"from": account4})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, marketItemId, newNFTPrice, {"from": account4})

    accountNFTs = cardinalHouseMarketplace.fetchMyNFTs(account4.address)
    assert len(accountNFTs) == 1

    assert cardinalToken.balanceOf(account4.address) == initialAccount4Balance - newNFTPrice
    assert cardinalToken.balanceOf(account5.address) == initialAccount5Balance + newNFTPrice

    assert accountNFTs[0][3] == account5.address
    assert accountNFTs[0][4] == account4.address

    tokenOwner = cardinalNFT.ownerOf(tokenId)
    assert tokenOwner == account4.address

    assert account.balance() == ownerInitialBalance + listingFee

    accountNFTs = cardinalHouseMarketplace.fetchMyNFTs(account4.address)
    assert len(accountNFTs) == 1
    assert accountNFTs[0][0] == 2
    assert accountNFTs[0][1] == cardinalNFT.address
    assert accountNFTs[0][2] == 1
    assert accountNFTs[0][3] == account5.address
    assert accountNFTs[0][4] == account4.address
    assert accountNFTs[0][5] == newNFTPrice
    assert accountNFTs[0][6] == True
    assert accountNFTs[0][7] == "Test Token"
    assert accountNFTs[0][8] == listingFee

    # User can cancel market sale
    assert len(cardinalHouseMarketplace.fetchMarketItems()) == 0
    initialAccount4Balance = account4.balance()
    cardinalNFT.approve(cardinalHouseMarketplace.address, tokenId, {"from": account4})
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, NFTPrice, {"from": account4, "value": listingFee})
    assert account4.balance() == initialAccount4Balance - listingFee

    # Make sure someone random can't cancel the market sale
    marketItemId += 1
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.cancelMarketSale(cardinalNFT.address, marketItemId, {"from": account2})
    assert "You can only cancel your own NFT listings." in str(ex.value)

    assert len(cardinalHouseMarketplace.fetchMarketItems()) == 1
    cardinalHouseMarketplace.cancelMarketSale(cardinalNFT.address, marketItemId, {"from": account4})
    assert len(cardinalHouseMarketplace.fetchMarketItems()) == 0
    assert account4.balance() == initialAccount4Balance
    
    # Owner can cancel any NFT listing
    initialAccountBalance = account.balance()
    initialAccount4Balance = account4.balance()
    cardinalNFT.approve(cardinalHouseMarketplace.address, tokenId, {"from": account4})
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, NFTPrice, {"from": account4, "value": listingFee})

    marketItemId += 1
    cardinalHouseMarketplace.cancelMarketSale(cardinalNFT.address, marketItemId, {"from": account})
    assert cardinalNFT.ownerOf(tokenId) == account4.address
    assert account.balance() == initialAccountBalance
    assert account4.balance() == initialAccount4Balance

    # Owner can create an NFT and assign a whitelist address to it.
    # Also make sure a non-owner can't assign a whitelist spot.
    listingFee = Web3.toWei(0, "ether")
    newDefaultListingFee = Web3.toWei(0, "ether")
    cardinalHouseMarketplace.setDefaultListingPrice(newDefaultListingFee, {"from": account})
    marketItemId += 1
    epoch_time = chain.time()
    cardinalNFT.createToken("Test Token", 1, listingFee, epoch_time, {"from": account})
    tokenId = cardinalNFT._tokenIds()

    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalNFT.addWhiteListToToken(account2.address, tokenId, {"from": account5})
    assert "revert: Ownable: caller is not the owner" in str(ex.value)

    # Add the whitelist address to the NFT.
    cardinalNFT.addWhiteListToToken(account2.address, tokenId, {"from": account})
    assert cardinalNFT.tokenIdToWhitelistAddress(tokenId) == account2.address

    # Put the NFT on the marketplace.
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, NFTPrice, {"from": account})

    # Someone who isn't account2 can't purchase the NFT.
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, marketItemId, NFTPrice, {"from": account5})
    assert "revert: This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT." in str(ex.value)

    # Account2 can purchase the NFT.
    cardinalToken.transfer(account2.address, NFTPrice * 2, {"from": account5.address})
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice, {"from": account2})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, marketItemId, NFTPrice, {"from": account2})

    assert cardinalNFT.ownerOf(tokenId) == account2.address

    # Account2 can put the NFT back on the marketplace.
    account2Balance = account2.balance
    cardinalNFT.approve(cardinalHouseMarketplace.address, tokenId, {"from": account2})
    cardinalHouseMarketplace.createMarketItem(cardinalNFT.address, tokenId, NFTPrice, {"from": account2, "value": listingFee})
    marketItemId += 1

    assert account2.balance == account2Balance

    # Account5 can purchase the NFT spot now that the owner isn't the seller.
    cardinalToken.approve(cardinalHouseMarketplace.address, NFTPrice, {"from": account5})
    cardinalHouseMarketplace.createMarketSale(cardinalNFT.address, marketItemId, NFTPrice, {"from": account5})

    assert cardinalNFT.ownerOf(tokenId) == account5.address
