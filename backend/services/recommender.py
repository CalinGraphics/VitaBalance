from typing import List, Dict, Optional
from domain.models import UserProfile, FoodItem, LabResultItem, FeedbackItem
from services.rule_engine import NutritionalRuleEngine

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
        
        if not filtered_deficits:
            return []
        
        recommendations = []
        
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
