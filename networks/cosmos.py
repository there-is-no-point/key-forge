import hashlib
import questionary
from bip_utils import Bip32Secp256k1
from bip_utils.bech32 import Bech32Encoder
import ui_manager


class NetworkGenerator:
    NAME = "Cosmos Ecosystem (Universal)"
    SYMBOL = "ATOM"

    @staticmethod
    def configure():
        action = questionary.select(
            "⚛️ Настройка Cosmos Generator:",
            choices=[
                "1. Нативный Cosmos (cosmos1...)",
                "2. Кастомный префикс (celestia1, osmo1...)",
                "3. 🛠  Полная настройка (Префикс + Coin Type)"
            ],
            style=ui_manager.custom_style
        ).ask()

        if not action: return None

        config = {"prefix": "cosmos", "coin_type": 118, "symbol": "ATOM"}

        if action.startswith("2"):
            custom_prefix = questionary.text(
                "Введите префикс (например: osmo, celestia):",
                validate=lambda x: True if x.isalpha() and len(x) > 0 else "Только буквы!",
                style=ui_manager.custom_style
            ).ask()
            if custom_prefix:
                config["prefix"] = custom_prefix.lower()
                config["symbol"] = custom_prefix.upper()

        elif action.startswith("3"):
            custom_prefix = questionary.text("1. Префикс (kava, terra):", style=ui_manager.custom_style).ask()
            custom_type = questionary.text("2. Coin Type ID (118, 459...):", default="118",
                                           style=ui_manager.custom_style).ask()
            if custom_prefix and custom_type:
                config["prefix"] = custom_prefix.lower()
                config["coin_type"] = int(custom_type)
                config["symbol"] = custom_prefix.upper()

        return config

    @staticmethod
    def generate(seed_bytes, config=None):
        # Дефолтные настройки, если config не пришел
        if not config:
            config = {"prefix": "cosmos", "coin_type": 118}

        # Чистая логика генерации
        coin_type = config.get("coin_type", 118)
        prefix = config.get("prefix", "cosmos")

        bip44_path = f"m/44'/{coin_type}'/0'/0/0"
        bip_obj = Bip32Secp256k1.FromSeed(seed_bytes)
        acc_obj = bip_obj.DerivePath(bip44_path)

        pub_key_bytes = acc_obj.PublicKey().RawCompressed().ToBytes()
        sha256_hash = hashlib.sha256(pub_key_bytes).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)

        address = Bech32Encoder.Encode(prefix, ripemd160.digest())

        return {
            "address": address,
            "private_key": acc_obj.PrivateKey().Raw().ToHex(),
            "path": bip44_path,
            "type": f"Cosmos (ID: {coin_type})"
        }