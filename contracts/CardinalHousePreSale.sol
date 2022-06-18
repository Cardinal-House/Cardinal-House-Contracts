// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;
 
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import './CardinalToken.sol';

/**
 * @title Cardinal House Presale contract
 * @dev Contract responsible for the Cardinal House presale mechanisms
 */
contract CardinalHousePreSale is Ownable {

    // References the deployed Cardinal Token.
    CardinalToken public cardinalToken;

    // Mapping to determine how many Cardinal Tokens each address has purchased in the presale.
    mapping(address => uint256) public addressToAmountPurchased;

    // The limit for how many Cardinal Tokens each user can purchase during the presale.
    uint256 public purchaseCap = 150000 * 10 ** 18;

    // 1 Matic can be used to buy this many Cardinal Tokens.
    uint256 public MaticToCRNLRate = 52500;
 
    /**
    * @dev Once the Cardinal Token contract is deployed, this function is used to set a reference to that token in this contract.
    * @param CardinalTokenAddress address of the Cardinal Token.
     */
    function setToken(address payable CardinalTokenAddress) public onlyOwner {
        cardinalToken = CardinalToken(CardinalTokenAddress);
    }

    /**
    * @dev Gets the amount of Cardinal Tokens the sender owns.
    * @return the Cardinal Token balance of the sender
    */
    function getUserBalance() public view returns (uint256) {
        return cardinalToken.balanceOf(msg.sender);
    }
 
     /**
     * @dev Returns the contract address
     * @return contract address
     */
    function getContractAddress() public view returns (address) {
        return address(this);
    }
 
     /**
     * @dev Returns the Cardinal Token address
     * @return Cardinal Token contract address
     */
    function getTokenAddress() public view returns (address) {
        return cardinalToken.getContractAddress();
    }
 
    /**
    * @dev Allows a user to pay Matic for Cardinal Tokens. Conversion rate is 1 Matic to MaticToCRNLRate Cardinal Tokens (CRNL) where MaticToCRNLRate is the variable defined in the contract.
     */
    function purchaseCardinalTokens() public payable {
        // 1 Matic = [MaticToCRNLRate] Cardinal Tokens to transfer to msg sender
        uint256 CardinalTokenAmount = msg.value * MaticToCRNLRate;
        require(addressToAmountPurchased[msg.sender] + CardinalTokenAmount <= purchaseCap,  "You cannot purchase this many Cardinal Tokens, that would put you past your presale cap.");
 
        cardinalToken.transfer(msg.sender, CardinalTokenAmount);
        addressToAmountPurchased[msg.sender] += CardinalTokenAmount;
    }

    /**
    * @dev Only owner function to change the presale Cardinal Token purchase cap per user.
    * @param newPurchaseCap the new Cardinal Token purchase cap in CRNL (NOT Matic). Use the conversion rate to figure out how many Cardinal Tokens to set here.
     */
    function changeCardinalTokenPurchaseCap(uint256 newPurchaseCap) public onlyOwner {
        purchaseCap = newPurchaseCap;
    }

    /**
    * @dev Only owner function to change the conversion rate for Matic to Cardinal Token.
    * @param newConversionRate the new Matic to Cardinal Token conversion rate.
     */
    function changeMaticToCardinalTokenRate(uint256 newConversionRate) public onlyOwner {
        MaticToCRNLRate = newConversionRate;
    }
 
    /**
    * @dev Only owner function to withdraw the Matic from this contract.
    * @param amount the amount of Matic to withdraw from the pre-sale contract.
     */
    function withdrawMatic(uint256 amount) public onlyOwner {
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Failed to send Matic");
    }
 
    /**
    * @dev Gets the amount of Matic that the contract has.
    * @return the amount of Matic the contract has.
     */
    function getContractMatic() public view returns(uint256) {
        return address(this).balance;
    }
 
    /**
    * @dev Gets the Cardinal Token balance of the contract.
    * @return the amount of Cardinal Tokens the contract has.
     */
    function getContractTokens() public view returns(uint256) {
        return cardinalToken.balanceOf(address(this));
    }
}