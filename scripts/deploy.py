from brownie import network, config, CardinalToken, CardinalHousePreSale, CardinalHousePolling, MockWETH, PancakeRouter, PancakeFactory
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from web3 import Web3

INITIAL_SUPPLY = Web3.toWei(10000000, "ether")

PROD_MEMBER_GIVEAWAY_ADDRESS = "0x0cd73249a242eD5D7492882DB17B1295B47C0De4"
PROD_MARKETING_ADDRESS = "0xA5597787BE507719b83c6Aa2d1367517929e5CDD"
PROD_DEVELOPER_ADDRESS = "0x8Ac220AdC2952B93a180F364D62A6061fC54d6AC"
PROD_LIQUIDITY_ADDRESS = "0x5Dc0Dea428D20a5e21FC9AfcdF131A26f3C905D8"
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"

PROD = True

def deploy_cardinal_house(memberGiveawayWalletAddress=None, marketingWalletAddress=None, developerWalletAddress=None, liquidityWalletAddress=None, burnWalletAddress=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    print(currNetwork)
    if PROD and currNetwork in config["networks"] and "dex_router" in config["networks"][currNetwork]:
        print("Setting production addresses...")
        memberGiveawayWalletAddress = PROD_MEMBER_GIVEAWAY_ADDRESS
        marketingWalletAddress = PROD_MARKETING_ADDRESS
        developerWalletAddress = PROD_DEVELOPER_ADDRESS
        liquidityWalletAddress = PROD_LIQUIDITY_ADDRESS
        burnWalletAddress = BURN_ADDRESS
    else:
        if not memberGiveawayWalletAddress:
            memberGiveawayWalletAddress = account.address
        if not marketingWalletAddress:
            marketingWalletAddress = account.address
        if not developerWalletAddress:
            developerWalletAddress = account.address
        if not liquidityWalletAddress:
            liquidityWalletAddress = account.address
        if not burnWalletAddress:
            # 0x000000000000000000000000000000000000dEaD is a standard burn wallet address.
            burnWalletAddress = BURN_ADDRESS

    if currNetwork in config["networks"] and "dex_router" in config["networks"][currNetwork]:
        dexRouterAddress = config["networks"][currNetwork]["dex_router"]
    else:
        # Deploy mocked dex router and factory.
        WETHAddress = MockWETH.deploy({"from": account})
        dexFactoryAddress = PancakeFactory.deploy(account.address, {"from": account})
        dexRouterAddress = PancakeRouter.deploy(dexFactoryAddress, WETHAddress, {"from": account})


    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    cardinalHousePreSale = CardinalHousePreSale.deploy({"from": account}, publish_source=publishSource)
    if str(type(cardinalHousePreSale)) == 'TransactionReceipt':
        cardinalHousePreSale.wait(1)
        cardinalHousePreSale = cardinalHousePreSale.return_value
    
    print(f"Cardinal House Pre-Sale deployed to {cardinalHousePreSale.address}")
    cardinalToken = CardinalToken.deploy(
        INITIAL_SUPPLY,
        cardinalHousePreSale.address,
        burnWalletAddress,
        liquidityWalletAddress,
        memberGiveawayWalletAddress,
        marketingWalletAddress,
        developerWalletAddress,
        dexRouterAddress,
        {"from": account},
        publish_source=publishSource
    )

    if str(type(cardinalToken)) == 'TransactionReceipt':
        cardinalToken.wait(1)
        cardinalToken = cardinalToken.return_value

    print(f"Cardinal Token deployed to {cardinalToken.address}")

    cardinalHousePolling = CardinalHousePolling.deploy(cardinalToken.address, {"from": account}, publish_source=publishSource)

    transaction = cardinalHousePreSale.setToken(cardinalToken.address, {"from": account})
    transaction.wait(1)
    print("Successfully set the Cardinal Token for the presale.")

    return cardinalToken, cardinalHousePreSale, cardinalHousePolling

def main():
    deploy_cardinal_house()