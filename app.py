import pandas as pd
from datetime import datetime
import streamlit as st
import math
from retrieve_latest_data import latest_asset_transfer
from staking_script import download_latest_stats
import base64

st.set_page_config(
    page_title="Al Goanna Staking",
)

asa_df = pd.read_csv('data/algoanna_asas.csv')
staking_df = pd.read_csv('data/staking_data.csv')

wallet_addresses = staking_df['Wallet Address'].unique()
wallet_addresses = [addr for addr in wallet_addresses if len(str(addr)) == 58]

staking_df = staking_df[staking_df['Wallet Address'].isin(wallet_addresses)].reset_index(drop=True)
staking_df['asa_id'] = staking_df['ASA ID'].apply(lambda x: int(x))

input_cols = st.columns(2)
selected_asa_id = input_cols[0].selectbox('Select the Al Goanna ID', options=asa_df.asa_id.unique())
required_staking_days = input_cols[1].number_input(label='Required staking days', min_value=1, max_value=365, value=56)

description = """
Downloading process:
- Press the 'Updated the latest staked stats' button to get the latest updates from the blockchain.
- Once the previous step has completed, press the 'Download the latest staked data' to download the .csv file.
"""
st.sidebar.write(description)
st.sidebar.warning('The downloading takes around couple of minutes.')
if st.sidebar.button('Updated the latest staked stats'):
    download_latest_stats(staking_period_days=required_staking_days)

latest_data = pd.read_csv('latest_staked_stats.csv').to_csv().encode('utf-8')
st.sidebar.download_button(
    label="Download the latest staked data",
    data=latest_data,
    file_name='staked_data.csv',
    mime='text/csv',
)

# Movement info
curr_staking_df = staking_df[staking_df.asa_id == selected_asa_id].reset_index(drop=True)
latest_staking_date = datetime.strptime('10 January 2010', '%d %B %Y')
staked_wallet = 'Not staked'

for _, row in curr_staking_df.iterrows():
    staked_date = datetime.strptime(row['Date'], '%d %B %Y')

    if staked_date >= latest_staking_date:
        latest_staking_date = staked_date
        staked_wallet = row['Wallet Address']

latest_txn = latest_asset_transfer(selected_asa_id)
txn_date = datetime.utcfromtimestamp(latest_txn.round_time)
txn_difference = datetime.now() - txn_date

curr_df = asa_df[asa_df.asa_id == selected_asa_id].reset_index(drop=True)

st.image(curr_df.ipfs_image.values[0], caption=f'{curr_df.name.values[0]}')

st.text('Last transfer')
st.warning(datetime.utcfromtimestamp(latest_txn.round_time))

st.text('Owner')
st.warning(latest_txn.receiver if latest_txn.amount == 1 else latest_txn.close_address)

st.text('Transaction ID')
st.warning(latest_txn.tx_id)

st.text('Staked date')
st.warning(latest_staking_date)

st.text('Wallet that staked the Al Goanna')
st.warning(staked_wallet)

st.text('Staking days')
staking_days = int(txn_difference.days)
st.warning(staking_days)

st.text('Is eligible for egg?')

if staking_days > required_staking_days:
    st.success('Eligible')
else:
    st.error('Not Eligible')

st.text('Voted')
st.warning('Has not voted yet')
