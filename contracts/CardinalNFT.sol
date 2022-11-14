// SPDX-License-Identifier: MIT
pragma solidity 0.8.8;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title Cardinal House NFT Contract
 * @dev NFT contract that will be used with the marketplace contract
 */
contract CardinalNFT is ERC721URIStorage, ERC721Enumerable, Ownable {
    using Counters for Counters.Counter;

    // Counter to give each NFT a unique ID.
    Counters.Counter public _tokenIds;

    // Address of the Cardinal NFT marketplace.
    address public marketplaceAddress;

    // Contract for USDC - for membership payments
    IERC20 public USDC;

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

    // Mapping to determine which addresses can add and remove other addresses from the member mapping.
    mapping (address => bool) public addressIsAdmin;

    // Mapping to determine membership discount for addresses.
    mapping (address => uint256) public addressToMembershipDiscount;

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

    // The current price of the membership NFT in USDC
    uint256 public membershipPriceInUSDC;

    event membershipNFTMinted(address indexed owner, uint256 indexed tokenId);
    event memberChargedForMembership(address indexed member, uint256 indexed tokenId, uint256 membershipPrice, uint256 currTimeStamp);
    event membershipNFTBurnt(address indexed owner, uint256 indexed tokenId);
    event tokenURIUpdated(uint256 indexed tokenId, string newTokenURI);
    event membershipPriceUpdated(uint256 indexed newMembershipPrice);
    event typeIdUpdated(string indexed typeIdThatWasUpdated, uint256 indexed newTypeId);
    event memberDiscountSet(address indexed member, uint256 indexed discountAmount);

    constructor(address _marketplaceAddress, address _USDC) ERC721("CardinalHouseNFT", "CRNLNFT") {
        marketplaceAddress = _marketplaceAddress;
        USDC = IERC20(_USDC);
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

                emit membershipNFTBurnt(NFTOwner, tokenId);

                membershipTokenIds[i] = membershipTokenIds[membershipTokenIds.length-1];
                membershipTokenIds.pop();
            }
        }
    }

    /**
    * @dev Only owner function to burn a membership NFT
    * @param tokenId the tokenId of the membership NFT to burn
     */
    function burnMembershiptNFTManually(uint256 tokenId) external onlyOwner {
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
    * @dev Allows someone to mint a membership NFT by paying USDC
    * @return the ID of the newly minted membership NFT
     */
    function mintMembershipNFT() external returns (uint) {
        uint256 currMembershipPriceInUSDC = membershipPriceInUSDC;

        if (addressToMembershipDiscount[msg.sender] > 0) {
            currMembershipPriceInUSDC = membershipPriceInUSDC * addressToMembershipDiscount[msg.sender] / 100;
        }

        require(USDC.balanceOf(msg.sender) >= currMembershipPriceInUSDC, "You don't have enough USDC to pay for the membership NFT.");
        require(USDC.allowance(msg.sender, address(this)) >= currMembershipPriceInUSDC, "You haven't approved this contract to spend enough of your USDC to pay for the membership NFT.");
        
        USDC.transferFrom(msg.sender, address(this), currMembershipPriceInUSDC);

        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenIdToTypeId[newItemId] = membershipTypeId;
        tokenIdToListingFee[newItemId] = 0;
        _mint(msg.sender, newItemId);
        membershipNFTToLastPaid[newItemId] = block.timestamp;
        addressToMembershipDiscount[msg.sender] = 0;
        _setTokenURI(newItemId, membershipTokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        membershipTokenIds.push(newItemId);

        emit membershipNFTMinted(msg.sender, newItemId);

        return newItemId;
    }

    /**
    * @dev Only owner function to update the timestamp for a membership NFT after it has been paid for for a month.
    * @param tokenId the ID of the membership NFT to have the timestamp updated for
    * @param lastPaidTimestamp the timestamp to update the membership NFT to for when it was last paid for
     */
    function updateMembershipNFTLastPaid(uint256 tokenId, uint256 lastPaidTimestamp) external onlyOwner {
        membershipNFTToLastPaid[tokenId] = lastPaidTimestamp;
    }

    /**
    * @dev Only owner function to take funds from an address to pay for the next month of a membership
    * @param member the address of the member that is being charged for the next month of a membership
    * @param tokenId the token ID that the member is being charged
    * @param currTimeStamp the current timestamp for the transaction to avoid relying on block.timestamp
    * @return 0 for success, 1 for failure and NFT burn
     */
    function chargeMemberForMembership(address member, uint256 tokenId, uint256 currTimeStamp) external onlyOwner returns (uint) {
        require(ownerOf(tokenId) == member, "This address doesn't own the NFT specified.");
        require(ownerOf(tokenId) != owner() && ownerOf(tokenId) != marketplaceAddress, "Can't charge the owner or marketplace for the membership.");

        uint256 currMembershipPriceInUSDC = membershipPriceInUSDC;

        if (addressToMembershipDiscount[member] > 0) {
            currMembershipPriceInUSDC = membershipPriceInUSDC * addressToMembershipDiscount[member] / 100;
        }

        if (USDC.balanceOf(member) < currMembershipPriceInUSDC || USDC.allowance(member, address(this)) < currMembershipPriceInUSDC) {
            burnMembershipNFT(tokenId);
            return 1;
        }

        USDC.transferFrom(member, address(this), currMembershipPriceInUSDC);

        if (currTimeStamp > 0) {
            membershipNFTToLastPaid[tokenId] = currTimeStamp;
        }
        else {
            membershipNFTToLastPaid[tokenId] = block.timestamp;
        }

        addressToMembershipDiscount[member] = 0;

        emit memberChargedForMembership(member, tokenId, currMembershipPriceInUSDC, currTimeStamp);

        return 0;
    }

    /**
    * @dev Only owner function to withdraw the USDC that are paid to this contract for the Membership NFTs.
     */
    function withdrawMembershipNFTFunds() external onlyOwner {
        USDC.transfer(owner(), USDC.balanceOf(address(this)));
    }

    /**
    * @dev Only owner function to mint a new NFT.
    * @param newTokenURI the token URI on IPFS for the NFT metadata
    * @param typeId the type ID of the NFT to distinguish what type of NFT it is (Original Cardinal, membership, service)
    * @param listingFee the fee the user pays when putting the NFT for sale on the marketplace
    * @param currTimeStamp the current timestamp for the transaction to avoid relying on block.timestamp
    * @return the ID of the newly minted NFT
     */
    function createToken(string memory newTokenURI, uint256 typeId, uint256 listingFee, uint256 currTimeStamp) external onlyOwner returns (uint) {
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();

        tokenIdToTypeId[newItemId] = typeId;
        tokenIdToListingFee[newItemId] = listingFee;
        _mint(msg.sender, newItemId);
        _setTokenURI(newItemId, newTokenURI);
        approve(address(this), newItemId);
        setApprovalForAll(marketplaceAddress, true);

        if (typeId == originalCardinalTypeId) {
            originalCardinalTokenIds.push(newItemId);
        }
        else if (typeId == membershipTypeId) {
            membershipTokenIds.push(newItemId);

            if (currTimeStamp > 0) {
                membershipNFTToLastPaid[newItemId] = currTimeStamp;
            }
            else {
                membershipNFTToLastPaid[newItemId] = block.timestamp;
            }
        }

        return newItemId;
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
    * @dev Function to get all token URIs for Original Cardinal NFTs that a given user owns.
    * @param userAddress the user's address to get token URIs of
    * @return list of token URIs for a user's Original Cardinal NFTs
     */
    function getUserOriginalCardinalTokenURIs(address userAddress) external view returns (string[] memory) {
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
    function getUserMembershipTokenURIs(address userAddress) external view returns (string[] memory) {
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
    function getUserServiceTokenURIs(address userAddress) external view returns (string[] memory) {
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
    function getOriginalCardinalTokenIds() external view returns (uint256[] memory) {
        return originalCardinalTokenIds;
    }

    /**
    * @dev Function to get a list of all the membership NFT IDs.
    * @return list of the membership NFT IDs
     */
    function getMembershipTokenIds() external view returns (uint256[] memory) {
        return membershipTokenIds;
    }

    /**
    * @dev Only owner function to update the timestamp for when a user last paid for their membership.
    * @param tokenId the token ID to update the membership last paid timestamp for
    * @param newLastPaid the new timestamp that represents when the user last paid for their membership NFT
    */
    function updateMembershipNFTToLastPaid(uint256 tokenId, uint256 newLastPaid) external onlyOwner {
        membershipNFTToLastPaid[tokenId] = newLastPaid;
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
    * @dev updates the type ID of an NFT.
    * @param tokenId the ID of the NFT to update the type ID of
    * @param newTypeId the type ID value for the NFT
     */
    function updateTokenTypeId(uint256 tokenId, uint256 newTypeId) external onlyOwner {
        tokenIdToTypeId[tokenId] = newTypeId;
    }

    /**
    * @dev updates the type ID that represents the Original Cardinal NFTs
    * @param newOriginalCardinalTypeId the new type ID of the Original Cardinal NFTs
     */
    function updateOriginalCardinalTypeId(uint256 newOriginalCardinalTypeId) external onlyOwner {
        originalCardinalTypeId = newOriginalCardinalTypeId;
        emit typeIdUpdated("originalCardinalTypeId", newOriginalCardinalTypeId);
    }

    /**
    * @dev updates the type ID that represents the membership NFTs
    * @param newMembershipTypeId the new type ID of the membership NFTs
     */
    function updateMembershipTypeId(uint256 newMembershipTypeId) external onlyOwner {
        membershipTypeId = newMembershipTypeId;
        emit typeIdUpdated("membershipTypeId", newMembershipTypeId);
    }

    /**
    * @dev updates the type ID that represents the service NFTs
    * @param newServiceTypeId the new type ID of the service NFTs
     */
    function updateServiceTypeId(uint256 newServiceTypeId) external onlyOwner {
        serviceTypeId = newServiceTypeId;
        emit typeIdUpdated("serviceTypeId", newServiceTypeId);
    }

    /**
    * @dev updates the membership NFT token URI
    * @param newMembershipTokenURI the new type ID of the service NFTs
     */
    function updateMembershipTokenURI(string memory newMembershipTokenURI) external onlyOwner {
        membershipTokenURI = newMembershipTokenURI;
    }

    /**
    * @dev sets the price of the membership NFTs in USDC
    * @param newMembershipPrice the new price of the membership NFTs in USDC
     */
    function updateMembershipPrice(uint256 newMembershipPrice) external onlyOwner {
        membershipPriceInUSDC = newMembershipPrice;
        emit membershipPriceUpdated(newMembershipPrice);
    }

    /**
    * @dev Only owner function to set the reference to the USDC contract
    * @param _USDC the address for the USDC contract
    */
    function setUSDCContract(address _USDC) external onlyOwner {
        USDC = IERC20(_USDC);
    }

    /**
    * @dev Only owner function to update the admin mapping.
    * @param adminAddress the address to admin rights for
    * @param isAdmin boolean to determine if the address is an admin or not
    */
    function setAdminUser(address adminAddress, bool isAdmin) external onlyOwner {
        addressIsAdmin[adminAddress] = isAdmin;
    }

    /**
    * @dev Allows contract admins to manually add an address as a member. Necessary for memberships purchased through Patreon.
    * @param memberAddress the address of the member being added
    */
    function addMember(address memberAddress) external {
        require(addressIsAdmin[msg.sender], "Only contract admins can add members.");

        addressIsMember[memberAddress] = true;
    }

    /**
    * @dev Allows contract admins to manually remove an address as a member. Necessary for when a membership bought through Patreon expires.
    * @param memberAddress the address to remove from the membership list
    */
    function removeMember(address memberAddress) external {
        require(addressIsAdmin[msg.sender], "Only contract admins can remove a member.");

        addressIsMember[memberAddress] = false;
    }

    /**
    * @dev Allows contract admins to set a membership discount for an address.
    * @param memberAddress the address to give the discount to
    * @param discountAmount the discount amount, 90 for 90% of membership price, 75 for 75% of membership price, etc.
    */
    function setMemberDiscount(address memberAddress, uint256 discountAmount) external {
        require(addressIsAdmin[msg.sender], "Only contract admins can set a membership discount.");
        addressToMembershipDiscount[memberAddress] = discountAmount;
        emit memberDiscountSet(memberAddress, discountAmount);
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