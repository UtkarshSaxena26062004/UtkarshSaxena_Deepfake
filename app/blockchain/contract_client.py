from web3 import Web3
import json

GANACHE_URL = 'http://127.0.0.1:7545'

class ContractClient:
    def __init__(self, abi_path='app/blockchain/contract_abi.json'):
        with open(abi_path,'r') as f:
            data = json.load(f)
        self.abi = data['abi']
        self.address = data['address']
        self.w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        self.contract = self.w3.eth.contract(address=self.address, abi=self.abi)
        self.account = self.w3.eth.accounts[0]

    def store_hash(self, hexhash):
        tx = self.contract.functions.storeHash(hexhash).transact({'from': self.account})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt

    def verify_hash(self, hexhash):
        return self.contract.functions.verifyHash(hexhash).call()
