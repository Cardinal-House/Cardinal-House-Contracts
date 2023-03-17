// SPDX-License-Identifier: MIT
pragma solidity 0.8.8;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import './CardinalNFT.sol';

/**
 * @title Node Runner Contract
 * @dev NFT contract that will be used with the marketplace contract
 */
contract NodeRunner is ERC721URIStorage, ERC721Enumerable, Pausable, Ownable {
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
    event nodeRewardsDepositedChunk(uint256 indexed amount, uint256 startIndex, uint256 endIndex);
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
    @dev Only owner function to pause the Node Runner minting.
    */
    function pauseMinting() external onlyOwner {
        _pause();
    }

    /**
    @dev Only owner function to unpause the Node Runner minting.
    */
    function unpauseMinting() external onlyOwner {
        _unpause();
    }    

    /**
    * @dev Private helper function to perform the minting of Node Runner NFTs.
    * @param nftCount the number of NFTs to mint
    * @param receiver the receiver of the NFTs upon minting
    * @return newItemIds the ID(s) of the newly minted Node Runner NFT(s)
    */
    function _mintNodeRunnerNFT(uint256 nftCount, address receiver) private returns (uint[] memory) {
        uint256[] memory mintedNFTIds = new uint256[](nftCount);
        uint256 i = 0;

        for (i = 0; i < nftCount; i += 1) {
            _tokenIds.increment();
            uint256 newItemId = _tokenIds.current();

            tokenIdToListingFee[newItemId] = defaultListingFee;
            _mint(receiver, newItemId);
            _setTokenURI(newItemId, nodeRunnerTokenURI);
            _approve(address(this), newItemId);
            _setApprovalForAll(receiver, marketplaceAddress, true);

            mintedNFTIds[i] = newItemId;

            emit nodeRunnerNFTMinted(receiver, newItemId);
        }

        return mintedNFTIds;
    }

    /**
    * @dev Allows someone to mint a Node Runner NFT by paying USDC
    * @param nftCount the number of NFTs to mint
    * @return newItemIds the ID(s) of the newly minted Node Runner NFT(s)
     */
    function mintNodeRunnerNFT(uint256 nftCount) external whenNotPaused returns (uint[] memory) {
        require(nftCount > 0, "You have to mint at least one Node Runner NFT.");
        require(nftCount + _tokenIds.current() <= maxNFTs, "There aren't enough Node Runner NFTs for this node for you to mint you amount you chose. Another node will be available soon!");
        require(cardinalNFT.addressIsMember(msg.sender), "Only Cardinal Crew Members can participate in Node Runner.");
        require(USDC.balanceOf(msg.sender) >= NFTPriceInUSDC * nftCount, "You don't have enough USDC to pay for the Node Runner NFT(s).");
        require(USDC.allowance(msg.sender, address(this)) >= NFTPriceInUSDC * nftCount, "You haven't approved this contract to spend enough of your USDC to pay for the Node Runner NFT(s).");

        USDC.transferFrom(msg.sender, address(this), NFTPriceInUSDC * nftCount);
        
        return _mintNodeRunnerNFT(nftCount, msg.sender);
    }

    /**
    * @dev Only owner function to mint NFTs to users for price balancing.
    * @param nftCount number of NFTs to mint
    * @param receiver the receiver of the NFTs upon minting
    * @return newItemIds the ID(s) of the newly minted Node Runner NFT(s)
    */
    function ownerMintNodeRunnerNFT(uint256 nftCount, address receiver) external onlyOwner returns (uint[] memory) {
        require(nftCount > 0, "You have to mint at least one Node Runner NFT.");
        require(cardinalNFT.addressIsMember(receiver), "Receiving user is not a Cardinal Crew Member.");
        return _mintNodeRunnerNFT(nftCount, receiver);
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
        require(msg.value >= _tokenIds.current(), "You must deposit enough Matic so it can be divided by the number of NFT holders for the node.");
        require(_tokenIds.current() > 0, "No NFTs have been minted for this node yet.");

        for (uint i = 1; i <= _tokenIds.current(); i++) {
            address NFTOwner = ownerOf(i);
            addressToMaticCanClaim[NFTOwner] = addressToMaticCanClaim[NFTOwner] + (msg.value / _tokenIds.current());
        }

        emit nodeRewardsDeposited(msg.value);
    }

    /**
    * @dev Function to deposit rewards in Matic in chunks from the node into the contract for NFT holders to claim.
    * @param startIndex the first index to deposit rewards for with this chunk.
    * @param endIndex the last index to deposit rewards for with this chunk.
    */
    function depositNodeRewardsInChunks(uint256 startIndex, uint256 endIndex) external payable {
        if (endIndex > _tokenIds.current()) {
            endIndex = _tokenIds.current();
        }
        require(endIndex > startIndex, "endIndex must be greater than startIndex");
        require(startIndex > 0, "startIndex must be greater than 0.");
        uint256 numNFTs = endIndex - startIndex + 1;

        require(msg.value >= numNFTs, "You must deposit enough Matic so it can be divided by the number of NFT holders based on the current chunk size.");
        require(_tokenIds.current() > 0, "No NFTs have been minted for this node yet.");

        for (uint i = startIndex; i <= endIndex; i++) {
            address NFTOwner = ownerOf(i);
            addressToMaticCanClaim[NFTOwner] = addressToMaticCanClaim[NFTOwner] + (msg.value / numNFTs);
        }

        emit nodeRewardsDepositedChunk(msg.value, startIndex, endIndex);
    }

    /**
    @dev Function for NFT holders to claim their node rewards.
    */
    function claimNodeRewards() external {
        require(cardinalNFT.addressIsMember(msg.sender), "Only Cardinal Crew Members can participate in Node Runner.");
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
        uint256 userTokenCount = balanceOf(userAddress);
        uint256 currTokenId = 0;
        string[] memory userNFTTokenURIs = new string[](userTokenCount);

        for (uint256 i; i < userTokenCount; i++) {
            currTokenId = tokenOfOwnerByIndex(userAddress, i);
            userNFTTokenURIs[i] = tokenURI(currTokenId);
        }

        return userNFTTokenURIs;
    }

    /**
    * @dev Function to get all token IDs for tokens that a given user owns.
    * @param userAddress the user's address to get token IDs of
    * @return list of token IDs for a user's NFTs
     */
    function getUserTokenIDs(address userAddress) external view returns (uint256[] memory) {
        uint256 userTokenCount = balanceOf(userAddress);
        uint256[] memory userNFTTokenIDs = new uint256[](userTokenCount);

        for (uint256 i; i < userTokenCount; i++) {
            userNFTTokenIDs[i] = tokenOfOwnerByIndex(userAddress, i);
        }

        return userNFTTokenIDs;
    }

    /**
    * @dev updates the Node Runner NFT token URI
    * @param newNodeRunnerTokenURI the new token URI for the Node Runner NFTs
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

    /**
    * @dev function for the marketplace to determine if an address is a Cardinal Crew member.
    * @param user the address to check the Cardinal Crew membership of
    */
    function addressIsMember(address user) external view returns (bool) {
        return cardinalNFT.addressIsMember(user);
    }

    // Override function since both ERC721URIStorage and ERC721Enumerable inherit from ERC721 and so both have a definition for _burn.
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    // Override function since both ERC721URIStorage and ERC721Enumerable inherit from ERC721 and so both have a definition for _beforeTokenTransfer.
    function _beforeTokenTransfer(address from, address to, uint256 tokenId) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    // Override function since both ERC721URIStorage and ERC721Enumerable inherit from ERC721 and so both have a definition for supportsInterface.
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    // Override function since both ERC721URIStorage and ERC721Enumerable inherit from ERC721 and so both have a definition for tokenURI.
    function tokenURI(uint256 tokenId) public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }
}