
from typing import List, Dict, Optional, Tuple
import re
from dataclasses import dataclass
from domain.models import FoodItem, UserProfile, LabResultItem
from enum import Enum
from services.medical_rules_loader import load_medical_rules_config, normalize_clinical_text
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
        self.medical_rules_config = self._load_medical_rules_config()

    def _normalize_text(self, value: str) -> str:
        """Normalizează textul pentru matching robust (diacritice, underscore, spații)."""
        return normalize_clinical_text(value)

    def _load_medical_rules_config(self) -> Dict:
        """Încarcă reguli medicale externe (fără hardcodare în cod)."""
        return load_medical_rules_config()

    def _user_has_hyperlipidemia_profile(self, conditions_norm: str) -> bool:
        if not conditions_norm:
            return False
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
        return any(m in conditions_norm for m in markers)

    def _portion_for_food(self, food: FoodItem, user: UserProfile) -> int:
        cat = self._normalize_text(food.category or "")
        portions = {
            "peste & fructe de mare": 130,
            "carne": 130,
            "oua": 120,
            "leguminoase": 170,
            "legume": 200,
            "fructe": 180,
            "lactate": 200,
            "nuci & seminte": 40,
            "cereale": 150,
            "alte": 140,
            "altele": 140,
        }
        base = float(portions.get(cat, 150))
        activity_factor = {
            "sedentary": 0.95,
            "moderate": 1.0,
            "active": 1.1,
            "very_active": 1.2,
        }.get((user.activity_level or "moderate").lower(), 1.0)
        adjusted = int(round(base * activity_factor))
        return max(30, adjusted)
    
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

            # Acoperire generică pentru nutrienții deficitari care nu au reguli scoped active.
            # Fără acest pas, unele deficite (ex. anemie + vitamina D) pot părea că nu schimbă recomandările.
            portion_grams = self._portion_for_food(food, user)
            food_values = {
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
            nutrient_labels = {
                'iron': 'fier',
                'magnesium': 'magneziu',
                'calcium': 'calciu',
                'vitamin_d': 'vitamina D',
                'vitamin_b12': 'vitamina B12',
                'zinc': 'zinc',
                'vitamin_c': 'vitamina C',
                'folate': 'folat',
                'vitamin_a': 'vitamina A',
                'iodine': 'iod',
                'vitamin_k': 'vitamina K',
                'potassium': 'potasiu',
            }
            for nutrient_str, deficit_amount in deficits.items():
                if deficit_amount <= 0 or nutrient_str in nutrient_scores:
                    continue
                nutrient_value = food_values.get(nutrient_str, 0)
                if nutrient_value <= 0:
                    continue
                portion_value = (nutrient_value * portion_grams) / 100.0
                generic_score = min(4.0, (portion_value / max(1.0, deficit_amount)) * 2.5)
                if generic_score <= 0:
                    continue
                nutrient_scores[nutrient_str] = generic_score
                final_explanations.append(
                    f"Contribuie la deficitul de {nutrient_labels.get(nutrient_str, nutrient_str)}: "
                    f"~{portion_value:.1f} per porția sugerată ({portion_grams}g)."
                )
                final_matched_rules.append(f"generic_{nutrient_str}")
            
            total_score = sum(nutrient_scores.values())
            nutrients_covered = list(nutrient_scores.keys())
            coverage = self._calculate_coverage(food, user, deficits, nutrients_covered)
            
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
        
        coverage = self._calculate_coverage(food, user, deficits, nutrients_covered)
        
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
            portion_grams = self._portion_for_food(food, user)
            portion_value = (iron_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=10.0,
                explanation=f"Recomandat pentru deficit sever de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_severe_high",
                nutrient=NutrientType.IRON.value,
                priority=10
            )
        
        elif deficiency_level == DeficiencyLevel.SEVERE and iron_content >= thresholds['medium']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (iron_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.0,
                explanation=f"Recomandat pentru deficit sever de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_severe_medium",
                nutrient=NutrientType.IRON.value,
                priority=9
            )
        
        # REGULĂ 3: Deficit moderat + Iron high
        elif deficiency_level == DeficiencyLevel.MODERATE and iron_content >= thresholds['high']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (iron_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.5,
                explanation=f"Recomandat pentru deficit moderat de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_moderate_high",
                nutrient=NutrientType.IRON.value,
                priority=8
            )
        
        # REGULĂ 4: Deficit moderat + Iron medium
        elif deficiency_level == DeficiencyLevel.MODERATE and iron_content >= thresholds['medium']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (iron_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=6.0,
                explanation=f"Recomandat pentru deficit moderat de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_moderate_medium",
                nutrient=NutrientType.IRON.value,
                priority=7
            )
        
        # REGULĂ 5: Deficit mild + Iron high
        elif deficiency_level == DeficiencyLevel.MILD and iron_content >= thresholds['high']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (iron_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=7.0,
                explanation=f"Recomandat pentru deficit ușor de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="iron_mild_high",
                nutrient=NutrientType.IRON.value,
                priority=6
            )
        
        # REGULĂ 6: Orice deficit + Iron low (dar peste pragul minim)
        elif iron_content >= thresholds['low']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (iron_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=4.0,
                explanation=f"Recomandat pentru aport de fier. Conține {iron_content:.1f} mg fier/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg fier, acoperind {coverage_pct:.1f}% din deficit.",
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
            portion_grams = self._portion_for_food(food, user)
            portion_value = (magnesium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=10.0,
                explanation=f"Recomandat pentru deficit sever de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_severe_high",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=10
            )
        
        elif deficiency_level == DeficiencyLevel.SEVERE and magnesium_content >= thresholds['medium']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (magnesium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.0,
                explanation=f"Recomandat pentru deficit sever de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_severe_medium",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=9
            )
        
        # REGULĂ 3: Deficit moderat + Magnesium high
        elif deficiency_level == DeficiencyLevel.MODERATE and magnesium_content >= thresholds['high']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (magnesium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.5,
                explanation=f"Recomandat pentru deficit moderat de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_moderate_high",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=8
            )
        
        # REGULĂ 4: Deficit moderat + Magnesium medium
        elif deficiency_level == DeficiencyLevel.MODERATE and magnesium_content >= thresholds['medium']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (magnesium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=6.0,
                explanation=f"Recomandat pentru deficit moderat de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_moderate_medium",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=7
            )
        
        # REGULĂ 5: Deficit mild + Magnesium high
        elif deficiency_level == DeficiencyLevel.MILD and magnesium_content >= thresholds['high']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (magnesium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=7.0,
                explanation=f"Recomandat pentru deficit ușor de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="magnesium_mild_high",
                nutrient=NutrientType.MAGNESIUM.value,
                priority=6
            )
        
        # REGULĂ 6: Orice deficit + Magnesium low
        elif magnesium_content >= thresholds['low']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (magnesium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=4.0,
                explanation=f"Recomandat pentru aport de magneziu. Conține {magnesium_content:.1f} mg magneziu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg magneziu, acoperind {coverage_pct:.1f}% din deficit.",
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
            portion_grams = self._portion_for_food(food, user)
            portion_value = (calcium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=10.0,
                explanation=f"Recomandat pentru deficit sever de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_severe_high",
                nutrient=NutrientType.CALCIUM.value,
                priority=10
            )
        
        elif deficiency_level == DeficiencyLevel.SEVERE and calcium_content >= thresholds['medium']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (calcium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.0,
                explanation=f"Recomandat pentru deficit sever de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_severe_medium",
                nutrient=NutrientType.CALCIUM.value,
                priority=9
            )
        
        # REGULĂ 3: Deficit moderat + Calcium high
        elif deficiency_level == DeficiencyLevel.MODERATE and calcium_content >= thresholds['high']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (calcium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=8.5,
                explanation=f"Recomandat pentru deficit moderat de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_moderate_high",
                nutrient=NutrientType.CALCIUM.value,
                priority=8
            )
        
        # REGULĂ 4: Deficit moderat + Calcium medium
        elif deficiency_level == DeficiencyLevel.MODERATE and calcium_content >= thresholds['medium']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (calcium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=6.0,
                explanation=f"Recomandat pentru deficit moderat de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_moderate_medium",
                nutrient=NutrientType.CALCIUM.value,
                priority=7
            )
        
        # REGULĂ 5: Deficit mild + Calcium high
        elif deficiency_level == DeficiencyLevel.MILD and calcium_content >= thresholds['high']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (calcium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=7.0,
                explanation=f"Recomandat pentru deficit ușor de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
                rule_name="calcium_mild_high",
                nutrient=NutrientType.CALCIUM.value,
                priority=6
            )
        
        # REGULĂ 6: Orice deficit + Calcium low
        elif calcium_content >= thresholds['low']:
            portion_grams = self._portion_for_food(food, user)
            portion_value = (calcium_content * portion_grams) / 100
            coverage_pct = min(100, (portion_value / deficit) * 100)
            return RuleResult(
                matched=True,
                score=4.0,
                explanation=f"Recomandat pentru aport de calciu. Conține {calcium_content:.1f} mg calciu/100g. "
                           f"O porție de {portion_grams}g oferă ~{portion_value:.1f} mg calciu, acoperind {coverage_pct:.1f}% din deficit.",
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
    
    # Sinonime: când utilizatorul menționează X, verificăm și variantele în numele alimentelor
    FOOD_RESTRICTION_SYNONYMS: Dict[str, List[str]] = {
        'pătlăgele': ['pătlăgele', 'patlagele', 'vinete', 'eggplant'],
        'vinete': ['vinete', 'pătlăgele', 'patlagele'],
        'roșii': ['roșii', 'rosii', 'tomate', 'tomatoes'],
        'tomate': ['tomate', 'roșii', 'rosii'],
        'ardei': ['ardei', 'piper', 'pepper'],
        'ciocolată': ['ciocolată', 'ciocolata', 'chocolate', 'ciocolata'],
        'cafea': ['cafea', 'coffee', 'espresso'],
        'alcool': ['alcool', 'bere', 'vin', 'vinuri'],
        'zahăr': ['zahăr', 'zahar', 'sugar', 'dulce'],
        'dulciuri': ['dulciuri', 'dulce', 'bomboane', 'prăjituri'],
        'sare': ['sare', 'sodium', 'sarat'],
        'gluten': ['gluten', 'grâu', 'grau', 'făină', 'faina', 'pâine', 'paine'],
        'spanac': ['spanac', 'spinach'],
        'varză': ['varză', 'varza', 'varza', 'cabbage', 'broccoli'],
        'fasole': ['fasole', 'beans', 'fasole'],
        'linte': ['linte', 'lentils'],
        'mazăre': ['mazăre', 'mazare', 'mazăre', 'peas'],
        'castraveți': ['castraveți', 'castraveti', 'cucumber'],
        'ceapă': ['ceapă', 'ceapa', 'onion'],
        'usturoi': ['usturoi', 'garlic'],
        'cartofi': ['cartofi', 'potato', 'cartof'],
    }

    def _parse_food_restrictions(self, medical_conditions: str) -> Dict[str, List[str]]:
        """
        Parsează condițiile medicale și identifică interziceri pentru categorii de alimente.
        Extrage și restricțiile din condiții medicale cunoscute.
        
        Returnează un dicționar cu:
        - 'forbidden_categories': lista de categorii interzise
        - 'forbidden_keywords': lista de cuvinte cheie interzise
        - 'preferred_categories': categorii preferate (ex: vreau carne de porc)
        """
        if not medical_conditions:
            return {'forbidden_categories': [], 'forbidden_keywords': [], 'preferred_categories': []}
        
        conditions_lower = self._normalize_text(medical_conditions)
        forbidden_categories = []
        forbidden_keywords = []
        
        # 1) Condiții medicale din config extern → restricții alimentare
        for rule in self.medical_rules_config.get("condition_food_rules", []):
            condition_patterns = [self._normalize_text(x) for x in rule.get("condition_patterns", [])]
            avoid_keywords = [self._normalize_text(x) for x in rule.get("avoid_keywords", [])]
            if any(p and p in conditions_lower for p in condition_patterns):
                for kw in avoid_keywords:
                    if kw and kw not in forbidden_keywords:
                        forbidden_keywords.append(kw)
        
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
            'pui': [
                'nu mananc pui', 'nu mănânc pui', 'fara pui', 'fără pui',
                'no chicken', 'evit pui', 'interzis pui', 'nu pot pui', 'nu pot mânca pui'
            ],
            'porc': [
                'nu mananc porc', 'nu mănânc porc', 'fara porc', 'fără porc',
                'no pork', 'evit porc', 'interzis porc', 'nu pot porc', 'nu pot mânca porc'
            ],
            'vita': [
                'nu mananc vita', 'nu mănânc vită', 'nu mananc vaca', 'nu mănânc vacă',
                'fara vita', 'fără vită', 'no beef', 'evit vita', 'interzis vita'
            ],
            'miel': [
                'nu mananc miel', 'nu mănânc miel', 'fara miel', 'fără miel',
                'no lamb', 'evit miel', 'interzis miel', 'nu pot miel'
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
            ],
            'roșii': [
                'nu mananc rosii', 'nu mănânc roșii', 'fara rosii', 'fără roșii',
                'no tomatoes', 'evit rosii', 'evit roșii', 'nu pot rosii',
                'alergie la rosii', 'alergie la roșii', 'intoleranță la roșii'
            ],
            'ardei': [
                'nu mananc ardei', 'nu mănânc ardei', 'fara ardei', 'fără ardei',
                'no peppers', 'evit ardei', 'nu pot ardei', 'alergie la ardei'
            ],
            'ciocolată': [
                'nu mananc ciocolata', 'nu mănânc ciocolată', 'fara ciocolata', 'fără ciocolată',
                'no chocolate', 'evit ciocolata', 'nu am voie ciocolata'
            ],
            'cafea': [
                'nu beau cafea', 'nu pot cafea', 'fara cafea', 'fără cafea',
                'no coffee', 'evit cafea', 'nu am voie cafea'
            ],
            'alcool': [
                'nu beau alcool', 'fara alcool', 'fără alcool', 'no alcohol',
                'evit alcool', 'abstinent', 'nu am voie alcool'
            ],
            'zahăr': [
                'nu mananc zahar', 'nu mănânc zahăr', 'fara zahar', 'fără zahăr',
                'low sugar', 'no sugar', 'fără dulciuri', 'evit zahar', 'evit zahăr'
            ],
            'gluten': [
                'fara gluten', 'fără gluten', 'no gluten', 'evit gluten',
                'intoleranță gluten', 'celiachie', 'sensibilitate la gluten'
            ],
        }
        
        for category, patterns in category_patterns.items():
            patterns_norm = [self._normalize_text(p) for p in patterns]
            if any(pattern in conditions_lower for pattern in patterns_norm):
                forbidden_categories.append(category)

        # Extrage explicit liste compuse după negări de tip:
        # "nu mananc peste, pui", "nu am voie peste si pui", etc.
        list_patterns = [
            r'nu\s+(?:mananc|pot manca|am voie)\s+([^.;!?]+)',
            r'fara\s+([^.;!?]+)',
            r'evit\s+([^.;!?]+)',
            r'nu\s+consum\s+([^.;!?]+)',
            r'exclud\s+([^.;!?]+)',
            r'interzis\s+([^.;!?]+)',
        ]
        for pattern in list_patterns:
            for m in re.finditer(pattern, conditions_lower):
                segment = m.group(1)
                # Tăiem eventuale continuări care schimbă sensul propoziției.
                segment = re.split(r'\b(?:dar|insa|except|in afara de)\b', segment)[0]
                parts = re.split(r',|\bsi\b|\bsau\b', segment)
                for part in parts:
                    token = part.strip()
                    if not token:
                        continue
                    # Curățare de stop words uzuale din expresii compuse.
                    token = re.sub(r'\b(?:de|din|la|cu|pe|care|ce|sa)\b', ' ', token).strip()
                    token = re.sub(r'\s+', ' ', token).strip()
                    if len(token) > 2 and token not in forbidden_keywords:
                        forbidden_keywords.append(token)
        
        # Patternuri generale – extrag orice aliment menționat ca interzis
        general_patterns = [
            r'nu\s+(?:mănânc|mananc|pot\s+mânca|pot\s+mananca|am\s+voie)\s+(?:să\s+)?(?:manc|mânc)\s+([a-zăâîșț\s]+?)(?:\.|,|;|$|\s+și\s+|\s+si\s+|\s+sau\s+|\s+or\s+)',
            r'nu\s+(?:mănânc|mananc|pot\s+mânca|pot\s+mananca)\s+([a-zăâîșț]+)',
            r'nu\s+am\s+voie\s+(?:la\s+|să\s+mânc\s+|sa\s+mananc\s+)?([a-zăâîșț\s]+?)(?:\.|,|;|$|\s+și\s+|\s+si\s+|\s+sau\s+)',
            r'nu\s+am\s+voie\s+([a-zăâîșț]+)',
            r'fără\s+([a-zăâîșț\s]+?)(?:\s|\.|,|;|$)',
            r'fara\s+([a-zăâîșț\s]+?)(?:\s|\.|,|;|$)',
            r'evit\s+([a-zăâîșț]+)',
            r'interzis\s+([a-zăâîșț]+)',
            r'(?:nu\s+)?suport\s+([a-zăâîșț]+)',
            r'(?:nu\s+)?suportă\s+([a-zăâîșț]+)',
            r'(?:mă|ma)\s+deranjează\s+([a-zăâîșț]+)',
            r'am\s+probleme\s+(?:cu\s+|la\s+)([a-zăâîșț]+)',
            r'intoleranță\s+(?:la\s+)?([a-zăâîșț]+)',
            r'intoleranta\s+(?:la\s+)?([a-zăâîșț]+)',
            r'alergie\s+(?:la\s+)?([a-zăâîșț]+)',
            r'alergic\s+(?:la\s+)?([a-zăâîșț]+)',
            r'nu\s+pot\s+tolera\s+([a-zăâîșț]+)',
            r'(?:sau|or|și|si)\s+([a-zăâîșț]+)\s+(?:nu\s+)?(?:mănânc|mananc|am\s+voie)',
            # Formulări de tipul „alimente care au cartofi”, „alimente care conțin X”
            r'alimente\s+care\s+au\s+([a-zăâîșț\s]+?)(?:\.|,|;|$)',
            r'alimente\s+care\s+conțin\s+([a-zăâîșț\s]+?)(?:\.|,|;|$)',
        ]
        
        for pattern in general_patterns:
            matches = re.findall(pattern, conditions_lower)
            for match in matches:
                # Curăță și extrage cuvinte
                words = [w.strip() for w in match.split() if len(w.strip()) > 2 and w.strip() not in ('sau', 'și', 'si', 'sau', 'de', 'la', 'cu')]
                for w in words:
                    if w not in forbidden_keywords:
                        forbidden_keywords.append(w)
                if len(match.strip()) > 2 and len(words) == 0 and match.strip() not in forbidden_keywords:
                    forbidden_keywords.append(match.strip())
        
        # Extragem și din enunțuri "X sau Y nu mănânc"
        split_phrases = re.split(r'[.,;!?]', conditions_lower)
        for phrase in split_phrases:
            if 'nu mănânc' in phrase or 'nu mananc' in phrase or 'nu am voie' in phrase or 'fără' in phrase or 'fara' in phrase:
                parts = re.split(r'\s+(?:sau|or|și|si)\s+', phrase)
                for part in parts:
                    m = re.search(r'(?:nu\s+(?:mănânc|mananc|am\s+voie)|fără|fara|evit)\s+(.+)', part)
                    if m:
                        extracted = m.group(1).strip()
                        words = [w.strip() for w in re.split(r'[\s,]+', extracted) if len(w.strip()) > 2]
                        for w in words:
                            if w not in forbidden_keywords:
                                forbidden_keywords.append(w)
        
        # Normalizare: scoatem articole/sufixe românești (lactatele->lactate, rosii->roșii)
        def _stem_ro(word: str) -> str:
            w = word.strip().lower()
            for suf in ['le', 'ul', 'ului', 'ei', 'ilor', 'ele']:
                if len(w) > len(suf) + 2 and w.endswith(suf):
                    return w[:-len(suf)]
            return w
        
        # Expandăm cu sinonime + stem
        expanded_keywords: List[str] = []
        seen: set = set()
        for kw in forbidden_keywords:
            kw_norm = self._normalize_text(kw)
            for form in [kw_norm, _stem_ro(kw_norm)]:
                if form and len(form) > 2 and form not in seen:
                    expanded_keywords.append(form)
                    seen.add(form)
            if kw_norm in self.FOOD_RESTRICTION_SYNONYMS:
                for syn in self.FOOD_RESTRICTION_SYNONYMS[kw_norm]:
                    syn_norm = self._normalize_text(syn)
                    if syn_norm not in seen:
                        expanded_keywords.append(syn_norm)
                        seen.add(syn_norm)
        forbidden_keywords = expanded_keywords
        
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
            'gluten': ['gluten', 'grâu', 'grau', 'wheat'],
            'roșii': ['rosii', 'roșii', 'tomate', 'tomatoes'],
            'ardei': ['ardei', 'piper'],
            'ciocolată': ['ciocolata', 'ciocolată', 'chocolate'],
            'cafea': ['cafea', 'coffee'],
            'alcool': ['alcool', 'bere', 'vin'],
            'zahăr': ['zahar', 'zahăr', 'sugar'],
        }
        
        positive_patterns = [
            ('vreau', ['porc', 'pui', 'vita', 'vită', 'miel', 'peste', 'pește', 'carne']),
            ('doresc', ['porc', 'pui', 'vita', 'vită', 'miel', 'peste', 'pește', 'carne']),
            ('prefer', ['porc', 'pui', 'vita', 'vită', 'miel', 'peste', 'pește']),
        ]
        preferred_categories: List[str] = []
        for verb, categories in positive_patterns:
            for cat in categories:
                if f'{verb} {cat}' in conditions_lower or f'{verb} carne de {cat}' in conditions_lower:
                    preferred_categories.append(cat)
        
        words = re.split(r'[,\s\.;]+', conditions_lower)
        for word in words:
            word = word.strip()
            if len(word) > 2:
                for category, keywords in simple_food_keywords.items():
                    if word in keywords:
                        if category not in forbidden_categories:
                            if not any(positive in conditions_lower for positive in [
                                'pot mânca', 'pot mananca', 'pot consuma', 'mănânc', 'mananc',
                                'consum', 'mănâncă', 'mananca', 'vreau', 'doresc', 'prefer'
                            ]):
                                forbidden_categories.append(category)
                                break
        
        return {
            'forbidden_categories': forbidden_categories,
            'forbidden_keywords': forbidden_keywords,
            'preferred_categories': list(set(preferred_categories))
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
                    'keywords': ['gluten', 'grâu', 'grau', 'grău', 'făină', 'faina', 
                                'pâine', 'paine', 'pâini', 'paste', 'spaghete', 'macaroane', 
                                'tortilla', 'cereale', 'wheat', 'barley', 'rye', 'seitan', 
                                'ovăz', 'orz', 'secară', 'malț']
                },
                'nuci': {
                    'categories': [],
                    'keywords': [
                        'nuci', 'nuca', 'nucă', 'alune', 'migdale', 'fistic',
                        'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut',
                        'pignoli', 'pinoli', 'nuci de pin', 'nuca de pin',
                        'pesto', 'kibbeh', 'baklava', 'nougat', 'gianduja', 'marzipan', 'martipan',
                    ]
                },
                'nucă': {
                    'categories': [],
                    'keywords': [
                        'nuci', 'nuca', 'nucă', 'alune', 'migdale', 'fistic',
                        'caju', 'macadamia', 'pecan', 'nuts', 'almond', 'walnut', 'hazelnut',
                        'pignoli', 'pinoli', 'nuci de pin', 'nuca de pin',
                        'pesto', 'kibbeh', 'baklava', 'nougat', 'gianduja', 'marzipan', 'martipan',
                    ]
                },
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
                        'midie', 'midii', 'scoici', 'scallop', 'calamar', 'sepie', 'icre', 'hering',
                        'anchois', 'sushi', 'sashimi',
                    ]
                },
                'pește': {
                    'categories': ['peste', 'fructe de mare'],
                    'keywords': [
                        'peste', 'pește', 'pescarus', 'somon', 'ton', 'sardine', 'macrou',
                        'crap', 'salau', 'fish', 'seafood', 'homar', 'lobster', 'crevet', 'crab',
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
                
                allergy_info = None
                for allergy_key, mapping in allergy_mappings.items():
                    if allergy_key == user_allergy_clean or user_allergy_clean in allergy_key or allergy_key in user_allergy_clean:
                        allergy_info = mapping
                        break
                
                if allergy_info:
                    if allergy_info['categories'] and any(
                        self._normalize_text(cat) in food_category_lower
                        for cat in allergy_info['categories']
                    ):
                        return False

                    for keyword in allergy_info['keywords']:
                        kw = self._normalize_text(keyword)
                        if kw and (kw in food_name_lower or kw in food_category_lower):
                            return False
                
                if food.allergens:
                    food_allergens = [a.strip().lower() for a in food.allergens.split(',') if a.strip()]
                    for allergen in food_allergens:
                        if user_allergy_clean in allergen or allergen in user_allergy_clean:
                            return False
                
                if user_allergy_clean and (user_allergy_clean in food_name_lower or user_allergy_clean in food_category_lower):
                    return False
        
        if user.medical_conditions:
            conditions_lower = self._normalize_text(user.medical_conditions)
            food_name_lower = self._normalize_text(food.name or '')
            food_category_lower = self._normalize_text(food.category or '')
            
            restrictions = self._parse_food_restrictions(user.medical_conditions)
            preferred = set(restrictions.get('preferred_categories', []) or [])
            
            for forbidden_category in restrictions['forbidden_categories']:
                # Dacă utilizatorul a spus "vreau carne de porc" etc., permite alimentul preferat
                if forbidden_category in preferred:
                    continue
                if preferred and forbidden_category == 'carne':
                    if any(p in food_category_lower or p in food_name_lower for p in ['porc', 'pui', 'vita', 'vită', 'miel']) and \
                       any(p in preferred for p in ['porc', 'pui', 'vita', 'vită', 'miel']):
                        continue
                
                if self._normalize_text(forbidden_category) in food_category_lower:
                    return False
                
                category_mappings = {
                    'legume': ['legume', 'leguma', 'vegetable', 'vegetables', 'leguminoase'],
                    'fructe': ['fructe', 'fructa', 'fruit', 'fruits'],
                    'cereale': ['cereale', 'cereala', 'grain', 'grains', 'cereal'],
                    'carne': ['carne', 'meat', 'pui', 'porc', 'vita', 'miel'],
                    'pui': ['pui', 'puișor', 'puisoare', 'chicken', 'curcan', 'curcană', 'găină', 'gaina'],
                    'porc': ['porc', 'porcine', 'pork', 'bacon', 'șuncă', 'sunca', 'ceafă', 'ceafa', 'muschi', 'cârnați', 'carnati'],
                    'vita': ['vita', 'vită', 'vaca', 'vacă', 'beef', 'carne de vita', 'carne de vită'],
                    'miel': ['miel', 'miel de', 'lamb', 'oaie', 'mouton'],
                    'peste': [
                        'peste', 'pește', 'pescarus', 'fish', 'seafood', 'fructe de mare',
                        'homar', 'lobster', 'crevet', 'crab', 'midie', 'scoici', 'calamar', 'sepie',
                    ],
                    'lactate': ['lactate', 'lapte', 'dairy', 'milk'],
                    'semințe': ['semințe', 'seminte', 'seeds'],
                    'nuci': ['nuci', 'nucă', 'nuts'],
                    'leguminoase': ['leguminoase', 'fasole', 'linte', 'legumes', 'beans'],
                    'ouă': ['ouă', 'oua', 'ou', 'eggs'],
                    'soia': ['soia', 'soy'],
                    'roșii': ['roșii', 'rosii', 'tomate', 'tomatoes', 'ketchup', 'sos de roșii'],
                    'ardei': ['ardei', 'ardei gras', 'piper', 'pepper', 'ardei iute'],
                    'ciocolată': ['ciocolată', 'ciocolata', 'chocolate', 'cacao'],
                    'cafea': ['cafea', 'coffee', 'espresso', 'cappuccino'],
                    'alcool': ['alcool', 'bere', 'vin', 'vinuri', 'alcoholic'],
                    'zahăr': ['zahăr', 'zahar', 'sugar', 'dulce', 'dulciuri', 'bomboane', 'prăjituri'],
                    'gluten': ['gluten', 'grâu', 'grau', 'făină', 'faina', 'pâine', 'paine', 'paste', 'spaghete'],
                }
                
                if forbidden_category in category_mappings:
                    for variant in category_mappings[forbidden_category]:
                        variant_norm = self._normalize_text(variant)
                        if variant_norm in food_category_lower or variant_norm in food_name_lower:
                            return False
            
            for keyword in restrictions['forbidden_keywords']:
                kw = self._normalize_text(keyword)
                if not kw:
                    continue
                if re.search(rf"\b{re.escape(kw)}\b", food_name_lower) or re.search(rf"\b{re.escape(kw)}\b", food_category_lower):
                    return False
                if kw in food_name_lower or kw in food_category_lower:
                    return False
            
            # Reguli de tip "dacă ai condiția X, evită trigger-ele Y" din config extern.
            for rule in self.medical_rules_config.get("condition_trigger_rules", []):
                condition_patterns = [self._normalize_text(x) for x in rule.get("condition_patterns", [])]
                avoid_keywords = [self._normalize_text(x) for x in rule.get("avoid_keywords", [])]
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
            
            if any(self._normalize_text(r) in conditions_lower for r in seed_restrictions):
                if 'semințe' in food_category_lower or 'seminte' in food_category_lower:
                    return False
                if any(self._normalize_text(k) in food_name_lower for k in seed_keywords):
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
            
            if any(self._normalize_text(r) in conditions_lower for r in nuts_restrictions):
                if any(self._normalize_text(k) in food_name_lower or self._normalize_text(k) in food_category_lower for k in nuts_keywords):
                    return False
            
            dairy_restrictions = [
                'nu am voie lactate', 'nu am voie lapte', 'fără lactate', 'fără lapte',
                'no dairy', 'no milk', 'fara lactate', 'fara lapte',
                'interzis lactate', 'interzis lapte', 'evit lactate', 'evit lapte'
            ]
            dairy_keywords = ['lactate', 'lapte', 'branza', 'iaurt', 'smantana', 'unt', 'telemea',
                            'cascaval', 'ricotta', 'mozzarella', 'gorgonzola', 'parmezan',
                            'cheddar', 'feta', 'brie', 'camembert', 'dairy']
            
            if any(self._normalize_text(r) in conditions_lower for r in dairy_restrictions):
                if any(self._normalize_text(k) in food_name_lower or self._normalize_text(k) in food_category_lower for k in dairy_keywords):
                    return False
        
        lipids = self._normalize_text(user.medical_conditions or "")
        if self._user_has_hyperlipidemia_profile(lipids):
            chol = float(food.cholesterol or 0)
            fatv = float(food.fat or 0)
            if chol >= 95 or (fatv >= 24 and chol >= 40):
                return False

        return True
    
    def _calculate_coverage(
        self,
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        nutrients_covered: List[str]
    ) -> float:
        """
        Calculează procentul mediu de acoperire.
        Ajustare importantă: când deficitul estimat e foarte mic (sau când biomarker-ul e ușor sub prag),
        raportul (portion/deficit) saturează imediat la 100% și pare „mereu 100”.
        Pentru stabilitate, folosim un denominator minim legat de RDI (25% din RDI) pentru nutrienții deficitari.
        """
        portion_grams = self._portion_for_food(food, user)
        total_weighted_coverage = 0
        total_weight = 0

        # RDI per nutrient pentru a evita denom foarte mic -> 100% peste tot
        try:
            from services.deficit_calculator import DeficitCalculator
            calc = DeficitCalculator()
            rdi_map = {k: calc.get_rdi(k, user) for k in deficits.keys()}
        except Exception:
            rdi_map = {}
        
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
                    rdi = rdi_map.get(nutrient) or 0
                    denom = deficits[nutrient]
                    if rdi and rdi > 0:
                        denom = max(denom, 0.25 * rdi)
                    # Randament descrescător: evită saturarea la 100% pentru deficite mici.
                    # Ex: portion=4.5, denom=2 => 4.5/(4.5+2)=69% (în loc de 225% -> 100).
                    coverage_pct = (portion_value / (portion_value + denom) * 100) if (portion_value > 0 and denom > 0) else 0
                    # Ponderăm după deficit (nu după denom) ca să păstrăm importanța reală a golului estimat.
                    weight = deficits[nutrient]
                    total_weighted_coverage += coverage_pct * weight
                    total_weight += weight
        
        return total_weighted_coverage / total_weight if total_weight > 0 else 0

