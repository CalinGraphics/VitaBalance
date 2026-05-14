from typing import List, Dict, Optional, Tuple
import re
import unicodedata
from domain.models import FoodItem, UserProfile
from services.medical_rules_loader import normalize_clinical_text
from services.deficit_calculator import DeficitCalculator

# Separă blocurile afișate în UI (Rezumat / detaliu / mențiune) — trebuie să coincidă cu frontend.
EXPL_SECTION_SEP = "\n\n---\n\n"


class ExplanationGenerator:
    """Generează explicații pentru recomandări: text principal + detalii cu valori per porție și VNR (model)."""

    NUTRIENT_LABELS_RO: Dict[str, str] = {
        "iron": "fier",
        "calcium": "calciu",
        "vitamin_d": "vitamina D",
        "vitamin_b12": "vitamina B12",
        "magnesium": "magneziu",
        "protein": "proteine",
        "zinc": "zinc",
        "folate": "folat (B9)",
        "vitamin_a": "vitamina A",
        "vitamin_c": "vitamina C",
        "iodine": "iod",
        "vitamin_k": "vitamina K",
        "potassium": "potasiu",
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
        nutrients_covered: Optional[List[str]] = None,
    ) -> Dict:
        if explanations and len(explanations) > 0:
            return self._generate_from_rule_explanations(
                food=food,
                user=user,
                explanations=explanations,
                matched_rules=matched_rules or [],
                coverage=coverage,
                has_lab_data=has_lab_data,
                deficits=deficits,
                nutrients_covered=nutrients_covered,
            )

        return self._generate_traditional_explanation(
            food=food,
            user=user,
            deficits=deficits,
            score=score,
            coverage=coverage,
        )

    def _generate_from_rule_explanations(
        self,
        food: FoodItem,
        user: UserProfile,
        explanations: List[str],
        matched_rules: List[str],
        coverage: float,
        has_lab_data: bool = False,
        deficits: Optional[Dict[str, float]] = None,
        nutrients_covered: Optional[List[str]] = None,
    ) -> Dict:
        portion = self._estimate_portion_by_category(food, user)
        is_fallback_profile_based = "fallback_profile_based" in matched_rules

        if explanations:
            seen: set[str] = set()
            unique_explanations: List[str] = []
            for ex in explanations:
                t = (ex or "").strip()
                if not t or t in seen:
                    continue
                seen.add(t)
                unique_explanations.append(t)
            main_text = ". ".join(unique_explanations)
        else:
            main_text = f"Am recomandat {food.name.lower()} pentru valoarea sa nutrițională."
        if not has_lab_data and "deficit" in main_text.lower():
            main_text = (
                f"Am recomandat {food.name.lower()} pentru profilul său nutritiv "
                "și compatibilitatea cu nevoile tale generale."
            )

        factual = self._rdi_portion_sentence(
            food, user, portion, nutrients_covered, deficits or {}
        )
        disclaim = "Valorile sunt orientative (catalog + model); nu înlocuiesc consultul medical."
        blocks = [main_text.rstrip().rstrip(".")]
        if factual:
            blocks.append(factual.rstrip().rstrip("."))
        blocks.append(disclaim)
        main_text_out = EXPL_SECTION_SEP.join(blocks)

        reasons = []
        dt = (user.diet_type or "").strip()
        if dt:
            reasons.append(f"Adaptat profilului tău (dietă: {dt}).")
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
        tips = list(dict.fromkeys(tips))
        if not tips:
            tips = ["Poți integra acest aliment în mesele zilnice pentru un echilibru nutrițional mai bun."]
        alternatives = self._generate_alternatives(food, user)

        return {
            "text": main_text_out,
            "portion": portion,
            "reasons": reasons,
            "tips": tips,
            "alternatives": alternatives if alternatives else None,
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

    def _food_nutrient_value(self, food: FoodItem, nutrient: str) -> float:
        m = {
            "iron": food.iron,
            "calcium": food.calcium,
            "vitamin_d": food.vitamin_d,
            "vitamin_b12": food.vitamin_b12,
            "magnesium": food.magnesium,
            "protein": food.protein,
            "zinc": food.zinc,
            "folate": getattr(food, "folate", None),
            "vitamin_a": getattr(food, "vitamin_a", None),
            "vitamin_c": food.vitamin_c,
            "iodine": getattr(food, "iodine", None),
            "vitamin_k": getattr(food, "vitamin_k", None),
            "potassium": getattr(food, "potassium", None),
        }
        v = m.get(nutrient)
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _rdi_reference_amount(self, nutrient: str, rdi: float) -> float:
        """Același reper ca la compararea din motor: vitamina D în catalog = µg/100g, VNR model = UI/zi."""
        if nutrient == "vitamin_d" and rdi > 0:
            return rdi / 40.0
        return rdi

    def _format_amount_for_nutrient(self, nutrient: str, amount: float) -> str:
        if amount <= 0:
            return "0"
        if nutrient == "protein":
            return f"{amount:.1f} g"
        if nutrient in ("vitamin_b12", "folate", "vitamin_a", "iodine", "vitamin_k"):
            return f"{amount:.1f} μg"
        if nutrient == "vitamin_d":
            return f"{amount:.1f} μg"
        if nutrient in ("iron", "calcium", "magnesium", "zinc", "vitamin_c"):
            return f"{amount:.1f} mg"
        if nutrient == "potassium":
            return f"{amount:.0f} mg"
        return f"{amount:.1f}"

    def _rdi_portion_sentence(
        self,
        food: FoodItem,
        user: UserProfile,
        portion: int,
        nutrients_covered: Optional[List[str]],
        deficits: Dict[str, float],
    ) -> str:
        """Propoziție scurtă cu cantități la porție și % față de VNR în model (DeficitCalculator)."""
        calc = DeficitCalculator()
        keys = list(nutrients_covered or [])
        # Strict: afișăm doar nutrienți cu deficit modelat > 0 (nevoia pacientului), nu „bonus” din motor.
        keys = [k for k in keys if (deficits.get(k, 0) or 0) > 0]
        if not keys:
            keys = [k for k, v in sorted(deficits.items(), key=lambda x: -x[1]) if v and v > 0]
        seen = set()
        ordered = []
        for k in keys:
            if k in seen:
                continue
            if k not in self.NUTRIENT_LABELS_RO:
                continue
            seen.add(k)
            ordered.append(k)
        ordered = [k for k in ordered if self._food_nutrient_value(food, k) > 0][:4]
        if not ordered:
            return ""

        parts: List[str] = []
        for n in ordered:
            v100 = self._food_nutrient_value(food, n)
            rdi = calc.get_rdi(n, user)
            ref = self._rdi_reference_amount(n, rdi)
            if ref <= 0:
                continue
            at_portion = v100 * float(portion) / 100.0
            pct = min(100.0, (at_portion / ref) * 100.0)
            label = self.NUTRIENT_LABELS_RO.get(n, n)
            amt = self._format_amount_for_nutrient(n, at_portion)
            parts.append(
                f"{label}: ~{amt} (~{pct:.0f}% din reperul zilnic din model pentru {label})"
            )
        if not parts:
            return ""
        return "La porția estimată (~" + str(portion) + " g): " + " · ".join(parts) + "."

    def _generate_traditional_explanation(
        self,
        food: FoodItem,
        user: UserProfile,
        deficits: Dict[str, float],
        score: float,
        coverage: float,
    ) -> Dict:
        portion = self._estimate_portion_by_category(food, user)
        reasons: List[str] = []
        tips: List[str] = []
        alternatives: List[str] = []

        top_nutrients = self._get_top_nutrients(food, deficits)
        calc = DeficitCalculator()

        if top_nutrients:
            intro = f"Pentru **{food.name}**, în modelul actual de necesități nutriționale, contează în special: "
            detail_parts: List[str] = []
            for nutrient, value_per_100 in top_nutrients:
                label = self.NUTRIENT_LABELS_RO.get(nutrient, nutrient)
                at_portion = value_per_100 * float(portion) / 100.0
                rdi = calc.get_rdi(nutrient, user)
                ref = self._rdi_reference_amount(nutrient, rdi)
                pct = min(100.0, (at_portion / ref) * 100.0) if ref > 0 else 0.0
                amt = self._format_amount_for_nutrient(nutrient, at_portion)
                detail_parts.append(
                    f"**{label}** (~**{amt}** la ~{portion} g, adică ~**{pct:.0f}%** din reperul zilnic din model pentru {label})"
                )
            main_text = intro + "; ".join(detail_parts) + "."
        else:
            main_text = (
                f"**{food.name}** este propus(ă) ca opțiune compatibilă cu profilul și restricțiile tale, "
                f"cu acoperire orientativă în model de ~**{coverage:.0f}%** pentru țintele curente."
            )

        for nutrient, value_per_100 in top_nutrients[:3]:
            label = self.NUTRIENT_LABELS_RO.get(nutrient, nutrient)
            reasons.append(
                f"Conține ~{self._format_amount_for_nutrient(nutrient, value_per_100)} {label} per 100 g (date catalog)."
            )

        if user.diet_type == "vegan":
            reasons.append("Compatibil cu regim vegan")
        elif user.diet_type == "vegetarian":
            reasons.append("Compatibil cu regim vegetarian")

        if user.medical_conditions:
            conditions = [c.strip().lower() for c in user.medical_conditions.split(",")]
            if "rinichi" in str(conditions) or "oxalati" in str(conditions):
                if "spanac" in food.name.lower() or "rabarbar" in food.name.lower():
                    reasons.append("Atenție: poate fi nepotrivit dacă ai restricții legate de oxalați/rinichi.")

        if food.iron and food.iron > 1.0:
            tips.append("Sfat: combină cu surse de vitamina C (ex. ardei, citrice) pentru absorbție mai bună a fierului.")
        if food.calcium and food.calcium > 50:
            tips.append("Sfat: separă temporal consumul foarte bogat în calciu de cel foarte bogat în fier, dacă e cazul.")
        if food.vitamin_d and food.vitamin_d > 0:
            tips.append("Sfat: expunerea solară moderată contribuie la sinteza vitaminei D; urmează recomandările medicale.")

        if food.category == "legume":
            alternatives.append("Dacă nu-ți place, încearcă alte legume verzi: linte, fasole, mazăre")
        elif food.category == "carne":
            alternatives.append(self._meat_alternatives_line(user))

        return {
            "text": main_text,
            "portion": portion,
            "reasons": reasons,
            "tips": tips if tips else None,
            "alternatives": alternatives if alternatives else None,
        }

    def _estimate_portion_by_category(self, food: FoodItem, user: Optional[UserProfile] = None) -> int:
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

    def _get_top_nutrients(self, food: FoodItem, deficits: Dict[str, float]) -> List[Tuple[str, float]]:
        """Nutrienți din aliment care se suprapun cu deficitele modelate, sortați după relevanță."""
        keys = list(self.NUTRIENT_LABELS_RO.keys())
        relevance: List[Tuple[str, float, float]] = []
        for nutrient in keys:
            deficit = deficits.get(nutrient, 0) or 0
            if deficit <= 0:
                continue
            value = self._food_nutrient_value(food, nutrient)
            if value <= 0:
                continue
            relevance.append((nutrient, value, value * deficit))
        relevance.sort(key=lambda x: x[2], reverse=True)
        return [(a, b) for a, b, _ in relevance[:4]]

    def _generate_tips_from_rules(
        self, matched_rules: List[str], food: FoodItem, user: Optional[UserProfile] = None
    ) -> List[str]:
        tips: List[str] = []
        if food.iron and food.iron > 1.0:
            tips.append("Combină cu vitamina C (lămâie, ardei) pentru absorbție mai bună a fierului.")
        if food.calcium and food.calcium > 50:
            tips.append("Evită consumul simultan cu alimente foarte bogate în fier, pentru absorbție optimă.")
        if food.vitamin_d and food.vitamin_d > 0:
            tips.append("Expunerea la soare (10–15 min zilnic) poate ajuta la sinteza vitaminei D.")
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
        alternatives: List[str] = []
        if food.category == "legume":
            alternatives.append("Dacă nu-ți place, încearcă alte legume verzi: linte, fasole, mazăre")
        elif food.category == "carne":
            alternatives.append(self._meat_alternatives_line(user))
        elif food.category == "lactate":
            alternatives.append("Alternative: iaurt, brânză, lapte")
        return alternatives
