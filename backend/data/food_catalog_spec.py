"""
Specificația catalogului validat de alimente.

Aici NU există valori nutriționale scrise de mână. Fiecare aliment indică un rând din USDA FoodData Central
(SR Legacy, aprilie 2018, https://fdc.nal.usda.gov/download-datasets) prin `fdc_id`; valorile la 100 g sunt extrase
de `scripts/build_food_catalog.py` și scrise în `data/foods_catalog.json`. Ce lipsește în USDA rămâne `null`.

Ce se scrie de mână (și trebuie verificat la review):
- numele RO/EN, categoria, porția realistă și marcajele de siguranță de mai jos;
- porțiile urmează convențiile: nuci/semințe 30 g, pește gătit 130 g, leguminoase gătite 150 g, legume cu
  frunze 80 g, alte legume 80 g (porția „5 pe zi”, NHS), pâine 1 felie ≈ 40 g, ou 1 buc = 50 g, fructe = o bucată
  medie (greutatea porției comestibile din USDA, rotunjită), fructe uscate 30 g (NHS).

Marcaje (`flags`):
- raw_animal       — pește/fructe de mare consumate crude (sashimi, stridii crude);
- high_mercury     — pești din lista FDA/EPA „Choices to Avoid” (2021): pește-spadă, macrou regal, tilefish;
- liver            — ficat (vitamina A preformată în cantități foarte mari);
- soft_mould_cheese— brânzeturi moi cu mucegai (Brie, Camembert): risc de Listeria (NHS, „Foods to avoid in pregnancy”);
- ultra_processed  — NOVA grupa 4 (Monteiro et al., Public Health Nutr. 2019);
- refined_grain    — făină rafinată / cereale decorticate;
- added_sugar      — produse în care zahărul adăugat e ingredient principal;
- high_oxalate     — legume cu frunze bogate în oxalați (spanac, mangold, frunze de sfeclă): fierul și calciul
                     se absorb slab (Gillooly et al., Br J Nutr 1983;49:331; Weaver et al., J Food Sci 1987;52:1029).
- us_enriched      — produs din făină fortificată obligatoriu în SUA (fier, acid folic). În România fortificarea nu e
                     obligatorie, deci fierul și folatul acestor produse NU se folosesc (devin null la build).
                     TODO: de înlocuit cu valori pentru produse românești când avem o sursă.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class FoodSpec:
    key: str
    fdc_id: int
    name_ro: str
    name_en: str
    category: str
    portion_g: float
    portion_ro: str
    portion_en: str
    animal: Optional[str] = None  # None | dairy | egg | fish | shellfish | meat | poultry
    allergens: Tuple[str, ...] = ()  # coduri din frontend: lactoza, gluten, nuci, oua, soia, peste, crustacee, arahide, sesam, mustar
    flags: Tuple[str, ...] = field(default_factory=tuple)


# Categoriile (cheie stabilă -> etichetă RO/EN). Diversitatea și „alternativele similare” lucrează pe aceste chei.
CATEGORIES = {
    "nuts": ("Nuci", "Nuts"),
    "seeds": ("Semințe", "Seeds"),
    "legumes": ("Leguminoase", "Legumes"),
    "leafy_greens": ("Legume cu frunze verzi", "Leafy greens"),
    "vegetables": ("Legume", "Vegetables"),
    "fruits": ("Fructe", "Fruits"),
    "dried_fruits": ("Fructe uscate", "Dried fruit"),
    "fish": ("Pește", "Fish"),
    "shellfish": ("Fructe de mare", "Shellfish"),
    "meat": ("Carne", "Meat"),
    "poultry": ("Carne de pasăre", "Poultry"),
    "offal": ("Organe", "Offal"),
    "processed_meat": ("Mezeluri", "Processed meat"),
    "eggs": ("Ouă", "Eggs"),
    "dairy": ("Lactate", "Dairy"),
    "cheese": ("Brânzeturi", "Cheese"),
    "plant_milks": ("Băuturi vegetale", "Plant-based drinks"),
    "whole_grains": ("Cereale integrale", "Whole grains"),
    "refined_grains": ("Cereale rafinate", "Refined grains"),
    "bakery": ("Produse de patiserie", "Bakery products"),
    "sweets_snacks": ("Dulciuri și gustări", "Sweets and snacks"),
}

NUT = ("nuci",)
DAIRY = ("lactoza",)
GLUTEN = ("gluten",)
# Moluștele sunt alergen separat de crustacee (Reg. UE 1169/2011, anexa II). Le marcăm cu ambele coduri: cine a
# declarat „crustacee” se referă adesea la fructe de mare în general, iar excluderea în plus e varianta sigură.
MOLLUSC = ("crustacee", "moluste")

FOODS: Tuple[FoodSpec, ...] = (
    # --- Nuci (30 g = o mână) ---
    FoodSpec("almonds", 170567, "Migdale", "Almonds", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("walnuts", 170187, "Nuci", "Walnuts", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("hazelnuts", 170581, "Alune de pădure", "Hazelnuts", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("cashews", 170162, "Caju crud", "Raw cashews", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("pistachios", 170184, "Fistic crud", "Raw pistachios", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("brazil_nuts", 170569, "Nuci braziliene", "Brazil nuts", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("pecans", 170182, "Nuci pecan", "Pecans", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("pine_nuts", 170591, "Semințe de pin", "Pine nuts", "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=NUT),
    FoodSpec("mixed_nuts", 170585, "Amestec de nuci (cu arahide), prăjite fără sare", "Mixed nuts with peanuts, dry roasted, unsalted",
             "nuts", 30, "o mână (30 g)", "a handful (30 g)", allergens=("nuci", "arahide")),
    FoodSpec("peanut_butter", 172470, "Unt de arahide fără sare", "Peanut butter, unsalted", "nuts", 30,
             "2 linguri (30 g)", "2 tablespoons (30 g)", allergens=("arahide",)),
    # --- Semințe (30 g) ---
    FoodSpec("pumpkin_seeds", 170556, "Semințe de dovleac", "Pumpkin seeds", "seeds", 30, "o mână (30 g)", "a handful (30 g)"),
    FoodSpec("sunflower_seeds", 170562, "Semințe de floarea-soarelui", "Sunflower seeds", "seeds", 30, "o mână (30 g)", "a handful (30 g)"),
    FoodSpec("chia_seeds", 170554, "Semințe de chia", "Chia seeds", "seeds", 30, "2 linguri (30 g)", "2 tablespoons (30 g)"),
    FoodSpec("flaxseed", 169414, "Semințe de in", "Flaxseed", "seeds", 30, "2 linguri (30 g)", "2 tablespoons (30 g)"),
    FoodSpec("sesame_seeds", 170150, "Semințe de susan", "Sesame seeds", "seeds", 30, "2 linguri (30 g)", "2 tablespoons (30 g)",
             allergens=("sesam",)),
    FoodSpec("hemp_seeds", 170148, "Semințe de cânepă decorticate", "Hulled hemp seeds", "seeds", 30, "2 linguri (30 g)", "2 tablespoons (30 g)"),
    # --- Leguminoase gătite (150 g) ---
    FoodSpec("black_beans", 173735, "Fasole neagră fiartă", "Black beans, cooked", "legumes", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("white_beans", 175203, "Fasole albă fiartă", "White beans, cooked", "legumes", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("kidney_beans", 173740, "Fasole roșie fiartă", "Kidney beans, cooked", "legumes", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("lentils", 172421, "Linte fiartă", "Lentils, cooked", "legumes", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("chickpeas", 173757, "Năut fiert", "Chickpeas, cooked", "legumes", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("edamame", 168411, "Edamame (boabe de soia verzi)", "Edamame", "legumes", 150, "un castron mic (150 g)", "a small bowl (150 g)",
             allergens=("soia",)),
    FoodSpec("tofu", 172448, "Tofu tare", "Firm tofu", "legumes", 100, "o felie groasă (100 g)", "a thick slice (100 g)", allergens=("soia",)),
    FoodSpec("tempeh", 174272, "Tempeh", "Tempeh", "legumes", 100, "o porție (100 g)", "a serving (100 g)", allergens=("soia",)),
    FoodSpec("hummus", 174289, "Hummus", "Hummus", "legumes", 60, "4 linguri (60 g)", "4 tablespoons (60 g)", allergens=("sesam",)),
    FoodSpec("green_peas", 170017, "Mazăre verde fiartă", "Green peas, cooked", "legumes", 80, "o porție (80 g)", "a serving (80 g)"),
    # --- Legume cu frunze verzi (80 g) ---
    FoodSpec("spinach_raw", 168462, "Spanac crud", "Raw spinach", "leafy_greens", 80, "un bol (80 g)", "a bowl (80 g)", flags=("high_oxalate",)),
    FoodSpec("spinach_cooked", 168463, "Spanac fiert", "Cooked spinach", "leafy_greens", 80, "o porție (80 g)", "a serving (80 g)", flags=("high_oxalate",)),
    FoodSpec("kale", 168421, "Kale crud", "Raw kale", "leafy_greens", 80, "un bol (80 g)", "a bowl (80 g)"),
    FoodSpec("swiss_chard", 170401, "Mangold fiert", "Swiss chard, cooked", "leafy_greens", 80, "o porție (80 g)", "a serving (80 g)", flags=("high_oxalate",)),
    FoodSpec("arugula", 169387, "Rucola", "Arugula", "leafy_greens", 80, "un bol (80 g)", "a bowl (80 g)"),
    FoodSpec("romaine", 169247, "Salată romană", "Romaine lettuce", "leafy_greens", 80, "un bol (80 g)", "a bowl (80 g)"),
    FoodSpec("beet_greens", 170376, "Frunze de sfeclă fierte", "Beet greens, cooked", "leafy_greens", 80, "o porție (80 g)", "a serving (80 g)", flags=("high_oxalate",)),
    FoodSpec("collards", 170407, "Varză furajeră (collard) fiartă", "Collard greens, cooked", "leafy_greens", 80, "o porție (80 g)", "a serving (80 g)"),
    # --- Alte legume (80 g; cartofii o bucată medie) ---
    FoodSpec("broccoli_raw", 170379, "Broccoli crud", "Raw broccoli", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("broccoli_cooked", 169967, "Broccoli fiert", "Cooked broccoli", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("brussels_sprouts", 169971, "Varză de Bruxelles fiartă", "Brussels sprouts, cooked", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("cauliflower", 169986, "Conopidă", "Cauliflower", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("cabbage", 169975, "Varză albă", "White cabbage", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("carrots", 170393, "Morcovi cruzi", "Raw carrots", "vegetables", 80, "un morcov mediu (80 g)", "a medium carrot (80 g)"),
    FoodSpec("red_pepper", 170108, "Ardei gras roșu", "Red bell pepper", "vegetables", 80, "jumătate de ardei (80 g)", "half a pepper (80 g)"),
    FoodSpec("tomatoes", 170457, "Roșii", "Tomatoes", "vegetables", 80, "o roșie medie (80 g)", "a medium tomato (80 g)"),
    FoodSpec("cucumber", 168409, "Castravete cu coajă", "Cucumber with peel", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("zucchini", 169291, "Dovlecel", "Zucchini", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("green_beans", 169141, "Fasole verde fiartă", "Green beans, cooked", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("asparagus", 168390, "Sparanghel fiert", "Asparagus, cooked", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("beets", 169146, "Sfeclă roșie fiartă", "Beets, cooked", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("onion", 170000, "Ceapă", "Onion", "vegetables", 80, "o ceapă mică (80 g)", "a small onion (80 g)"),
    FoodSpec("mushrooms", 169251, "Ciuperci albe", "White mushrooms", "vegetables", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("mushrooms_uv", 169376, "Ciuperci albe expuse la UV", "UV-exposed white mushrooms", "vegetables", 80,
             "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("sweet_potato", 168483, "Cartof dulce copt", "Baked sweet potato", "vegetables", 150, "un cartof mediu (150 g)", "a medium potato (150 g)"),
    FoodSpec("potato", 170093, "Cartof copt cu coajă", "Baked potato with skin", "vegetables", 170, "un cartof mediu (170 g)", "a medium potato (170 g)"),
    FoodSpec("avocado", 171705, "Avocado", "Avocado", "vegetables", 75, "jumătate de avocado (75 g)", "half an avocado (75 g)"),
    # --- Fructe (o bucată medie) ---
    FoodSpec("orange", 169097, "Portocală", "Orange", "fruits", 130, "o portocală medie (130 g)", "a medium orange (130 g)"),
    FoodSpec("kiwi", 168153, "Kiwi", "Kiwi", "fruits", 75, "un kiwi (75 g)", "one kiwi (75 g)"),
    FoodSpec("strawberries", 167762, "Căpșuni", "Strawberries", "fruits", 150, "un bol (150 g)", "a bowl (150 g)"),
    FoodSpec("banana", 173944, "Banană", "Banana", "fruits", 120, "o banană medie (120 g)", "a medium banana (120 g)"),
    FoodSpec("apple", 171688, "Măr cu coajă", "Apple with skin", "fruits", 180, "un măr mediu (180 g)", "a medium apple (180 g)"),
    FoodSpec("blueberries", 171711, "Afine", "Blueberries", "fruits", 80, "o mână (80 g)", "a handful (80 g)"),
    FoodSpec("pear", 169118, "Pară", "Pear", "fruits", 180, "o pară medie (180 g)", "a medium pear (180 g)"),
    FoodSpec("cherries", 171719, "Cireșe", "Sweet cherries", "fruits", 80, "o mână (80 g)", "a handful (80 g)"),
    FoodSpec("grapes", 174683, "Struguri", "Grapes", "fruits", 80, "o mână (80 g)", "a handful (80 g)"),
    FoodSpec("pomegranate", 169134, "Rodie", "Pomegranate", "fruits", 80, "o porție (80 g)", "a serving (80 g)"),
    FoodSpec("guava", 173044, "Guava", "Guava", "fruits", 55, "un fruct (55 g)", "one fruit (55 g)"),
    # --- Fructe uscate (30 g) ---
    FoodSpec("dried_apricots", 173941, "Caise uscate", "Dried apricots", "dried_fruits", 30, "o mână mică (30 g)", "a small handful (30 g)"),
    FoodSpec("prunes", 168162, "Prune uscate", "Prunes", "dried_fruits", 30, "o mână mică (30 g)", "a small handful (30 g)"),
    FoodSpec("dried_figs", 174665, "Smochine uscate", "Dried figs", "dried_fruits", 30, "o mână mică (30 g)", "a small handful (30 g)"),
    FoodSpec("dates", 168191, "Curmale Medjool", "Medjool dates", "dried_fruits", 30, "o mână mică (30 g)", "a small handful (30 g)"),
    # --- Pește (130 g gătit) ---
    FoodSpec("salmon_farmed", 175168, "Somon de crescătorie, gătit", "Farmed salmon, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",)),
    FoodSpec("salmon_wild", 171998, "Somon sălbatic, gătit", "Wild salmon, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",)),
    FoodSpec("salmon_sashimi", 175167, "Somon crud (sashimi)", "Raw salmon (sashimi)", "fish", 100, "o porție (100 g)", "a serving (100 g)",
             animal="fish", allergens=("peste",), flags=("raw_animal",)),
    FoodSpec("trout", 173718, "Păstrăv de crescătorie, gătit", "Farmed rainbow trout, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",)),
    FoodSpec("sardines", 175139, "Sardine în ulei, scurse", "Sardines in oil, drained", "fish", 90, "o conservă mică (90 g)", "a small can (90 g)",
             animal="fish", allergens=("peste",)),
    FoodSpec("herring", 175117, "Hering gătit", "Herring, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",)),
    FoodSpec("mackerel", 175120, "Macrou atlantic, gătit", "Atlantic mackerel, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",)),
    FoodSpec("cod", 171956, "Cod gătit", "Cod, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)", animal="fish", allergens=("peste",)),
    FoodSpec("carp", 174185, "Crap gătit", "Carp, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)", animal="fish", allergens=("peste",)),
    FoodSpec("tuna_light_can", 173709, "Ton light în apă, conservă", "Light tuna canned in water", "fish", 100, "o conservă scursă (100 g)",
             "a drained can (100 g)", animal="fish", allergens=("peste",)),
    FoodSpec("swordfish", 173704, "Pește-spadă gătit", "Swordfish, cooked", "fish", 130, "o bucată (130 g)", "a steak (130 g)",
             animal="fish", allergens=("peste",), flags=("high_mercury",)),
    FoodSpec("king_mackerel", 174236, "Macrou regal, gătit", "King mackerel, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",), flags=("high_mercury",)),
    FoodSpec("tilefish", 175152, "Tilefish gătit", "Tilefish, cooked", "fish", 130, "o bucată (130 g)", "a fillet (130 g)",
             animal="fish", allergens=("peste",), flags=("high_mercury",)),
    # --- Fructe de mare ---
    FoodSpec("oysters_raw", 171978, "Stridii crude", "Raw oysters", "shellfish", 85, "6 stridii (85 g)", "6 oysters (85 g)",
             animal="shellfish", allergens=MOLLUSC, flags=("raw_animal",)),
    FoodSpec("mussels", 174217, "Midii gătite", "Mussels, cooked", "shellfish", 100, "o porție (100 g)", "a serving (100 g)",
             animal="shellfish", allergens=MOLLUSC),
    FoodSpec("clams", 171975, "Scoici gătite", "Clams, cooked", "shellfish", 85, "o porție (85 g)", "a serving (85 g)",
             animal="shellfish", allergens=MOLLUSC),
    FoodSpec("shrimp", 175180, "Creveți gătiți", "Shrimp, cooked", "shellfish", 100, "o porție (100 g)", "a serving (100 g)",
             animal="shellfish", allergens=("crustacee",)),
    # --- Carne (120 g gătită) ---
    FoodSpec("beef_lean", 173118, "Vită slabă (sirloin), la grătar", "Lean beef sirloin, grilled", "meat", 120, "o bucată (120 g)", "a piece (120 g)", animal="meat"),
    FoodSpec("beef_ground", 174031, "Carne tocată de vită 90% slabă, gătită", "Ground beef 90% lean, cooked", "meat", 120, "o porție (120 g)",
             "a serving (120 g)", animal="meat"),
    FoodSpec("pork_tenderloin", 168250, "Mușchi de porc la cuptor", "Pork tenderloin, roasted", "meat", 120, "o bucată (120 g)", "a piece (120 g)", animal="meat"),
    FoodSpec("chicken_breast", 171477, "Piept de pui la cuptor", "Roasted chicken breast", "poultry", 120, "o bucată (120 g)", "a piece (120 g)", animal="poultry"),
    FoodSpec("chicken_thigh", 172388, "Pulpă de pui la cuptor (fără piele)", "Roasted chicken thigh, skinless", "poultry", 120, "o bucată (120 g)",
             "a piece (120 g)", animal="poultry"),
    FoodSpec("turkey_breast", 171496, "Piept de curcan la cuptor", "Roasted turkey breast", "poultry", 120, "o bucată (120 g)", "a piece (120 g)", animal="poultry"),
    FoodSpec("beef_liver", 168627, "Ficat de vită gătit", "Beef liver, cooked", "offal", 100, "o porție (100 g)", "a serving (100 g)",
             animal="meat", flags=("liver",)),
    FoodSpec("chicken_liver", 171061, "Ficat de pui gătit", "Chicken liver, cooked", "offal", 100, "o porție (100 g)", "a serving (100 g)",
             animal="poultry", flags=("liver",)),
    FoodSpec("ham", 173864, "Șuncă feliată", "Sliced ham", "processed_meat", 50, "3 felii (50 g)", "3 slices (50 g)", animal="meat",
             flags=("ultra_processed",)),
    FoodSpec("salami", 174603, "Salam italian", "Italian salami", "processed_meat", 30, "5 felii (30 g)", "5 slices (30 g)", animal="meat",
             flags=("ultra_processed",)),
    FoodSpec("frankfurter", 173862, "Crenvurști de vită", "Beef frankfurters", "processed_meat", 50, "un crenvurst (50 g)", "one frankfurter (50 g)",
             animal="meat", flags=("ultra_processed",)),
    # --- Ouă (1 buc = 50 g) ---
    FoodSpec("egg_boiled", 173424, "Ou fiert tare", "Hard-boiled egg", "eggs", 50, "un ou (50 g)", "one egg (50 g)", animal="egg", allergens=("oua",)),
    # --- Lactate ---
    FoodSpec("milk_whole", 172217, "Lapte integral (nefortificat)", "Whole milk (unfortified)", "dairy", 250, "un pahar (250 ml)", "a glass (250 ml)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("milk_semi", 172205, "Lapte 2% grăsime (nefortificat)", "2% milk (unfortified)", "dairy", 250, "un pahar (250 ml)", "a glass (250 ml)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("yogurt_plain", 171284, "Iaurt natural din lapte integral", "Plain whole-milk yogurt", "dairy", 150, "un pahar (150 g)", "a pot (150 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("yogurt_greek", 170894, "Iaurt grecesc degresat", "Nonfat Greek yogurt", "dairy", 150, "un pahar (150 g)", "a pot (150 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("cottage_cheese", 172182, "Brânză de vaci 2%", "Cottage cheese 2%", "cheese", 100, "o porție (100 g)", "a serving (100 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("ricotta", 171248, "Ricotta semidegresată", "Part-skim ricotta", "cheese", 60, "o porție (60 g)", "a serving (60 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("cheddar", 173414, "Cașcaval cheddar", "Cheddar cheese", "cheese", 30, "o felie groasă (30 g)", "a thick slice (30 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("mozzarella", 170847, "Mozzarella semidegresată", "Part-skim mozzarella", "cheese", 30, "o felie (30 g)", "a slice (30 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("feta", 173420, "Brânză feta", "Feta cheese", "cheese", 30, "o felie (30 g)", "a slice (30 g)", animal="dairy", allergens=DAIRY),
    FoodSpec("parmesan", 170848, "Parmezan", "Parmesan", "cheese", 15, "o lingură rasă (15 g)", "a grated tablespoon (15 g)",
             animal="dairy", allergens=DAIRY),
    FoodSpec("brie", 172177, "Brânză Brie", "Brie cheese", "cheese", 30, "o felie (30 g)", "a slice (30 g)", animal="dairy", allergens=DAIRY,
             flags=("soft_mould_cheese",)),
    FoodSpec("camembert", 172178, "Brânză Camembert", "Camembert cheese", "cheese", 30, "o felie (30 g)", "a slice (30 g)", animal="dairy",
             allergens=DAIRY, flags=("soft_mould_cheese",)),
    # --- Băuturi vegetale ---
    FoodSpec("soy_milk_fortified", 175215, "Lapte de soia neîndulcit, fortificat (Ca, vitaminele A, D, B12)",
             "Unsweetened soy milk, fortified (Ca, vitamins A, D, B12)", "plant_milks", 250, "un pahar (250 ml)", "a glass (250 ml)",
             allergens=("soia",)),
    FoodSpec("almond_milk", 174832, "Băutură de migdale neîndulcită, fortificată (Ca, vitamina D)", "Unsweetened almond drink, fortified (Ca, vitamin D)", "plant_milks", 250, "un pahar (250 ml)",
             "a glass (250 ml)", allergens=NUT),
    # --- Cereale integrale ---
    FoodSpec("oats", 173904, "Fulgi de ovăz (nefortificați)", "Rolled oats (unfortified)", "whole_grains", 40, "4 linguri (40 g, crude)",
             "4 tablespoons (40 g, dry)", allergens=GLUTEN),
    FoodSpec("quinoa", 168917, "Quinoa fiartă", "Cooked quinoa", "whole_grains", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("brown_rice", 169704, "Orez brun fiert", "Cooked brown rice", "whole_grains", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("buckwheat", 170686, "Hrișcă fiartă", "Cooked buckwheat", "whole_grains", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("millet", 168871, "Mei fiert", "Cooked millet", "whole_grains", 150, "un castron mic (150 g)", "a small bowl (150 g)"),
    FoodSpec("bulgur", 170287, "Bulgur fiert", "Cooked bulgur", "whole_grains", 150, "un castron mic (150 g)", "a small bowl (150 g)", allergens=GLUTEN),
    FoodSpec("wholewheat_pasta", 168910, "Paste integrale fierte", "Cooked whole-wheat pasta", "whole_grains", 180, "o farfurie (180 g)",
             "a plate (180 g)", allergens=GLUTEN),
    FoodSpec("wholewheat_bread", 172688, "Pâine integrală", "Whole-wheat bread", "whole_grains", 40, "o felie (40 g)", "one slice (40 g)",
             allergens=GLUTEN),
    FoodSpec("rye_bread", 172684, "Pâine de secară", "Rye bread", "whole_grains", 40, "o felie (40 g)", "one slice (40 g)", allergens=GLUTEN),
    # --- Cereale rafinate și patiserie ---
    FoodSpec("white_rice", 168878, "Orez alb fiert", "Cooked white rice", "refined_grains", 150, "un castron mic (150 g)", "a small bowl (150 g)",
             flags=("refined_grain", "us_enriched")),
    FoodSpec("white_pasta", 169737, "Paste albe fierte", "Cooked white pasta", "refined_grains", 180, "o farfurie (180 g)", "a plate (180 g)",
             allergens=GLUTEN, flags=("refined_grain", "us_enriched")),
    FoodSpec("white_bread", 174924, "Pâine albă", "White bread", "refined_grains", 40, "o felie (40 g)", "one slice (40 g)",
             allergens=GLUTEN, flags=("refined_grain", "ultra_processed", "us_enriched")),
    FoodSpec("bagel", 174899, "Bagel simplu", "Plain bagel", "bakery", 100, "un bagel (100 g)", "one bagel (100 g)",
             allergens=GLUTEN, flags=("refined_grain", "ultra_processed", "us_enriched")),
    FoodSpec("croutons", 172752, "Crutoane condimentate", "Seasoned croutons", "bakery", 15, "o mână (15 g)", "a handful (15 g)",
             allergens=GLUTEN, flags=("refined_grain", "ultra_processed", "us_enriched")),
    FoodSpec("pancakes", 175009, "Clătite americane (de casă)", "Homemade pancakes", "bakery", 80, "2 clătite mici (80 g)", "2 small pancakes (80 g)",
             allergens=GLUTEN + ("oua",) + DAIRY, flags=("refined_grain",)),
    FoodSpec("blueberry_muffin", 172765, "Brioșă cu afine", "Blueberry muffin", "bakery", 110, "o brioșă (110 g)", "one muffin (110 g)",
             allergens=GLUTEN + ("oua",) + DAIRY, flags=("refined_grain", "ultra_processed", "added_sugar", "us_enriched")),
    # --- Dulciuri și gustări (pentru contrast: trebuie să piardă la scor) ---
    FoodSpec("dark_chocolate", 170273, "Ciocolată neagră 70–85%", "Dark chocolate 70–85%", "sweets_snacks", 20, "2 pătrățele (20 g)",
             "2 squares (20 g)", flags=("added_sugar",)),
    FoodSpec("milk_chocolate", 167587, "Ciocolată cu lapte", "Milk chocolate", "sweets_snacks", 20, "2 pătrățele (20 g)", "2 squares (20 g)",
             allergens=DAIRY, flags=("added_sugar", "ultra_processed")),
    FoodSpec("potato_chips", 169677, "Chipsuri din cartofi, sărate", "Salted potato chips", "sweets_snacks", 30, "o pungă mică (30 g)",
             "a small bag (30 g)", flags=("ultra_processed",)),
    FoodSpec("chocolate_chip_cookies", 172716, "Biscuiți cu bucăți de ciocolată", "Chocolate chip cookies", "sweets_snacks", 30, "2 biscuiți (30 g)",
             "2 cookies (30 g)", allergens=GLUTEN + DAIRY + ("oua",), flags=("refined_grain", "ultra_processed", "added_sugar", "us_enriched")),
)
