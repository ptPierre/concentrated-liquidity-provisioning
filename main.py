import os
import time
from datetime import datetime, timedelta
import requests
import json
import logging
import matplotlib.pyplot as plt
from web3 import Web3
from dotenv import load_dotenv


load_dotenv()

ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

if not ALCHEMY_API_KEY or not PRIVATE_KEY:
    raise Exception("Please set your ALCHEMY_API_KEY and PRIVATE_KEY in the .env file.")


# Connect to Alchemy
alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}"
web3 = Web3(Web3.HTTPProvider(alchemy_url))

if web3.isConnected():
    print("Successfully connected to Ethereum node.")
else:
    raise Exception("Failed to connect to Ethereum node.")

# Access wallet
private_key = PRIVATE_KEY
account = web3.eth.account.from_key(private_key)
print(f"Using account: {account.address}")


# Load the ABI of the liquidity pool contract
with open('pool.json') as f:
    pool_abi = json.load(f)

# Replace with the actual pool contract address
pool_address = web3.toChecksumAddress('0xYourPoolContractAddress')

# Initialize contract
pool_contract = web3.eth.contract(address=pool_address, abi=pool_abi)


def get_market_data():
    # To be implemented 


LOWER_BOUND = 1000
UPPER_BOUND = 2000
# Defining liquidity range and timeout
LIQUIDITY_RANGE = (LOWER_BOUND, UPPER_BOUND)  # Example range in USD
TIMEOUT = timedelta(hours=10)
liquidity_exit_time = None


# Logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info('Bot started.')



def exit_liquidity_pool():
    try:
        # Get the latest nonce
        nonce = web3.eth.getTransactionCount(account.address)

        # Build the transaction
        # Function exitPool() has to be changed depending on which protocol
        tx = pool_contract.functions.exitPool().buildTransaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 200000,  # Estimate the gas limit appropriately
            'gasPrice': web3.toWei('50', 'gwei')  # You might want to adjust the gas price
        })

        # Signing transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)

        # Sending transaction
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(f"Transaction sent with hash: {tx_hash.hex()}")
        logging.info(f"Transaction sent with hash: {tx_hash.hex()}")

        # Waiting for the transaction to be mined
        receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        print(f"Transaction successful with receipt: {receipt}")
        logging.info(f"Transaction successful with receipt: {receipt}")

    except Exception as e:
        print(f"An error occurred while exiting the liquidity pool: {e}")
        logging.error(f"An error occurred while exiting the liquidity pool: {e}")


try:
    while True:
        current_price = get_market_data()

        if current_price is None:
            print("Failed to retrieve price data. Skipping this iteration.")
            logging.warning("Failed to retrieve price data. Skipping this iteration.")
            time.sleep(300)
            continue

        print(f"Current Price: ${current_price}")
        logging.info(f"Current Price: ${current_price}")

        prices.append(current_price)
        timestamps.append(datetime.now())

        # Check if the price is outside the liquidity range
        if not (LIQUIDITY_RANGE[0] <= current_price <= LIQUIDITY_RANGE[1]):
            if liquidity_exit_time is None:
                liquidity_exit_time = datetime.now()
                print("Price left the liquidity range. Starting timer.")
                logging.info("Price left the liquidity range. Starting timer.")
            else:
                elapsed_time = datetime.now() - liquidity_exit_time
                if elapsed_time >= TIMEOUT:
                    print("Price has been out of range for 10 hours. Exiting liquidity pool.")
                    logging.info("Price has been out of range for 10 hours. Exiting liquidity pool.")
                    # Exit the liquidity pool
                    exit_liquidity_pool()
                    liquidity_exit_time = None
        else:
            if liquidity_exit_time is not None:
                print("Price re-entered the liquidity range. Resetting timer.")
                logging.info("Price re-entered the liquidity range. Resetting timer.")
                liquidity_exit_time = None

        # Wait for 5 minutes before the next check
        time.sleep(300)

except KeyboardInterrupt:
    print("Bot emergency stop")
    logging.info("Bot stopped by user.")


except Exception as e:
    print(f"An unexpected error occurred: {e}")
    logging.error(f"An unexpected error occurred: {e}")
