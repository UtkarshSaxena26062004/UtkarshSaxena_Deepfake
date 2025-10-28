from web3 import Web3
from solcx import compile_standard, install_solc
import json

GANACHE_URL = 'http://127.0.0.1:7545'

def compile_and_deploy(sol_path):
    install_solc('0.8.10')
    with open(sol_path, 'r') as f:
        source = f.read()
    compiled = compile_standard({
        'language': 'Solidity',
        'sources': {'VideoVerification.sol': {'content': source}},
        'settings': {'outputSelection': {'*': {'*': ['abi','evm.bytecode']}}}
    }, solc_version='0.8.10')

    abi = compiled['contracts']['VideoVerification.sol']['VideoVerification']['abi']
    bytecode = compiled['contracts']['VideoVerification.sol']['VideoVerification']['evm']['bytecode']['object']

    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    acct = w3.eth.accounts[0]
    Video = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = Video.constructor().transact({'from': acct})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = tx_receipt.contractAddress
    print('Deployed at', address)
    with open('app/blockchain/contract_abi.json','w') as f:
        json.dump({'abi':abi,'address':address}, f)
    return abi, address

if __name__ == '__main__':
    compile_and_deploy('app/blockchain/VideoVerification.sol')
