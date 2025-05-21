import unittest
import sys
import os

# Add the parent directory (project root) to sys.path to allow importing from app.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import (
    CharacterSheet,
    Build,
    Abilities,
    Money,  # Added Money for Build model
    check_constitution_score
)

class TestConstitutionCheck(unittest.TestCase):

    def _create_mock_char_sheet(self, con_score: int) -> CharacterSheet:
        """Helper method to create a CharacterSheet with minimal valid data."""
        abilities = Abilities(
            str=10,  # Use alias 'str'
            dex=10,  # Use alias 'dex'
            con=con_score,  # Use alias 'con'
            int=10,  # Use alias 'int'
            wis=10,  # Use alias 'wis'
            cha=10   # Use alias 'cha'
        )
        money = Money(cp=0, sp=0, gp=0, pp=0)
        
        # Construct a dictionary with aliased keys, then use model_validate.
        # This is because the error messages consistently indicate Pydantic expects
        # the aliased keys 'class' and 'feats' during validation.
        build_params_with_aliases = {
            "name": "Test Character",
            "class": "Test Class",      # Using alias 'class' for class_name
            "level": 1,
            "ancestry": "Test Ancestry",
            "heritage": "Test Heritage",
            "background": "Test Background",
            "keyability": "str",
            "abilities": abilities,
            "proficiencies": {}, 
            "feats": [],                # Using alias 'feats' for feats_raw
            "specials": [],
            "equipment": [],
            "weapons": [],
            "money": money,
            "armor": [],
            "spellCasters": [],
            "focusPoints": 0,
            "focus": None
        }
        validated_build = Build.model_validate(build_params_with_aliases)

        # Note: processed_feats and free_archetype_active are handled by validators in Build model
        # For these tests, we don't need to explicitly set them unless their absence causes validation errors
        # or affects the logic being tested (which it doesn't for con_score).
        return CharacterSheet(success=True, build=validated_build)

    def test_con_score_high(self):
        """Test with a high Constitution score (14), expecting no suggestions."""
        character = self._create_mock_char_sheet(con_score=14)
        suggestions = check_constitution_score(character)
        self.assertEqual(len(suggestions), 0, "Should be no suggestions for high CON.")

    def test_con_score_low_standard_warning(self):
        """Test with a low Constitution score (11), expecting one standard warning."""
        character = self._create_mock_char_sheet(con_score=11)
        suggestions = check_constitution_score(character)
        self.assertEqual(len(suggestions), 1, "Should be one suggestion for low CON (11).")
        self.assertIn("Low Constitution (CON)", suggestions[0])
        self.assertIn("Your CON score of 11", suggestions[0])
        self.assertNotIn("Critically", suggestions[0], "Should not be a critical warning.")

    def test_con_score_very_low_critical_warning(self):
        """Test with a very low Constitution score (8), expecting one critical warning."""
        character = self._create_mock_char_sheet(con_score=8)
        suggestions = check_constitution_score(character)
        self.assertEqual(len(suggestions), 1, "Should be one suggestion for very low CON (8).")
        self.assertIn("Critically Low Constitution (CON)", suggestions[0])
        self.assertIn("Your CON score of 8", suggestions[0])

if __name__ == '__main__':
    unittest.main()
