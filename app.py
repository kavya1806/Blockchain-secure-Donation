from flask import Flask, render_template, request, jsonify
from web3 import Web3
from solcx import compile_source, install_solc
import random

app = Flask(__name__)

# Install and use a specific version of the Solidity compiler
install_solc('0.8.0')

# Connect to the local Ethereum node (e.g., Ganache)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Check connection
if not w3.isConnected():
    print("Failed to connect to Ethereum node.")
    exit()

# Solidity Smart Contract Source Code
contract_source_code = '''
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
'''

# Compile the contract
compiled_sol = compile_source(contract_source_code, solc_version='0.8.0')
contract_interface = compiled_sol['<stdin>:DonationTracker']

# Deploy the contract
DonationTracker = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

# Get the first account
w3.eth.defaultAccount = w3.eth.accounts[1]

# Deploy the contract
print("Deploying contract...")
tx_hash = DonationTracker.constructor().transact()
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
contract_address = tx_receipt.contractAddress

print(f"Contract deployed at address: {contract_address}")

contract = w3.eth.contract(address=contract_address, abi=contract_interface['abi'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/donate', methods=['POST'])
def donate():
    amount = request.json['amount']
    amount_wei = w3.toWei(float(amount), 'ether')

    w3.eth.defaultAccount = w3.eth.accounts[1]
    tx_hash = contract.functions.donate().transact({'value': amount_wei})
    w3.eth.waitForTransactionReceipt(tx_hash)

    return jsonify({'status': 'success'})

@app.route('/balance', methods=['GET'])
def get_balance():
    balance = contract.functions.getContractBalance().call()
    balance_eth = w3.fromWei(balance, 'ether')
    return jsonify({'balance': balance_eth})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount_eth = float(request.form['amount'])
    amount = w3.toWei(amount_eth, 'ether')

    # Withdraw from contract
    w3.eth.defaultAccount = w3.eth.accounts[0]
    tx_hash = contract.functions.withdraw(amount).transact()
    w3.eth.waitForTransactionReceipt(tx_hash)

    return jsonify({'status': 'withdrawn'})

@app.route('/phase/<phase>', methods=['GET'])
def get_phase(phase):
    amount = contract.functions.phaseDistribution(phase).call()
    amount_eth = w3.fromWei(amount, 'ether')
    return jsonify({'phase': phase, 'amount': amount_eth})

if __name__ == '__main__':
    app.run(debug=True)
