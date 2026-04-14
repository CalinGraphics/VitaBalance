from typing import List, Dict, Optional, Tuple, Any
from dataclasses import replace
import unicodedata
from domain.models import UserProfile, FoodItem, LabResultItem, FeedbackItem
from services.rule_engine import NutritionalRuleEngine
from services.deficit_calculator import DeficitCalculator
from services.medical_rules_loader import normalize_diet_type

class RecommenderService:
    # Dacă regulile pe deficite lasă prea puține variante (ex. vegan + alergii stricte),
    # completăm din recomandări de profil compatibile, fără a dubla food_id.
    MIN_RECOMMENDATIONS_TARGET = 10

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
        """Generează recomandări personalizate pentru utilizator.

        Folosește întotdeauna toate sursele de context:
        - profil (vârstă, greutate, dietă, alergii, condiții medicale)
        - analize medicale (valorile + câmpul de observații/diagnostic)
        """
        # Integrează observațiile / diagnosticul din analize în câmpul medical_conditions,
        # astfel încât restricțiile de tip „nu am voie pește sau legume” să fie respectate.
        effective_user = user
        if lab_results and lab_results.notes:
            merged_conditions = f"{user.medical_conditions or ''} {lab_results.notes or ''}".strip()
            if merged_conditions:
                effective_user = replace(user, medical_conditions=merged_conditions)
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
                    user=effective_user,
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
            fb = self._generate_fallback_recommendations(
                user=effective_user,
                foods=foods,
                target_nutrients=list(filtered_deficits.keys()) if filtered_deficits else None,
            )
            return self._filter_compatible_recommendations(effective_user, foods, fb)

        recommendations.sort(key=lambda x: (x['coverage'], x['score']), reverse=True)
        balanced = self._rebalance_by_category(
            user=effective_user, foods=foods, recommendations=recommendations
        )
        final = self._filter_compatible_recommendations(effective_user, foods, balanced)

        if len(final) < self.MIN_RECOMMENDATIONS_TARGET:
            fb = self._generate_fallback_recommendations(
                user=effective_user,
                foods=foods,
                target_nutrients=list(filtered_deficits.keys()) if filtered_deficits else None,
            )
            fb_ok = self._filter_compatible_recommendations(effective_user, foods, fb)
            seen = {r.get("food_id") for r in final if r.get("food_id") is not None}
            for r in fb_ok:
                fid = r.get("food_id")
                if fid is None or fid in seen:
                    continue
                seen.add(fid)
                final.append(r)
            final.sort(key=lambda x: (x["coverage"], x["score"]), reverse=True)
            balanced2 = self._rebalance_by_category(
                user=effective_user, foods=foods, recommendations=final
            )
            final = self._filter_compatible_recommendations(effective_user, foods, balanced2)

        return final

    def _filter_compatible_recommendations(
        self,
        user: UserProfile,
        foods: List[FoodItem],
        recommendations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Ultimă verificare: niciun aliment incompatibil cu profilul nu rămâne în listă."""
        by_id = {f.id: f for f in foods}
        out: List[Dict[str, Any]] = []
        for rec in recommendations:
            fid = rec.get("food_id")
            food = by_id.get(fid) if fid is not None else None
            if food is None:
                continue
            if self.rule_engine._is_compatible(food, user):  # type: ignore[attr-defined]
                out.append(rec)
        return out
    
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
        target_nutrients: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Fallback atunci când nu avem deficite clare sau regulile nu produc recomandări:
        - respectă întotdeauna profilul (dietă, alergii, condiții medicale)
        - prioritizează alimente cu densitate bună de micro și macronutrienți cheie
        """
        calc = DeficitCalculator()
        # RDI generic pentru utilizator, folosit ca referință de „cât de util” este un aliment
        active_targets = [n for n in (target_nutrients or []) if n in self.nutrients]
        nutrient_pool = active_targets if active_targets else list(self.nutrients)
        rdi_map: Dict[str, float] = {n: calc.get_rdi(n, user) for n in nutrient_pool}

        fallback_recommendations: List[Tuple[float, Dict]] = []

        nutrient_labels: Dict[str, str] = {
            'iron': 'Fier',
            'calcium': 'Calciu',
            'magnesium': 'Magneziu',
            'vitamin_d': 'Vitamina D',
            'vitamin_b12': 'Vitamina B12',
            'folate': 'Folat / acid folic',
            'zinc': 'Zinc',
            'vitamin_a': 'Vitamina A',
            'vitamin_c': 'Vitamina C',
            'iodine': 'Iod',
            'vitamin_k': 'Vitamina K',
            'potassium': 'Potasiu',
        }

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

            portion_grams = float(self._portion_for_category(food.category, user))
            total_score = 0.0
            total_coverage = 0.0
            covered_nutrients: List[str] = []
            nutrient_coverages: List[Tuple[str, float, float]] = []

            for nutrient, value_per_100g in nutrient_values.items():
                if nutrient not in nutrient_pool:
                    continue
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
                nutrient_coverages.append((nutrient, portion_value, coverage))

            if not covered_nutrients or total_score <= 0:
                continue

            # Penalizare pentru categorii mai puțin utile în recomandări principale
            # (ex: condimente/dulciuri/ultra-procesate), chiar dacă pe hârtie au micronutrienți.
            quality_factor = self._category_quality_factor(food.category)
            total_score *= quality_factor
            total_coverage *= quality_factor
            total_score *= self._category_preference_factor(food.category, user)
            total_coverage *= self._category_preference_factor(food.category, user)

            avg_coverage = total_coverage / len(covered_nutrients)

            pretty_nutrients = [
                nutrient_labels.get(n, n) for n in sorted(set(covered_nutrients))
            ]
            nutrients_text = ", ".join(pretty_nutrients)

            # Explicație mai specifică pe aliment:
            # evidențiem top contribuții nutriționale pentru porția sugerată.
            nutrient_coverages.sort(key=lambda x: x[2], reverse=True)
            highlights = nutrient_coverages[:3]
            highlight_parts: List[str] = []
            for nutrient, portion_value, cov in highlights:
                label = nutrient_labels.get(nutrient, nutrient)
                if portion_value >= 10:
                    amount = f"{portion_value:.0f}"
                else:
                    amount = f"{portion_value:.1f}"
                highlight_parts.append(
                    f"{label}: ~{amount} per porție ({cov:.1f}% din aportul zilnic recomandat)"
                )

            explanation = (
                f"{food.name} a fost selectat pe baza compatibilității clinico-nutriționale "
                "cu profilul tău, pentru porția alimentară orientativă recomandată. "
                f"Contribuții nutriționale dominante: {'; '.join(highlight_parts)}. "
                f"Acoperirea globală estimată vizează în principal: {nutrients_text}."
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

        # Diversitate pe categorii: evită top-uri dominate de o singură categorie.
        sorted_items = [item for _, item in fallback_recommendations]
        return self._rebalance_by_category(user=user, foods=foods, recommendations=sorted_items)

    def _normalize_category(self, category: str) -> str:
        raw = (category or "").strip().lower()
        folded = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
        return folded

    def _portion_for_category(self, category: str, user: Optional[UserProfile] = None) -> int:
        cat = self._normalize_category(category)
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
        if user:
            activity_factor = {
                "sedentary": 0.95,
                "moderate": 1.0,
                "active": 1.1,
                "very_active": 1.2,
            }.get((user.activity_level or "moderate").lower(), 1.0)
            base *= activity_factor
        return max(30, int(round(base)))

    def _category_quality_factor(self, category: str) -> float:
        cat = self._normalize_category(category)
        # Penalizăm explicit categoriile procesate/fried pentru a evita top-uri suboptimale clinic.
        if "procesat" in cat or "prăjit" in cat or "prajit" in cat:
            return 0.38
        penalties = {
            "condimente & mirodenii": 0.30,
            "dulciuri": 0.45,
            "snacks": 0.55,
            "bauturi": 0.55,
            "alte": 0.75,
            "altele": 0.75,
        }
        return penalties.get(cat, 1.0)

    def _max_items_per_category(self, category_key: str) -> int:
        caps = {
            "condimente & mirodenii": 1,
            "dulciuri": 1,
            "snacks": 1,
            "bauturi": 1,
        }
        return caps.get(category_key, 4)

    def _category_preference_factor(self, category: str, user: UserProfile) -> float:
        cat = self._normalize_category(category)
        diet = normalize_diet_type(user.diet_type)
        if diet == "omnivore":
            if cat in {"carne", "peste & fructe de mare", "oua"}:
                return 1.12
            if cat in {"nuci & seminte"}:
                return 0.88
        if diet == "pescatarian":
            if cat == "peste & fructe de mare":
                return 1.12
            if cat == "carne":
                return 0.1
        return 1.0

    def _rebalance_by_category(self, user: UserProfile, foods: List[FoodItem], recommendations: List[Dict]) -> List[Dict]:
        food_by_id = {f.id: f for f in foods}
        selected: List[Dict] = []
        per_category_counts: Dict[str, int] = {}
        name_family_counts: Dict[str, int] = {}
        for item in recommendations:
            food_obj = food_by_id.get(item.get("food_id"))
            category_key = self._normalize_category(food_obj.category if food_obj else "")
            max_per_category = self._max_items_per_category(category_key)
            current = per_category_counts.get(category_key, 0)
            if current >= max_per_category:
                continue
            family_key = self._name_family_key(food_obj.name if food_obj else "")
            if family_key:
                fam_count = name_family_counts.get(family_key, 0)
                if fam_count >= 1:
                    continue
            selected.append(item)
            per_category_counts[category_key] = current + 1
            if family_key:
                name_family_counts[family_key] = name_family_counts.get(family_key, 0) + 1
            if len(selected) >= 20:
                break

        # Pentru omnivori, asigură cel puțin 2 recomandări din surse animale dacă sunt disponibile.
        if normalize_diet_type(user.diet_type) == "omnivore":
            animal_categories = {"carne", "peste & fructe de mare", "oua"}
            selected_ids = {x.get("food_id") for x in selected}
            animal_selected = 0
            for item in selected:
                food_obj = food_by_id.get(item.get("food_id"))
                if food_obj and self._normalize_category(food_obj.category) in animal_categories:
                    animal_selected += 1
            if animal_selected < 2:
                for candidate in recommendations:
                    fid = candidate.get("food_id")
                    if fid in selected_ids:
                        continue
                    food_obj = food_by_id.get(fid)
                    if not food_obj:
                        continue
                    if self._normalize_category(food_obj.category) not in animal_categories:
                        continue
                    selected.append(candidate)
                    selected_ids.add(fid)
                    animal_selected += 1
                    if animal_selected >= 2 or len(selected) >= 20:
                        break

        selected.sort(key=lambda x: (x['coverage'], x['score']), reverse=True)
        return selected[:20]

    def _name_family_key(self, food_name: str) -> str:
        name = self._normalize_category(food_name or "")
        if "cartofi prajiti" in name:
            return "cartofi_prajiti"
        if "supa" in name and "conserva" in name:
            return "supa_conserva"
        return ""
