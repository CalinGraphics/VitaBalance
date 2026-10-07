"""
Iodul din alimentele catalogului validat.

Sursa: „USDA, FDA, and ODS-NIH Database for the Iodine Content of Common Foods”, Release 4.0 (octombrie 2024),
valori medii în µg / 100 g, analizate prin ICP-MS. https://www.ars.usda.gov/mafcl (IODINE_RELEASE_4.zip).
USDA SR Legacy nu are iod, deci aceste valori le înlocuiesc pe cele null din foods_catalog.json.

Reguli de potrivire (aceleași ca la restul catalogului: nu inventăm valori):
- doar când alimentul și modul de preparare corespund (ex. „Fish, cod, baked” pentru codul gătit); unde baza de date
  are doar varianta crudă și catalogul are varianta gătită (ex. păstrăv, pește-spadă, stridii), iodul rămâne null;
- pâinea: varianta FĂRĂ condiționer cu iodat (folosit doar în SUA), nu cea cu iodat (~600 µg/100 g);
- n = numărul de probe analizate; valorile cu n = 1 sunt marcate cu TODO (incertitudine mare).
"""
from __future__ import annotations

from typing import Dict, Tuple

IODINE_SOURCE = "usda_fda_ods_iodine_r4_2024"

# food_key -> (DB_ID din baza de iod, descrierea din baza de date, µg iod / 100 g, n probe)
IODINE_PER_100G: Dict[str, Tuple[int, str, float, int]] = {
    # Lactate
    "milk_whole": (20, "Milk, whole, fluid", 33.5, 59),
    "milk_semi": (21, "Milk, reduced fat (2%), fluid", 35.8, 59),
    "yogurt_plain": (448, "Yogurt, whole milk, plain", 32.3, 8),
    "yogurt_greek": (361, "Yogurt, Greek, plain, nonfat", 51.2, 6),
    "cottage_cheese": (161, "Cottage cheese, creamed, reduced fat", 36.6, 11),
    "ricotta": (350, "Cheese, ricotta, whole milk", 66.0, 1),  # TODO: o singură probă și grăsime diferită
    "cheddar": (25, "Cheese, cheddar (sharp/mild)", 45.9, 38),
    "mozzarella": (191, "Cheese, mozzarella", 51.0, 30),
    "feta": (450, "Cheese, feta, whole milk, crumbled", 48.4, 8),
    "parmesan": (349, "Cheese, parmesan, grated", 82.4, 9),
    # Ouă
    "egg_boiled": (34, "Eggs, hard-boiled", 61.0, 35),
    # Pește și fructe de mare (preparare corespunzătoare)
    "cod": (186, "Fish, cod, baked", 172.1, 28),
    "salmon_farmed": (158, "Fish, salmon, steaks/fillets, baked", 12.8, 35),
    "salmon_wild": (158, "Fish, salmon, steaks/fillets, baked", 12.8, 35),
    "salmon_sashimi": (496, "Fish, salmon, Atlantic, farmed, raw", 3.2, 8),
    "tuna_light_can": (166, "Fish, tuna, canned in water, drained", 8.7, 15),
    "shrimp": (132, "Crustaceans, shrimp, precooked, shell removed, no tail", 15.2, 39),
    "clams": (392, "Mollusks, clam, mixed species, canned, drained solids", 66.5, 4),
    # Carne
    "beef_ground": (251, "Beef, ground, pan-cooked", 7.5, 35),
    "beef_lean": (260, "Beef steak, loin/sirloin, broiled", 4.7, 34),
    "beef_liver": (335, "Beef/calf, liver, pan-cooked with oil", 16.4, 7),
    "pork_tenderloin": (333, "Pork roast, loin, oven-roasted", 0.4, 7),
    "chicken_breast": (130, "Chicken breast, oven-roasted (skin removed)", 1.2, 35),
    "chicken_thigh": (163, "Chicken thigh, oven-roasted (skin removed)", 0.9, 35),
    "turkey_breast": (30, "Turkey breast, oven-roasted", 4.8, 35),
    # Vegetale (iod aproape zero: valoarea măsurată contează, ca să nu fie tratată ca „necunoscut”)
    "spinach_raw": (206, "Spinach, raw", 6.7, 27),
    "spinach_cooked": (1, "Spinach, fresh/frozen, boiled", 3.9, 8),
    "potato": (84, "Potato, with peel, baked", 0.5, 35),
    "white_beans": (323, "Beans, white, from dry, boiled", 0.1, 7),
    "tofu": (458, "Tofu, firm, plain, drained solids", 0.0, 1),  # TODO: o singură probă
    "almonds": (227, "Almonds, shelled", 0.0, 3),
    "almond_milk": (210, "Beverage, almond", 0.4, 9),
    "soy_milk_fortified": (213, "Beverage, soy, shelf stable", 1.3, 6),
    "white_rice": (40, "Rice, white, enriched, cooked", 0.2, 34),
    "brown_rice": (200, "Rice, brown, cooked", 0.0, 28),
    "quinoa": (223, "Quinoa, cooked", 0.0, 3),
    "white_bread": (46, "Bread, white, enriched, pre-sliced", 1.8, 15),
    "wholewheat_bread": (48, "Bread, whole-wheat, commercially prepared", 1.9, 21),
    "rye_bread": (337, "Bread, rye", 0.6, 7),
}
