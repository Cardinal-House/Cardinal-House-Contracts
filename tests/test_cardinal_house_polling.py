from scripts.common_funcs import retrieve_account, waitForTransactionsToComplete, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DECIMALS
from scripts.deploy import deploy_cardinal_house
from brownie import network, accounts, exceptions
from web3 import Web3
import pytest

LIQUIDITY_SUPPLY = Web3.toWei(300000000, "ether")

def test_owner_can_make_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()

    # Act
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})

    # Assert
    assert cardinalHousePolling.votingOpen() == True
    assert cardinalHousePolling.currPollTitle() == "Test Poll"
    assert cardinalHousePolling.getNumberOfProposals() == 3
    assert cardinalHousePolling.proposals(0)[0] == "Test Option 1"
    assert cardinalHousePolling.proposals(0)[1] == 0
    assert cardinalHousePolling.proposals(1)[0] == "Test Option 2"
    assert cardinalHousePolling.proposals(1)[1] == 0
    assert cardinalHousePolling.proposals(2)[0] == "Test Option 3"
    assert cardinalHousePolling.proposals(2)[1] == 0

def test_non_owner_cant_make_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")
    
    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()

    # Act/Assert
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account2})
    assert "Ownable: caller is not the owner" in str(ex.value)

def test_users_can_vote_in_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, 50000, {"from": account})
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    cardinalHousePolling.vote(0, {"from": account})
    cardinalHousePolling.vote(1, {"from": account2})

    # Assert
    assert cardinalHousePolling.proposals(0)[1] == cardinalToken.balanceOf(account.address)
    assert cardinalHousePolling.proposals(1)[1] == cardinalToken.balanceOf(account2.address)
    assert cardinalHousePolling.winningProposalName() == "Test Option 1"

def test_users_can_vote_in_poll_2():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, accountCardinalBalance * 3 / 8, {"from": account})
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    cardinalHousePolling.vote(2, {"from": account})
    cardinalHousePolling.vote(2, {"from": account2})

    # Assert
    assert cardinalHousePolling.proposals(2)[1] == cardinalToken.balanceOf(account.address) + cardinalToken.balanceOf(account2.address)
    assert cardinalHousePolling.winningProposalName() == "Test Option 3"

def test_user_without_CRNL_cant_vote():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})

    # Assert/Act
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePolling.vote(0, {"from": account2})
    assert "You need Cardinal Tokens to be able to vote." in str(ex.value)

def test_user_cant_vote_twice():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})

    # Assert/Act
    cardinalHousePolling.vote(0, {"from": account})
    with pytest.raises(exceptions.VirtualMachineError) as ex:
        cardinalHousePolling.vote(1, {"from": account})
    assert "You have already voted in this poll." in str(ex.value)

def test_owner_can_close_poll():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, accountCardinalBalance / 5, {"from": account})
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    cardinalHousePolling.vote(2, {"from": account})
    cardinalHousePolling.vote(0, {"from": account2})

    cardinalHousePolling.closePoll({"from": account})

    # Assert
    assert cardinalHousePolling.votingOpen() == False
    assert cardinalHousePolling.winningProposalName() == "Test Option 3"
    assert cardinalHousePolling.pastPolls(0)[0] == "Test Poll" 
    assert cardinalHousePolling.pastPolls(0)[1] == "Test Option 3" 
    assert cardinalHousePolling.pastPolls(0)[2] == 3
    
    for i in range(cardinalHousePolling.pastPolls(0)[2]):
        assert cardinalHousePolling.getPastProposal(0, i)[0] == f"Test Option {i + 1}"

    assert cardinalHousePolling.getPastProposal(0, 0)[1] == cardinalToken.balanceOf(account2.address)
    assert cardinalHousePolling.getPastProposal(0, 2)[1] == cardinalToken.balanceOf(account.address)

def test_past_proposals_store_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("This test is only for local blockchains.")

    account = retrieve_account()
    account2 = retrieve_account(2)
    account3 = retrieve_account(3)
    cardinalToken, cardinalHousePreSale, cardinalHousePolling = deploy_cardinal_house()
    uniswapPair = cardinalToken.uniswapPair()
    accountCardinalBalance = cardinalToken.balanceOf(account.address)
    cardinalToken.transfer(uniswapPair, accountCardinalBalance / 2, {"from": account})
    cardinalToken.setContractTokenDivisor(1, {"from": account})

    # Act
    cardinalToken.transfer(account2.address, accountCardinalBalance / 10, {"from": account})
    cardinalToken.transfer(account3.address, accountCardinalBalance / 5, {"from": account})
    cardinalHousePolling.createNewPoll("Test Poll", ["Test Option 1", "Test Option 2", "Test Option 3"], {"from": account})
    cardinalHousePolling.vote(2, {"from": account})
    cardinalHousePolling.vote(0, {"from": account2})
    cardinalHousePolling.vote(1, {"from": account3})

    cardinalHousePolling.closePoll({"from": account})

    cardinalHousePolling.createNewPoll("Test Poll 2", ["Test Option 4", "Test Option 5", "Test Option 6", "Test Option 7", "Test Option 8"], {"from": account})
    cardinalHousePolling.vote(3, {"from": account})
    cardinalHousePolling.vote(3, {"from": account2})
    cardinalHousePolling.vote(4, {"from": account3})

    cardinalHousePolling.closePoll({"from": account})

    # Assert
    assert cardinalHousePolling.votingOpen() == False
    assert cardinalHousePolling.winningProposalName() == "Test Option 7"
    assert cardinalHousePolling.pastPolls(1)[0] == "Test Poll 2" 
    assert cardinalHousePolling.pastPolls(1)[1] == "Test Option 7" 
    assert cardinalHousePolling.pastPolls(1)[2] == 5
    assert cardinalHousePolling.numPastPolls() == 2

    for i in range(cardinalHousePolling.numPastPolls()):
        for j in range(cardinalHousePolling.pastPolls(i)[2]):
            assert cardinalHousePolling.getPastProposal(i, j)[0] == f"Test Option {3*i + j + 1}"

    assert cardinalHousePolling.getPastProposal(0, 0)[1] == cardinalToken.balanceOf(account2.address)
    assert cardinalHousePolling.getPastProposal(0, 1)[1] == cardinalToken.balanceOf(account3.address)
    assert cardinalHousePolling.getPastProposal(0, 2)[1] == cardinalToken.balanceOf(account.address)

    assert cardinalHousePolling.getPastProposal(1, 3)[1] == cardinalToken.balanceOf(account.address) + cardinalToken.balanceOf(account2.address)
    assert cardinalHousePolling.getPastProposal(1, 4)[1] == cardinalToken.balanceOf(account3.address)