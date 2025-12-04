from typing import List, Dict, Optional
import numpy as np
from models import User, Food, LabResult

class RecommenderService:
    """Serviciu pentru generarea recomandărilor bazate pe algoritmi content-based"""
    
    def __init__(self):
        self.nutrients = ['iron', 'calcium', 'vitamin_d', 'vitamin_b12', 'magnesium', 'protein', 'zinc']
    
    def generate_recommendations(
        self,
        user: User,
        deficits: Dict[str, float],
        foods: List[Food],
        lab_results: Optional[LabResult] = None
    ) -> List[Dict]:
        """
        Generează recomandări personalizate pentru utilizator
        """
        # Aplică reguli medicale critice mai întâi
        critical_foods = self._apply_medical_rules(user, deficits, foods, lab_results)
        
        # Calculează scoruri content-based
        scored_foods = []
        
        for food in foods:
            # Verifică dacă alimentul este compatibil
            if not self._is_compatible(food, user):
                continue
            
            # Calculează scorul content-based
            score = self._calculate_content_score(food, deficits)
            
            # Aplică penalități
            score = self._apply_penalties(score, food, user)
            
            # Calculează acoperirea deficitului
            coverage = self._calculate_coverage(food, deficits)
            
            scored_foods.append({
                'food_id': food.id,
                'score': score,
                'coverage': coverage
            })
        
        # Combină cu alimentele critice
        if critical_foods:
            for cf in critical_foods:
                # Verifică dacă nu există deja în listă
                existing = next((f for f in scored_foods if f['food_id'] == cf['food_id']), None)
                if existing:
                    # Crește scorul pentru alimentele critice
                    existing['score'] = max(existing['score'], cf['score'])
                else:
                    scored_foods.append(cf)
        
        # Sortează după scor
        scored_foods.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_foods
    
    def _calculate_content_score(self, food: Food, deficits: Dict[str, float]) -> float:
        """
        Calculează scorul content-based folosind cosine similarity sau dot product
        """
        # Construiește vectorul alimentului
        food_vector = np.array([
            food.iron,
            food.calcium,
            food.vitamin_d / 40,  # Normalizează (IU -> aproximativ mg echivalent)
            food.vitamin_b12,
            food.magnesium,
            food.protein,
            food.zinc
        ])
        
        # Construiește vectorul nevoilor utilizatorului
        # Normalizează deficiențele pentru a crea un vector de importanță
        max_deficit = max(deficits.values()) if deficits.values() else 1
        need_vector = np.array([
            deficits.get('iron', 0) / max_deficit if max_deficit > 0 else 0,
            deficits.get('calcium', 0) / max_deficit if max_deficit > 0 else 0,
            deficits.get('vitamin_d', 0) / max_deficit if max_deficit > 0 else 0,
            deficits.get('vitamin_b12', 0) / max_deficit if max_deficit > 0 else 0,
            deficits.get('magnesium', 0) / max_deficit if max_deficit > 0 else 0,
            deficits.get('protein', 0) / max_deficit if max_deficit > 0 else 0,
            deficits.get('zinc', 0) / max_deficit if max_deficit > 0 else 0
        ])
        
        # Normalizează vectorul alimentului
        food_norm = np.linalg.norm(food_vector)
        if food_norm == 0:
            return 0
        
        food_vector_normalized = food_vector / food_norm
        
        # Calculează cosine similarity
        need_norm = np.linalg.norm(need_vector)
        if need_norm == 0:
            return 0
        
        need_vector_normalized = need_vector / need_norm
        
        cosine_similarity = np.dot(food_vector_normalized, need_vector_normalized)
        
        # Ajustează scorul pentru a reflecta cantitatea absolută de nutrienți
        # (nu doar similaritatea, ci și cât de mult oferă)
        quantity_bonus = np.sum(food_vector * need_vector) / 100  # Factor de scalare
        
        final_score = cosine_similarity * 0.7 + (quantity_bonus / 10) * 0.3
        
        return float(final_score)
    
    def _is_compatible(self, food: Food, user: User) -> bool:
        """Verifică dacă alimentul este compatibil cu profilul utilizatorului"""
        # Verifică restricții dietetice
        if user.diet_type == 'vegetarian' or user.diet_type == 'vegan':
            meat_categories = ['carne', 'pui', 'porc', 'vita', 'miel']
            if any(cat in food.category.lower() for cat in meat_categories):
                return False
        
        if user.diet_type == 'vegan':
            dairy_categories = ['lactate', 'lapte', 'branza', 'iaurt']
            if any(cat in food.category.lower() for cat in dairy_categories):
                return False
        
        # Verifică alergii
        if user.allergies and food.allergens:
            user_allergies = [a.strip().lower() for a in user.allergies.split(',')]
            food_allergens = [a.strip().lower() for a in food.allergens.split(',')]
            
            for allergy in user_allergies:
                if any(allergy in allergen for allergen in food_allergens):
                    return False
        
        return True
    
    def _apply_penalties(self, score: float, food: Food, user: User) -> float:
        """Aplică penalități pentru feedback negativ anterior"""
        # TODO: Implementează penalități bazate pe feedback-ul utilizatorului
        # Pentru moment, returnează scorul neschimbat
        return score
    
    def _calculate_coverage(self, food: Food, deficits: Dict[str, float]) -> float:
        """
        Calculează procentul din deficit pe care îl acoperă o porție standard (150g)
        """
        portion_grams = 150
        total_coverage = 0
        nutrients_covered = 0
        
        nutrient_mapping = {
            'iron': food.iron,
            'calcium': food.calcium,
            'vitamin_d': food.vitamin_d,
            'vitamin_b12': food.vitamin_b12,
            'magnesium': food.magnesium,
            'protein': food.protein,
            'zinc': food.zinc
        }
        
        for nutrient, deficit in deficits.items():
            if deficit > 0 and nutrient in nutrient_mapping:
                food_value = nutrient_mapping[nutrient]
                portion_value = (food_value * portion_grams) / 100
                
                if deficit > 0:
                    coverage = min(100, (portion_value / deficit) * 100)
                    total_coverage += coverage
                    nutrients_covered += 1
        
        return total_coverage / nutrients_covered if nutrients_covered > 0 else 0
    
    def _apply_medical_rules(
        self,
        user: User,
        deficits: Dict[str, float],
        foods: List[Food],
        lab_results: Optional[LabResult]
    ) -> List[Dict]:
        """
        Aplică reguli medicale critice pentru cazuri severe
        """
        critical_recommendations = []
        
        if lab_results:
            # Deficit sever de fier (ferritin < 15)
            if lab_results.ferritin and lab_results.ferritin < 15:
                # Recomandă surse de fier heme (carne roșie, ficat)
                heme_iron_foods = [
                    f for f in foods
                    if any(cat in f.category.lower() for cat in ['carne', 'ficat', 'vita', 'porc'])
                    and f.iron > 2.0
                ]
                
                for food in heme_iron_foods[:3]:  # Top 3
                    if self._is_compatible(food, user):
                        critical_recommendations.append({
                            'food_id': food.id,
                            'score': 10.0,  # Scor foarte mare pentru prioritizare
                            'coverage': 50.0,
                            'critical': True,
                            'reason': 'Deficit sever de fier - recomandare medicală'
                        })
            
            # Vitamina D scăzută (< 20 ng/mL)
            if lab_results.vitamin_d and lab_results.vitamin_d < 20:
                # Recomandă alimente fortificate cu vitamina D
                vitamin_d_foods = [
                    f for f in foods
                    if f.vitamin_d > 50  # Alimente cu vitamina D
                ]
                
                for food in vitamin_d_foods[:2]:  # Top 2
                    if self._is_compatible(food, user):
                        critical_recommendations.append({
                            'food_id': food.id,
                            'score': 9.0,
                            'coverage': 40.0,
                            'critical': True,
                            'reason': 'Vitamina D scăzută - recomandare medicală'
                        })
            
            # B12 deficitară la vegetarieni/vegani
            if (lab_results.vitamin_b12 and lab_results.vitamin_b12 < 200 and
                (user.diet_type == 'vegetarian' or user.diet_type == 'vegan')):
                # Pentru vegetarieni/vegani cu B12 scăzută, recomandă direct suplimente
                # (dar pentru MVP, putem recomanda alimente fortificate)
                b12_foods = [
                    f for f in foods
                    if f.vitamin_b12 > 1.0
                ]
                
                for food in b12_foods[:2]:
                    if self._is_compatible(food, user):
                        critical_recommendations.append({
                            'food_id': food.id,
                            'score': 8.5,
                            'coverage': 30.0,
                            'critical': True,
                            'reason': 'B12 deficitară - recomandare pentru suplimente'
                        })
        
        return critical_recommendations

