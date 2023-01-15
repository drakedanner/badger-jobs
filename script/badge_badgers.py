import os

from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware
from shroomdk import ShroomDK

from abis import BADGER_ABI

config = load_dotenv()

ALCHEMY_API_KEY = os.environ.get("ALCHEMY_API_KEY")
SHROOMDK_API_KEY = os.environ.get("SHROOMDK_API_KEY")
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(f'https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

sdk = ShroomDK(SHROOMDK_API_KEY)

badger = w3.eth.contract(
    address="0x1133BCDd1fC810B27d33cEf6578D0FA94a49490b", 
    abi=BADGER_ABI
)

caller = "0xcA32Ed9f1eD2974bB59682f4E70Ff92D85E433B8"

network_data = {
    'chainId': w3.eth.chain_id,
    'from': caller,
    'nonce': w3.eth.getTransactionCount(caller)
}

def main():
    sql = f"""
        with creators as 
        (
        select 
        distinct origin_from_address as user,
        count(tx_hash) as amount
        from 
        polygon.core.fact_event_logs
        where block_timestamp::date > '2022-10-16'::date 
        and contract_Address = lower('0x218b3c623ffb9c5e4dbb9142e6ca6f6559f1c2d6')
        and origin_function_signature = '0x7b366213'
        group by 1 
        )
        -- , operator_balances as 
        -- (
        --   select 
        
        -- )
        select 
        *
        from 
        creators 
    """

    query_result_set = sdk.query(
        sql,
        timeout_minutes=10,
        ttl_minutes=60
    )
    
    addresses = [w3.toChecksumAddress(x['user']) for x in query_result_set.records]
    token_id = 3
    amounts = [x['amount'] for x in query_result_set.records]

    # Get the transactions data and builds is so that any account could sign it
    transaction = badger.functions.leaderMintBatch(
        addresses,
        token_id,
        amounts,
        "0x"
    ).build_transaction(network_data)

    # Signs it with the private key that was provided in .env, but does
    # not send it to the mempool.
    signed_tx = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)

    # Sends a transaction and resolves immediately to confirm success of sending
    # rather than processing. At this point, the transaction has been submitted.
    send = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Now we need to wait for the transaction to complete.
    # We don't actually need to if nothing happens after this, but 
    # this is where you would add retries if it failed, etc.
    tx_receipt = w3.eth.wait_for_transaction_receipt(send)

    print('tx_receipt', tx_receipt)

if __name__ == '__main__':
    main()