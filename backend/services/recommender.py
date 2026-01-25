from typing import List, Dict, Optional
import numpy as np
from models import User, Food, LabResult, Feedback
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
        user: User,
        deficits: Dict[str, float],
        foods: List[Food],
        lab_results: Optional[LabResult] = None,
        user_feedbacks: Optional[List[Feedback]] = None,
        feedback_by_food: Optional[Dict[int, List]] = None
    ) -> List[Dict]:
        """
        Generează recomandări personalizate pentru utilizator
        """
        filtered_deficits = {
            k: v for k, v in deficits.items() 
            if k in self.nutrients and v > 0
        }
        
        if not filtered_deficits:
            return []
        
        recommendations = []
        
        for food in foods:
            # Evaluează alimentul folosind rule engine
            recommendation = self.rule_engine.evaluate_food(
                food=food,
                user=user,
                deficits=filtered_deficits,
                lab_results=lab_results
            )
            
            if recommendation:
                # Aplică ajustări bazate pe feedback (dacă există)
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
                    'explanations': recommendation.explanations,  # Lista de explicații din reguli
                    'matched_rules': recommendation.matched_rules,  # Numele regulilor care s-au potrivit
                    'nutrients_covered': recommendation.nutrients_covered
                })
        
        # Sortează după coverage (procent) descrescător, apoi după scor ca tie-breaker
        recommendations.sort(key=lambda x: (x['coverage'], x['score']), reverse=True)
        
        # Returnează recomandările (max 20 pentru performanță)
        return recommendations[:20]
    
    def _apply_feedback_adjustments(
        self,
        score: float,
        food: Food,
        user: User,
        user_feedbacks: Optional[List[Feedback]] = None,
        feedback_by_food: Optional[Dict[int, List]] = None
    ) -> float:
        """
        Aplică ajustări la scor bazate pe feedback-ul utilizatorului
        
        Această metodă permite sistemului să învețe din feedback-ul utilizatorilor,
        ajustând scorurile pentru a reflecta preferințele reale.
        
        Args:
            score: Scorul inițial din rule engine
            food: Alimentul evaluat
            user: Utilizatorul
            user_feedbacks: Feedback-uri generale ale utilizatorului
            feedback_by_food: Feedback-uri grupate pe aliment
        
        Returns:
            Scorul ajustat
        """
        adjustment_factor = 1.0
        
        # Verifică feedback-ul specific pentru acest aliment
        if feedback_by_food and food.id in feedback_by_food:
            food_feedbacks = feedback_by_food[food.id]
            ratings = [f.rating for f in food_feedbacks if f.rating is not None]
            
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                # Ajustează scorul bazat pe rating-ul mediu
                # Rating 5 = +20%, Rating 1 = -20%, Rating -1 = -40%
                if avg_rating >= 4:
                    adjustment_factor = 1.2
                elif avg_rating >= 3:
                    adjustment_factor = 1.0
                elif avg_rating >= 2:
                    adjustment_factor = 0.8
                elif avg_rating >= 1:
                    adjustment_factor = 0.6
                else:  # avg_rating == -1 (dislike)
                    adjustment_factor = 0.4
        
        return score * adjustment_factor
