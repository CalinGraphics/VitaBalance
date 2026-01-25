from typing import List, Dict, Optional
from models import Food, User

class ExplanationGenerator:
    """Generează explicații detaliate și personalizate pentru fiecare recomandare"""
    
    def __init__(self):
        self.nutrient_names = {
            'iron': 'fier',
            'calcium': 'calciu',
            'vitamin_d': 'vitamina D',
            'vitamin_b12': 'vitamina B12',
            'magnesium': 'magneziu',
            'protein': 'proteine',
            'zinc': 'zinc'
        }
    
    def generate_explanation(
        self,
        food: Food,
        user: User,
        deficits: Dict[str, float],
        score: float,
        coverage: float,
        explanations: Optional[List[str]] = None,
        matched_rules: Optional[List[str]] = None
    ) -> Dict:
        """Generează o explicație completă pentru o recomandare"""
        if explanations and len(explanations) > 0:
            return self._generate_from_rule_explanations(
                food=food,
                explanations=explanations,
                matched_rules=matched_rules or [],
                coverage=coverage
            )
        
        return self._generate_traditional_explanation(
            food=food,
            user=user,
            deficits=deficits,
            score=score,
            coverage=coverage
        )
    
    def _generate_from_rule_explanations(
        self,
        food: Food,
        explanations: List[str],
        matched_rules: List[str],
        coverage: float
    ) -> Dict:
        portion = 150
        
        if explanations:
            main_text = " ".join(explanations)
        else:
            main_text = f"Am recomandat {food.name.lower()} pentru valoarea sa nutrițională."
        
        reasons = explanations.copy() if explanations else []
        
        if coverage > 0:
            reasons.append(f"Acoperă {coverage:.1f}% din deficitul tău nutrițional total")
        
        tips = self._generate_tips_from_rules(matched_rules, food)
        alternatives = self._generate_alternatives(food)
        
        return {
            'text': main_text,
            'portion': portion,
            'reasons': reasons,
            'tips': tips if tips else None,
            'alternatives': alternatives if alternatives else None
        }
    
    def _generate_traditional_explanation(
        self,
        food: Food,
        user: User,
        deficits: Dict[str, float],
        score: float,
        coverage: float
    ) -> Dict:
        """Generează explicație tradițională (fallback)"""
        portion = 150
        reasons = []
        tips = []
        alternatives = []
        
        top_nutrients = self._get_top_nutrients(food, deficits)
        main_text = f"Am recomandat {food.name.lower()} pentru că "
        
        nutrient_descriptions = []
        for nutrient, value in top_nutrients:
            nutrient_ro = self.nutrient_names.get(nutrient, nutrient)
            portion_value = (value * portion) / 100
            deficit = deficits.get(nutrient, 0)
            if deficit > 0:
                coverage_pct = min(100, (portion_value / deficit) * 100)
                nutrient_descriptions.append(
                    f"conține {value:.1f} mg {nutrient_ro} per 100g, "
                    f"iar o porție de {portion}g îți oferă aproximativ {portion_value:.1f} mg, "
                    f"acoperind {coverage_pct:.1f}% din deficitul tău zilnic estimat ({deficit:.1f} mg)"
                )
        
        main_text += "; ".join(nutrient_descriptions) + "."
        
        for nutrient, value in top_nutrients[:3]:
            nutrient_ro = self.nutrient_names.get(nutrient, nutrient)
            reasons.append(f"Conține {value:.1f} mg {nutrient_ro} per 100g")
            
            deficit = deficits.get(nutrient, 0)
            if deficit > 0:
                portion_value = (value * portion) / 100
                coverage_pct = min(100, (portion_value / deficit) * 100)
                reasons.append(
                    f"O porție de {portion}g acoperă {coverage_pct:.1f}% din deficitul tău de {nutrient_ro}"
                )
        
        if user.diet_type in ['vegetarian', 'vegan']:
            reasons.append("Compatibil cu regim vegetarian")
        elif user.diet_type == 'vegan':
            reasons.append("Compatibil cu regim vegan")
        
        if user.medical_conditions:
            conditions = [c.strip().lower() for c in user.medical_conditions.split(',')]
            if 'rinichi' in str(conditions) or 'oxalati' in str(conditions):
                if 'spanac' in food.name.lower() or 'rabarbar' in food.name.lower():
                    reasons.append("⚠️ Exclus dacă ai probleme cu rinichii (oxalați ridicați)")
        
        if food.iron > 1.0:
            tips.append("Sfat: Combină-l cu vitamina C (ex: lămâie) pentru absorbție mai bună a fierului!")
        
        if food.calcium > 50:
            tips.append("Sfat: Evită consumul simultan cu alimente bogate în fier, pentru o absorbție optimă!")
        
        if food.vitamin_d > 0:
            tips.append("Sfat: Expunerea la soare (10-15 minute zilnic) ajută la sinteza vitaminei D!")
        
        if food.category == 'legume':
            alternatives.append("Dacă nu-ți place, încearcă alte legume verzi: linte, fasole, mazăre")
        elif food.category == 'carne':
            alternatives.append("Alternative: ficat de vită, carne de porc, pește")
        
        return {
            'text': main_text,
            'portion': portion,
            'reasons': reasons,
            'tips': tips if tips else None,
            'alternatives': alternatives if alternatives else None
        }
    
    def _get_top_nutrients(self, food: Food, deficits: Dict[str, float]) -> List[tuple]:
        """Identifică nutrienții principali din aliment care corespund deficitelor"""
        nutrient_values = {
            'iron': food.iron,
            'calcium': food.calcium,
            'vitamin_d': food.vitamin_d / 40,  # Normalizează
            'vitamin_b12': food.vitamin_b12,
            'magnesium': food.magnesium,
            'protein': food.protein,
            'zinc': food.zinc
        }
        
        relevance = []
        for nutrient, value in nutrient_values.items():
            deficit = deficits.get(nutrient, 0)
            if deficit > 0 and value > 0:
                relevance.append((nutrient, value, value * deficit))
        
        relevance.sort(key=lambda x: x[2], reverse=True)
        return [(nutrient, value) for nutrient, value, _ in relevance[:3]]
    
    def _generate_tips_from_rules(self, matched_rules: List[str], food: Food) -> List[str]:
        """Generează sfaturi bazate pe regulile care s-au potrivit"""
        tips = []
        
        # Sfaturi generale bazate pe aliment
        if food.iron and food.iron > 1.0:
            tips.append("Sfat: Combină-l cu vitamina C (ex: lămâie) pentru absorbție mai bună a fierului!")
        
        if food.calcium and food.calcium > 50:
            tips.append("Sfat: Evită consumul simultan cu alimente bogate în fier, pentru o absorbție optimă!")
        
        if food.vitamin_d and food.vitamin_d > 0:
            tips.append("Sfat: Expunerea la soare (10-15 minute zilnic) ajută la sinteza vitaminei D!")
        
        return tips
    
    def _generate_alternatives(self, food: Food) -> List[str]:
        """Generează alternative similare pentru aliment"""
        alternatives = []
        
        if food.category == 'legume':
            alternatives.append("Dacă nu-ți place, încearcă alte legume verzi: linte, fasole, mazăre")
        elif food.category == 'carne':
            alternatives.append("Alternative: ficat de vită, carne de porc, pește")
        elif food.category == 'lactate':
            alternatives.append("Alternative: iaurt, brânză, lapte")
        
        return alternatives

