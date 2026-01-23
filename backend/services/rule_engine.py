
from typing import List, Dict, Optional, Tuple
from models import Food, User, LabResult
from dataclasses import dataclass
from enum import Enum
from services.scoped_rules import ScopedRulesEngine, NutrientType as ScopedNutrientType, ScopedRuleResult


class NutrientType(str, Enum):
    """Tipuri de nutrienți suportați"""
    IRON = "iron"
    MAGNESIUM = "magnesium"
    CALCIUM = "calcium"


class DeficiencyLevel(str, Enum):
    """Niveluri de deficiență"""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class RuleResult:
    """Rezultat al evaluării unei reguli"""
    matched: bool
    score: float
    explanation: str
    rule_name: str
    nutrient: str
    priority: int


@dataclass
class FoodRecommendation:
    """Recomandare de aliment cu explicații"""
    food_id: int
    score: float
    coverage: float
    explanations: List[str]
    matched_rules: List[str]
    nutrients_covered: List[str]


class NutritionalRuleEngine:
    
    def __init__(self):
        # Păstrăm threshold-urile pentru compatibilitate
        self.nutrient_thresholds = {
            NutrientType.IRON: {
                'high': 3.0,
                'medium': 1.5,
                'low': 0.5
            },
            NutrientType.MAGNESIUM: {
                'high': 100.0,
                'medium': 50.0,
                'low': 20.0
            },
            NutrientType.CALCIUM: {
                'high': 200.0,
                'medium': 100.0,
                'low': 50.0
            }
        }
        self.scoped_rules_engine = ScopedRulesEngine()
    
    def evaluate_food(
        self,
        food: Food,
        user: User,
        deficits: Dict[str, float],
        lab_results: Optional[LabResult] = None
    ) -> Optional[FoodRecommendation]:
        """
        Evaluează un aliment folosind toate regulile disponibile (scoped rules + reguli tradiționale)
        
        Returnează None dacă alimentul nu trece verificările de compatibilitate
        """
        # Verifică compatibilitatea de bază
        if not self._is_compatible(food, user):
            return None
        
        # Evaluează regulile cu scop pentru toți nutrienții
        scoped_rule_results: List[ScopedRuleResult] = []
        
        # Mapare de la string la ScopedNutrientType
        nutrient_mapping = {
            'iron': ScopedNutrientType.IRON,
            'vitamin_d': ScopedNutrientType.VITAMIN_D,
            'vitamin_b12': ScopedNutrientType.VITAMIN_B12,
            'folate': ScopedNutrientType.FOLATE,
            'calcium': ScopedNutrientType.CALCIUM,
            'magnesium': ScopedNutrientType.MAGNESIUM,
            'zinc': ScopedNutrientType.ZINC,
            'vitamin_a': ScopedNutrientType.VITAMIN_A,
            'vitamin_c': ScopedNutrientType.VITAMIN_C,
            'iodine': ScopedNutrientType.IODINE,
            'vitamin_k': ScopedNutrientType.VITAMIN_K,
            'potassium': ScopedNutrientType.POTASSIUM,
        }
        
        # Evaluează regulile cu scop pentru fiecare nutrient cu deficit
        for nutrient_str, deficit_amount in deficits.items():
            if deficit_amount <= 0:
                continue
            
            nutrient_type = nutrient_mapping.get(nutrient_str)
            if nutrient_type:
                results = self.scoped_rules_engine.evaluate_rules_for_nutrient(
                    nutrient=nutrient_type,
                    food=food,
                    user=user,
                    deficit=deficit_amount,
                    lab_results=lab_results
                )
                scoped_rule_results.extend(results)
        
        # Dacă avem rezultate din scoped rules, le folosim cu prioritate
        if scoped_rule_results:
            # Procesează rezultatele scoped rules
            # Agregă rezultatele pentru același nutrient (dacă există multiple reguli)
            nutrient_scores: Dict[str, float] = {}
            nutrient_explanations: Dict[str, List[str]] = {}
            nutrient_contexts: Dict[str, List[str]] = {}
            nutrient_rules: Dict[str, List[str]] = {}
            
            for result in scoped_rule_results:
                nutrient_str = result.rule.nutrient.value
                if nutrient_str not in nutrient_scores:
                    nutrient_scores[nutrient_str] = 0
                    nutrient_explanations[nutrient_str] = []
                    nutrient_contexts[nutrient_str] = []
                    nutrient_rules[nutrient_str] = []
                
                nutrient_scores[nutrient_str] += result.score
                nutrient_explanations[nutrient_str].append(result.explanation)
                nutrient_contexts[nutrient_str].append(result.context)
                nutrient_rules[nutrient_str].append(f"{result.rule.scope.value}_weight_{result.rule.weight}")
            
            # Construiește explicațiile finale cu context
            final_explanations = []
            final_matched_rules = []
            
            for nutrient_str in nutrient_scores.keys():
                # Combină explicațiile pentru acest nutrient
                explanations_text = " ".join(nutrient_explanations[nutrient_str])
                contexts_text = ", ".join(set(nutrient_contexts[nutrient_str]))
                
                # Adaugă contextul în explicație
                if contexts_text:
                    final_explanation = f"[Context: {contexts_text}] {explanations_text}"
                else:
                    final_explanation = explanations_text
                
                final_explanations.append(final_explanation)
                final_matched_rules.extend(nutrient_rules[nutrient_str])
            
            # Calculează scorul total (suma scorurilor ponderate)
            total_score = sum(nutrient_scores.values())
            
            # Calculează acoperirea
            nutrients_covered = list(nutrient_scores.keys())
            coverage = self._calculate_coverage(food, deficits, nutrients_covered)
            
            return FoodRecommendation(
                food_id=food.id,
                score=total_score,
                coverage=coverage,
                explanations=final_explanations,
                matched_rules=final_matched_rules,
                nutrients_covered=nutrients_covered
            )
        
        # Dacă nu s-au găsit reguli cu scop, folosește regulile tradiționale pentru compatibilitate
        # Fallback la regulile tradiționale pentru Iron, Magnesium, Calcium
        rule_results: List[RuleResult] = []
        
        # Evaluează regulile tradiționale doar pentru nutrienții care nu au fost acoperiți de scoped rules
        # și care au deficiențe
        if deficits.get(NutrientType.IRON.value, 0) > 0:
            iron_result = self._evaluate_iron_rules(food, user, deficits, lab_results)
            if iron_result:
                rule_results.append(iron_result)
        
        if deficits.get(NutrientType.MAGNESIUM.value, 0) > 0:
            magnesium_result = self._evaluate_magnesium_rules(food, user, deficits, lab_results)
            if magnesium_result:
                rule_results.append(magnesium_result)
        
        if deficits.get(NutrientType.CALCIUM.value, 0) > 0:
            calcium_result = self._evaluate_calcium_rules(food, user, deficits, lab_results)
            if calcium_result:
                rule_results.append(calcium_result)
        
        # Dacă nu s-au găsit rezultate nici din scoped rules, nici din regulile tradiționale
        if not rule_results:
            return None
        
        # Calculează scorul total și explicațiile (mod tradițional)
        total_score = sum(r.score for r in rule_results)
        explanations = [r.explanation for r in rule_results]
        matched_rules = [r.rule_name for r in rule_results]
        nutrients_covered = list(set(r.nutrient for r in rule_results))
        
        coverage = self._calculate_coverage(food, deficits, nutrients_covered)
        
        return FoodRecommendation(
            food_id=food.id,
            score=total_score,
            coverage=coverage,
            explanations=explanations,
            matched_rules=matched_rules,
            nutrients_covered=nutrients_covered
        )
    
    def _evaluate_iron_rules(
        self,
        food: Food,
        user: User,
        deficits: Dict[str, float],
        lab_results: Optional[LabResult]
    ) -> Optional[RuleResult]:
        """
        REGULĂ IF-ELSE pentru Iron
        
        Reguli explicite:
        IF deficit_iron > 0 THEN
            IF iron_content >= 3.0 mg/100g THEN
                score = 10.0, explanation = "Aliment bogat în fier"
            ELSE IF iron_content >= 1.5 mg/100g THEN
                score = 7.0, explanation = "Aliment cu conținut moderat de fier"
            ELSE IF iron_content >= 0.5 mg/100g THEN
                score = 4.0, explanation = "Aliment cu conținut redus de fier"
            ELSE
                return None (nu recomandă)
        END IF
        """
        deficit = deficits.get(NutrientType.IRON.value, 0)
        if deficit <= 0:
            return None
        
        iron_content = food.iron or 0
        thresholds = self.nutrient_thresholds[NutrientType.IRON]
        
        # Determină nivelul deficienței
        deficiency_level = self._classify_deficiency(deficit, NutrientType.IRON)
        
        # REGULĂ 1: Deficit sever + Iron high
        if deficiency_level == DeficiencyLevel.SEVERE and iron_content >= thresholds['high']:
            portion_value = (iron_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=10.0,
                explanation=f"Recomandat pentru deficit sever de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_severe_high",
                nutrient=NutrientType.IRON.value,
                priority=10
            )
        
        # REGULĂ 2: Deficit sever + Iron medium
        elif deficiency_level == DeficiencyLevel.SEVERE and iron_content >= thresholds['medium']:
            portion_value = (iron_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.0,
                explanation=f"Recomandat pentru deficit sever de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_severe_medium",
                nutrient=NutrientType.IRON.value,
                priority=9
            )
        
        # REGULĂ 3: Deficit moderat + Iron high
        elif deficiency_level == DeficiencyLevel.MODERATE and iron_content >= thresholds['high']:
            portion_value = (iron_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.5,
                explanation=f"Recomandat pentru deficit moderat de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_moderate_high",
                nutrient=NutrientType.IRON.value,
                priority=8
            )
        
        # REGULĂ 4: Deficit moderat + Iron medium
        elif deficiency_level == DeficiencyLevel.MODERATE and iron_content >= thresholds['medium']:
            portion_value = (iron_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=6.0,
                explanation=f"Recomandat pentru deficit moderat de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_moderate_medium",
                nutrient=NutrientType.IRON.value,
                priority=7
            )
        
        # REGULĂ 5: Deficit mild + Iron high
        elif deficiency_level == DeficiencyLevel.MILD and iron_content >= thresholds['high']:
            portion_value = (iron_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=7.0,
                explanation=f"Recomandat pentru deficit ușor de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_mild_high",
                nutrient=NutrientType.IRON.value,
                priority=6
            )
        
        # REGULĂ 6: Orice deficit + Iron low (dar peste pragul minim)
        elif iron_content >= thresholds['low']:
            portion_value = (iron_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=4.0,
                explanation=f"Recomandat pentru aport de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_low",
                nutrient=NutrientType.IRON.value,
                priority=4
            )
        
        # Nu se potrivește niciună regulă
        return None
    
    def _evaluate_magnesium_rules(
        self,
        food: Food,
        user: User,
        deficits: Dict[str, float],
        lab_results: Optional[LabResult]
    ) -> Optional[RuleResult]:
        """
        REGULĂ IF-ELSE pentru Magnesium
        
        Similar cu Iron, dar cu praguri diferite pentru magnesiu
        """
        deficit = deficits.get(NutrientType.MAGNESIUM.value, 0)
        if deficit <= 0:
            return None
        
        magnesium_content = food.magnesium or 0
        thresholds = self.nutrient_thresholds[NutrientType.MAGNESIUM]
        deficiency_level = self._classify_deficiency(deficit, NutrientType.MAGNESIUM)
        
        # REGULĂ 1: Deficit sever + Magnesium high
        if deficiency_level == DeficiencyLevel.SEVERE and magnesium_content >= thresholds['high']:
            portion_value = (magnesium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=10.0,
                explanation=f"Recomandat pentru deficit sever de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_severe_high",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=10
            )
        
        # REGULĂ 2: Deficit sever + Magnesium medium
        elif deficiency_level == DeficiencyLevel.SEVERE and magnesium_content >= thresholds['medium']:
            portion_value = (magnesium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.0,
                explanation=f"Recomandat pentru deficit sever de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_severe_medium",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=9
            )
        
        # REGULĂ 3: Deficit moderat + Magnesium high
        elif deficiency_level == DeficiencyLevel.MODERATE and magnesium_content >= thresholds['high']:
            portion_value = (magnesium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.5,
                explanation=f"Recomandat pentru deficit moderat de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_moderate_high",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=8
            )
        
        # REGULĂ 4: Deficit moderat + Magnesium medium
        elif deficiency_level == DeficiencyLevel.MODERATE and magnesium_content >= thresholds['medium']:
            portion_value = (magnesium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=6.0,
                explanation=f"Recomandat pentru deficit moderat de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_moderate_medium",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=7
            )
        
        # REGULĂ 5: Deficit mild + Magnesium high
        elif deficiency_level == DeficiencyLevel.MILD and magnesium_content >= thresholds['high']:
            portion_value = (magnesium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=7.0,
                explanation=f"Recomandat pentru deficit ușor de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_mild_high",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=6
            )
        
        # REGULĂ 6: Orice deficit + Magnesium low
        elif magnesium_content >= thresholds['low']:
            portion_value = (magnesium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=4.0,
                explanation=f"Recomandat pentru aport de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_low",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=4
            )
        
        return None
    
    def _evaluate_calcium_rules(
        self,
        food: Food,
        user: User,
        deficits: Dict[str, float],
        lab_results: Optional[LabResult]
    ) -> Optional[RuleResult]:
        """
        REGULĂ IF-ELSE pentru Calcium
        
        Similar cu Iron și Magnesium, dar cu praguri specifice pentru calciu
        """
        deficit = deficits.get(NutrientType.CALCIUM.value, 0)
        if deficit <= 0:
            return None
        
        calcium_content = food.calcium or 0
        thresholds = self.nutrient_thresholds[NutrientType.CALCIUM]
        deficiency_level = self._classify_deficiency(deficit, NutrientType.CALCIUM)
        
        # REGULĂ 1: Deficit sever + Calcium high
        if deficiency_level == DeficiencyLevel.SEVERE and calcium_content >= thresholds['high']:
            portion_value = (calcium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=10.0,
                explanation=f"Recomandat pentru deficit sever de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_severe_high",
                nutrient=NutrientType.CALCIUM.value,
                priority=10
            )
        
        # REGULĂ 2: Deficit sever + Calcium medium
        elif deficiency_level == DeficiencyLevel.SEVERE and calcium_content >= thresholds['medium']:
            portion_value = (calcium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.0,
                explanation=f"Recomandat pentru deficit sever de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_severe_medium",
                nutrient=NutrientType.CALCIUM.value,
                priority=9
            )
        
        # REGULĂ 3: Deficit moderat + Calcium high
        elif deficiency_level == DeficiencyLevel.MODERATE and calcium_content >= thresholds['high']:
            portion_value = (calcium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.5,
                explanation=f"Recomandat pentru deficit moderat de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_moderate_high",
                nutrient=NutrientType.CALCIUM.value,
                priority=8
            )
        
        # REGULĂ 4: Deficit moderat + Calcium medium
        elif deficiency_level == DeficiencyLevel.MODERATE and calcium_content >= thresholds['medium']:
            portion_value = (calcium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=6.0,
                explanation=f"Recomandat pentru deficit moderat de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_moderate_medium",
                nutrient=NutrientType.CALCIUM.value,
                priority=7
            )
        
        # REGULĂ 5: Deficit mild + Calcium high
        elif deficiency_level == DeficiencyLevel.MILD and calcium_content >= thresholds['high']:
            portion_value = (calcium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=7.0,
                explanation=f"Recomandat pentru deficit ușor de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_mild_high",
                nutrient=NutrientType.CALCIUM.value,
                priority=6
            )
        
        # REGULĂ 6: Orice deficit + Calcium low
        elif calcium_content >= thresholds['low']:
            portion_value = (calcium_content * 150) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=4.0,
                explanation=f"Recomandat pentru aport de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de 150g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_low",
                nutrient=NutrientType.CALCIUM.value,
                priority=4
            )
        
        return None
    
    def _classify_deficiency(self, deficit: float, nutrient: NutrientType) -> DeficiencyLevel:
        """
        Clasifică nivelul deficienței pentru un nutrient
        
        Praguri relative bazate pe RDI estimat
        """
        # Praguri relative (procente din RDI tipic)
        if nutrient == NutrientType.IRON:
            severe_threshold = 10.0  # mg
            moderate_threshold = 5.0
        elif nutrient == NutrientType.MAGNESIUM:
            severe_threshold = 200.0  # mg
            moderate_threshold = 100.0
        elif nutrient == NutrientType.CALCIUM:
            severe_threshold = 500.0  # mg
            moderate_threshold = 250.0
        else:
            severe_threshold = 100.0
            moderate_threshold = 50.0
        
        if deficit >= severe_threshold:
            return DeficiencyLevel.SEVERE
        elif deficit >= moderate_threshold:
            return DeficiencyLevel.MODERATE
        elif deficit > 0:
            return DeficiencyLevel.MILD
        else:
            return DeficiencyLevel.NONE
    
    def _is_compatible(self, food: Food, user: User) -> bool:
        """Verifică dacă alimentul este compatibil cu profilul utilizatorului"""
        # Verifică restricții dietetice
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
        
        # Verifică alergii - verificare îmbunătățită cu mapping complet
        if user.allergies:
            user_allergies = [a.strip().lower() for a in user.allergies.split(',')]
            food_name_lower = food.name.lower()
            food_category_lower = food.category.lower() if food.category else ''
            
            # Mapping complet de alergii către categorii și cuvinte cheie
            allergy_mappings = {
                # Lactoză/Lactate - cel mai important
                'lactoza': {
                    'categories': ['lactate'],
                    'keywords': ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt', 'telemea', 
                                'cascaval', 'ricotta', 'mozzarella', 'gorgonzola', 'parmezan', 
                                'cheddar', 'feta', 'brie', 'camembert', 'dairy', 'lactos', 'lactate']
                },
                'lactoză': {
                    'categories': ['lactate'],
                    'keywords': ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt', 'telemea', 
                                'cascaval', 'ricotta', 'mozzarella', 'gorgonzola', 'parmezan', 
                                'cheddar', 'feta', 'brie', 'camembert', 'dairy', 'lactos', 'lactate']
                },
                'lactate': {
                    'categories': ['lactate'],
                    'keywords': ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt', 'telemea', 
                                'cascaval', 'ricotta', 'mozzarella', 'gorgonzola', 'parmezan', 
                                'cheddar', 'feta', 'brie', 'camembert', 'dairy', 'lactos']
                },
                # Gluten
                'gluten': {
                    'categories': ['cereale'],
                    'keywords': ['gluten', 'grâu', 'grau', 'grâu', 'făină', 'faina', 'pâine', 'paine', 
                                'paste', 'spaghete', 'macaroane', 'tortilla', 'cereale', 'wheat', 
                                'barley', 'rye', 'seitan']
                },
                # Nuci
                'nuci': {
                    'categories': [],
                    'keywords': ['nuci', 'nucă', 'nuca', 'nuc', 'alune', 'migdale', 'fistic', 
                                'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut']
                },
                'nucă': {
                    'categories': [],
                    'keywords': ['nuci', 'nucă', 'nuca', 'nuc', 'alune', 'migdale', 'fistic', 
                                'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut']
                },
                # Ouă
                'ouă': {
                    'categories': [],
                    'keywords': ['ouă', 'oua', 'ou', 'egg', 'eggs', 'albus', 'galbenus']
                },
                'oua': {
                    'categories': [],
                    'keywords': ['ouă', 'oua', 'ou', 'egg', 'eggs', 'albus', 'galbenus']
                },
                # Soia
                'soia': {
                    'categories': ['legume'],
                    'keywords': ['soia', 'soy', 'tofu', 'tempeh', 'miso', 'sos de soia']
                },
                # Peste/Pește
                'peste': {
                    'categories': ['peste'],
                    'keywords': ['peste', 'pește', 'pescăruș', 'somon', 'ton', 'sardine', 'macrou', 
                                'crap', 'șalău', 'salau', 'fish', 'seafood']
                },
                'pește': {
                    'categories': ['peste'],
                    'keywords': ['peste', 'pește', 'pescăruș', 'somon', 'ton', 'sardine', 'macrou', 
                                'crap', 'șalău', 'salau', 'fish', 'seafood']
                },
                # Crustacee
                'crustacee': {
                    'categories': [],
                    'keywords': ['crustacee', 'creveți', 'creveti', 'crab', 'homar', 'langustă', 
                                'langusta', 'shrimp', 'lobster', 'crab']
                },
                # Arahide
                'arahide': {
                    'categories': [],
                    'keywords': ['arahide', 'alune de pământ', 'alune de pamant', 'peanut', 'peanuts']
                }
            }
            
            # Verifică fiecare alergie a utilizatorului
            for user_allergy in user_allergies:
                user_allergy_clean = user_allergy.strip().lower()
                
                # Verifică dacă există mapping pentru această alergie
                allergy_info = None
                for allergy_key, mapping in allergy_mappings.items():
                    if allergy_key == user_allergy_clean or user_allergy_clean in allergy_key or allergy_key in user_allergy_clean:
                        allergy_info = mapping
                        break
                
                if allergy_info:
                    # Verifică categoria alimentului
                    if allergy_info['categories'] and food_category_lower in allergy_info['categories']:
                        return False
                    
                    # Verifică cuvintele cheie în nume și categorie
                    for keyword in allergy_info['keywords']:
                        if keyword in food_name_lower or keyword in food_category_lower:
                            return False
                
                # Verifică alergii generale prin câmpul allergens (pentru alergia curentă)
                if food.allergens:
                    food_allergens = [a.strip().lower() for a in food.allergens.split(',') if a.strip()]
                    for allergen in food_allergens:
                        # Verifică potrivire exactă sau parțială
                        if user_allergy_clean in allergen or allergen in user_allergy_clean:
                            return False
                
                # Verifică și în numele alimentului și categorie (fallback)
                if user_allergy_clean and (user_allergy_clean in food_name_lower or user_allergy_clean in food_category_lower):
                    return False
        
        # Verifică condiții medicale
        if user.medical_conditions:
            conditions = [c.strip().lower() for c in user.medical_conditions.split(',')]
            food_name_lower = food.name.lower() if food.name else ''
            food_category_lower = food.category.lower() if food.category else ''
            
            # Probleme cu rinichii - evită oxalați ridicați
            if any('rinichi' in c or 'oxalat' in c or 'renal' in c for c in conditions):
                high_oxalate_foods = ['spanac', 'rabarbar', 'nucă', 'ciocolată', 'ceai']
                if any(ox in food_name_lower or ox in food_category_lower for ox in high_oxalate_foods):
                    return False
            
            # Diabet - evită alimente cu indice glicemic foarte ridicat
            if any('diabet' in c or 'glicemie' in c for c in conditions):
                high_gi_foods = ['zahăr', 'sirop', 'dulceață', 'bomboane']
                if any(gi in food_name_lower for gi in high_gi_foods):
                    return False
            
            # Hipertensiune - evită alimente cu sodiu ridicat
            if any('hipertensiune' in c or 'tensiune' in c for c in conditions):
                high_sodium_foods = ['sare', 'salam', 'cârnați', 'conservă']
                if any(sod in food_name_lower or sod in food_category_lower for sod in high_sodium_foods):
                    return False
        
        return True
    
    def _calculate_coverage(
        self,
        food: Food,
        deficits: Dict[str, float],
        nutrients_covered: List[str]
    ) -> float:
        """Calculează procentul mediu de acoperire a deficitelor"""
        portion_grams = 150
        total_weighted_coverage = 0
        total_weight = 0
        
        # Mapare extinsă pentru toți nutrienții
        nutrient_mapping = {
            'iron': food.iron or 0,
            'magnesium': food.magnesium or 0,
            'calcium': food.calcium or 0,
            'vitamin_d': food.vitamin_d or 0,  # IU
            'vitamin_b12': food.vitamin_b12 or 0,
            'zinc': food.zinc or 0,
            'vitamin_c': food.vitamin_c or 0,
            'folate': getattr(food, 'folate', 0) or 0,
            'vitamin_a': getattr(food, 'vitamin_a', 0) or 0,
            'iodine': getattr(food, 'iodine', 0) or 0,
            'vitamin_k': getattr(food, 'vitamin_k', 0) or 0,
            'potassium': getattr(food, 'potassium', 0) or 0,
        }
        
        for nutrient in nutrients_covered:
            if nutrient in deficits and deficits[nutrient] > 0:
                food_value = nutrient_mapping.get(nutrient, 0)
                if food_value > 0:
                    portion_value = (food_value * portion_grams) / 100
                    coverage_pct = min(100, (portion_value / deficits[nutrient]) * 100) if deficits[nutrient] > 0 else 0
                    weight = deficits[nutrient]
                    total_weighted_coverage += coverage_pct * weight
                    total_weight += weight
        
        return total_weighted_coverage / total_weight if total_weight > 0 else 0

