// SPDX-License-Identifier: MIT
pragma solidity 0.8.8;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import './CardinalNFT.sol';

/**
 * @title Node Runner Contract
 * @dev NFT contract that will be used with the marketplace contract
 */
contract NodeRunner is ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;

    // Counter to give each NFT a unique ID.
    Counters.Counter public _tokenIds;

    // Address of the Cardinal House marketplace.
    address public marketplaceAddress;

    // References the deployed Cardinal NFT contract.
    CardinalNFT public cardinalNFT;

    // Contract for USDC - for NFT payments
    IERC20 public USDC;

    // Default listing fee for NFTs
    uint256 public defaultListingFee;

    // Number of NFTs that can be minted for this node.
    uint256 public maxNFTs;

    // NFT price in USDC
    uint256 public NFTPriceInUSDC;

    // The token URI for all of the NFTs in this contract
    string public nodeRunnerTokenURI;

    // Each NFT will have a unique listing fee that is kept track of in this mapping.
    mapping(uint256 => uint256) public tokenIdToListingFee;
    
    // Mapping of token ID to address for whitelist spots.
    mapping(uint256 => address) public tokenIdToWhitelistAddress;

    // Mapping to determine how much Matic each address can withdraw from node rewards.
    mapping(address => uint256) public addressToMaticCanClaim;

    // Mapping to determine how much Matic each address has claimed.
    mapping(address => uint256) public addressToMaticClaimed;

    event nodeRunnerNFTMinted(address indexed owner, uint256 indexed tokenId);
    event nodeRewardsDeposited(uint256 indexed amount);
    event nodeRewardsClaimed(address indexed claimer, uint256 amount);
    event tokenURIUpdated(uint256 indexed tokenId, string newTokenURI);

    constructor(address _marketplaceAddress, address payable CardinalNFTAddress, address _USDC, uint256 _defaultListingFee, uint256 _maxNFTs, uint256 _NFTPriceInUSDC) ERC721("NodeRunnerNFT", "NRNFT") {
        marketplaceAddress = _marketplaceAddress;
        cardinalNFT = CardinalNFT(CardinalNFTAddress);
        USDC = IERC20(_USDC);
        defaultListingFee = _defaultListingFee;
        maxNFTs = _maxNFTs;
        NFTPriceInUSDC = _NFTPriceInUSDC;
    }

    /**
    * @dev Allows someone to mint a Node Runner NFT by paying USDC
    * @return newItemId the ID of the newly minted Node Runner NFT
     */
    function mintNodeRunnerNFT() external returns (uint) {
        require(cardinalNFT.addressIsMember(msg.sender), "Only Cardinal Crew Members can participate in Node Runner.");
        require(_tokenIds.current() < maxNFTs, "The maximum number of Node Runner NFTs for this node have already been minted! Another node will be available soon!");
        require(USDC.balanceOf(msg.sender) >= NFTPriceInUSDC, "You don't have enough USDC to pay for the Node Runner NFT.");
        require(USDC.allowance(msg.sender, address(this)) >= NFTPriceInUSDC, "You haven't approved this contract to spend enough of your USDC to pay for the Node Runner NFT.");
        
        USDC.transferFrom(msg.sender, address(this), NFTPriceInUSDC);

        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenIdToListingFee[newItemId] = defaultListingFee;
        _mint(msg.sender, newItemId);
        _setTokenURI(newItemId, nodeRunnerTokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        emit nodeRunnerNFTMinted(msg.sender, newItemId);

        return newItemId;
    }

    /**
    * @dev Only owner function to mint a new NFT.
    * @param newTokenURI the token URI on IPFS for the NFT metadata
    * @return newItemId the ID of the newly minted NFT
     */
    function createToken(string memory newTokenURI) external onlyOwner returns (uint) {
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenIdToListingFee[newItemId] = defaultListingFee;
        _mint(msg.sender, newItemId);
        _setTokenURI(newItemId, nodeRunnerTokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        emit nodeRunnerNFTMinted(msg.sender, newItemId);

        return newItemId;
    }

    /**
    * @dev Function to deposit rewards in Matic from the node into the contract for NFT holders to claim.
    */
    function depositNodeRewards() external payable {
        require(msg.value >= maxNFTs, "You must deposit enough Matic so it can be divided by the maximum number of NFT holders for the node.");
        require(_tokenIds.current() > 0, "No NFTs have been minted for this node yet.");

        for (uint i = 1; i <= _tokenIds.current(); i++) {
            address NFTOwner = ownerOf(i);
            addressToMaticCanClaim[NFTOwner] = addressToMaticCanClaim[NFTOwner] + (msg.value / maxNFTs);
        }

        emit nodeRewardsDeposited(msg.value);
    }

    /**
    @dev Function for NFT holders to claim their node rewards.
    */
    function claimNodeRewards() external {
        require(addressToMaticCanClaim[msg.sender] > 0, "You don't have any node rewards to claim! If you have an NFT for this node, please wait until the next reward deposit.");
        
        uint256 claimAmount = addressToMaticCanClaim[msg.sender];
        addressToMaticCanClaim[msg.sender] = 0;
        (bool success, ) = msg.sender.call{value: claimAmount}("");
        require(success, "Failed to send Matic");

        emit nodeRewardsClaimed(msg.sender, claimAmount);

        addressToMaticClaimed[msg.sender] = addressToMaticClaimed[msg.sender] + claimAmount;
    }

    /**
    * @dev Only owner function to withdraw the USDC that is paid to this contract for the Node Runner NFTs.
     */
    function withdrawNodeFunds() external onlyOwner {
        USDC.transfer(owner(), USDC.balanceOf(address(this)));
    }

    /**
    * @dev Setter function for the token URI of an NFT.
    * @param tokenId the ID of the NFT to update the token URI of
    * @param newTokenURI the token URI to update the NFT with
     */
    function setTokenURI(uint256 tokenId, string memory newTokenURI) external onlyOwner {
        _setTokenURI(tokenId, newTokenURI);
        emit tokenURIUpdated(tokenId, newTokenURI);
    }

    /**
    * @dev Function to get all token URIs for tokens that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's NFTs
     */
    function getUserTokenURIs(address userAddress) external view returns (string[] memory) {
        uint NFTCount = _tokenIds.current();
        uint userNFTCount = 0;
        uint currentIndex = 0;

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress) {
                userNFTCount += 1;
            }
        }

        string[] memory userNFTTokenURIs = new string[](userNFTCount);

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress) {
                string memory currentNFT = tokenURI(id);
                userNFTTokenURIs[currentIndex] = currentNFT;
                currentIndex += 1;
            }
        }
        
        return userNFTTokenURIs;
    }

    /**
    * @dev updates the Node Runner NFT token URI
    * @param newNodeRunnerTokenURI the new type ID of the Node Runner NFTs
     */
    function updateNodeRunnerTokenURI(string memory newNodeRunnerTokenURI) external onlyOwner {
        nodeRunnerTokenURI = newNodeRunnerTokenURI;
    }

    /**
    * @dev Function to assign an NFT to a whitelist spot so only one address can purchase the NFT.
    * @param whiteListAddress the address of the user who will be able to purchase the NFT
    * @param tokenId the ID of the NFT that the whitelist spot is for
     */
    function addWhiteListToToken(address whiteListAddress, uint256 tokenId) external onlyOwner {
        tokenIdToWhitelistAddress[tokenId] = whiteListAddress;
    }

    /**
    * @dev updates the listing fee of an NFT.
    * @param tokenId the ID of the NFT to update the listing fee of
    * @param newListingFee the listing fee value for the NFT
     */
    function updateTokenListingFee(uint256 tokenId, uint256 newListingFee) external onlyOwner {
        tokenIdToListingFee[tokenId] = newListingFee;
    }

    /**
    * @dev updates the marketplace address.
    * @param newMarketplaceAddress the new marketplace address
     */
    function updateMarketplaceAddress(address newMarketplaceAddress) external onlyOwner {
        marketplaceAddress = newMarketplaceAddress;
    }

    /**
    * @dev updates the USDC contract.
    * @param newUSDCAddress the new USDC address
     */
    function updateUSDCAddress(address newUSDCAddress) external onlyOwner {
        USDC = IERC20(newUSDCAddress);
    }

    /**
    * @dev updates the default listing fee for the NFTs.
    * @param newDefaultListingFee the new default listing fee
     */
    function updateDefaultListingFee(uint256 newDefaultListingFee) external onlyOwner {
        defaultListingFee = newDefaultListingFee;
    }

    /**
    * @dev updates the maximum number of NFTs that can be minted for the node this contract represents.
    * @param newMaxNFTs the new maximum number of NFTs that can be minted in this contract
     */
    function updateMaxNFTs(uint256 newMaxNFTs) external onlyOwner {
        maxNFTs = newMaxNFTs;
    }

    /**
    * @dev updates the price of each NFT.
    * @param newNFTPriceInUSDC the price of each NFT in USDC
     */
    function updateNFTPriceInUSDC(uint256 newNFTPriceInUSDC) external onlyOwner {
        NFTPriceInUSDC = newNFTPriceInUSDC;
    }
}