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
        select 
        distinct origin_from_address as user
        from 
        ethereum.core.fact_event_logs
        where current_date::date - block_timestamp::date < 1
        and origin_from_address in 
        (lower('0x0a453F46f8AE9a99b2B901A26b53e92BE6c3c43E')
        ,lower('0x18ccc241cce98a67564e367ebc1f1f0e692e3188')
        ,lower('0x270c45737830a67f669311ba69e7eae73fb9aed3')
        ,lower('0x2EFF303377B9E01e042B7F80fB42836B35FB1a49')
        ,lower('0x30599f99b06160b9cd8F448A1226Add925Df864e')
        ,lower('0x385fFdc5cFDE800B3625A5a323a8b16677F044a2')
        ,lower('0x3895fac343820b5C20c424079F414149B7008578')
        ,lower('0x4f980eB8e0C2723477e29044F72FcB5964241A2C')
        ,lower('0x5562303C3AE2751773Edd248d3cbDc447ED8d82A')
        ,lower('0x581bef12967f06f2ebfcabb7504fa61f0326cd9a')
        ,lower('0x5fb41DbeE72536E2761FC474bE221a06dbd7d812')
        ,lower('0x62180042606624f02D8A130dA8A3171e9b33894d')
        ,lower('0x6C7c3806B3CaE601b1D99c017E4592753ba8D41e')
        ,lower('0x7498e7573b8d2741b2e46B504A8c1b42B6c23C3C')
        ,lower('0x7C2145E13C6917296d2e95BD5B1f5706c1A99F72')
        ,lower('0x802dEbc52e025461a592069f05a3df386Ee67187')
        ,lower('0x8061E1bA8414989bD41Be7bC5037bd1b0b15F169')
        ,lower('0x9E14Ed39DA8d5A5481555Bf7CC36187E4E7C194b')
        ,lower('0xC322E8Ec33e9b0a34c7cD185C616087D9842ad50')
        ,lower('0xda70761A63d5D0DdE3bdE3b179126127Cccb44b3')
        ,lower('0xed46a40c088D11546Eb4811e565E88A03ae8a07c')
        ,lower('0xFd64E8E4e7DDeC10FD7b1667f3409307dcb5D1c0')
        ,lower('0xF76E2d2Bba0292cF88f71934AfF52Ea54bAa64D9')
        ,lower('0xA3cF6a0d0e42F6386f8D81a3aD82EBe4c558857A')
        ,lower('0x09dD35BbF83e64E90F998e54C9D0ecB9B0E614B5')
        ,lower('0x39E856863e5F6f0654a0b87B12bc921DA23D06BB')
        ,lower('0x348eE4ed9363299832C33DBB1B52C7fBD5571754')
        ,lower('0xFf8D58f85a4f7199c4b9461F787cD456Ad30e594')
        ,lower('0x5B32132EEA7F4654B0FA13A649037A3D1C83350c')
        ,lower('0x477c2087F3D6e49b1BE5C790A33b3a025A4Fa569')
        ,lower('0xe47003021Bbed2EC04625476f686350FB4E0FB38')
        ,lower('0x5EA2DF46C4d022382bb2Cc9561f39CF24060d6d8')
        ,lower('0xD06608313eA30AFf0C89a1b3617bce50765e5CA4')
        ,lower('0xa7a9593478dc4c4f191Cc97a88da0C1299aF0355')
        ,lower('0x8363b3C46C057F9218DDC2F8fa87994173b57d82')
        ,lower('0x1ccb2945F1325e061b40Fe5b0B452f0E76fB7278')
        ,lower('0xB55d9b50AC5748Bd9377757a0c6D463C771ca813')
        ,lower('0xf5B96Fc090A491C861C601f2b051FAE552194Aa3'))
    """

    query_result_set = sdk.query(
        sql,
        timeout_minutes=10,
        ttl_minutes=60
    )
    
    addresses = [w3.toChecksumAddress(x['user']) for x in query_result_set.records]
    token_id = 3
    amounts = [1] * len(query_result_set.records)

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