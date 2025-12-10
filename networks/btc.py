import questionary
from bip_utils import (
    Bip44, Bip44Coins, Bip44Changes,
    Bip49, Bip49Coins,
    Bip84, Bip84Coins,
    Bip86, Bip86Coins
)
# Подключаем наш новый менеджер стилей
import ui_manager

class NetworkGenerator:
    NAME = "Bitcoin (Multi-Format)"
    SYMBOL = "BTC"

    @staticmethod
    def configure():
        """
        Возвращает конфигурацию (словарь), выбранную пользователем.
        НЕ СОХРАНЯЕТ состояние внутри класса.
        """
        choice = questionary.select(
            "🟠 Выберите формат Bitcoin адресов:",
            choices=[
                questionary.Choice("Native Segwit (bc1q...) - [BIP-84] Рекомендуется", value="NATIVE"),
                questionary.Choice("Taproot (bc1p...)       - [BIP-86] Новый стандарт", value="TAPROOT"),
                questionary.Choice("Legacy (1...)           - [BIP-44] Старый формат", value="LEGACY"),
                questionary.Choice("Nested Segwit (3...)    - [BIP-49] Совместимый", value="NESTED"),
            ],
            style=ui_manager.custom_style
        ).ask()

        if not choice:
            return None # Отмена

        # Формируем конфиг, который уйдет в main.py
        config = {
            "mode": choice,
            "symbol_suffix": f"_{choice}" if choice != "NATIVE" else ""
        }
        return config

    @staticmethod
    def generate(seed_bytes, config=None):
        """
        Принимает seed и config (словарь, полученный из configure)
        """
        # Если конфиг не передали (дефолт), используем NATIVE
        mode = config.get("mode", "NATIVE") if config else "NATIVE"

        if mode == "NATIVE":
            bip_obj = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
            type_str = "Native (BIP-84)"
        elif mode == "TAPROOT":
            bip_obj = Bip86.FromSeed(seed_bytes, Bip86Coins.BITCOIN)
            type_str = "Taproot (BIP-86)"
        elif mode == "LEGACY":
            bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
            type_str = "Legacy (BIP-44)"
        elif mode == "NESTED":
            bip_obj = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)
            type_str = "Nested (BIP-49)"
        else:
            bip_obj = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
            type_str = "Native (Default)"

        acc_obj = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

        return {
            "address": acc_obj.PublicKey().ToAddress(),
            "private_key": acc_obj.PrivateKey().ToWif(),
            "type": type_str
        }