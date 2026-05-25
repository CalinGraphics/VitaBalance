"""Categorii compuse — cereale nu sunt lactate."""
import unittest

from services.food_category_resolver import (
    resolve_category_group,
    resolve_category_display_label,
    beverage_hint_from_name,
)


class TestFoodCategoryResolver(unittest.TestCase):
    def test_cereale_procesate_is_cereale(self):
        self.assertEqual(resolve_category_group("Cereale/Procesate"), "cereale")
        self.assertEqual(resolve_category_display_label("Cereale/Procesate"), "Cereale")

    def test_mese_cereale_is_cereale_not_lactate(self):
        self.assertEqual(resolve_category_group("Mese/Cereale"), "cereale")

    def test_proteine_lactate_is_lactate(self):
        self.assertEqual(resolve_category_group("Proteine/Lactate"), "lactate")

    def test_paine_integrala_not_beverage(self):
        self.assertIsNone(beverage_hint_from_name("Pâine Integrală Prăjită (1 felie)"))
        self.assertIsNone(beverage_hint_from_name("Terci de Ovăz (gătit)"))

    def test_lapte_drink_is_ml_hint(self):
        self.assertEqual(beverage_hint_from_name("Lapte cu Ciocolată"), 200)


if __name__ == "__main__":
    unittest.main()
