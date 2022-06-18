// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0 <0.9.0;

import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import './CardinalNFT.sol';
import './CardinalToken.sol';

/**
 * @title Cardinal House NFT Marketplace Contract
 * @dev NFT marketplace contract that users will interact with on the Cardinal House website
 */
contract CardinalHouseMarketplace is ReentrancyGuard, Ownable {
  using Counters for Counters.Counter;

  // Counter to give each marketplace item a unique ID.
  Counters.Counter public _itemIds;

  // Counter to keep track of how many items have been sold on the Cardinal House marketplace.
  Counters.Counter public _itemsSold;

  // The default listing fee for any users that want to resell their Cardinal NFTs.
  uint256 defaultListingPrice = 0 ether;

  // Properties of a Cardinal NFT on the marketplace.
  struct MarketItem {
    uint itemId;
    address nftContract;
    uint256 tokenId;
    address payable seller;
    address payable owner;
    uint256 price;
    bool sold;
    string tokenURI;
    uint256 listingPrice;
  }

  // Maps each NFT's marketplace item ID to all of the properties for the NFT on the marketplace.
  mapping(uint256 => MarketItem) public idToMarketItem;

  // If the NFT contract address ever changes, this mapping keeps track of past NFT contract addresses
  // so that users can still sell NFTs minted with the old contract on the marketplace. If a user tries
  // to sell an NFT from a contract that isn't true in this mapping, it will be rejected.
  mapping (address => bool) public addressToPreviousNFTAddress;

  // Blacklist mapping for listing and purchasing Cardinal NFTs.
  // If this mapping is true for an address then they can't use the marketplace.
  mapping (address => bool) public blacklist;

  // Event emitted whenever a Cardinal NFT is put up for sale on the Cardinal House marketplace.
  event MarketItemCreated (
    uint indexed itemId,
    address indexed nftContract,
    uint256 indexed tokenId,
    address seller,
    address owner,
    uint256 price,
    bool sold,
    string tokenURI,
    uint256 listingPrice
  );

  // References the deployed Cardinal Token.
  CardinalToken public cardinalToken;

  // References the deployed Cardinal NFT contract.
  CardinalNFT public cardinalNFT;

  constructor(address payable CardinalTokenAddress) {
    cardinalToken = CardinalToken(CardinalTokenAddress);
  }

  /**
  * @dev Gets the listing price for listing an NFT on the marketplace
  * @return the current listing price
  */
  function getDefaultListingPrice() public view returns (uint256) {
    return defaultListingPrice;
  }

  /**
  * @dev Only owner function to set the listing price
  * @param newDefaultListingPrice the new default listing price
  */
  function setDefaultListingPrice(uint256 newDefaultListingPrice) public onlyOwner {
      defaultListingPrice = newDefaultListingPrice;
  }

  /**
  * @dev Only owner function to set the reference to the Cardinal Token (CRNL)
  * @param CardinalTokenAddress the contract address for the Cardinal Token
  */
  function setCardinalToken(address payable CardinalTokenAddress) public onlyOwner {
      cardinalToken = CardinalToken(CardinalTokenAddress);
  }

  /**
  * @dev Only owner function to set the reference to the Cardinal NFT contract
  * @param CardinalNFTAddress the address for the Cardinal NFT contract
  */
  function setCardinalNFT(address payable CardinalNFTAddress) public onlyOwner {
      cardinalNFT = CardinalNFT(CardinalNFTAddress);
      addressToPreviousNFTAddress[CardinalNFTAddress] = true;
  }
  
  /**
  * @dev Function to list a Cardinal NFT on the marketplace
  * @param nftContract contract that the NFT was minted on. Only accepts Cardinal NFT contract addresses
  * @param tokenId the token ID of the NFT on the NFT contract
  * @param price the price of the token in Cardinal Tokens (CRNL)
  */
  function createMarketItem(
    address nftContract,
    uint256 tokenId,
    uint256 price
  ) public payable nonReentrant {
    require(addressToPreviousNFTAddress[nftContract], "This isn't a valid Cardinal NFT contract.");
    require(!blacklist[msg.sender], "You have been blacklisted from the Cardinal House NFT marketplace. If you think this is an error, please contact the Cardinal House team.");
    require(price > 0, "The NFT price must be at least 1 wei.");

    uint256 nftListingPrice = cardinalNFT.tokenIdToListingFee(tokenId);
    if (nftListingPrice == 0) {
      nftListingPrice = defaultListingPrice;
    }

    if (msg.sender != owner() && nftListingPrice > 0) {
        require(msg.value == nftListingPrice, "Not enough or too much Matic was sent to pay the NFT listing fee.");
    }
    else if (nftListingPrice > 0) {
      payable(owner()).transfer(msg.value);
    }

    _itemIds.increment();
    uint256 itemId = _itemIds.current();
  
    idToMarketItem[itemId] =  MarketItem(
      itemId,
      nftContract,
      tokenId,
      payable(msg.sender),
      payable(address(0)),
      price,
      false,
      IERC721Metadata(nftContract).tokenURI(tokenId),
      nftListingPrice
    );

    IERC721(nftContract).transferFrom(msg.sender, address(this), tokenId);

    emit MarketItemCreated(
      itemId,
      nftContract,
      tokenId,
      msg.sender,
      address(0),
      price,
      false,
      IERC721Metadata(nftContract).tokenURI(tokenId),
      nftListingPrice
    );
  }

  /**
  * @dev Creates the sale of a marketplace item. Transfers ownership of the NFT and sends funds to the seller
  * @param nftContract contract that the NFT was minted on. Only accepts Cardinal NFT contract addresses
  * @param itemId the item ID of the NFT on the marketplace
  * @param amountIn the amount of Cardinal Token the user is supplying to purchase the NFT
  */
  function createMarketSale(
    address nftContract,
    uint256 itemId,
    uint256 amountIn
    ) public nonReentrant {
    require(addressToPreviousNFTAddress[nftContract], "This isn't a valid Cardinal NFT contract.");
    require(!blacklist[msg.sender], "You have been blacklisted from the Cardinal House NFT marketplace. If you think this is an error, please contact the Cardinal House team.");
    require(!idToMarketItem[itemId].sold, "This marketplace item has already been sold.");

    uint tokenId = idToMarketItem[itemId].tokenId;
    if (cardinalNFT.tokenIdToWhitelistAddress(tokenId) != address(0) && idToMarketItem[itemId].seller == owner()) {
      require(msg.sender == cardinalNFT.tokenIdToWhitelistAddress(tokenId), "This NFT has been assigned to someone through a Whitelist spot. Only they can purchase this NFT.");
    }

    uint price = idToMarketItem[itemId].price;
    require(amountIn == price, "Please submit the asking price in order to complete the purchase.");

    cardinalToken.transferFrom(msg.sender, idToMarketItem[itemId].seller, amountIn);

    IERC721(nftContract).transferFrom(address(this), msg.sender, tokenId);
    idToMarketItem[itemId].owner = payable(msg.sender);
    idToMarketItem[itemId].sold = true;
    _itemsSold.increment();

    if (idToMarketItem[itemId].seller != owner() && idToMarketItem[itemId].listingPrice > 0) {
      payable(owner()).transfer(idToMarketItem[itemId].listingPrice);
    }
  }

  /**
  * @dev Cancels an NFT listing on the marketplace and returns the listing fee to the seller
  * @param nftContract contract that the NFT was minted on. Only accepts Cardinal NFT contract addresses
  * @param itemId the item ID of the NFT on the marketplace
  */
  function cancelMarketSale(
    address nftContract,
    uint256 itemId
    ) public nonReentrant {
    require(addressToPreviousNFTAddress[nftContract], "This isn't a valid Cardinal NFT contract.");
    require(!blacklist[msg.sender], "You have been blacklisted from the Cardinal House NFT marketplace. If you think this is an error, please contact the Cardinal House team.");
    uint tokenId = idToMarketItem[itemId].tokenId;
    address itemSeller = idToMarketItem[itemId].seller;
    bool itemSold = idToMarketItem[itemId].sold;
    require(itemSeller == msg.sender || msg.sender == owner(), "You can only cancel your own NFT listings.");
    require(!itemSold, "This NFT has already been sold.");

    IERC721(nftContract).transferFrom(address(this), idToMarketItem[itemId].seller, tokenId);
    idToMarketItem[itemId].owner = payable(idToMarketItem[itemId].seller);
    idToMarketItem[itemId].sold = true;
    _itemsSold.increment();
    if (idToMarketItem[itemId].seller != owner() && idToMarketItem[itemId].listingPrice > 0) {
        payable(idToMarketItem[itemId].seller).transfer(idToMarketItem[itemId].listingPrice);
    }
  }

  /**
  * @dev Returns all unsold market items
  * @return the list of market items that haven't been sold
  */
  function fetchMarketItems() public view returns (MarketItem[] memory) {
    uint itemCount = _itemIds.current();
    uint unsoldItemCount = _itemIds.current() - _itemsSold.current();
    uint currentIndex = 0;

    MarketItem[] memory items = new MarketItem[](unsoldItemCount);
    for (uint i = 0; i < itemCount; i++) {
      if (idToMarketItem[i + 1].owner == address(0)) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }

  /**
  * @dev Returns only items that a user has purchased
  * @param user the user to fetch the NFTs for
  * @return the list of market items the user owners
  */
  function fetchMyNFTs(address user) public view returns (MarketItem[] memory) {
    uint totalItemCount = _itemIds.current();
    uint itemCount = 0;
    uint currentIndex = 0;

    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].owner == user) {
        itemCount += 1;
      }
    }

    MarketItem[] memory items = new MarketItem[](itemCount);
    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].owner == user) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }

  /**
  * @dev Returns only items a user has created
  * @param user the user to fetch the items created for
  * @return the list of market items the user has put on the market
  */
  function fetchItemsCreated(address user) public view returns (MarketItem[] memory) {
    uint totalItemCount = _itemIds.current();
    uint itemCount = 0;
    uint currentIndex = 0;

    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].seller == user) {
        itemCount += 1;
      }
    }

    MarketItem[] memory items = new MarketItem[](itemCount);
    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].seller == user) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }

  /**
  * @dev Returns only items a user has created that are currently for sale
  * @param user the user to fetch the unsold market items for
  * @return the list of market items the user has put on the market that are currently for sale
  */
  function fetchUnsoldItemsCreated(address user) public view returns (MarketItem[] memory) {
    uint totalItemCount = _itemIds.current();
    uint itemCount = 0;
    uint currentIndex = 0;

    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].seller == user && !idToMarketItem[i + 1].sold) {
        itemCount += 1;
      }
    }

    MarketItem[] memory items = new MarketItem[](itemCount);
    for (uint i = 0; i < totalItemCount; i++) {
      if (idToMarketItem[i + 1].seller == user && !idToMarketItem[i + 1].sold) {
        uint currentId = i + 1;
        MarketItem storage currentItem = idToMarketItem[currentId];
        items[currentIndex] = currentItem;
        currentIndex += 1;
      }
    }
    return items;
  }

  /**
  * @dev Updates the blacklist mapping for a given address
  * @param user the address that is being added or removed from the blacklist
  * @param blacklisted a boolean that determines if the given address is being added or removed from the blacklist
  */
  function updateBlackList(address user, bool blacklisted) public onlyOwner {
    blacklist[user] = blacklisted;
  }

}