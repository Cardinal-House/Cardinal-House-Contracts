from brownie import network, config, NodeRunner, CardinalHouseMarketplace
from brownie.network.contract import Contract
from scripts.common_funcs import retrieve_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS, DONT_PUBLISH_SOURCE_ENVIRONMENTS
from pinatapy import PinataPy
from web3 import Web3
import os

CARDINAL_MARKETPLACE_ADDRESS_TEST = "0xe8d93aB8ABC90495FDd5Bd797D8C8b2EBc63b43D"
CARDINAL_MARKETPLACE_ADDRESS = "0x16fA58F4CcDDcdD0a72fb71EAeDe896c2C4E77B0"
CARDINAL_NFT_ADDRESS_TEST = "0xEBadD172563627De64f995380820600335027933"
CARDINAL_NFT_ADDRESS = "0x94E2c821Fe8c7953595544e3DA4500cCC157FCa4"
USDC_ADDRESS_TEST_REAL = "0xe6b8a5CF854791412c1f6EFC7CAf629f5Df1c747"
USDC_ADDRESS_TEST = "0x03c83C3Ff23eCE0b81bF8DD64A403F7230522874"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

MAX_NFTS = "194"
NODE_RUNNER_NFT_IMAGE_PATH = "NodeRunnerNFT.png"
NODE_RUNNER_NFT_NAME = "Genesis DAG Node"
NODE_RUNNER_NFT_DESCRIPTION = "Phase One Genesis DAG Node NFT - This NFT represents a portion of a DAG node and also guarantees a whitelist spot for all future Node Runner nodes."
DEFAULT_LISTING_FEE = Web3.toWei(5, "ether")
NFT_PRICE_IN_USDC = 100 * pow(10, 6)

PROD = True

pinata = PinataPy(os.environ["PinataApiKey"], os.environ["PinataSecretApiKey"])

def deploy_node_runner(cardinalMarketplaceAddress=None, cardinalNFTAddress=None, USDCAddress=None, defaultListingFee=None, maxNFTs=None, NFTPriceInUSDC=None, NodeRunnerNFTImagePath=None, NodeRunnerNFTName=None, NodeRunnerNFTDescription=None):
    account = retrieve_account()

    currNetwork = network.show_active()
    if PROD:
        cardinalMarketplaceAddress = CARDINAL_MARKETPLACE_ADDRESS
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS
        USDCAddress = USDC_ADDRESS
    elif not cardinalMarketplaceAddress:
        cardinalMarketplaceAddress = CARDINAL_MARKETPLACE_ADDRESS_TEST
        cardinalNFTAddress = CARDINAL_NFT_ADDRESS_TEST
        USDCAddress = USDC_ADDRESS_TEST

    if not defaultListingFee:
        defaultListingFee = DEFAULT_LISTING_FEE

    if not maxNFTs:
        maxNFTs = MAX_NFTS

    if not NFTPriceInUSDC:
        NFTPriceInUSDC = NFT_PRICE_IN_USDC

    if not NodeRunnerNFTImagePath:
        NodeRunnerNFTImagePath = NODE_RUNNER_NFT_IMAGE_PATH

    if not NodeRunnerNFTName:
        NodeRunnerNFTName = NODE_RUNNER_NFT_NAME

    if not NodeRunnerNFTDescription:
        NodeRunnerNFTDescription = NODE_RUNNER_NFT_DESCRIPTION

    publishSource = currNetwork not in DONT_PUBLISH_SOURCE_ENVIRONMENTS

    if PROD:
        response = pinata.pin_file_to_ipfs(NodeRunnerNFTImagePath)

        currImageURL = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"

        currTokenURI = {
            "NFTName": NodeRunnerNFTName,
            "NFTDescription": NodeRunnerNFTDescription,
            "image": currImageURL
        }

        response = pinata.pin_json_to_ipfs(currTokenURI)
        NodeRunnerTokenURI = f"https://gateway.pinata.cloud/ipfs/{response['IpfsHash']}"
        print(NodeRunnerTokenURI)

    nodeRunner = NodeRunner.deploy(
        cardinalMarketplaceAddress,
        cardinalNFTAddress,
        USDCAddress,
        defaultListingFee,
        maxNFTs,
        NFTPriceInUSDC,
        {"from": account}, publish_source=publishSource
    )
    print(f"Node Runner deployed to {nodeRunner.address}")

    cardinalMarketplaceABI = CardinalHouseMarketplace.abi
    cardinalMarketplace = Contract.from_abi("CardinalHouseMarketplace", cardinalMarketplaceAddress, cardinalMarketplaceABI)

    transaction = cardinalMarketplace.whiteListNFTContract(nodeRunner.address, USDCAddress, True, {"from": account})
    transaction.wait(1)

    print("Successfully whitelisted the Node Runner NFT contract on the Cardinal House Marketplace!")

    if PROD:
        nodeRunner.updateNodeRunnerTokenURI(NodeRunnerTokenURI, {"from": account})
        print("Successfully set the token URI for the Node Runner contract!")

    return nodeRunner

def main():
    deploy_node_runner()