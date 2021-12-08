from algosdk.v2client import indexer
from pydantic import BaseModel
from typing import Optional, List


class Transaction(BaseModel):
    sender: str
    round_time: int
    confirmed_round: int
    note: Optional[str]
    group_id: Optional[str]
    tx_id: Optional[str]
    transaction_type: Optional[str]

    class Config:
        extra = "allow"

    @staticmethod
    def base_attributes(transaction: dict):
        attributes = dict()
        attributes["sender"] = transaction.get("sender", None)
        attributes["round_time"] = transaction.get("round-time", None)
        attributes["confirmed_round"] = transaction.get("confirmed-round", None)
        note = transaction.get("note", None)
        if note is not None:
            attributes["note"] = note

        attributes["group_id"] = transaction.get("group", None)
        attributes["tx_id"] = transaction.get("id", None)
        attributes["transaction_type"] = transaction["tx-type"]

        return attributes

    @staticmethod
    def init_from_transaction(transaction: dict):
        attributes = Transaction.base_attributes(transaction)
        return Transaction(**attributes)


class ASATransferTransaction(Transaction):
    receiver: str
    amount: int
    asa_id: int

    close_amount: int
    close_address: Optional[str]

    @property
    def is_opt_in(self) -> bool:
        return self.sender == self.receiver and self.amount == 0 and self.close_amount == 0

    @staticmethod
    def init_from_transaction(transaction):
        attributes = Transaction.base_attributes(transaction)

        asset_transfer_transaction = transaction.get("asset-transfer-transaction", None)
        if asset_transfer_transaction is None:
            raise NotImplementedError

        attributes["receiver"] = asset_transfer_transaction.get("receiver", None)
        attributes["amount"] = asset_transfer_transaction.get("amount", None)
        attributes["asa_id"] = asset_transfer_transaction.get("asset-id", None)

        attributes["close_amount"] = asset_transfer_transaction["close-amount"]
        attributes["close_address"] = asset_transfer_transaction.get("close-to", None)

        return ASATransferTransaction(**attributes)


def latest_asset_transfer(asa_id: int) -> Optional[ASATransferTransaction]:
    headers = {"User-Agent": "wawa"}
    indexer_client = indexer.IndexerClient(indexer_token="",
                                           indexer_address="https://algoexplorerapi.io/idx2",
                                           headers=headers)

    next_token = None
    asset_transfer_transactions: List[ASATransferTransaction] = []

    while True:
        if next_token is None:
            round_transactions = indexer_client.search_transactions(asset_id=asa_id)
        else:
            round_transactions = indexer_client.search_transactions(asset_id=asa_id,
                                                                    next_page=next_token)

        next_token = round_transactions.get("next-token", -1)

        if next_token == -1:
            break

        if len(round_transactions["transactions"]) == 0:
            break

        for t in round_transactions["transactions"]:
            try:
                asset_transfer_transactions.append(ASATransferTransaction.init_from_transaction(t))
            except NotImplementedError:
                continue

    latest_round_time = -1
    latest_txn = None

    for txn in asset_transfer_transactions:
        if (txn.amount == 1 or txn.close_amount == 1) and (txn.round_time > latest_round_time):
            latest_txn = txn
            latest_round_time = txn.round_time

    return latest_txn
