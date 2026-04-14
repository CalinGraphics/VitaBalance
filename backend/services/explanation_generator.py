from typing import List, Dict, Optional, Tuple
import re
import unicodedata
from domain.models import FoodItem, UserProfile
from services.medical_rules_loader import normalize_clinical_text


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
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        score: float,
        coverage: float,
        explanations: Optional[List[str]] = None,
        matched_rules: Optional[List[str]] = None,
        has_lab_data: bool = False,
    ) -> Dict:
        """Generează o explicație completă pentru o recomandare"""
        if explanations and len(explanations) > 0:
            return self._generate_from_rule_explanations(
                food=food,
                user=user,
                explanations=explanations,
                matched_rules=matched_rules or [],
                coverage=coverage,
                has_lab_data=has_lab_data,
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
        food: FoodItem,
        user: UserProfile,
        explanations: List[str],
        matched_rules: List[str],
        coverage: float,
        has_lab_data: bool = False,
    ) -> Dict:
        portion = self._estimate_portion_by_category(food, user)
        is_fallback_profile_based = 'fallback_profile_based' in matched_rules
        
        if explanations:
            main_text = " ".join(explanations)
        else:
            main_text = f"Am recomandat {food.name.lower()} pentru valoarea sa nutrițională."
        if not has_lab_data and "deficit" in main_text.lower():
            main_text = (
                f"Am recomandat {food.name.lower()} pentru profilul său nutritiv "
                "și compatibilitatea cu nevoile tale generale."
            )
        
        # Scurte bullet-uri, fără a repeta paragraful principal (evită dublarea în UI)
        reasons = []
        if is_fallback_profile_based:
            if has_lab_data:
                reasons.append(
                    "Recomandare de profil și analize: aliment compatibil ales pentru completarea "
                    "planului nutrițional; prioritizează în continuare aportul pentru deficitele identificate."
                )
            else:
                reasons.append(
                    "Recomandare de profil (fără biomarkeri disponibili), pe baza compatibilității alimentare."
                )
        elif has_lab_data:
            reasons.append("Recomandare informată de profilul tău și valorile disponibile din analize medicale.")
        else:
            reasons.append("Recomandare bazată pe profilul tău și modelul estimativ de necesar nutrițional.")
        
        tips = self._generate_tips_from_rules(matched_rules, food, user)
        tips.extend(self._clinical_priority_tips(user, main_text))
        # dedupe, păstrează ordinea
        tips = list(dict.fromkeys(tips))
        if not tips:
            tips = ["Poți integra acest aliment în mesele zilnice pentru un echilibru nutrițional mai bun."]
        alternatives = self._generate_alternatives(food, user)
        
        return {
            'text': main_text,
            'portion': portion,
            'reasons': reasons,
            'tips': tips,
            'alternatives': alternatives if alternatives else None
        }

    def _clinical_priority_tips(self, user: Optional[UserProfile], main_text: str) -> List[str]:
        if not user:
            return []
        diet = normalize_clinical_text(user.diet_type or "")
        med = normalize_clinical_text(user.medical_conditions or "")
        blob = f"{normalize_clinical_text(main_text or '')} {med}"
        out: List[str] = []
        if diet == "vegan":
            if "b12" in blob or "vitamina b12" in blob:
                out.append(
                    "Pentru B12 la dietă vegană, prioritizează alimente fortificate (fără soia, dacă e cazul) "
                    "și discută suplimentarea cu medicul curant."
                )
            if "vitamina d" in blob or "vitamin d" in blob:
                out.append(
                    "Pentru vitamina D, include surse fortificate și expunere solară controlată; "
                    "la nevoie, urmează recomandarea medicală pentru suplimentare."
                )
        return out
    
    def _generate_traditional_explanation(
        self,
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        score: float,
        coverage: float
    ) -> Dict:
        """Generează explicație tradițională (fallback)"""
        portion = self._estimate_portion_by_category(food, user)
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
        
        if user.diet_type == 'vegan':
            reasons.append("Compatibil cu regim vegan")
        elif user.diet_type == 'vegetarian':
            reasons.append("Compatibil cu regim vegetarian")
        
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
            alternatives.append(self._meat_alternatives_line(user))
        
        return {
            'text': main_text,
            'portion': portion,
            'reasons': reasons,
            'tips': tips if tips else None,
            'alternatives': alternatives if alternatives else None
        }

    def _estimate_portion_by_category(self, food: FoodItem, user: Optional[UserProfile] = None) -> int:
        """Porție orientativă în grame, diferențiată pe categorii alimentare."""
        category = self._normalize_category(food.category or "")
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
        base = float(portions.get(category, 150))
        if user:
            activity_factor = {
                "sedentary": 0.95,
                "moderate": 1.0,
                "active": 1.1,
                "very_active": 1.2,
            }.get((user.activity_level or "moderate").lower(), 1.0)
            base *= activity_factor
        return max(30, int(round(base)))

    def _normalize_category(self, value: str) -> str:
        raw = (value or "").strip().lower()
        return unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    
    def _get_top_nutrients(self, food: FoodItem, deficits: Dict[str, float]) -> List[tuple]:
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
    
    def _generate_tips_from_rules(
        self, matched_rules: List[str], food: FoodItem, user: Optional[UserProfile] = None
    ) -> List[str]:
        """Generează sfaturi bazate pe regulile care s-au potrivit și pe aliment"""
        tips = []
        
        if food.iron and food.iron > 1.0:
            tips.append("Combină cu vitamina C (lămâie, ardei) pentru absorbție mai bună a fierului.")
        
        if food.calcium and food.calcium > 50:
            tips.append("Evită consumul simultan cu alimente foarte bogate în fier, pentru absorbție optimă.")
        
        if food.vitamin_d and food.vitamin_d > 0:
            tips.append("Expunerea la soare (10-15 min zilnic) ajută la sinteza vitaminei D.")
        
        if food.magnesium and food.magnesium > 50:
            tips.append(self._magnesium_combo_tip(user))
        
        return tips

    def _allergy_fish_egg(self, user: Optional[UserProfile]) -> Tuple[bool, bool]:
        if not user or not user.allergies:
            return False, False
        parts = [
            normalize_clinical_text(p.strip())
            for p in re.split(r"[,;]", user.allergies)
            if p.strip()
        ]
        fish = any(p == "peste" or p.startswith("peste") for p in parts)
        egg = any(p in ("oua", "ou", "oue", "eggs", "egg") for p in parts)
        return fish, egg

    def _magnesium_combo_tip(self, user: Optional[UserProfile]) -> str:
        fish, egg = self._allergy_fish_egg(user)
        if fish and egg:
            return (
                "Magneziul se absoarbe mai bine cu vitamina D; poți combina cu surse vegetale "
                "sau lactate, conform toleranței tale."
            )
        if fish:
            return (
                "Magneziul se absoarbe mai bine cu vitamina D; poți combina cu ouă sau surse vegetale bogate în magneziu."
            )
        if egg:
            return (
                "Magneziul se absoarbe mai bine cu vitamina D; poți combina cu pește sau surse vegetale bogate în magneziu."
            )
        return (
            "Magneziul se absoarbe mai bine cu vitamina D; poți combina cu ou sau pește, dacă ți se potrivesc."
        )

    def _meat_alternatives_line(self, user: Optional[UserProfile]) -> str:
        fish, egg = self._allergy_fish_egg(user)
        base = "Alternative: ficat de vită, carne de porc"
        if not fish and not egg:
            return f"{base}, pește"
        if fish and not egg:
            return f"{base}, ouă (dacă sunt tolerate)"
        if egg and not fish:
            return f"{base}, pește (dacă este tolerat)"
        return f"{base}, leguminoase sau tofu (dacă ți se potrivesc)"

    def _generate_alternatives(self, food: FoodItem, user: Optional[UserProfile] = None) -> List[str]:
        """Generează alternative similare pentru aliment"""
        alternatives = []
        
        if food.category == 'legume':
            alternatives.append("Dacă nu-ți place, încearcă alte legume verzi: linte, fasole, mazăre")
        elif food.category == 'carne':
            alternatives.append(self._meat_alternatives_line(user))
        elif food.category == 'lactate':
            alternatives.append("Alternative: iaurt, brânză, lapte")
        
        return alternatives

