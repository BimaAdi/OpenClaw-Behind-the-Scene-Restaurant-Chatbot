from restaurant_chat import list_menu, search_menu, MENU


class TestListMenu:
    """Tests for list_menu function."""

    def test_list_menu_returns_all_items(self):
        """list_menu should return all menu items."""
        result = list_menu()
        assert len(result) == len(MENU)

    def test_list_menu_returns_correct_items(self):
        """list_menu should return the same items as MENU."""
        result = list_menu()
        assert result == MENU

    def test_list_menu_returns_list(self):
        """list_menu should return a list."""
        result = list_menu()
        assert isinstance(result, list)

    def test_list_menu_items_are_menu_items(self):
        """All returned items should be MenuItem type."""
        result = list_menu()
        for item in result:
            assert "menu" in item
            assert "price" in item


class TestSearchMenu:
    """Tests for search_menu function."""

    def test_search_menu_empty_keyword_returns_all(self):
        """search_menu with empty string should return all items."""
        result = search_menu("")
        assert len(result) == len(MENU)
        assert result == MENU

    def test_search_menu_whitespace_only_returns_all(self):
        """search_menu with whitespace only should return all items."""
        result = search_menu("   ")
        assert len(result) == len(MENU)
        assert result == MENU

    def test_search_menu_case_insensitive_lowercase(self):
        """search_menu should be case-insensitive for lowercase search."""
        result = search_menu("hamburger")
        assert len(result) == 1
        assert result[0]["menu"] == "Hamburger"

    def test_search_menu_case_insensitive_uppercase(self):
        """search_menu should be case-insensitive for uppercase search."""
        result = search_menu("PIZZA")
        assert len(result) == 1
        assert result[0]["menu"] == "Cheese Pizza"

    def test_search_menu_case_insensitive_mixed(self):
        """search_menu should be case-insensitive for mixed case search."""
        result = search_menu("ChIcKeN")
        assert len(result) == 1
        assert result[0]["menu"] == "Chicken Wings"

    def test_search_menu_partial_match(self):
        """search_menu should match partial strings."""
        result = search_menu("salad")
        assert len(result) == 1
        assert result[0]["menu"] == "Caesar Salad"

    def test_search_menu_multiple_matches(self):
        """search_menu should return multiple matches when applicable."""
        result = search_menu("a")
        # Items containing 'a': Hamburger, Cheese Pizza, Caesar Salad, Grilled Salmon, Steak, Chocolate Milkshake
        assert len(result) >= 2
        menu_names = [item["menu"] for item in result]
        assert "Hamburger" in menu_names
        assert "Caesar Salad" in menu_names

    def test_search_menu_no_matches(self):
        """search_menu should return empty list when no matches found."""
        result = search_menu("xyz")
        assert result == []

    def test_search_menu_whitespace_trimming(self):
        """search_menu should trim whitespace from keyword."""
        result_with_spaces = search_menu("  hamburger  ")
        result_without_spaces = search_menu("hamburger")
        assert result_with_spaces == result_without_spaces

    def test_search_menu_returns_list(self):
        """search_menu should always return a list."""
        result = search_menu("test")
        assert isinstance(result, list)

    def test_search_menu_specific_items(self):
        """search_menu should correctly find specific items."""
        test_cases = [
            ("fries", "Fries"),
            ("wings", "Chicken Wings"),
            ("salmon", "Grilled Salmon"),
            ("steak", "Steak"),
            ("tea", "Iced Tea"),
        ]
        for keyword, expected_menu in test_cases:
            result = search_menu(keyword)
            assert any(item["menu"] == expected_menu for item in result)
