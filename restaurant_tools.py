from typing import TypedDict


class MenuItem(TypedDict):
    menu: str
    price: int


MENU: list[MenuItem] = [
    {
        "menu": "Hamburger",
        "price": 5000,
    },
    {
        "menu": "Fries",
        "price": 2000,
    },
    {
        "menu": "Cheese Pizza",
        "price": 12000,
    },
    {
        "menu": "Chicken Wings",
        "price": 9000,
    },
    {
        "menu": "Spaghetti Bolognese",
        "price": 11000,
    },
    {
        "menu": "Caesar Salad",
        "price": 7000,
    },
    {
        "menu": "Grilled Salmon",
        "price": 15000,
    },
    {
        "menu": "Steak",
        "price": 18000,
    },
    {
        "menu": "Iced Tea",
        "price": 3000,
    },
    {
        "menu": "Chocolate Milkshake",
        "price": 4500,
    },
]


def list_menu() -> list[MenuItem]:
    return MENU


def search_menu(keyword: str) -> list[MenuItem]:
    normalized_keyword = keyword.casefold().strip()
    if not normalized_keyword:
        return MENU

    return [item for item in MENU if normalized_keyword in item["menu"].casefold()]


def format_menu(items: list[MenuItem]) -> str:
    if not items:
        return "No menu items found."
    return "\n".join([f"{item['menu']}: {item['price']}" for item in items])
