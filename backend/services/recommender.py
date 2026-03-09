from typing import List, Dict, Optional, Tuple
from domain.models import UserProfile, FoodItem, LabResultItem, FeedbackItem
from services.rule_engine import NutritionalRuleEngine
from services.deficit_calculator import DeficitCalculator

class RecommenderService:
    
    def __init__(self):
        self.rule_engine = NutritionalRuleEngine()
        self.nutrients = [
            'iron', 'calcium', 'magnesium', 'vitamin_d', 'vitamin_b12', 
            'folate', 'zinc', 'vitamin_a', 'vitamin_c', 'iodine', 
            'vitamin_k', 'potassium'
        ]
    
    def generate_recommendations(
        self,
        user: UserProfile,
        deficits: Dict[str, float],
        foods: List[FoodItem],
        lab_results: Optional[LabResultItem] = None,
        user_feedbacks: Optional[List[FeedbackItem]] = None,
        feedback_by_food: Optional[Dict[int, List]] = None
    ) -> List[Dict]:
        """Generează recomandări personalizate pentru utilizator"""
        filtered_deficits = {
            k: v for k, v in deficits.items()
            if k in self.nutrients and v > 0
        }

        # 1) Caz normal: există deficite relevante -> folosește rule engine
        recommendations: List[Dict] = []
        if filtered_deficits:
            for food in foods:
                recommendation = self.rule_engine.evaluate_food(
                    food=food,
                    user=user,
                    deficits=filtered_deficits,
                    lab_results=lab_results
                )

                if recommendation:
                    adjusted_score = self._apply_feedback_adjustments(
                        score=recommendation.score,
                        food=food,
                        user=user,
                        user_feedbacks=user_feedbacks,
                        feedback_by_food=feedback_by_food
                    )

                    recommendations.append({
                        'food_id': recommendation.food_id,
                        'score': adjusted_score,
                        'coverage': recommendation.coverage,
                        'explanations': recommendation.explanations,
                        'matched_rules': recommendation.matched_rules,
                        'nutrients_covered': recommendation.nutrients_covered
                    })

        # 2) Dacă nu există deficite sau regulile sunt prea restrictive și nu întorc nimic,
        # generează un fallback pe baza profilului utilizatorului (dietă, alergii, condiții medicale)
        if not recommendations:
            return self._generate_fallback_recommendations(user=user, foods=foods)

        recommendations.sort(key=lambda x: (x['coverage'], x['score']), reverse=True)
        return recommendations[:20]
    
    def _apply_feedback_adjustments(
        self,
        score: float,
        food: FoodItem,
        user: UserProfile,
        user_feedbacks: Optional[List[FeedbackItem]] = None,
        feedback_by_food: Optional[Dict[int, List]] = None
    ) -> float:
        """Aplică ajustări la scor bazate pe feedback-ul utilizatorului"""
        adjustment_factor = 1.0
        
        if feedback_by_food and food.id in feedback_by_food:
            food_feedbacks = feedback_by_food[food.id]
            ratings = [f.rating for f in food_feedbacks if f.rating is not None]
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                if avg_rating >= 4:
                    adjustment_factor = 1.2
                elif avg_rating >= 3:
                    adjustment_factor = 1.0
                elif avg_rating >= 2:
                    adjustment_factor = 0.8
                elif avg_rating >= 1:
                    adjustment_factor = 0.6
                else:
                    adjustment_factor = 0.4
        
        return score * adjustment_factor

    def _generate_fallback_recommendations(
        self,
        user: UserProfile,
        foods: List[FoodItem],
    ) -> List[Dict]:
        """
        Fallback atunci când nu avem deficite clare sau regulile nu produc recomandări:
        - respectă întotdeauna profilul (dietă, alergii, condiții medicale)
        - prioritizează alimente cu densitate bună de micro și macronutrienți cheie
        """
        calc = DeficitCalculator()
        # RDI generic pentru utilizator, folosit ca referință de „cât de util” este un aliment
        rdi_map: Dict[str, float] = {n: calc.get_rdi(n, user) for n in self.nutrients}

        fallback_recommendations: List[Tuple[float, Dict]] = []

        for food in foods:
            # Respectă toate restricțiile: dacă alimentul nu e compatibil, îl sărim.
            if not self.rule_engine._is_compatible(food, user):  # type: ignore[attr-defined]
                continue

            nutrient_values = {
                'iron': food.iron or 0,
                'calcium': food.calcium or 0,
                'magnesium': food.magnesium or 0,
                'vitamin_d': food.vitamin_d or 0,
                'vitamin_b12': food.vitamin_b12 or 0,
                'folate': getattr(food, 'folate', 0) or 0,
                'zinc': food.zinc or 0,
                'vitamin_a': getattr(food, 'vitamin_a', 0) or 0,
                'vitamin_c': food.vitamin_c or 0,
                'iodine': getattr(food, 'iodine', 0) or 0,
                'vitamin_k': getattr(food, 'vitamin_k', 0) or 0,
                'potassium': getattr(food, 'potassium', 0) or 0,
            }

            portion_grams = 150.0
            total_score = 0.0
            total_coverage = 0.0
            covered_nutrients: List[str] = []

            for nutrient, value_per_100g in nutrient_values.items():
                if value_per_100g <= 0:
                    continue
                rdi = rdi_map.get(nutrient) or 0
                if rdi <= 0:
                    continue
                portion_value = (value_per_100g * portion_grams) / 100.0
                coverage = min(100.0, (portion_value / rdi) * 100.0)
                if coverage <= 0:
                    continue
                total_score += coverage
                total_coverage += coverage
                covered_nutrients.append(nutrient)

            if not covered_nutrients or total_score <= 0:
                continue

            avg_coverage = total_coverage / len(covered_nutrients)

            explanation = (
                "Acest aliment are un profil nutritiv echilibrat și poate susține "
                "aportul zilnic recomandat pentru mai mulți nutrienți esențiali "
                f"({', '.join(sorted(covered_nutrients))})."
            )

            fallback_recommendations.append((
                total_score,
                {
                    'food_id': food.id,
                    'score': total_score,
                    'coverage': avg_coverage,
                    'explanations': [explanation],
                    'matched_rules': ['fallback_profile_based'],
                    'nutrients_covered': covered_nutrients,
                },
            ))

        # Sortează descrescător după scor total (densitate nutritivă globală)
        fallback_recommendations.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in fallback_recommendations[:20]]
