import os
import questionary

# Подключаем общие стили
import ui_manager
from ui_manager import print_success, print_error, print_info

# Импортируем базу знаний
from bip_utils import Bip44Coins

# --- ШАБЛОНЫ ---
STANDARD_TEMPLATE = """from bip_utils import {bip_import}, {coins_import}, Bip44Changes

class NetworkGenerator:
    NAME = "{display_name}"
    SYMBOL = "{symbol}"

    @staticmethod
    def generate(seed_bytes, config=None):
        # Стандартная генерация для {display_name}
        bip_obj = {bip_class}.FromSeed(seed_bytes, {coins_import}.{enum_name})
        acc_obj = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

        return {{
            "address": acc_obj.PublicKey().ToAddress(),
            "private_key": acc_obj.PrivateKey().Raw().ToHex()
        }}
"""

CUSTOM_TEMPLATE = """from bip_utils import Bip44, Bip44Coins, Bip44Changes
from bip_utils.bech32 import Bech32Encoder
import hashlib

class NetworkGenerator:
    NAME = "{display_name} (Custom)"
    SYMBOL = "{symbol}"

    @staticmethod
    def generate(seed_bytes, config=None):
        # Config placeholder

        # 1. Выбираем базовую криптографию
        if "{base_logic}" == "COSMOS":
             bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.COSMOS)
             prefix = "{cosmos_prefix}"
        elif "{base_logic}" == "SOLANA":
             bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
        elif "{base_logic}" == "BITCOIN":
             bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        else:
             # EVM
             bip_obj = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)

        acc_obj = bip_obj.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)

        # 3. ФОРМИРОВАНИЕ АДРЕСА
        if "{base_logic}" == "COSMOS":
            pub_key_bytes = acc_obj.PublicKey().RawCompressed().ToBytes()
            sha256 = hashlib.sha256(pub_key_bytes).digest()
            ripemd = hashlib.new('ripemd160')
            ripemd.update(sha256)
            address = Bech32Encoder.Encode(prefix, ripemd.digest())
            priv = acc_obj.PrivateKey().Raw().ToHex()

        elif "{base_logic}" == "BITCOIN":
            address = acc_obj.PublicKey().ToAddress()
            priv = acc_obj.PrivateKey().ToWif()

        else:
            address = acc_obj.PublicKey().ToAddress()
            priv = acc_obj.PrivateKey().Raw().ToHex()

        return {{
            "address": address,
            "private_key": priv,
            "path": "{derivation_path}"
        }}
"""


def get_coin_list():
    coins = []
    for coin in Bip44Coins:
        coins.append(coin.name)
    return sorted(coins)


def save_file(filename, content):
    if not os.path.exists("networks"):
        os.makedirs("networks")

    filepath = os.path.join("networks", filename)
    if os.path.exists(filepath):
        print_error(f"Файл {filename} уже существует!")
        if not questionary.confirm("Перезаписать?", style=ui_manager.custom_style).ask():
            return False

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print_error(f"Ошибка записи: {e}")
        return False


# --- ЛОГИКА ---

def run_custom_mode(default_name="My Custom Chain", default_ticker="MYCHAIN"):
    print_info("Режим ручной настройки")

    custom_name = questionary.text("Название сети (в меню):", default=default_name, style=ui_manager.custom_style).ask()
    if not custom_name: return

    custom_ticker = questionary.text("Тикер (для файла):", default=default_ticker, style=ui_manager.custom_style).ask()
    if not custom_ticker: return

    engine = questionary.select(
        "Выберите архитектуру:",
        choices=["EVM", "COSMOS SDK", "SOLANA", "BITCOIN FORK"],
        style=ui_manager.custom_style
    ).ask()

    if not engine: return

    base_logic = "EVM"
    cosmos_prefix = ""
    default_path = "m/44'/60'/0'/0/0"

    if "COSMOS" in engine:
        base_logic = "COSMOS"
        default_path = "m/44'/118'/0'/0/0"
        cosmos_prefix = questionary.text("Префикс (напр. celestia):", style=ui_manager.custom_style).ask()
    elif "SOLANA" in engine:
        base_logic = "SOLANA"
        default_path = "m/44'/501'/0'/0'"
    elif "BITCOIN" in engine:
        base_logic = "BITCOIN"
        default_path = "m/44'/0'/0'/0/0"

    derivation_path = questionary.text(f"Путь деривации ({base_logic}):", default=default_path,
                                       style=ui_manager.custom_style).ask()

    file_content = CUSTOM_TEMPLATE.format(
        display_name=custom_name, symbol=custom_ticker.upper(),
        base_logic=base_logic, derivation_path=derivation_path,
        cosmos_prefix=cosmos_prefix
    )

    filename = f"{custom_ticker.lower()}.py"
    if save_file(filename, file_content):
        print_success(f"Создано: networks/{filename}")


def run_search_mode():
    available_coins = get_coin_list()

    print_info("Начните вводить название (Tron, Doge)...")
    user_input = questionary.autocomplete(
        "Поиск сети:",
        choices=available_coins,
        ignore_case=True,
        style=ui_manager.custom_style
    ).ask()

    if not user_input: return

    if user_input.upper() not in [c.upper() for c in available_coins]:
        print_info("Монета не найдена в базе Bip44Coins.")
        if questionary.confirm("Перейти к ручной настройке?", style=ui_manager.custom_style).ask():
            run_custom_mode(default_name=user_input.title())
        return

    enum_name = user_input.upper()
    display_name = f"{enum_name.replace('_', ' ').title()} Network"
    symbol_input = questionary.text("Тикер файла:", default=enum_name.split('_')[0].title(),
                                    style=ui_manager.custom_style).ask()
    if not symbol_input: return

    filename = f"{symbol_input.lower()}.py"
    file_content = STANDARD_TEMPLATE.format(
        display_name=display_name, symbol=symbol_input.upper(),
        enum_name=enum_name, bip_import="Bip44", bip_class="Bip44",
        coins_import="Bip44Coins"
    )

    if save_file(filename, file_content):
        print_success(f"Создано: networks/{filename}")


def main():
    while True:
        action = questionary.select(
            "Wizard добавления сетей:",
            choices=["🔍 Выбор из списка", "🛠  Ручное добавление", "🔙 Назад в меню"],
            style=ui_manager.custom_style
        ).ask()

        if not action or "Назад" in action:
            # Убран вызов cleanup()
            return

        elif "Выбор" in action:
            run_search_mode()
        elif "Ручное" in action:
            run_custom_mode()


if __name__ == "__main__":
    main()