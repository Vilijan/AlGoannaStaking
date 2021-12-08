import pandas as pd
from retrieve_latest_data import latest_asset_transfer
from datetime import datetime


def download_latest_stats():
    asa_df = pd.read_csv('data/algoanna_asas.csv')
    staking_df = pd.read_csv('data/staking_data.csv')

    wallet_addresses = staking_df['Wallet Address'].unique()
    wallet_addresses = [addr for addr in wallet_addresses if len(str(addr)) == 58]

    staking_df = staking_df[staking_df['Wallet Address'].isin(wallet_addresses)].reset_index(drop=True)
    staking_df['asa_id'] = staking_df['ASA ID'].apply(lambda x: int(x))

    STAKING_PERIOD_DAYS = 56
    data = []
    columns = ['asa_id', 'name', 'latest_transfer_date', 'tx_id', 'staked_date', 'not_moved_days', 'staked_days',
               'eligible']

    for asa_idx, asa_id in enumerate(asa_df.asa_id.unique()):

        if asa_idx % 10 == 0:
            print(asa_idx)

        latest_txn = latest_asset_transfer(asa_id)

        if latest_txn is None:
            print(f'BUG for {asa_id}')
            continue
        asa_name = asa_df[asa_df.asa_id == asa_id].name.values[0]

        txn_date = datetime.utcfromtimestamp(latest_txn.round_time)
        txn_difference = datetime.now() - txn_date

        curr_staking_df = staking_df[staking_df.asa_id == asa_id].reset_index(drop=True)
        latest_staking_date = datetime.strptime('10 January 2010', '%d %B %Y')
        staked_wallet = 'Not staked'

        for _, row in curr_staking_df.iterrows():
            try:
                staked_date = datetime.strptime(row['Date'] + ' ' + row['Time'], '%d %B %Y %H:%M')
            except:
                continue

            if staked_date >= latest_staking_date:
                latest_staking_date = staked_date
                staked_wallet = row['Wallet Address']

        if staked_wallet == 'Not staked':
            data.append([
                asa_id,
                asa_name,
                txn_date,
                latest_txn.tx_id,
                'NOT STAKED',
                txn_difference.days,
                0,
                'No'
            ])
            continue

        days_staked = datetime.now() - latest_staking_date

        asa_owner = latest_txn.receiver if latest_txn.amount == 1 else latest_txn.close_address
        is_eligible = 'No'

        if txn_difference.days >= STAKING_PERIOD_DAYS and \
                days_staked.days >= STAKING_PERIOD_DAYS and \
                asa_owner == staked_wallet:
            is_eligible = 'Yes'

        data.append([
            asa_id,
            asa_name,
            txn_date,
            latest_txn.tx_id,
            latest_staking_date,
            txn_difference.days,
            days_staked.days,
            is_eligible
        ])

    df = pd.DataFrame(data=data, columns=columns)
    df.to_csv('latest_staked_stats.csv', index=False)
