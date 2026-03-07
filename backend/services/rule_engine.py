
from typing import List, Dict, Optional, Tuple
import re
from dataclasses import dataclass
from domain.models import FoodItem, UserProfile, LabResultItem
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
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        lab_results: Optional[LabResultItem] = None
    ) -> Optional[FoodRecommendation]:
        """Evaluează un aliment folosind toate regulile disponibile"""
        if not self._is_compatible(food, user):
            return None
        
        scoped_rule_results: List[ScopedRuleResult] = []
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
        
        if scoped_rule_results:
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
            
            final_explanations = []
            final_matched_rules = []
            
            for nutrient_str in nutrient_scores.keys():
                explanations_text = " ".join(nutrient_explanations[nutrient_str])
                contexts_text = ", ".join(set(nutrient_contexts[nutrient_str]))
                
                final_explanation = explanations_text
                final_explanations.append(final_explanation)
                final_matched_rules.extend(nutrient_rules[nutrient_str])
            
            total_score = sum(nutrient_scores.values())
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
        
        rule_results: List[RuleResult] = []
        
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
        
        if not rule_results:
            return None
        
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
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        lab_results: Optional[LabResultItem]
    ) -> Optional[RuleResult]:
        """Evaluează regulile pentru fier"""
        deficit = deficits.get(NutrientType.IRON.value, 0)
        if deficit <= 0:
            return None
        
        iron_content = food.iron or 0
        thresholds = self.nutrient_thresholds[NutrientType.IRON]
        deficiency_level = self._classify_deficiency(deficit, NutrientType.IRON)
        
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
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        lab_results: Optional[LabResultItem]
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
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        lab_results: Optional[LabResultItem]
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
    
    def _parse_food_restrictions(self, medical_conditions: str) -> Dict[str, List[str]]:
        """
        Parsează condițiile medicale și identifică interziceri pentru categorii de alimente.
        
        Returnează un dicționar cu:
        - 'forbidden_categories': lista de categorii interzise
        - 'forbidden_keywords': lista de cuvinte cheie interzise
        """
        if not medical_conditions:
            return {'forbidden_categories': [], 'forbidden_keywords': []}
        
        conditions_lower = medical_conditions.lower()
        forbidden_categories = []
        forbidden_keywords = []
        
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
        """Verifică dacă alimentul este compatibil cu profilul utilizatorului"""
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
            user_allergies = [a.strip().lower() for a in user.allergies.split(',')]
            food_name_lower = food.name.lower()
            food_category_lower = food.category.lower() if food.category else ''
            
            allergy_mappings = {
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
                'nuci': {
                    'categories': [],
                    'keywords': ['nuci', 'nucă', 'nuca', 'nuc', 'alune', 'migdale', 'fistic', 
                                'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut']
                },
                'nucă': {
                    'categories': [],
                    'keywords': ['nuci', 'nucă', 'nuca', 'nuc', 'alune', 'migdale', 'fistic', 
                                'caju', 'macadamia', 'pecan', 'nuts',                     'almond', 'walnut', 'hazelnut']
                },
                'ouă': {
                    'categories': [],
                    'keywords': ['ouă', 'oua', 'ou', 'egg', 'eggs', 'albus', 'galbenus']
                },
                'oua': {
                    'categories': [],
                    'keywords': ['ouă', 'oua', 'ou', 'egg', 'eggs', 'albus', 'galbenus']
                },
                'soia': {
                    'categories': ['legume'],
                    'keywords': ['soia', 'soy', 'tofu', 'tempeh', 'miso', 'sos de soia']
                },
                'peste': {
                    'categories': ['peste'],
                    'keywords': ['peste', 'pește', 'pescăruș', 'somon', 'ton', 'sardine', 'macrou', 
                                'crap', 'șalău', 'salau', 'fish', 'seafood']
                },
                'pește': {
                    'categories': ['peste'],
                    'keywords': ['peste', 'pește', 'pescăruș', 'somon', 'ton', 'sardine', 'macrou', 
                                'crap', 'șalău', 'salau',                     'fish', 'seafood']
                },
                'crustacee': {
                    'categories': [],
                    'keywords': ['crustacee', 'creveți', 'creveti', 'crab', 'homar', 'langustă', 
                                'langusta', 'shrimp', 'lobster', 'crab']
                },
                'arahide': {
                    'categories': [],
                    'keywords': ['arahide', 'alune de pământ', 'alune de pamant', 'peanut', 'peanuts']
                }
            }
            
            for user_allergy in user_allergies:
                user_allergy_clean = user_allergy.strip().lower()
                
                allergy_info = None
                for allergy_key, mapping in allergy_mappings.items():
                    if allergy_key == user_allergy_clean or user_allergy_clean in allergy_key or allergy_key in user_allergy_clean:
                        allergy_info = mapping
                        break
                
                if allergy_info:
                    if allergy_info['categories'] and food_category_lower in allergy_info['categories']:
                        return False
                    
                    for keyword in allergy_info['keywords']:
                        if keyword in food_name_lower or keyword in food_category_lower:
                            return False
                
                if food.allergens:
                    food_allergens = [a.strip().lower() for a in food.allergens.split(',') if a.strip()]
                    for allergen in food_allergens:
                        if user_allergy_clean in allergen or allergen in user_allergy_clean:
                            return False
                
                if user_allergy_clean and (user_allergy_clean in food_name_lower or user_allergy_clean in food_category_lower):
                    return False
        
        if user.medical_conditions:
            conditions_lower = user.medical_conditions.lower()
            food_name_lower = food.name.lower() if food.name else ''
            food_category_lower = food.category.lower() if food.category else ''
            
            restrictions = self._parse_food_restrictions(user.medical_conditions)
            
            for forbidden_category in restrictions['forbidden_categories']:
                if forbidden_category in food_category_lower:
                    return False
                
                category_mappings = {
                    'legume': ['legume', 'leguma', 'vegetable', 'vegetables', 'leguminoase'],
                    'fructe': ['fructe', 'fructa', 'fruit', 'fruits'],
                    'cereale': ['cereale', 'cereala', 'grain', 'grains', 'cereal'],
                    'carne': ['carne', 'meat', 'pui', 'porc', 'vita', 'miel'],
                    'peste': ['peste', 'pește', 'pescăruș', 'fish', 'seafood'],
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
                if keyword in food_name_lower or keyword in food_category_lower:
                    return False
            
            if 'rinichi' in conditions_lower or 'oxalat' in conditions_lower or 'renal' in conditions_lower:
                high_oxalate_foods = ['spanac', 'rabarbar', 'nucă', 'ciocolată', 'ceai']
                if any(ox in food_name_lower or ox in food_category_lower for ox in high_oxalate_foods):
                    return False
            
            if 'diabet' in conditions_lower or 'glicemie' in conditions_lower:
                high_gi_foods = ['zahăr', 'sirop', 'dulceață', 'bomboane']
                if any(gi in food_name_lower for gi in high_gi_foods):
                    return False
            
            if 'hipertensiune' in conditions_lower or 'tensiune' in conditions_lower:
                high_sodium_foods = ['sare', 'salam', 'cârnați', 'conservă']
                if any(sod in food_name_lower or sod in food_category_lower for sod in high_sodium_foods):
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
            
            if any(restriction in conditions_lower for restriction in seed_restrictions):
                if 'semințe' in food_category_lower or 'seminte' in food_category_lower:
                    return False
                if any(keyword in food_name_lower for keyword in seed_keywords):
                    return False
            
            nuts_restrictions = [
                'nu am voie nuci', 'nu am voie nucă', 'fără nuci', 'fără nucă',
                'no nuts', 'no nuts allowed', 'fara nuci', 'fara nucă',
                'interzis nuci', 'interzis nucă', 'evit nuci', 'evit nucă'
            ]
            nuts_keywords = ['nuci', 'nucă', 'nuca', 'nuc', 'alune', 'migdale', 'fistic',
                           'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut']
            
            if any(restriction in conditions_lower for restriction in nuts_restrictions):
                if any(keyword in food_name_lower or keyword in food_category_lower for keyword in nuts_keywords):
                    return False
            
            dairy_restrictions = [
                'nu am voie lactate', 'nu am voie lapte', 'fără lactate', 'fără lapte',
                'no dairy', 'no milk', 'fara lactate', 'fara lapte',
                'interzis lactate', 'interzis lapte', 'evit lactate', 'evit lapte'
            ]
            dairy_keywords = ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt', 'telemea',
                            'cascaval', 'ricotta', 'mozzarella', 'gorgonzola', 'parmezan',
                            'cheddar', 'feta', 'brie', 'camembert', 'dairy']
            
            if any(restriction in conditions_lower for restriction in dairy_restrictions):
                if any(keyword in food_name_lower or keyword in food_category_lower for keyword in dairy_keywords):
                    return False
        
        return True
    
    def _calculate_coverage(
        self,
        food: FoodItem,
        deficits: Dict[str, float],
        nutrients_covered: List[str]
    ) -> float:
        """Calculează procentul mediu de acoperire a deficitelor"""
        portion_grams = 150
        total_weighted_coverage = 0
        total_weight = 0
        
        nutrient_mapping = {
            'iron': food.iron or 0,
            'magnesium': food.magnesium or 0,
            'calcium': food.calcium or 0,
            'vitamin_d': food.vitamin_d or 0,
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

