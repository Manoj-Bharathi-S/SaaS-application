import hashlib
import json
import time

class Block:
    def __init__(self, index, timestamp, transactions, prev_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        # Create a copy of dict to exclude hash field for computation
        data = self.__dict__.copy()
        if 'hash' in data:
            del data['hash']
        block_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_transaction(self, tx_data):
        self.pending_transactions.append(tx_data)
        # Mine immediately for MVI/Demo purposes
        return self.mine()

    def mine(self):
        if not self.pending_transactions:
            return False
            
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=self.pending_transactions,
            prev_hash=self.last_block.hash
        )
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def validate_chain(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i-1]
            
            # Check 1: Hash integrity
            if curr.hash != curr.compute_hash():
                return False
            
            # Check 2: Link integrity
            if curr.prev_hash != prev.hash:
                return False
        return True
