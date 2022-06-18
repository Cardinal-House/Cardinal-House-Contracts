// SPDX-License-Identifier: MIT
 
pragma solidity >=0.8.0 <0.9.0;
 
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/Uniswap.sol";

/**
 * @title Cardinal House Token
 * @dev Token contract for the Cardinal House ecosystem currency
 */
contract CardinalToken is ERC20, Ownable {

    // Mapping to exclude some contracts from fees. Transfers are excluded from fees if address in this mapping is recipient or sender.
    mapping (address => bool) public excludedFromFees;

    // Blacklist mapping to prevent addresses from trading if necessary (i.e. flagged for malicious activity).
    mapping (address => bool) public blacklist;

    // Mapping to determine which addresses can mint Cardinal Tokens for bridging.
    mapping (address => bool) public minters;

    // Address of the contract for burning Cardinal Tokens.
    address public burnWalletAddress;

    // Liquidity wallet address used to hold 30% of the Cardinal Tokens for the liquidity pool.
    // After these tokens are moved to the DEX, this address will no longer be used.
    address public liquidityWalletAddress;

    // Address of the Cardinal Token presale contract.
    address public preSaleAddress;

    // Wallet address used for the Cardinal Token member giveaways.
    address payable public memberGiveawayWalletAddress;

    // Marketing wallet address used for funding marketing.
    address payable public marketingWalletAddress;

    // Developer wallet address used for funding the team.
    address payable public developerWalletAddress;

    // The DEX router address for swapping Cardinal Tokens for Matic.
    address public uniswapRouterAddress;

    // Member giveaway transaction fee - deployed at 2%.
    uint256 public memberGiveawayFeePercent = 2;

    // Marketing transaction fee - deployed at 2%.
    uint256 public marketingFeePercent = 2;

    // Developer team transaction fee - deployed at 1%.
    uint256 public developerFeePercent = 1;

    // DEX router interface.
    IUniswapV2Router02 private uniswapRouter;

    // Address of the Matic to Cardinal Token pair on the DEX.
    address public uniswapPair;

    // Determines how many Cardinal Tokens this contract needs before it swaps for Matic to pay fee wallets.
    uint256 public contractTokenDivisor = 1000;

    // Events to emit when the transaction fees are updated
    event memberGiveawayTransactionFeeUpdated(uint256 indexed transactionFeeAmount);
    event marketingTransactionFeeUpdated(uint256 indexed transactionFeeAmount);
    event developerTransactionFeeUpdated(uint256 indexed transactionFeeAmount);

    // Initial token distribution:
    // 35% - Pre-sale
    // 35% - Liquidity pool (6 month lockup period)
    // 10% - Marketing
    // 20% - Developer coins (6 month lockup period)
    constructor(
        uint256 initialSupply,
        address _preSaleAddress, 
        address _burnWalletAddress,
        address _liquidityWalletAddress,
        address payable _memberGiveawayWalletAddress,
        address payable _marketingWalletAddress,
        address payable _developerWalletAddress,
        address _uniswapRouterAddress) ERC20("CardinalToken", "CRNL") {
            preSaleAddress = _preSaleAddress;
            memberGiveawayWalletAddress = _memberGiveawayWalletAddress;
            burnWalletAddress = _burnWalletAddress;
            liquidityWalletAddress = _liquidityWalletAddress;
            marketingWalletAddress = _marketingWalletAddress;
            developerWalletAddress = _developerWalletAddress;
            uniswapRouterAddress = _uniswapRouterAddress;

            excludedFromFees[memberGiveawayWalletAddress] = true;
            excludedFromFees[developerWalletAddress] = true;
            excludedFromFees[marketingWalletAddress] = true;
            excludedFromFees[liquidityWalletAddress] = true;
            excludedFromFees[preSaleAddress] = true;

            _mint(preSaleAddress, ((initialSupply) * 35 / 100));
            _mint(liquidityWalletAddress, ((initialSupply) * 35 / 100));
            _mint(marketingWalletAddress, initialSupply / 10);
            _mint(developerWalletAddress, initialSupply / 5);

            IUniswapV2Router02 _uniswapV2Router = IUniswapV2Router02(uniswapRouterAddress);
            uniswapRouter = _uniswapV2Router;
            _approve(address(this), address(uniswapRouter), initialSupply);
            uniswapPair = IUniswapV2Factory(_uniswapV2Router.factory()).createPair(address(this), _uniswapV2Router.WETH());
            IERC20(uniswapPair).approve(address(uniswapRouter), type(uint256).max);
    }

    /**
     * @dev Returns the contract address
     * @return contract address
     */
    function getContractAddress() public view returns (address){
        return address(this);
    }

    /**
    * @dev Adds a user to be excluded from fees.
    * @param user address of the user to be excluded from fees.
     */
    function excludeUserFromFees(address user) public onlyOwner {
        excludedFromFees[user] = true;
    }

    /**
    * @dev Gets the current timestamp, used for testing + verification
    * @return the the timestamp of the current block
     */
    function getCurrentTimestamp() public view returns (uint256) {
        return block.timestamp;
    }

    /**
    * @dev Removes a user from the fee exclusion.
    * @param user address of the user than will now have to pay transaction fees.
     */
    function includeUsersInFees(address user) public onlyOwner {
        excludedFromFees[user] = false;
    }

    /**
     * @dev Overrides the BEP20 transfer function to include transaction fees.
     * @param recipient the recipient of the transfer
     * @param amount the amount to be transfered
     * @return bool representing if the transfer was successful
     */
    function transfer(address recipient, uint256 amount) public override returns (bool) {
        // Ensure the sender isn't blacklisted.
        require(!blacklist[_msgSender()], "You have been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team.");
        // Ensure the recipient isn't blacklisted.
        require(!blacklist[recipient], "The address you are trying to send Cardinal Tokens to has been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team.");

        // Stops investors from owning more than 2% of the total supply from purchasing Cardinal Tokens from the DEX.
        if (_msgSender() == uniswapPair && !excludedFromFees[_msgSender()] && !excludedFromFees[recipient]) {
            require((balanceOf(recipient) + amount) < (totalSupply() / 166), "You can't have more than 2% of the total Cardinal Token supply after a DEX swap.");
        }

        // If the sender or recipient is excluded from fees, perform the default transfer.
        if (excludedFromFees[_msgSender()] || excludedFromFees[recipient]) {
            _transfer(_msgSender(), recipient, amount);
            return true;
        }

        // Member giveaway transaction fee.
        uint256 memberGiveawayFee = (amount * memberGiveawayFeePercent) / 100;
        // Marketing team transaction fee.
        uint256 marketingFee = (amount * marketingFeePercent) / 100;
        // Developer team transaction fee.
        uint256 developerFee = (amount * developerFeePercent) / 100;

        // The total fee to send to the contract address (marketing + development).
        uint256 contractFee = marketingFee + developerFee;
 
        // Sends the transaction fees to the giveaway wallet and contract address
        _transfer(_msgSender(), memberGiveawayWalletAddress, memberGiveawayFee);
        _transfer(_msgSender(), address(this), contractFee);

        uint256 contractCardinalTokenBalance = balanceOf(address(this));

        if (_msgSender() != uniswapPair) {
            if (contractCardinalTokenBalance > balanceOf(uniswapPair) / contractTokenDivisor) {
                swapCardinalTokensForMatic(contractCardinalTokenBalance);
            }
                
            uint256 contractMaticBalance = address(this).balance;
            if (contractMaticBalance > 0) {
                sendFeesToWallets(address(this).balance);
            }
        }
 
        // Sends [initial amount] - [fees] to the recipient
        uint256 valueAfterFees = amount - contractFee - memberGiveawayFee;
        _transfer(_msgSender(), recipient, valueAfterFees);
        return true;
    }

    /**
     * @dev Overrides the BEP20 transferFrom function to include transaction fees.
     * @param from the address from where the tokens are coming from
     * @param to the recipient of the transfer
     * @param amount the amount to be transfered
     * @return bool representing if the transfer was successful
     */
    function transferFrom(address from, address to, uint256 amount) public override returns (bool) {
        // Ensure the sender isn't blacklisted.
        require(!blacklist[_msgSender()], "You have been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team.");
        // Ensure the address where the tokens are coming from isn't blacklisted.
        require(!blacklist[from], "The address you're trying to spend the Cardinal Tokens from has been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team.");
        // Ensure the recipient isn't blacklisted.
        require(!blacklist[to], "The address you are trying to send Cardinal Tokens to has been blacklisted from trading the Cardinal Token. If you think this is an error, please contact the Cardinal House team.");

        // If the from address or to address is excluded from fees, perform the default transferFrom.
        if (excludedFromFees[from] || excludedFromFees[to] || excludedFromFees[_msgSender()]) {
            _spendAllowance(from, _msgSender(), amount);
            _transfer(from, to, amount);
            return true;
        }

        // Member giveaway transaction fee.
        uint256 memberGiveawayFee = (amount * memberGiveawayFeePercent) / 100;
        // Marketing team transaction fee.
        uint256 marketingFee = (amount * marketingFeePercent) / 100;
        // Developer team transaction fee.
        uint256 developerFee = (amount * developerFeePercent) / 100;

        // The total fee to send to the contract address (marketing + development).
        uint256 contractFee = marketingFee + developerFee;
 
        // Sends the transaction fees to the giveaway wallet and contract address
        _spendAllowance(from, _msgSender(), amount);
        _transfer(from, memberGiveawayWalletAddress, memberGiveawayFee);
        _transfer(from, address(this), contractFee);

        uint256 contractCardinalTokenBalance = balanceOf(address(this));

        if (_msgSender() != uniswapPair) {
            if (contractCardinalTokenBalance > balanceOf(uniswapPair) / contractTokenDivisor) {
                swapCardinalTokensForMatic(contractCardinalTokenBalance);
            }
                
            uint256 contractMaticBalance = address(this).balance;
            if (contractMaticBalance > 0) {
                sendFeesToWallets(address(this).balance);
            }
        }
 
        // Sends [initial amount] - [fees] to the recipient
        uint256 valueAfterFees = amount - contractFee - memberGiveawayFee;
        _transfer(from, to, valueAfterFees);
        return true;
    }

    /**
     * @dev Swaps Cardinal Tokens from transaction fees to Matic.
     * @param amount the amount of Cardinal Tokens to swap
     */
    function swapCardinalTokensForMatic(uint256 amount) private {
        address[] memory path = new address[](2);
        path[0] = address(this);
        path[1] = uniswapRouter.WETH();
        _approve(address(this), address(uniswapRouter), amount);
        uniswapRouter.swapExactTokensForETHSupportingFeeOnTransferTokens(
            amount,
            0,
            path,
            address(this),
            block.timestamp
        );
    }

    /**
     * @dev Sends Matic to transaction fee wallets after Cardinal Token swaps.
     * @param amount the amount to be transfered
     */
    function sendFeesToWallets(uint256 amount) private {
        uint256 totalFee = marketingFeePercent + developerFeePercent;
        marketingWalletAddress.transfer((amount * marketingFeePercent) / totalFee);
        developerWalletAddress.transfer((amount * developerFeePercent) / totalFee);
    }

    /**
     * @dev Sends Matic to transaction fee wallets manually as opposed to happening automatically after a certain level of volume
     */
    function disperseFeesManually() public onlyOwner {
        uint256 contractMaticBalance = address(this).balance;
        sendFeesToWallets(contractMaticBalance);
    }

    /**
     * @dev Swaps all Cardinal Tokens in the contract for Matic and then disperses those funds to the transaction fee wallets.
     * @param amount the amount of Cardinal Tokens in the contract to swap for Matic
     * @param useAmount boolean to determine if the amount sent in is swapped for Matic or if the entire contract balance is swapped.
     */
    function swapCardinalTokensForMaticManually(uint256 amount, bool useAmount) public onlyOwner {
        if (useAmount) {
            swapCardinalTokensForMatic(amount);
        }
        else {
            uint256 contractCardinalTokenBalance = balanceOf(address(this));
            swapCardinalTokensForMatic(contractCardinalTokenBalance);
        }

        uint256 contractMaticBalance = address(this).balance;
        sendFeesToWallets(contractMaticBalance);
    }

    receive() external payable {}

    /**
     * @dev Sets the value that determines how many Cardinal Tokens need to be in the contract before it's swapped for Matic.
     * @param newDivisor the new divisor value to determine the swap threshold
     */
    function setContractTokenDivisor(uint256 newDivisor) public onlyOwner {
        contractTokenDivisor = newDivisor;
    }

    /**
    * @dev Updates the blacklist mapping for a given address
    * @param user the address that is being added or removed from the blacklist
    * @param blacklisted a boolean that determines if the given address is being added or removed from the blacklist
    */
    function updateBlackList(address user, bool blacklisted) public onlyOwner {
        blacklist[user] = blacklisted;
    }

    /**
    * @dev Function to update the member giveaway transaction fee - can't be more than 5 percent
    * @param newMemberGiveawayTransactionFee the new member giveaway transaction fee
    */
    function updateMemberGiveawayTransactionFee(uint256 newMemberGiveawayTransactionFee) public onlyOwner {
        require(newMemberGiveawayTransactionFee <= 5, "The member giveaway transaction fee can't be more than 5%.");
        memberGiveawayFeePercent = newMemberGiveawayTransactionFee;
        emit memberGiveawayTransactionFeeUpdated(newMemberGiveawayTransactionFee);
    }

    /**
    * @dev Function to update the marketing transaction fee - can't be more than 5 percent
    * @param newMarketingTransactionFee the new marketing transaction fee
    */
    function updateMarketingTransactionFee(uint256 newMarketingTransactionFee) public onlyOwner {
        require(newMarketingTransactionFee <= 5, "The marketing transaction fee can't be more than 5%.");
        marketingFeePercent = newMarketingTransactionFee;
        emit marketingTransactionFeeUpdated(newMarketingTransactionFee);
    }

    /**
    * @dev Function to update the developer transaction fee - can't be more than 5 percent
    * @param newDeveloperTransactionFee the new developer transaction fee
    */
    function updateDeveloperTransactionFee(uint256 newDeveloperTransactionFee) public onlyOwner {
        require(newDeveloperTransactionFee <= 5, "The developer transaction fee can't be more than 5%.");
        developerFeePercent = newDeveloperTransactionFee;
        emit developerTransactionFeeUpdated(newDeveloperTransactionFee);
    }

    /**
    * @dev Function to add or remove a Cardinal Token minter
    * @param user the address that will be added or removed as a minter
    * @param isMinter boolean representing if the address provided will be added or removed as a minter
    */
    function updateMinter(address user, bool isMinter) public onlyOwner {
        minters[user] = isMinter;
    }

    /**
    * @dev Minter only function to mint new Cardinal Tokens for bridging
    * @param user the address that the tokens will be minted to
    * @param amount the amount of tokens to be minted to the user
    */
    function mint(address user, uint256 amount) public {
        require(minters[_msgSender()], "You are not authorized to mint Cardinal Tokens.");
        _mint(user, amount);
    }

    /**
    * @dev Minter only function to burn Cardinal Tokens for bridging and deflation upon service purchases with the Cardinal Token
    * @param user the address to burn the tokens from
    * @param amount the amount of tokens to be burned
    */
    function burn(address user, uint256 amount) public {
        require(minters[_msgSender()], "You are not authorized to burn Cardinal Tokens.");
        _burn(user, amount);
    }
}