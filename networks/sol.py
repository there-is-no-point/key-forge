import base64
from bip_utils import Bip44, Bip44Coins, Bip44Changes

class NetworkGenerator:
    NAME = "Solana (SOL)"
    SYMBOL = "SOL"

    @staticmethod
    def generate(seed_bytes):
        bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
        acc_obj = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)

        return {
            "address": acc_obj.PublicKey().ToAddress(),
            "private_key": base64.b64encode(acc_obj.PrivateKey().Raw().ToBytes()).decode("utf-8")
        }