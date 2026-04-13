
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
from domain.models import UserProfile, FoodItem, LabResultItem
from services.medical_rules_loader import (
    load_medical_rules_config,
    normalize_clinical_text,
    resolve_allergy_token,
)


class NutrientType(str, Enum):
    """Tipuri de nutrienți suportați conform tabelului"""
    IRON = "iron"
    VITAMIN_D = "vitamin_d"
    VITAMIN_B12 = "vitamin_b12"
    FOLATE = "folate"
    CALCIUM = "calcium"
    MAGNESIUM = "magnesium"
    ZINC = "zinc"
    VITAMIN_A = "vitamin_a"
    VITAMIN_C = "vitamin_c"
    IODINE = "iodine"
    VITAMIN_K = "vitamin_k"
    POTASSIUM = "potassium"


class ScopeType(str, Enum):
    """Tipuri de scopuri (contexturi) pentru reguli"""
    # Tipuri de dietă
    DIET_VEGAN = "diet_vegan"
    DIET_VEGETARIAN = "diet_vegetarian"
    DIET_OMNIVORE = "diet_omnivore"
    DIET_PESCATARIAN = "diet_pescatarian"
    
    # Restricții alimentare
    LACTOSE_INTOLERANCE = "lactose_intolerance"
    GLUTEN_SENSITIVITY = "gluten_sensitivity"
    
    # Condiții medicale
    PREGNANCY = "pregnancy"
    OSTEOPOROSIS_RISK = "osteoporosis_risk"
    ELDERLY = "elderly"
    MALABSORPTION = "malabsorption"
    
    # Stil de viață
    LOW_SUN_EXPOSURE = "low_sun_exposure"
    HIGH_ACTIVITY = "high_activity"
    SMOKER = "smoker"
    TEA_COFFEE_MEALS = "tea_coffee_meals"
    
    # Altele
    HIGH_BMI = "high_bmi"
    LOW_VEGETABLE_INTAKE = "low_vegetable_intake"
    LOW_SALTED_IOIDIZED = "low_salted_iodized"
    THYROID_ISSUES = "thyroid_issues"
    RECENT_ANTIBIOTICS = "recent_antibiotics"
    HYPERTENSION = "hypertension"


@dataclass
class ScopedRule:
    nutrient: NutrientType
    scope: ScopeType
    weight: float  # 0.2 - 1.0
    recommended_foods: List[str]  # Lista de alimente recomandate
    explanation_template: str  # Template pentru explicație
    clinical_threshold: Optional[float] = None  # Prag biomarker (ex: ferritin < 30)


@dataclass
class ScopedRuleResult:
    rule: ScopedRule
    matched: bool
    score: float
    explanation: str
    context: str


class ScopedRulesEngine:
    def __init__(self):
        self.rules = self._initialize_rules()
        self.medical_rules_config: Dict[str, Any] = load_medical_rules_config()
    
    def _initialize_rules(self) -> Dict[NutrientType, List[ScopedRule]]:
        rules = {}
        
        # FIER - Ferritin < 30 ng/mL
        rules[NutrientType.IRON] = [
            ScopedRule(
                nutrient=NutrientType.IRON,
                scope=ScopeType.DIET_VEGAN,
                weight=1.0,
                recommended_foods=['linte', 'năut', 'spanac'],
                explanation_template="Pentru că ești vegan și este indicat aport suplimentar de fier pe baza analizelor disponibile, recomandăm {foods} + vitamina C pentru absorbție mai bună.",
                clinical_threshold=30.0
            ),
            ScopedRule(
                nutrient=NutrientType.IRON,
                scope=ScopeType.DIET_OMNIVORE,
                weight=1.0,
                recommended_foods=['carne roșie', 'ficat'],
                explanation_template="Pentru că ai dietă omnivoră și este indicat aport suplimentar de fier pe baza analizelor disponibile, recomandăm {foods}.",
                clinical_threshold=30.0
            ),
            ScopedRule(
                nutrient=NutrientType.IRON,
                scope=ScopeType.TEA_COFFEE_MEALS,
                weight=0.6,
                recommended_foods=[],
                explanation_template="Evită ceaiul și cafeaua la masă pentru a îmbunătăți absorbția fierului.",
                clinical_threshold=30.0
            ),
        ]
        
        # VITAMINA D - 25(OH)D < 20 ng/mL
        rules[NutrientType.VITAMIN_D] = [
            ScopedRule(
                nutrient=NutrientType.VITAMIN_D,
                scope=ScopeType.LOW_SUN_EXPOSURE,
                weight=1.0,
                recommended_foods=['expunere solară', 'alimente fortificate'],
                explanation_template="Pentru că ai expunere solară redusă și este indicat aport de vitamina D pe baza contextului clinic, recomandăm expunere solară + alimente fortificate.",
                clinical_threshold=20.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_D,
                scope=ScopeType.DIET_VEGAN,
                weight=1.0,
                recommended_foods=['ciuperci UV', 'lapte vegetal fortificat'],
                explanation_template="Pentru că ești vegan și este indicat aport de vitamina D pe baza analizelor disponibile, recomandăm {foods}.",
                clinical_threshold=20.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_D,
                scope=ScopeType.HIGH_BMI,
                weight=0.6,
                recommended_foods=['aport crescut de vitamina D'],
                explanation_template="Pentru că ai IMC crescut și este indicat aport de vitamina D conform analizelor disponibile, recomandăm aport crescut de vitamina D.",
                clinical_threshold=20.0
            ),
        ]
        
        # VITAMINA B12 - B12 < 200 pg/mL
        rules[NutrientType.VITAMIN_B12] = [
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.DIET_VEGAN,
                weight=1.0,
                recommended_foods=['alimente fortificate', 'drojdie inactivă'],
                explanation_template="Pentru că ești vegan și este indicat aport de vitamina B12 pe baza analizelor disponibile, recomandăm {foods}.",
                clinical_threshold=200.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.ELDERLY,
                weight=0.8,
                recommended_foods=['suplimentare recomandată'],
                explanation_template="Pentru că ești în vârstă și este indicat aport de vitamina B12 conform contextului, recomandăm suplimentare.",
                clinical_threshold=200.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.MALABSORPTION,
                weight=0.8,
                recommended_foods=['suplimentare recomandată'],
                explanation_template="Pentru că ai malabsorbție și este indicat aport de vitamina B12 conform contextului, recomandăm suplimentare.",
                clinical_threshold=200.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.DIET_OMNIVORE,
                weight=0.6,
                recommended_foods=['carne', 'pește', 'lactate'],
                explanation_template="Pentru că ai dietă omnivoră și este indicat aport de vitamina B12 pe baza analizelor disponibile, recomandăm {foods}.",
                clinical_threshold=200.0
            ),
        ]
        
        # FOLAT (B9) - Folat < 3 ng/mL
        rules[NutrientType.FOLATE] = [
            ScopedRule(
                nutrient=NutrientType.FOLATE,
                scope=ScopeType.PREGNANCY,
                weight=1.0,
                recommended_foods=['frunze verzi', 'leguminoase'],
                explanation_template="Pentru că ești în sarcină și ai deficit de folat (Folat < 3 ng/mL), recomandăm {foods}.",
                clinical_threshold=3.0
            ),
            ScopedRule(
                nutrient=NutrientType.FOLATE,
                scope=ScopeType.LOW_VEGETABLE_INTAKE,
                weight=0.8,
                recommended_foods=['avocado', 'citrice'],
                explanation_template="Pentru că ai aport vegetal scăzut și deficit de folat, recomandăm {foods}.",
                clinical_threshold=3.0
            ),
        ]
        
        # CALCIU - < 8.5 mg/dL
        rules[NutrientType.CALCIUM] = [
            ScopedRule(
                nutrient=NutrientType.CALCIUM,
                scope=ScopeType.LACTOSE_INTOLERANCE,
                weight=1.0,
                recommended_foods=['kale', 'broccoli', 'migdale'],
                explanation_template="Pentru că ai intoleranță la lactoză și deficit de calciu (< 8.5 mg/dL), recomandăm {foods}.",
                clinical_threshold=8.5
            ),
            ScopedRule(
                nutrient=NutrientType.CALCIUM,
                scope=ScopeType.DIET_OMNIVORE,
                weight=0.8,
                recommended_foods=['lapte', 'iaurt', 'brânză'],
                explanation_template="Pentru că ai dietă omnivoră și deficit de calciu, recomandăm {foods}.",
                clinical_threshold=8.5
            ),
            ScopedRule(
                nutrient=NutrientType.CALCIUM,
                scope=ScopeType.OSTEOPOROSIS_RISK,
                weight=1.0,
                recommended_foods=['calciu + vitamina D'],
                explanation_template="Pentru că ai risc de osteoporoză și deficit de calciu, recomandăm calciu + vitamina D.",
                clinical_threshold=8.5
            ),
        ]
        
        # MAGNEZIU - Mg < 1.7 mg/dL
        rules[NutrientType.MAGNESIUM] = [
            ScopedRule(
                nutrient=NutrientType.MAGNESIUM,
                scope=ScopeType.HIGH_ACTIVITY,
                weight=0.8,
                recommended_foods=['nuci', 'cereale integrale'],
                explanation_template="Pentru că ai activitate intensă și deficit de magneziu (Mg < 1.7 mg/dL), recomandăm {foods}.",
                clinical_threshold=1.7
            ),
            ScopedRule(
                nutrient=NutrientType.MAGNESIUM,
                scope=ScopeType.LOW_VEGETABLE_INTAKE,
                weight=1.0,
                recommended_foods=['frunze verzi'],
                explanation_template="Pentru că ai aport vegetal scăzut și deficit de magneziu, recomandăm {foods}.",
                clinical_threshold=1.7
            ),
        ]
        
        # ZINC - < 70 μg/dL
        rules[NutrientType.ZINC] = [
            ScopedRule(
                nutrient=NutrientType.ZINC,
                scope=ScopeType.DIET_VEGAN,
                weight=1.0,
                recommended_foods=['fasole', 'linte', 'semințe'],
                explanation_template="Pentru că ești vegan/vegetarian și ai deficit de zinc (< 70 μg/dL), recomandăm {foods}.",
                clinical_threshold=70.0
            ),
            ScopedRule(
                nutrient=NutrientType.ZINC,
                scope=ScopeType.DIET_VEGETARIAN,
                weight=1.0,
                recommended_foods=['fasole', 'linte', 'semințe'],
                explanation_template="Pentru că ești vegan/vegetarian și ai deficit de zinc, recomandăm {foods}.",
                clinical_threshold=70.0
            ),
            ScopedRule(
                nutrient=NutrientType.ZINC,
                scope=ScopeType.DIET_OMNIVORE,
                weight=0.8,
                recommended_foods=['carne', 'fructe de mare'],
                explanation_template="Pentru că ai dietă omnivoră și deficit de zinc, recomandăm {foods}.",
                clinical_threshold=70.0
            ),
        ]
        
        # VITAMINA A - < 20 μg/dL
        rules[NutrientType.VITAMIN_A] = [
            ScopedRule(
                nutrient=NutrientType.VITAMIN_A,
                scope=ScopeType.LOW_VEGETABLE_INTAKE,
                weight=1.0,
                recommended_foods=['morcovi', 'spanac'],
                explanation_template="Pentru că ai aport scăzut de legume și deficit de vitamina A (< 20 μg/dL), recomandăm {foods}.",
                clinical_threshold=20.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_A,
                scope=ScopeType.DIET_OMNIVORE,
                weight=0.6,
                recommended_foods=['ficat în cantități mici'],
                explanation_template="Pentru că ai dietă omnivoră și deficit de vitamina A, recomandăm ficat în cantități mici.",
                clinical_threshold=20.0
            ),
        ]
        
        # VITAMINA C - < 23 μmol/L
        rules[NutrientType.VITAMIN_C] = [
            ScopedRule(
                nutrient=NutrientType.VITAMIN_C,
                scope=ScopeType.SMOKER,
                weight=1.0,
                recommended_foods=['citrice', 'ardei gras'],
                explanation_template="Pentru că fumezi și ai deficit de vitamina C (< 23 μmol/L), recomandăm {foods}.",
                clinical_threshold=23.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_C,
                scope=ScopeType.LOW_VEGETABLE_INTAKE,
                weight=0.8,
                recommended_foods=['roșii', 'broccoli'],
                explanation_template="Pentru că ai aport scăzut de fructe/legume și deficit de vitamina C, recomandăm {foods}.",
                clinical_threshold=23.0
            ),
        ]
        
        # IOD - < 100 μg/L
        rules[NutrientType.IODINE] = [
            ScopedRule(
                nutrient=NutrientType.IODINE,
                scope=ScopeType.LOW_SALTED_IOIDIZED,
                weight=1.0,
                recommended_foods=['sare iodată'],
                explanation_template="Pentru că ai consum redus de sare iodată și deficit de iod (< 100 μg/L), recomandăm folosirea sării iodate.",
                clinical_threshold=100.0
            ),
            ScopedRule(
                nutrient=NutrientType.IODINE,
                scope=ScopeType.DIET_VEGAN,
                weight=0.8,
                recommended_foods=['alge marine'],
                explanation_template="Pentru că ești vegan și ai deficit de iod, recomandăm {foods}.",
                clinical_threshold=100.0
            ),
            ScopedRule(
                nutrient=NutrientType.IODINE,
                scope=ScopeType.THYROID_ISSUES,
                weight=0.6,
                recommended_foods=['aport stabil'],
                explanation_template="Pentru că ai afecțiuni tiroidiene și deficit de iod, recomandăm aport stabil.",
                clinical_threshold=100.0
            ),
        ]
        
        # VITAMINA K - PT/INR crescut
        rules[NutrientType.VITAMIN_K] = [
            ScopedRule(
                nutrient=NutrientType.VITAMIN_K,
                scope=ScopeType.LOW_VEGETABLE_INTAKE,
                weight=1.0,
                recommended_foods=['kale', 'broccoli'],
                explanation_template="Pentru că ai aport scăzut de legume verzi și coagulare deficitară (PT/INR crescut), recomandăm {foods}.",
                clinical_threshold=None  # PT/INR nu este un prag numeric direct
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_K,
                scope=ScopeType.RECENT_ANTIBIOTICS,
                weight=0.8,
                recommended_foods=['alimente fermentate'],
                explanation_template="Pentru că ai luat antibiotice recent și coagulare deficitară, recomandăm {foods}.",
                clinical_threshold=None
            ),
        ]
        
        # POTASIU - K < 3.5 mmol/L
        rules[NutrientType.POTASSIUM] = [
            ScopedRule(
                nutrient=NutrientType.POTASSIUM,
                scope=ScopeType.HIGH_ACTIVITY,
                weight=0.8,
                recommended_foods=['banane', 'cartofi'],
                explanation_template="Pentru că ești sportiv/transpirație crescută și ai hipokaliemie (K < 3.5 mmol/L), recomandăm {foods}.",
                clinical_threshold=3.5
            ),
            ScopedRule(
                nutrient=NutrientType.POTASSIUM,
                scope=ScopeType.HYPERTENSION,
                weight=1.0,
                recommended_foods=['alimente bogate în potasiu'],
                explanation_template="Pentru că ai hipertensiune și hipokaliemie, recomandăm alimente bogate în potasiu.",
                clinical_threshold=3.5
            ),
        ]
        
        return rules
    
    def get_user_scopes(self, user: UserProfile, lab_results: Optional[LabResultItem] = None) -> List[ScopeType]:
        scopes = []
        
        if user.diet_type == 'vegan':
            scopes.append(ScopeType.DIET_VEGAN)
        elif user.diet_type == 'vegetarian':
            scopes.append(ScopeType.DIET_VEGETARIAN)
        elif user.diet_type == 'omnivore':
            scopes.append(ScopeType.DIET_OMNIVORE)
        elif user.diet_type == 'pescatarian':
            scopes.append(ScopeType.DIET_PESCATARIAN)
        
        if user.allergies:
            allergies_lower = user.allergies.lower()
            if 'lactoza' in allergies_lower or 'lactoză' in allergies_lower or 'lactate' in allergies_lower:
                scopes.append(ScopeType.LACTOSE_INTOLERANCE)
            if 'gluten' in allergies_lower:
                scopes.append(ScopeType.GLUTEN_SENSITIVITY)
        
        if user.medical_conditions:
            conditions_lower = user.medical_conditions.lower()
            if 'sarcină' in conditions_lower or 'pregnant' in conditions_lower:
                scopes.append(ScopeType.PREGNANCY)
            if 'osteoporoză' in conditions_lower or 'osteoporoza' in conditions_lower:
                scopes.append(ScopeType.OSTEOPOROSIS_RISK)
            if 'hipertensiune' in conditions_lower or 'tensiune' in conditions_lower:
                scopes.append(ScopeType.HYPERTENSION)
            if 'tiroid' in conditions_lower or 'tiroida' in conditions_lower:
                scopes.append(ScopeType.THYROID_ISSUES)
            if 'fumător' in conditions_lower or 'smoker' in conditions_lower or 'fumezi' in conditions_lower:
                scopes.append(ScopeType.SMOKER)
            if 'malabsorbție' in conditions_lower or 'malabsorption' in conditions_lower:
                scopes.append(ScopeType.MALABSORPTION)
            if 'antibiotice' in conditions_lower or 'antibiotics' in conditions_lower:
                scopes.append(ScopeType.RECENT_ANTIBIOTICS)
            if 'soare' in conditions_lower or 'sun' in conditions_lower or 'expunere solară' in conditions_lower:
                pass
            elif 'lipsă expunere' in conditions_lower or 'low sun' in conditions_lower:
                scopes.append(ScopeType.LOW_SUN_EXPOSURE)
            if 'legume' in conditions_lower or 'vegetable' in conditions_lower:
                if 'scăzut' in conditions_lower or 'low' in conditions_lower:
                    scopes.append(ScopeType.LOW_VEGETABLE_INTAKE)
            if 'sare' in conditions_lower or 'salt' in conditions_lower:
                if 'scăzut' in conditions_lower or 'low' in conditions_lower or 'iodată' not in conditions_lower:
                    scopes.append(ScopeType.LOW_SALTED_IOIDIZED)
            if 'ceai' in conditions_lower or 'cafea' in conditions_lower or 'tea' in conditions_lower or 'coffee' in conditions_lower:
                if 'masă' in conditions_lower or 'meal' in conditions_lower:
                    scopes.append(ScopeType.TEA_COFFEE_MEALS)
        
        if user.age and user.age >= 65:
            scopes.append(ScopeType.ELDERLY)
        
        if user.activity_level in ['active', 'very_active']:
            scopes.append(ScopeType.HIGH_ACTIVITY)
        
        if user.weight and user.height:
            bmi = user.weight / ((user.height / 100) ** 2)
            if bmi >= 30:
                scopes.append(ScopeType.HIGH_BMI)
        
        if lab_results:
            if lab_results.vitamin_d and lab_results.vitamin_d < 20:
                scopes.append(ScopeType.LOW_SUN_EXPOSURE)
        
        return scopes
    
    def evaluate_rules_for_nutrient(
        self,
        nutrient: NutrientType,
        food: FoodItem,
        user: UserProfile,
        deficit: float,
        lab_results: Optional[LabResultItem] = None
    ) -> List[ScopedRuleResult]:
        """Evaluează regulile pentru un nutrient și returnează cele care se potrivesc"""
        if nutrient not in self.rules:
            return []
        
        if not self._is_compatible(food, user):
            return []
        
        user_scopes = self.get_user_scopes(user, lab_results)
        matching_rules = []
        
        for rule in self.rules[nutrient]:
            if rule.scope not in user_scopes:
                continue
            
            if rule.clinical_threshold is not None and lab_results:
                biomarker_value = self._get_biomarker_value(lab_results, nutrient)
                if biomarker_value is not None and biomarker_value >= rule.clinical_threshold:
                    continue
            
            if not self._is_food_compatible_with_rule(food, rule, user):
                continue
            
            nutrient_value = self._get_nutrient_value(food, nutrient)
            # Dacă nu avem deloc valoare pentru nutrient la acest aliment,
            # nu îl folosim pentru acoperirea deficitului (evităm recomandări cu 0% acoperire).
            if nutrient_value <= 0:
                continue

            food_matches = self._food_matches_recommendations(food, rule.recommended_foods)
            # Dacă există o listă explicită de alimente recomandate și nu se potrivește deloc, trecem peste.
            if rule.recommended_foods and not food_matches:
                continue
            
            base_score = min(10.0, (nutrient_value / max(1, deficit)) * 10)
            weighted_score = base_score * rule.weight
            explanation = self._generate_explanation(rule, food, nutrient_value, deficit, lab_results, user)
            
            matching_rules.append(ScopedRuleResult(
                rule=rule,
                matched=True,
                score=weighted_score,
                explanation=explanation,
                context=self._get_scope_label(rule.scope)
            ))
        
        return matching_rules
    
    def _get_nutrient_value(self, food: FoodItem, nutrient: NutrientType) -> float:
        """Extrage valoarea nutrientului din aliment"""
        mapping = {
            NutrientType.IRON: food.iron or 0,
            NutrientType.CALCIUM: food.calcium or 0,
            NutrientType.MAGNESIUM: food.magnesium or 0,
            NutrientType.ZINC: food.zinc or 0,
            NutrientType.VITAMIN_D: (food.vitamin_d or 0) / 40,
            NutrientType.VITAMIN_B12: food.vitamin_b12 or 0,
            NutrientType.VITAMIN_C: food.vitamin_c or 0,
            NutrientType.FOLATE: food.folate or 0,
            NutrientType.VITAMIN_A: food.vitamin_a or 0,
            NutrientType.IODINE: food.iodine or 0,
            NutrientType.VITAMIN_K: food.vitamin_k or 0,
            NutrientType.POTASSIUM: food.potassium or 0,
        }
        return mapping.get(nutrient, 0)
    
    def _food_matches_recommendations(self, food: FoodItem, recommended_foods: List[str]) -> bool:
        if not recommended_foods:
            return True
        
        food_name_lower = food.name.lower() if food.name else ''
        food_category_lower = food.category.lower() if food.category else ''
        
        for recommended in recommended_foods:
            recommended_lower = recommended.lower()
            if recommended_lower in food_name_lower or recommended_lower in food_category_lower:
                return True
            recommended_words = recommended_lower.split()
            if any(word in food_name_lower or word in food_category_lower for word in recommended_words if len(word) > 3):
                return True
        
        return False
    
    def _generate_explanation(
        self,
        rule: ScopedRule,
        food: FoodItem,
        nutrient_value: float,
        deficit: float,
        lab_results: Optional[LabResultItem] = None,
        user: Optional[UserProfile] = None,
    ) -> str:
        """Generează explicația pentru regulă; nu afirma praguri de laborator dacă valoarea lipsește."""
        context_label = self._get_scope_label(rule.scope)
        biomarker_text = ""

        if lab_results and rule.clinical_threshold is not None:
            biomarker_value = self._get_biomarker_value(lab_results, rule.nutrient)

            if rule.nutrient == NutrientType.IRON:
                ferr = getattr(lab_results, "ferritin", None)
                hb = getattr(lab_results, "hemoglobin", None)
                if ferr is not None and ferr < rule.clinical_threshold:
                    biomarker_text = (
                        f"feritina din analize este {ferr:.1f} ng/mL (sub {rule.clinical_threshold:g} ng/mL)"
                    )
                elif ferr is None and hb is not None:
                    biomarker_text = (
                        f"hemoglobina măsurată este {hb:.1f} g/dL; feritina nu este disponibilă în buletin — "
                        "necesarul de fier este estimat din hemoglobină"
                    )
            elif rule.nutrient == NutrientType.VITAMIN_D:
                if biomarker_value is not None and biomarker_value < rule.clinical_threshold:
                    biomarker_text = (
                        f"vitamina D din analize este {biomarker_value:.1f} ng/mL "
                        f"(sub {rule.clinical_threshold:g} ng/mL)"
                    )
            elif rule.nutrient == NutrientType.VITAMIN_B12:
                if biomarker_value is not None and biomarker_value < rule.clinical_threshold:
                    biomarker_text = (
                        f"vitamina B12 din analize este {biomarker_value:.1f} pg/mL "
                        f"(sub {rule.clinical_threshold:g} pg/mL)"
                    )
            elif biomarker_value is not None:
                if rule.nutrient == NutrientType.CALCIUM:
                    biomarker_text = f"nivelul tău de calciu este scăzut (< {rule.clinical_threshold} mg/dL)"
                elif rule.nutrient == NutrientType.MAGNESIUM:
                    biomarker_text = f"nivelul tău de magneziu este scăzut (< {rule.clinical_threshold} mg/dL)"
                elif rule.nutrient == NutrientType.ZINC:
                    biomarker_text = f"nivelul tău de zinc este scăzut (< {rule.clinical_threshold} μg/dL)"
                elif rule.nutrient == NutrientType.FOLATE:
                    biomarker_text = f"nivelul tău de folat este scăzut (< {rule.clinical_threshold} ng/mL)"
                elif rule.nutrient == NutrientType.VITAMIN_A:
                    biomarker_text = f"nivelul tău de vitamina A este scăzut (< {rule.clinical_threshold} μg/dL)"
                elif rule.nutrient == NutrientType.IODINE:
                    biomarker_text = f"nivelul tău de iod este scăzut (< {rule.clinical_threshold} μg/L)"
                elif rule.nutrient == NutrientType.POTASSIUM:
                    biomarker_text = f"nivelul tău de potasiu este scăzut (< {rule.clinical_threshold} mmol/L)"

        rec_foods = self._recommended_foods_safe_for_user(rule.recommended_foods, user)
        foods_str = ", ".join(rec_foods) if rec_foods else food.name

        tpl = rule.explanation_template
        has_foods_placeholder = "{foods}" in tpl
        if biomarker_text and (rule.recommended_foods or has_foods_placeholder):
            explanation = f"Pentru că {context_label.lower()} și {biomarker_text}, recomandăm {foods_str}."
        elif biomarker_text:
            explanation = f"{tpl.format(foods=foods_str)} ({biomarker_text})."
        else:
            explanation = tpl.format(foods=foods_str)

        if nutrient_value > 0:
            explanation += f" {food.name} conține {nutrient_value:.1f} {self._get_nutrient_unit(rule.nutrient)} per 100g."

        return explanation

    def _recommended_foods_safe_for_user(
        self, recommended: Optional[List[str]], user: Optional[UserProfile]
    ) -> List[str]:
        """Elimină din lista afișată surse tipice interzise de alergiile declarate (ex. pește, ouă)."""
        if not recommended:
            return []
        if not user or not user.allergies:
            return list(recommended)
        parts = [
            normalize_clinical_text(p.strip())
            for p in re.split(r"[,;]", user.allergies)
            if p.strip()
        ]
        fish_al = any(p == "peste" or p.startswith("peste") for p in parts)
        egg_al = any(p in ("oua", "ou", "oue", "eggs", "egg") for p in parts)
        out: List[str] = []
        for item in recommended:
            low = normalize_clinical_text(item)
            skip = False
            if fish_al:
                if any(x in low for x in ("peste", "pesc", "fish", "fructe de mare")):
                    skip = True
            if egg_al:
                if any(x in low for x in ("oua", "ou", "egg", "galbenus")):
                    skip = True
            if not skip:
                out.append(item)
        return out if out else list(recommended)

    def _get_biomarker_value(self, lab_results: Optional[LabResultItem], nutrient: NutrientType) -> Optional[float]:
        """Extrage valoarea biomarkerului pentru nutrient"""
        if lab_results is None:
            return None
        mapping = {
            NutrientType.IRON: lab_results.ferritin,
            NutrientType.CALCIUM: lab_results.calcium,
            NutrientType.MAGNESIUM: lab_results.magnesium,
            NutrientType.ZINC: lab_results.zinc,
            NutrientType.VITAMIN_D: lab_results.vitamin_d,
            NutrientType.VITAMIN_B12: lab_results.vitamin_b12,
            NutrientType.FOLATE: lab_results.folate,
            NutrientType.VITAMIN_A: lab_results.vitamin_a,
            NutrientType.IODINE: lab_results.iodine,
            NutrientType.POTASSIUM: lab_results.potassium,
        }
        return mapping.get(nutrient)
    
    def _get_nutrient_unit(self, nutrient: NutrientType) -> str:
        units = {
            NutrientType.IRON: "mg",
            NutrientType.CALCIUM: "mg",
            NutrientType.MAGNESIUM: "mg",
            NutrientType.ZINC: "mg",
            NutrientType.VITAMIN_D: "IU",
            NutrientType.VITAMIN_B12: "mcg",
            NutrientType.VITAMIN_C: "mg",
            NutrientType.FOLATE: "mcg",
            NutrientType.VITAMIN_A: "mcg",
            NutrientType.IODINE: "mcg",
            NutrientType.VITAMIN_K: "mcg",
            NutrientType.POTASSIUM: "mg",
        }
        return units.get(nutrient, "")
    
    def _get_scope_label(self, scope: ScopeType) -> str:
        labels = {
            ScopeType.DIET_VEGAN: "Dietă vegană",
            ScopeType.DIET_VEGETARIAN: "Dietă vegetariană",
            ScopeType.DIET_OMNIVORE: "Dietă omnivoră",
            ScopeType.DIET_PESCATARIAN: "Dietă pescatariană",
            ScopeType.LACTOSE_INTOLERANCE: "Intoleranță la lactoză",
            ScopeType.GLUTEN_SENSITIVITY: "Sensibilitate la gluten",
            ScopeType.PREGNANCY: "Sarcină",
            ScopeType.OSTEOPOROSIS_RISK: "Risc de osteoporoză",
            ScopeType.ELDERLY: "Vârstnici",
            ScopeType.MALABSORPTION: "Malabsorbție",
            ScopeType.LOW_SUN_EXPOSURE: "Expunere solară redusă",
            ScopeType.HIGH_ACTIVITY: "Activitate intensă",
            ScopeType.SMOKER: "Fumător",
            ScopeType.TEA_COFFEE_MEALS: "Ceai/cafea la masă",
            ScopeType.HIGH_BMI: "IMC crescut",
            ScopeType.LOW_VEGETABLE_INTAKE: "Aport vegetal scăzut",
            ScopeType.LOW_SALTED_IOIDIZED: "Consum redus sare iodată",
            ScopeType.THYROID_ISSUES: "Afecțiuni tiroidiene",
            ScopeType.RECENT_ANTIBIOTICS: "Antibiotice recente",
            ScopeType.HYPERTENSION: "Hipertensiune",
        }
        return labels.get(scope, str(scope))
    
    def _parse_food_restrictions(self, medical_conditions: str) -> Dict[str, List[str]]:
        """Parsează condițiile medicale și identifică interziceri de alimente"""
        if not medical_conditions:
            return {'forbidden_categories': [], 'forbidden_keywords': []}
        
        conditions_lower = normalize_clinical_text(medical_conditions)
        forbidden_categories = []
        forbidden_keywords = []

        for rule in self.medical_rules_config.get("condition_food_rules", []):
            condition_patterns = [normalize_clinical_text(x) for x in rule.get("condition_patterns", [])]
            if any(p and p in conditions_lower for p in condition_patterns):
                for raw_kw in rule.get("avoid_keywords", []):
                    kn = normalize_clinical_text(raw_kw)
                    if kn and kn not in forbidden_keywords:
                        forbidden_keywords.append(kn)
        
        category_patterns = {
            'legume': [
                'nu mananc legume', 'nu mănânc legume', 'nu mananc leguma', 'nu mănânc leguma',
                'fara legume', 'fără legume', 'no vegetables', 'no veggies',
                'evit legume', 'interzis legume', 'nu pot legume', 'nu pot mânca legume'
            ],
            'fructe': [
                'nu mananc fructe', 'nu mănânc fructe', 'nu mananc fructa', 'nu mănânc fructa',
                'fara fructe', 'fără fructe', 'no fruits', 'no fruit',
                'evit fructe', 'interzis fructe', 'nu pot fructe', 'nu pot mânca fructe'
            ],
            'cereale': [
                'nu mananc cereale', 'nu mănânc cereale', 'nu mananc cereala', 'nu mănânc cereala',
                'fara cereale', 'fără cereale', 'no grains', 'no cereals',
                'evit cereale', 'interzis cereale', 'nu pot cereale', 'nu pot mânca cereale'
            ],
            'carne': [
                'nu mananc carne', 'nu mănânc carne', 'fara carne', 'fără carne',
                'no meat', 'no red meat', 'evit carne', 'interzis carne',
                'nu pot carne', 'nu pot mânca carne'
            ],
            'peste': [
                'nu mananc peste', 'nu mănânc pește', 'nu mananc pesti', 'nu mănânc pești',
                'fara peste', 'fără pește', 'no fish', 'no seafood',
                'evit peste', 'interzis peste', 'nu pot peste', 'nu pot mânca peste'
            ],
            'lactate': [
                'nu mananc lactate', 'nu mănânc lactate', 'nu mananc lapte', 'nu mănânc lapte',
                'fara lactate', 'fără lactate', 'fara lapte', 'fără lapte',
                'no dairy', 'no milk', 'evit lactate', 'interzis lactate'
            ],
            'semințe': [
                'nu mananc seminte', 'nu mănânc semințe', 'nu am voie seminte', 'nu am voie semințe',
                'fara seminte', 'fără semințe', 'no seeds', 'evit seminte', 'interzis seminte'
            ],
            'nuci': [
                'nu mananc nuci', 'nu mănânc nuci', 'nu mananc nuca', 'nu mănânc nucă',
                'fara nuci', 'fără nuci', 'no nuts', 'evit nuci', 'interzis nuci'
            ],
            'leguminoase': [
                'nu mananc leguminoase', 'nu mănânc leguminoase', 'nu mananc fasole', 'nu mănânc fasole',
                'nu mananc linte', 'nu mănânc linte', 'fara leguminoase', 'fără leguminoase',
                'no legumes', 'no beans', 'evit leguminoase', 'interzis leguminoase'
            ],
            'ouă': [
                'nu mananc oua', 'nu mănânc ouă', 'nu mananc ou', 'nu mănânc ou',
                'fara oua', 'fără ouă', 'no eggs', 'evit oua', 'interzis oua'
            ],
            'soia': [
                'nu mananc soia', 'nu mănânc soia', 'fara soia', 'fără soia',
                'no soy', 'evit soia', 'interzis soia'
            ]
        }
        
        for category, patterns in category_patterns.items():
            if any(pattern in conditions_lower for pattern in patterns):
                forbidden_categories.append(category)
        
        general_patterns = [
            r'nu\s+(?:mănânc|mananc|pot\s+mânca|pot\s+mananca)\s+([a-zăâîșț]+)',
            r'fără\s+([a-zăâîșț]+)',
            r'fara\s+([a-zăâîșț]+)',
            r'evit\s+([a-zăâîșț]+)',
            r'interzis\s+([a-zăâîșț]+)'
        ]
        
        for pattern in general_patterns:
            matches = re.findall(pattern, conditions_lower)
            for match in matches:
                if match and len(match) > 2:
                    forbidden_keywords.append(match)
        
        simple_food_keywords = {
            'ouă': ['ouă', 'oua', 'ou', 'eggs'],
            'legume': ['legume', 'leguma', 'vegetable', 'vegetables'],
            'fructe': ['fructe', 'fructa', 'fruit', 'fruits'],
            'cereale': ['cereale', 'cereala', 'grain', 'grains', 'cereal'],
            'carne': ['carne', 'meat'],
            'peste': ['peste', 'pește', 'fish', 'seafood'],
            'lactate': ['lactate', 'lapte', 'dairy', 'milk'],
            'semințe': ['semințe', 'seminte', 'seeds'],
            'nuci': ['nuci', 'nucă', 'nuts'],
            'leguminoase': ['leguminoase', 'fasole', 'linte', 'legumes', 'beans'],
            'soia': ['soia', 'soy'],
            'gluten': ['gluten', 'grâu', 'grau', 'wheat']
        }
        
        words = re.split(r'[,\s\.;]+', conditions_lower)
        for word in words:
            word = word.strip()
            if len(word) > 2:
                for category, keywords in simple_food_keywords.items():
                    if word in keywords:
                        if category not in forbidden_categories:
                            if not any(positive in conditions_lower for positive in [
                                'pot mânca', 'pot mananca', 'pot consuma', 'mănânc', 'mananc',
                                'consum', 'mănâncă', 'mananca'
                            ]):
                                forbidden_categories.append(category)
                                break
        
        return {
            'forbidden_categories': forbidden_categories,
            'forbidden_keywords': forbidden_keywords
        }
    
    def _is_compatible(self, food: FoodItem, user: UserProfile) -> bool:
        """Verifică compatibilitatea alimentului cu restricțiile utilizatorului"""
        if user.diet_type == 'vegetarian' or user.diet_type == 'vegan':
            meat_categories = ['carne', 'pui', 'porc', 'vita', 'miel', 'pește', 'peste']
            if any(cat in food.category.lower() for cat in meat_categories):
                return False
        
        if user.diet_type == 'vegan':
            dairy_categories = ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt']
            if any(cat in food.category.lower() for cat in dairy_categories):
                return False
        
        if user.diet_type == 'pescatarian':
            meat_categories = ['carne', 'pui', 'porc', 'vita', 'miel']
            if any(cat in food.category.lower() for cat in meat_categories):
                return False
        
        if user.allergies:
            user_allergies = [
                a.strip().lower()
                for a in re.split(r'[,;]+', user.allergies)
                if a.strip()
            ]
            food_name_lower = normalize_clinical_text(food.name or '')
            food_category_lower = normalize_clinical_text(food.category or '')
            
            allergy_mappings = {
                'lactoza': {
                    'categories': ['lactate', 'lapte', 'branza', 'branzeturi'],
                    'keywords': ['lactate', 'lapte', 'branza', 'brânză', 'branzeturi', 'brânzeturi', 
                                'iaurt', 'smantana', 'smântână', 'unt', 'telemea', 
                                'cascaval', 'cașcaval', 'ricotta', 'mozzarella', 'gorgonzola', 
                                'parmezan', 'cheddar', 'feta', 'brie', 'camembert', 'dairy', 'lactos']
                },
                'lactoză': {
                    'categories': ['lactate', 'lapte', 'branza', 'branzeturi'],
                    'keywords': ['lactate', 'lapte', 'branza', 'brânză', 'branzeturi', 'brânzeturi', 
                                'iaurt', 'smantana', 'smântână', 'unt', 'telemea', 
                                'cascaval', 'cașcaval', 'ricotta', 'mozzarella', 'gorgonzola', 
                                'parmezan', 'cheddar', 'feta', 'brie', 'camembert', 'dairy', 'lactos']
                },
                'lactate': {
                    'categories': ['lactate', 'lapte', 'branza', 'branzeturi'],
                    'keywords': ['lactate', 'lapte', 'branza', 'brânză', 'branzeturi', 'brânzeturi', 
                                'iaurt', 'smantana', 'smântână', 'unt', 'telemea', 
                                'cascaval', 'cașcaval', 'ricotta', 'mozzarella', 'gorgonzola', 
                                'parmezan', 'cheddar', 'feta', 'brie', 'camembert', 'dairy', 'lactos']
                },
                # Gluten
                'gluten': {
                    'categories': ['cereale', 'paini', 'paste', 'faina'],
                    'keywords': ['gluten', 'grâu', 'grau', 'grău', 'făină', 'faina', 'făină', 
                                'pâine', 'paine', 'pâini', 'paste', 'spaghete', 'macaroane', 
                                'tortilla', 'cereale', 'wheat', 'barley', 'rye', 'seitan', 
                                'ovăz', 'orz', 'secară', 'malț']
                },
                'nuci': {
                    'categories': [],
                    'keywords': [
                        'nuci', 'nuca', 'alune', 'migdale', 'fistic',
                        'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut',
                        'pignoli', 'pinoli', 'nuci de pin', 'nuca de pin',
                        'pesto', 'kibbeh', 'baklava', 'nougat', 'gianduja', 'marzipan', 'martipan',
                    ]
                },
                'nucă': {
                    'categories': [],
                    'keywords': [
                        'nuci', 'nuca', 'alune', 'migdale', 'fistic',
                        'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut',
                        'pignoli', 'pinoli', 'nuci de pin', 'nuca de pin',
                        'pesto', 'kibbeh', 'baklava', 'nougat', 'gianduja', 'marzipan', 'martipan',
                    ]
                },
                'semințe': {
                    'categories': [],
                    'keywords': ['semințe', 'seminte', 'semințe de', 'seminte de', 'chia', 'flax',
                                'in', 'sunflower', 'pumpkin', 'sesame', 'sezam', 'semințe de in',
                                'semințe de chia', 'semințe de dovleac', 'semințe de susan']
                },
                'seminte': {
                    'categories': [],
                    'keywords': ['semințe', 'seminte', 'semințe de', 'seminte de', 'chia', 'flax',
                                'in', 'sunflower', 'pumpkin', 'sesame', 'sezam']
                },
                # Ouă
                'ouă': {
                    'categories': [],
                    'keywords': [
                        'ouă', 'oua', 'ou', 'egg', 'eggs', 'albus', 'galbenus',
                        'cobb', 'piccata', 'picatta', 'maionez', 'majonez', 'mayonnaise',
                        'carbonara', 'hollandaise', 'tiramisu', 'custard', 'flan', 'papanasi',
                        'clatite', 'clătite', 'briosa', 'brioșa', 'pancakes', 'waffle', 'waffles',
                    ]
                },
                'oua': {
                    'categories': [],
                    'keywords': [
                        'ouă', 'oua', 'ou', 'egg', 'eggs', 'albus', 'galbenus',
                        'cobb', 'piccata', 'picatta', 'maionez', 'majonez', 'mayonnaise',
                        'carbonara', 'hollandaise', 'tiramisu', 'custard', 'flan', 'papanasi',
                        'clatite', 'clătite', 'briosa', 'brioșa', 'pancakes', 'waffle', 'waffles',
                    ]
                },
                'soia': {
                    'categories': ['legume'],
                    'keywords': ['soia', 'soy', 'tofu', 'tempeh', 'miso', 'sos de soia']
                },
                'peste': {
                    'categories': ['peste', 'fructe de mare'],
                    'keywords': [
                        'peste', 'pește', 'pescarus', 'somon', 'ton', 'sardine', 'macrou',
                        'crap', 'salau', 'fish', 'seafood', 'homar', 'lobster', 'crevet', 'crab',
                        'shrimp', 'prawn', 'prawns',
                        'midie', 'midii', 'scoici', 'scallop', 'calamar', 'sepie', 'icre', 'hering',
                        'anchois', 'sushi', 'sashimi',
                    ]
                },
                'pește': {
                    'categories': ['peste', 'fructe de mare'],
                    'keywords': [
                        'peste', 'pește', 'pescarus', 'somon', 'ton', 'sardine', 'macrou',
                        'crap', 'salau', 'fish', 'seafood', 'homar', 'lobster', 'crevet', 'crab',
                        'shrimp', 'prawn', 'prawns',
                        'midie', 'midii', 'scoici', 'scallop', 'calamar', 'sepie', 'icre', 'hering',
                        'anchois', 'sushi', 'sashimi',
                    ]
                },
                'crustacee': {
                    'categories': [],
                    'keywords': ['crustacee', 'creveți', 'creveti', 'crab', 'homar', 'langustă', 
                                'langusta', 'shrimp', 'lobster', 'crab']
                },
                'arahide': {
                    'categories': [],
                    'keywords': ['arahide', 'alune de pământ', 'alune de pamant', 'peanut', 'peanuts']
                },
                'sesam': {
                    'categories': [],
                    'keywords': ['sesam', 'susan', 'sezam', 'semințe de susan', 'seminte de susan', 
                                'sesame', 'tahini', 'halva', 'halvă', 'susan']
                },
                'mustar': {
                    'categories': [],
                    'keywords': ['mustar', 'muștar', 'mustard', 'condimente cu mustar']
                }
            }
            
            for user_allergy in user_allergies:
                user_allergy_clean = user_allergy.strip().lower()
                user_allergy_norm = normalize_clinical_text(user_allergy_clean)
                lookup_norm = resolve_allergy_token(user_allergy_norm)
                
                allergy_info = None
                for allergy_key, mapping in allergy_mappings.items():
                    key_norm = normalize_clinical_text(allergy_key)
                    if (
                        allergy_key == user_allergy_clean
                        or key_norm == user_allergy_norm
                        or key_norm == lookup_norm
                        or user_allergy_clean in allergy_key
                        or allergy_key in user_allergy_clean
                    ):
                        allergy_info = mapping
                        break
                    if len(user_allergy_norm) >= 3 and (
                        user_allergy_norm in key_norm or key_norm in user_allergy_norm
                    ):
                        allergy_info = mapping
                        break
                
                if allergy_info:
                    if allergy_info['categories'] and any(
                        normalize_clinical_text(cat) in food_category_lower
                        for cat in allergy_info['categories']
                    ):
                        return False

                    for keyword in allergy_info['keywords']:
                        kw = normalize_clinical_text(keyword)
                        if kw and (kw in food_name_lower or kw in food_category_lower):
                            return False
                
                if food.allergens:
                    food_allergens = [
                        a.strip().lower()
                        for a in re.split(r'[,;]+', food.allergens)
                        if a.strip()
                    ]
                    for allergen in food_allergens:
                        ag_norm = normalize_clinical_text(allergen)
                        if user_allergy_clean in allergen or allergen in user_allergy_clean:
                            return False
                        if ag_norm == user_allergy_norm or ag_norm == lookup_norm:
                            return False
                        if len(user_allergy_norm) >= 3 and (
                            user_allergy_norm in ag_norm or ag_norm in user_allergy_norm
                        ):
                            return False
                
                if len(user_allergy_norm) >= 3 and (
                    user_allergy_norm in food_name_lower or user_allergy_norm in food_category_lower
                ):
                    return False
        
        if user.medical_conditions:
            conditions_lower = normalize_clinical_text(user.medical_conditions)
            food_name_lower = normalize_clinical_text(food.name or '')
            food_category_lower = normalize_clinical_text(food.category or '')
            
            restrictions = self._parse_food_restrictions(user.medical_conditions)
            
            for forbidden_category in restrictions['forbidden_categories']:
                if forbidden_category in food_category_lower:
                    return False
                
                category_mappings = {
                    'legume': ['legume', 'leguma', 'vegetable', 'vegetables', 'leguminoase'],
                    'fructe': ['fructe', 'fructa', 'fruit', 'fruits'],
                    'cereale': ['cereale', 'cereala', 'grain', 'grains', 'cereal'],
                    'carne': ['carne', 'meat', 'pui', 'porc', 'vita', 'miel'],
                    'peste': [
                        'peste', 'pește', 'pescarus', 'fish', 'seafood', 'fructe de mare',
                        'homar', 'lobster', 'crevet', 'crab', 'midie', 'scoici', 'calamar', 'sepie',
                    ],
                    'lactate': ['lactate', 'lapte', 'dairy', 'milk'],
                    'semințe': ['semințe', 'seminte', 'seeds'],
                    'nuci': ['nuci', 'nucă', 'nuts'],
                    'leguminoase': ['leguminoase', 'fasole', 'linte', 'legumes', 'beans'],
                    'ouă': ['ouă', 'oua', 'ou', 'eggs'],
                    'soia': ['soia', 'soy']
                }
                
                if forbidden_category in category_mappings:
                    for variant in category_mappings[forbidden_category]:
                        if variant in food_category_lower or variant in food_name_lower:
                            return False
            
            for keyword in restrictions['forbidden_keywords']:
                kw = normalize_clinical_text(keyword)
                if not kw:
                    continue
                if re.search(rf"\b{re.escape(kw)}\b", food_name_lower) or re.search(
                    rf"\b{re.escape(kw)}\b", food_category_lower
                ):
                    return False
                if kw in food_name_lower or kw in food_category_lower:
                    return False

            for rule in self.medical_rules_config.get("condition_trigger_rules", []):
                condition_patterns = [normalize_clinical_text(x) for x in rule.get("condition_patterns", [])]
                avoid_keywords = [normalize_clinical_text(x) for x in rule.get("avoid_keywords", [])]
                if not any(p and p in conditions_lower for p in condition_patterns):
                    continue
                for kw in avoid_keywords:
                    if not kw:
                        continue
                    if kw in food_name_lower or kw in food_category_lower:
                        return False
            
            seed_restrictions = [
                'nu am voie seminte', 'nu am voie semințe', 'fără seminte', 'fără semințe',
                'no seeds', 'no seeds allowed', 'fara seminte', 'fara semințe',
                'interzis seminte', 'interzis semințe', 'evit seminte', 'evit semințe'
            ]
            seed_keywords = ['semințe', 'seminte', 'semințe de', 'seminte de', 'chia', 'flax',
                           'in', 'sunflower', 'pumpkin', 'sesame', 'sezam', 'semințe de in',
                           'semințe de chia', 'semințe de dovleac', 'semințe de susan',
                           'semințe de floarea-soarelui', 'seminte de floarea-soarelui']
            
            if any(normalize_clinical_text(r) in conditions_lower for r in seed_restrictions):
                if 'semințe' in food_category_lower or 'seminte' in food_category_lower:
                    return False
                if any(normalize_clinical_text(k) in food_name_lower for k in seed_keywords):
                    return False
            
            nuts_restrictions = [
                'nu am voie nuci', 'nu am voie nucă', 'fără nuci', 'fără nucă',
                'no nuts', 'no nuts allowed', 'fara nuci', 'fara nucă',
                'interzis nuci', 'interzis nucă', 'evit nuci', 'evit nucă'
            ]
            nuts_keywords = [
                'nuci', 'nuca', 'alune', 'migdale', 'fistic',
                'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut',
                'pignoli', 'pinoli', 'nuci de pin', 'nuca de pin',
                'pesto', 'kibbeh', 'baklava', 'nougat', 'gianduja', 'marzipan', 'martipan',
            ]
            
            if any(normalize_clinical_text(r) in conditions_lower for r in nuts_restrictions):
                if any(
                    normalize_clinical_text(k) in food_name_lower
                    or normalize_clinical_text(k) in food_category_lower
                    for k in nuts_keywords
                ):
                    return False
            
            dairy_restrictions = [
                'nu am voie lactate', 'nu am voie lapte', 'fără lactate', 'fără lapte',
                'no dairy', 'no milk', 'fara lactate', 'fara lapte',
                'interzis lactate', 'interzis lapte', 'evit lactate', 'evit lapte'
            ]
            dairy_keywords = ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt', 'telemea',
                            'cascaval', 'ricotta', 'mozzarella', 'gorgonzola', 'parmezan',
                            'cheddar', 'feta', 'brie', 'camembert', 'dairy']
            
            if any(normalize_clinical_text(r) in conditions_lower for r in dairy_restrictions):
                if any(
                    normalize_clinical_text(k) in food_name_lower
                    or normalize_clinical_text(k) in food_category_lower
                    for k in dairy_keywords
                ):
                    return False
            
            gluten_restrictions = [
                'nu am voie gluten', 'fără gluten', 'no gluten', 'fara gluten',
                'interzis gluten', 'evit gluten', 'fără grâu', 'fara grau'
            ]
            gluten_keywords = ['gluten', 'grâu', 'grau', 'făină', 'faina', 'pâine', 'paine',
                             'paste', 'spaghete', 'macaroane', 'wheat', 'barley', 'rye']
            
            if any(normalize_clinical_text(r) in conditions_lower for r in gluten_restrictions):
                if any(
                    normalize_clinical_text(k) in food_name_lower
                    or normalize_clinical_text(k) in food_category_lower
                    for k in gluten_keywords
                ):
                    return False

        lipids = normalize_clinical_text(user.medical_conditions or "")
        if lipids:
            markers = (
                "colesterol ridicat",
                "colesterol marit",
                "hipercolesterolemie",
                "dislipidemie",
                "dislipidemia",
                "colesterol mare",
                "ldl marit",
                "trigliceride mari",
                "trigliceride",
                "boli cardiovasculare",
                "risc cardiovascular",
                "ateroscleroza",
                "cord ischemic",
            )
            if any(m in lipids for m in markers):
                chol = float(food.cholesterol or 0)
                fatv = float(food.fat or 0)
                if chol >= 95 or (fatv >= 24 and chol >= 40):
                    return False
        
        return True
    
    def _is_food_compatible_with_rule(self, food: FoodItem, rule: ScopedRule, user: UserProfile) -> bool:
        """Verifică dacă alimentul este compatibil cu regula specifică"""
        if rule.scope == ScopeType.DIET_VEGAN:
            meat_categories = ['carne', 'pui', 'porc', 'vita', 'miel', 'pește', 'peste']
            dairy_categories = ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt']
            food_category_lower = food.category.lower() if food.category else ''
            if any(cat in food_category_lower for cat in meat_categories + dairy_categories):
                return False
        
        if rule.scope == ScopeType.DIET_VEGETARIAN:
            meat_categories = ['carne', 'pui', 'porc', 'vita', 'miel', 'pește', 'peste']
            food_category_lower = food.category.lower() if food.category else ''
            if any(cat in food_category_lower for cat in meat_categories):
                return False
        
        if rule.scope == ScopeType.DIET_PESCATARIAN:
            meat_categories = ['carne', 'pui', 'porc', 'vita', 'miel']
            food_category_lower = food.category.lower() if food.category else ''
            if any(cat in food_category_lower for cat in meat_categories):
                return False
        
        if rule.scope == ScopeType.LACTOSE_INTOLERANCE:
            dairy_categories = ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt']
            food_category_lower = food.category.lower() if food.category else ''
            food_name_lower = food.name.lower() if food.name else ''
            if any(cat in food_category_lower or cat in food_name_lower for cat in dairy_categories):
                return False
        
        if rule.scope == ScopeType.GLUTEN_SENSITIVITY:
            gluten_keywords = ['gluten', 'grâu', 'grau', 'făină', 'faina', 'pâine', 'paine', 
                             'paste', 'spaghete', 'macaroane', 'wheat', 'barley', 'rye']
            food_category_lower = food.category.lower() if food.category else ''
            food_name_lower = food.name.lower() if food.name else ''
            if any(keyword in food_category_lower or keyword in food_name_lower for keyword in gluten_keywords):
                return False
        
        if user.allergies and rule.recommended_foods:
            user_allergies = [a.strip().lower() for a in user.allergies.split(',')]
            food_name_lower = food.name.lower() if food.name else ''
            food_category_lower = food.category.lower() if food.category else ''
            
            for recommended in rule.recommended_foods:
                recommended_lower = recommended.lower()
                for allergy in user_allergies:
                    allergy_clean = allergy.strip().lower()
                    if allergy_clean in recommended_lower or recommended_lower in allergy_clean:
                        if allergy_clean in food_name_lower or allergy_clean in food_category_lower:
                            return False
        
        return True