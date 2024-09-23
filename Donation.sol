// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DonationTracker {
    struct Donation {
        address donor;
        uint amount;
    }

    mapping(uint => Donation) public donations;
    mapping(string => uint) public phaseDistribution;
    uint public donationCount;
    uint public totalFunds;
    address public owner;

    string[] public phases = ["Children's Food", "Agriculture", "Support for Homeless"];
    uint public balance;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function.");
        _;
    }

    function donate() public payable {
        require(msg.value > 0, "Donation must be greater than 0");

        donations[donationCount] = Donation(msg.sender, msg.value);
        donationCount++;
        totalFunds += msg.value;

        // Randomly distribute the donation among the phases
        uint randomPhase = uint(keccak256(abi.encodePacked(block.timestamp, msg.sender))) % 100;

        if (randomPhase < 40) {
            phaseDistribution["Children's Food"] += msg.value;
        } else if (randomPhase < 70) {
            phaseDistribution["Agriculture"] += msg.value;
        } else {
            phaseDistribution["Support for Homeless"] += msg.value;
        }

        // Retain a portion in the balance for withdrawals
        balance += msg.value / 10; // 10% of the donation remains in balance
    }

    function withdraw(uint amount) public onlyOwner {
        require(amount <= balance, "Insufficient balance.");
        payable(owner).transfer(amount);
        balance -= amount; // Reduce the balance after withdrawal
    }

    function getContractBalance() public view returns (uint) {
        return address(this).balance;
    }
}
