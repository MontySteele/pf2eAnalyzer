import unittest
from app import check_basic_consumables, CharacterSheet, Build, Abilities, Money, ProcessedFeat, Weapon, Armor, SpellCaster # Added missing imports

# Dummy data for Abilities and Money that can be reused
default_abilities = Abilities(str=10, dex=10, con=10, int=10, wis=10, cha=10)
default_money = Money(cp=0, sp=0, gp=0, pp=0)
# Dummy data for other Build fields that are required but not relevant to these tests
default_processed_feats: list[ProcessedFeat] = []
default_weapons: list[Weapon] = []
default_armor: list[Armor] = []
default_spellcasters: list[SpellCaster] = []


class TestCheckBasicConsumables(unittest.TestCase):

    def _create_character_sheet(self, level: int, equipment: list) -> CharacterSheet:
        """Helper method to create a CharacterSheet with minimal data."""
        build_data = Build(
            name="Test Character",
            class_name="Fighter",
            level=level,
            ancestry="Human",
            heritage="Versatile Human",
            background="Warrior",
            keyability="str",
            abilities=default_abilities,
            proficiencies={}, # Minimal
            feats_raw=[], # Minimal
            processed_feats=default_processed_feats, # Using default
            specials=[], # Minimal
            equipment=equipment,
            weapons=default_weapons, # Using default
            money=default_money,
            armor=default_armor, # Using default
            spellCasters=default_spellcasters, # Using default
            focusPoints=0,
            # free_archetype_active will be set by validator
        )
        return CharacterSheet(success=True, build=build_data)

    def test_level_3_no_healing_potions(self):
        character_sheet = self._create_character_sheet(level=3, equipment=[])
        suggestions = check_basic_consumables(character_sheet)
        self.assertListEqual(
            suggestions,
            ["Character is above level 1 and has no healing potions. Consider acquiring some for survivability."]
        )

    def test_level_3_with_healing_potion(self):
        character_sheet = self._create_character_sheet(
            level=3,
            equipment=[{"name": "Minor Healing Potion", "qty": 1}]
        )
        suggestions = check_basic_consumables(character_sheet)
        self.assertListEqual(suggestions, [])

    def test_level_1_no_healing_potions(self):
        character_sheet = self._create_character_sheet(level=1, equipment=[])
        suggestions = check_basic_consumables(character_sheet)
        self.assertListEqual(suggestions, [])

    def test_with_elixir_of_life(self):
        character_sheet = self._create_character_sheet(
            level=3,
            equipment=[{"name": "Elixir of Life", "qty": 1}]
        )
        suggestions = check_basic_consumables(character_sheet)
        self.assertListEqual(
            suggestions,
            ["Character is above level 1 and has no healing potions. Consider acquiring some for survivability."]
        )

    def test_case_insensitive_potion_name(self):
        character_sheet = self._create_character_sheet(
            level=3,
            equipment=[{"name": "healing Potion of Radiance", "qty": 1}]
        )
        suggestions = check_basic_consumables(character_sheet)
        self.assertListEqual(suggestions, [])

    def test_level_5_with_greater_healing_potion(self):
        character_sheet = self._create_character_sheet(
            level=5,
            equipment=[{"name": "Greater Healing Potion", "qty": 3}]
        )
        suggestions = check_basic_consumables(character_sheet)
        self.assertListEqual(suggestions, [])

if __name__ == '__main__':
    unittest.main()
