// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./CardinalToken.sol";

/**
 * @title Cardinal House NFT Contract
 * @dev NFT contract that will be used with the marketplace contract
 */
contract CardinalNFT is ERC721URIStorage, Ownable {
    using Counters for Counters.Counter;

    // Counter to give each NFT a unique ID.
    Counters.Counter public _tokenIds;

    // Address of the Cardinal NFT marketplace.
    address public marketplaceAddress;

    // Contract for the Cardinal Token (CRNL).
    CardinalToken public cardinalToken;

    // Each NFT will be associated with an ID that determines the type of NFT it is
    // This makes it easy to identify sets of NFTs like Original Cardinal NFTs, membership NFTs, and service NFTs
    mapping(uint256 => uint256) public tokenIdToTypeId;

    // Each NFT will have a unique listing fee that is kept track of in this mapping.
    mapping(uint256 => uint256) public tokenIdToListingFee;
    
    // Mapping of token ID to address for whitelist spots.
    mapping(uint256 => address) public tokenIdToWhitelistAddress;

    // Mapping to determine if an address has a membership (either Original Cardinal NFT or membership NFT)
    mapping(address => bool) public addressIsMember;

    // Mapping to determine the number of membership NFTs an address has (especially if they have Original Cardinal NFT and membership NFT)
    mapping(address => uint256) public addressToMemberNFTCount;

    // Maps each membership NFT ID to the last block timestamp that the membership was paid for.
    mapping(uint256 => uint256) public membershipNFTToLastPaid;

    // The type ID for the Original Cardinal NFTs.
    uint256 public originalCardinalTypeId = 1;

    // The type ID for the membership NFTs.
    uint256 public membershipTypeId = 2;

    // The type ID for the service NFTs.
    uint256 public serviceTypeId = 3;

    // Array of the Original Cardinal token IDs.
    uint256[] public originalCardinalTokenIds;

    // Array of the membership token IDs.
    uint256[] public membershipTokenIds;

    // The token URI for all membership NFTs
    string public membershipTokenURI;

    // The current price of the membership NFT in Cardinal Tokens
    uint256 public membershipPriceInCardinalTokens;

    constructor(address _marketplaceAddress, address payable _cardinalTokenAddress) ERC721("CardinalHouseNFT", "CRNLNFT") {
        marketplaceAddress = _marketplaceAddress;
        cardinalToken = CardinalToken(_cardinalTokenAddress);
    }

    /**
    * @dev Only owner function to burn a membership NFT
    * @param tokenId the tokenId of the membership NFT to burn
     */
    function burnMembershipNFT(uint256 tokenId) private {
        for (uint i = 0; i < membershipTokenIds.length; i++) {
            if (membershipTokenIds[i] == tokenId) {
                address NFTOwner = ownerOf(membershipTokenIds[i]);
                _transfer(NFTOwner, address(this), membershipTokenIds[i]);

                membershipTokenIds[i] = membershipTokenIds[membershipTokenIds.length-1];
                membershipTokenIds.pop();
            }
        }
    }

    /**
    * @dev Only owner function to burn a membership NFT
    * @param tokenId the tokenId of the membership NFT to burn
     */
    function burnMembershiptNFTManually(uint256 tokenId) public onlyOwner {
        burnMembershipNFT(tokenId);
    }

    /**
     * @dev After a token transfer, update the addressToMember mapping if the NFT is an Original Cardinal or membership NFT
     * @param from the sender's address
     * @param to the recipient's address
     * @param tokenId the tokenId that was transferred
     */
    function _afterTokenTransfer(address from, address to, uint256 tokenId) internal virtual override {
        if (tokenIdToTypeId[tokenId] == membershipTypeId || tokenIdToTypeId[tokenId] == originalCardinalTypeId) {
            if (from != owner() && from != marketplaceAddress && from != address(0)) {
                if (addressToMemberNFTCount[from] > 0) {
                    addressToMemberNFTCount[from] = addressToMemberNFTCount[from] - 1;
                    if (addressToMemberNFTCount[from] == 0) {
                        addressIsMember[from] = false;
                    }
                }
                else {
                    addressIsMember[from] = false;
                }
            }
            addressIsMember[to] = true;
            addressToMemberNFTCount[to] = addressToMemberNFTCount[to] + 1;
        }

        super._afterTokenTransfer(from, to, tokenId);
    }

    /**
    * @dev Allows someone to mint a membership NFT by paying Cardinal Tokens
    * @return the ID of the newly minted membership NFT
     */
    function mintMembershipNFT() public returns (uint) {
        require(cardinalToken.balanceOf(msg.sender) >= membershipPriceInCardinalTokens, "You don't have enough Cardinal Tokens to pay for the membership NFT.");
        require(cardinalToken.allowance(msg.sender, address(this)) >= membershipPriceInCardinalTokens, "You haven't approved this contract to spend enough of your Cardinal Tokens to pay for the membership NFT.");
        
        cardinalToken.transferFrom(msg.sender, address(this), membershipPriceInCardinalTokens);

        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenIdToTypeId[newItemId] = membershipTypeId;
        tokenIdToListingFee[newItemId] = 0;
        _mint(msg.sender, newItemId);
        membershipNFTToLastPaid[newItemId] = block.timestamp;
        _setTokenURI(newItemId, membershipTokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        membershipTokenIds.push(newItemId);

        return newItemId;
    }

    /**
    * @dev Only owner function to update the timestamp for a membership NFT after it has been paid for for a month.
    * @param tokenId the ID of the membership NFT to have the timestamp updated for
    * @param lastPaidTimestamp the timestamp to update the membership NFT to for when it was last paid for
     */
    function updateMembershipNFTLastPaid(uint256 tokenId, uint256 lastPaidTimestamp) public onlyOwner {
        membershipNFTToLastPaid[tokenId] = lastPaidTimestamp;
    }

    /**
    * @dev Only owner function to take funds from an address to pay for the next month of a membership
    * @param member the address of the member that is being charged for the next month of a membership
    * @param tokenId the token ID that the member is being charged 
    * @return 0 for success, 1 for failure and NFT burn
     */
    function chargeMemberForMembership(address member, uint256 tokenId) public onlyOwner returns (uint) {
        require(ownerOf(tokenId) == member, "This address doesn't own the NFT specified.");
        require(ownerOf(tokenId) != owner() && ownerOf(tokenId) != marketplaceAddress, "Can't charge the owner or marketplace for the membership.");

        if (cardinalToken.balanceOf(member) < membershipPriceInCardinalTokens || cardinalToken.allowance(member, address(this)) < membershipPriceInCardinalTokens) {
            burnMembershipNFT(tokenId);
            return 1;
        }
        cardinalToken.transferFrom(member, address(this), membershipPriceInCardinalTokens);
        membershipNFTToLastPaid[tokenId] = block.timestamp;
        return 0;
    }

    /**
    * @dev Only owner function to withdraw the Cardinal Tokens that are paid to this contract for the Membership NFTs.
     */
    function withdrawMembershipNFTFunds() public onlyOwner {
        cardinalToken.transfer(owner(), cardinalToken.balanceOf(address(this)));
    }

    /**
    * @dev Only owner function to mint a new NFT.
    * @param tokenURI the token URI on IPFS for the NFT metadata
    * @param typeId the type ID of the NFT to distinguish what type of NFT it is (Original Cardinal, membership, service)
    * @param listingFee the fee the user pays when putting the NFT for sale on the marketplace
    * @return the ID of the newly minted NFT
     */
    function createToken(string memory tokenURI, uint256 typeId, uint256 listingFee) public onlyOwner returns (uint) {
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenIdToTypeId[newItemId] = typeId;
        tokenIdToListingFee[newItemId] = listingFee;
        _mint(msg.sender, newItemId);
        _setTokenURI(newItemId, tokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        if (typeId == originalCardinalTypeId) {
            originalCardinalTokenIds.push(newItemId);
        }
        else if (typeId == membershipTypeId) {
            membershipTokenIds.push(newItemId);
            membershipNFTToLastPaid[newItemId] = block.timestamp;
        }

        return newItemId;
    }

    /**
    * @dev Setter function for the token URI of an NFT.
    * @param tokenId the ID of the NFT to update the token URI of
    * @param newTokenURI the token URI to update the NFT with
     */
    function setTokenURI(uint256 tokenId, string memory newTokenURI) public onlyOwner {
        _setTokenURI(tokenId, newTokenURI);
    }

    /**
    * @dev Function to get all token URIs for tokens that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's NFTs
     */
    function getUserTokenURIs(address userAddress) public view returns (string[] memory) {
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
    * @dev Function to get all token URIs for Original Cardinal NFTs that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's Original Cardinal NFTs
     */
    function getUserOriginalCardinalTokenURIs(address userAddress) public view returns (string[] memory) {
        uint NFTCount = _tokenIds.current();
        uint userNFTCount = 0;
        uint currentIndex = 0;

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress && tokenIdToTypeId[id] == originalCardinalTypeId) {
                userNFTCount += 1;
            }
        }

        string[] memory userNFTTokenURIs = new string[](userNFTCount);

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress && tokenIdToTypeId[id] == originalCardinalTypeId) {
                string memory currentNFT = tokenURI(id);
                userNFTTokenURIs[currentIndex] = currentNFT;
                currentIndex += 1;
            }
        }
        
        return userNFTTokenURIs;
    }

    /**
    * @dev Function to get all token URIs for membership NFTs that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's membership NFTs
     */
    function getUserMembershipTokenURIs(address userAddress) public view returns (string[] memory) {
        uint NFTCount = _tokenIds.current();
        uint userNFTCount = 0;
        uint currentIndex = 0;

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress && (tokenIdToTypeId[id] == originalCardinalTypeId || tokenIdToTypeId[id] == membershipTypeId)) {
                userNFTCount += 1;
            }
        }

        string[] memory userNFTTokenURIs = new string[](userNFTCount);

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress && (tokenIdToTypeId[id] == originalCardinalTypeId || tokenIdToTypeId[id] == membershipTypeId)) {
                string memory currentNFT = tokenURI(id);
                userNFTTokenURIs[currentIndex] = currentNFT;
                currentIndex += 1;
            }
        }
        
        return userNFTTokenURIs;
    }

    /**
    * @dev Function to get all token URIs for service NFTs that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's service NFTs
     */
    function getUserServiceTokenURIs(address userAddress) public view returns (string[] memory) {
        uint NFTCount = _tokenIds.current();
        uint userNFTCount = 0;
        uint currentIndex = 0;

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress && tokenIdToTypeId[id] == serviceTypeId) {
                userNFTCount += 1;
            }
        }

        string[] memory userNFTTokenURIs = new string[](userNFTCount);

        for (uint id = 1; id <= NFTCount; id++) {
            if (ownerOf(id) == userAddress && tokenIdToTypeId[id] == serviceTypeId) {
                string memory currentNFT = tokenURI(id);
                userNFTTokenURIs[currentIndex] = currentNFT;
                currentIndex += 1;
            }
        }
        
        return userNFTTokenURIs;
    }

    /**
    * @dev Function to get a list of all the Original Cardinal NFT IDs.
    * @return list of the Original Cardinal NFT IDs
     */
    function getOriginalCardinalTokenIds() public view returns (uint256[] memory) {
        return originalCardinalTokenIds;
    }

    /**
    * @dev Function to get a list of all the membership NFT IDs.
    * @return list of the membership NFT IDs
     */
    function getMembershipTokenIds() public view returns (uint256[] memory) {
        return membershipTokenIds;
    }

    /**
    * @dev Function to assign an NFT to a whitelist spot so only one address can purchase the NFT.
    * @param whiteListAddress the address of the user who will be able to purchase the NFT
    * @param tokenId the ID of the NFT that the whitelist spot is for
     */
    function addWhiteListToToken(address whiteListAddress, uint256 tokenId) public onlyOwner {
        tokenIdToWhitelistAddress[tokenId] = whiteListAddress;
    }

    /**
    * @dev updates the listing fee of an NFT.
    * @param tokenId the ID of the NFT to update the listing fee of
    * @param newListingFee the listing fee value for the NFT
     */
    function updateTokenListingFee(uint256 tokenId, uint256 newListingFee) public onlyOwner {
        tokenIdToListingFee[tokenId] = newListingFee;
    }

    /**
    * @dev updates the type ID of an NFT.
    * @param tokenId the ID of the NFT to update the type ID of
    * @param newTypeId the type ID value for the NFT
     */
    function updateTokenTypeId(uint256 tokenId, uint256 newTypeId) public onlyOwner {
        tokenIdToTypeId[tokenId] = newTypeId;
    }

    /**
    * @dev updates the type ID that represents the Original Cardinal NFTs
    * @param newOriginalCardinalTypeId the new type ID of the Original Cardinal NFTs
     */
    function updateOriginalCardinalTypeId(uint256 newOriginalCardinalTypeId) public onlyOwner {
        originalCardinalTypeId = newOriginalCardinalTypeId;
    }

    /**
    * @dev updates the type ID that represents the membership NFTs
    * @param newMembershipTypeId the new type ID of the membership NFTs
     */
    function updateMembershipTypeId(uint256 newMembershipTypeId) public onlyOwner {
        membershipTypeId = newMembershipTypeId;
    }

    /**
    * @dev updates the type ID that represents the service NFTs
    * @param newServiceTypeId the new type ID of the service NFTs
     */
    function updateServiceTypeId(uint256 newServiceTypeId) public onlyOwner {
        serviceTypeId = newServiceTypeId;
    }

    /**
    * @dev updates the membership NFT token URI
    * @param newMembershipTokenURI the new type ID of the service NFTs
     */
    function updateMembershipTokenURI(string memory newMembershipTokenURI) public onlyOwner {
        membershipTokenURI = newMembershipTokenURI;
    }

    /**
    * @dev sets the price of the membership NFTs in Cardinal Tokens
    * @param newMembershipPrice the new price of the membership NFTs in Cardinal Tokens
     */
    function updateMembershipPrice(uint256 newMembershipPrice) public onlyOwner {
        membershipPriceInCardinalTokens = newMembershipPrice;
    }

    /**
    * @dev Only owner function to set the reference to the Cardinal Token contract
    * @param cardinalTokenAddress the address for the Cardinal Token contract
    */
    function setCardinalToken(address payable cardinalTokenAddress) public onlyOwner {
        cardinalToken = CardinalToken(cardinalTokenAddress);
    }

}