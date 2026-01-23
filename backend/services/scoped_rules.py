
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from models import User, Food, LabResult


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
    
    def _initialize_rules(self) -> Dict[NutrientType, List[ScopedRule]]:
        rules = {}
        
        # FIER - Ferritin < 30 ng/mL
        rules[NutrientType.IRON] = [
            ScopedRule(
                nutrient=NutrientType.IRON,
                scope=ScopeType.DIET_VEGAN,
                weight=1.0,
                recommended_foods=['linte', 'năut', 'spanac'],
                explanation_template="Pentru că ești vegan și ai deficit de fier (feritină < 30 ng/mL), recomandăm {foods} + vitamina C pentru absorbție mai bună.",
                clinical_threshold=30.0
            ),
            ScopedRule(
                nutrient=NutrientType.IRON,
                scope=ScopeType.DIET_OMNIVORE,
                weight=1.0,
                recommended_foods=['carne roșie', 'ficat'],
                explanation_template="Pentru că ai dietă omnivoră și deficit de fier (feritină < 30 ng/mL), recomandăm {foods}.",
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
                explanation_template="Pentru că ai expunere solară redusă și deficit de vitamina D (25(OH)D < 20 ng/mL), recomandăm expunere solară + alimente fortificate.",
                clinical_threshold=20.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_D,
                scope=ScopeType.DIET_VEGAN,
                weight=1.0,
                recommended_foods=['ciuperci UV', 'lapte vegetal fortificat'],
                explanation_template="Pentru că ești vegan și ai deficit de vitamina D (25(OH)D < 20 ng/mL), recomandăm {foods}.",
                clinical_threshold=20.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_D,
                scope=ScopeType.HIGH_BMI,
                weight=0.6,
                recommended_foods=['aport crescut de vitamina D'],
                explanation_template="Pentru că ai IMC crescut și deficit de vitamina D, recomandăm aport crescut de vitamina D.",
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
                explanation_template="Pentru că ești vegan și ai deficit de vitamina B12 (B12 < 200 pg/mL), recomandăm {foods}.",
                clinical_threshold=200.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.ELDERLY,
                weight=0.8,
                recommended_foods=['suplimentare recomandată'],
                explanation_template="Pentru că ești în vârstă și ai deficit de vitamina B12, recomandăm suplimentare.",
                clinical_threshold=200.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.MALABSORPTION,
                weight=0.8,
                recommended_foods=['suplimentare recomandată'],
                explanation_template="Pentru că ai malabsorbție și deficit de vitamina B12, recomandăm suplimentare.",
                clinical_threshold=200.0
            ),
            ScopedRule(
                nutrient=NutrientType.VITAMIN_B12,
                scope=ScopeType.DIET_OMNIVORE,
                weight=0.6,
                recommended_foods=['carne', 'pește', 'lactate'],
                explanation_template="Pentru că ai dietă omnivoră și deficit de vitamina B12, recomandăm {foods}.",
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
    
    def get_user_scopes(self, user: User, lab_results: Optional[LabResult] = None) -> List[ScopeType]:
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
        food: Food,
        user: User,
        deficit: float,
        lab_results: Optional[LabResult] = None
    ) -> List[ScopedRuleResult]:
        """
        Evaluează toate regulile pentru un nutrient specific
        Returnează lista de rezultate pentru regulile care se potrivesc
        """
        if nutrient not in self.rules:
            return []
        
        user_scopes = self.get_user_scopes(user, lab_results)
        matching_rules = []
        
        for rule in self.rules[nutrient]:
            # Verifică dacă regula se aplică în contextul utilizatorului
            if rule.scope not in user_scopes:
                continue
            
            # Verifică dacă alimentul conține nutrientul necesar
            nutrient_value = self._get_nutrient_value(food, nutrient)
            
            # Verifică dacă alimentul este în lista de recomandări sau conține nutrientul
            food_matches = self._food_matches_recommendations(food, rule.recommended_foods)
            
            # Regula se aplică dacă alimentul se potrivește cu recomandările SAU conține nutrientul
            if food_matches or nutrient_value > 0:
                base_score = min(10.0, (nutrient_value / max(1, deficit)) * 10)
                weighted_score = base_score * rule.weight
                explanation = self._generate_explanation(rule, food, nutrient_value, deficit)
                
                matching_rules.append(ScopedRuleResult(
                    rule=rule,
                    matched=True,
                    score=weighted_score,
                    explanation=explanation,
                    context=self._get_scope_label(rule.scope)
                ))
        
        return matching_rules
    
    def _get_nutrient_value(self, food: Food, nutrient: NutrientType) -> float:
        """Extrage valoarea nutrientului din aliment"""
        mapping = {
            NutrientType.IRON: food.iron or 0,
            NutrientType.CALCIUM: food.calcium or 0,
            NutrientType.MAGNESIUM: food.magnesium or 0,
            NutrientType.ZINC: food.zinc or 0,
            NutrientType.VITAMIN_D: (food.vitamin_d or 0) / 40,  # Convert IU to approximate mg
            NutrientType.VITAMIN_B12: food.vitamin_b12 or 0,
            NutrientType.VITAMIN_C: food.vitamin_c or 0,
            # Pentru nutrienții care nu sunt în modelul Food, returnează 0
            NutrientType.FOLATE: 0,
            NutrientType.VITAMIN_A: 0,
            NutrientType.IODINE: 0,
            NutrientType.VITAMIN_K: 0,
            NutrientType.POTASSIUM: 0,
        }
        return mapping.get(nutrient, 0)
    
    def _food_matches_recommendations(self, food: Food, recommended_foods: List[str]) -> bool:
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
        food: Food,
        nutrient_value: float,
        deficit: float
    ) -> str:
        """Generează explicația pentru regulă"""
        foods_str = ', '.join(rule.recommended_foods) if rule.recommended_foods else food.name
        
        explanation = rule.explanation_template.format(foods=foods_str)
        
        # Adaugă informații despre conținutul nutrientului
        if nutrient_value > 0:
            explanation += f" {food.name} conține {nutrient_value:.1f} {self._get_nutrient_unit(rule.nutrient)} per 100g."
        
        return explanation
    
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
