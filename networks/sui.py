from bip_utils import Bip44, Bip44Coins, Bip44Changes

class NetworkGenerator:
    NAME = "SUI Network"
    SYMBOL = "SUI"

    @staticmethod
    def generate(seed_bytes):
        bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.SUI)
        acc_obj = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

        return {
            "address": acc_obj.PublicKey().ToAddress(),
            "private_key": acc_obj.PrivateKey().Raw().ToHex()
        }