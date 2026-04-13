from typing import Dict, Optional
import re
import unicodedata
from domain.models import UserProfile, LabResultItem
from services.medical_rules_loader import normalize_clinical_text


class DeficitCalculator:
    # Nutrienți care au corespondent direct în modelul de analize.
    # Dacă există un set de analize, dar valoarea e NULL pentru unul dintre acești
    # nutrienți, îl tratăm ca „necunoscut” și NU estimăm deficit din dietă.
    LAB_BACKED_NUTRIENTS = {
        'iron', 'calcium', 'vitamin_d', 'vitamin_b12', 'magnesium',
        'protein', 'zinc', 'folate', 'vitamin_a', 'iodine', 'vitamin_k', 'potassium'
    }

    RDI_TABLES = {
        'iron': {
            'M': {'18-50': 8, '50+': 8},
            'F': {'18-50': 18, '50+': 8},
            'other': {'18-50': 13, '50+': 8}
        },
        'calcium': {
            'M': {'18-50': 1000, '50+': 1000},
            'F': {'18-50': 1000, '50+': 1200},
            'other': {'18-50': 1000, '50+': 1100}
        },
        'vitamin_d': {
            'M': {'18-70': 600, '70+': 800},
            'F': {'18-70': 600, '70+': 800},
            'other': {'18-70': 600, '70+': 800}
        },
        'vitamin_b12': {
            'M': {'all': 2.4},
            'F': {'all': 2.4},
            'other': {'all': 2.4}
        },
        'magnesium': {
            'M': {'18-30': 400, '30+': 420},
            'F': {'18-30': 310, '30+': 320},
            'other': {'18-30': 355, '30+': 370}
        },
        'protein': {
            'M': {'sedentary': 0.8, 'moderate': 1.0, 'active': 1.2, 'very_active': 1.5},
            'F': {'sedentary': 0.8, 'moderate': 0.9, 'active': 1.1, 'very_active': 1.3},
            'other': {'sedentary': 0.8, 'moderate': 0.95, 'active': 1.15, 'very_active': 1.4}
        },
        'zinc': {
            'M': {'all': 11},
            'F': {'all': 8},
            'other': {'all': 9.5}
        },
        'folate': {
            'M': {'all': 400},
            'F': {'all': 400, 'pregnancy': 600},
            'other': {'all': 400}
        },
        'vitamin_a': {
            'M': {'all': 900},
            'F': {'all': 700},
            'other': {'all': 800}
        },
        'vitamin_c': {
            'M': {'all': 90},
            'F': {'all': 75},
            'other': {'all': 82.5}
        },
        'iodine': {
            'M': {'all': 150},
            'F': {'all': 150},
            'other': {'all': 150}
        },
        'vitamin_k': {
            'M': {'all': 120},
            'F': {'all': 90},
            'other': {'all': 105}
        },
        'potassium': {
            'M': {'all': 3400},
            'F': {'all': 2600},
            'other': {'all': 3000}
        }
    }

    def _normalized_sex(self, user: UserProfile) -> str:
        """M / F / other — tolerează m/f, male/female, femeie/bărbat din UI sau DB."""
        raw = normalize_clinical_text(user.sex or "")
        if not raw or raw == "other":
            return "other"
        if raw in ("m", "male", "man"):
            return "M"
        if raw in ("f", "female", "woman"):
            return "F"
        if raw.startswith("fem") or raw.startswith("femin"):
            return "F"
        if "barbat" in raw or raw.startswith("mascul"):
            return "M"
        if len(raw) == 1 and raw in "mf":
            return raw.upper()
        return "other"

    def _normalized_activity(self, user: UserProfile) -> str:
        raw = (user.activity_level or "moderate").strip().lower()
        aliases = {
            "low": "sedentary",
            "lightly_active": "moderate",
            "light": "moderate",
            "medium": "moderate",
            "high": "active",
            "very active": "very_active",
            "extreme": "very_active",
        }
        a = aliases.get(raw, raw)
        valid = {"sedentary", "moderate", "active", "very_active"}
        return a if a in valid else "moderate"

    def _normalized_diet(self, user: UserProfile) -> str:
        d = (user.diet_type or "omnivore").strip().lower()
        valid = {"omnivore", "vegetarian", "vegan", "pescatarian"}
        return d if d in valid else "omnivore"

    def _user_likely_pregnant(self, user: UserProfile) -> bool:
        blob = normalize_clinical_text(
            f"{user.medical_conditions or ''} {getattr(user, 'bio', None) or ''}"
        )
        if not blob:
            return False
        markers = (
            "sarcina", "sarcinii", "gravid", "gravida", "pregnant", "pregnancy",
            "insarcinata", "însărcinată",
        )
        return any(m in blob for m in markers)
    
    def get_age_group(self, age: int) -> str:
        """Determină grupa de vârstă"""
        if age is None:
            return '18-50'  # Default pentru vârsta lipsă
        if age < 18:
            return '18-30'
        elif age < 30:
            return '18-30'
        elif age < 50:
            return '18-50'
        elif age < 70:
            return '50+'
        else:
            return '70+'
    
    def get_rdi(self, nutrient: str, user: UserProfile) -> float:
        if nutrient not in self.RDI_TABLES:
            return 0
        
        table = self.RDI_TABLES[nutrient]
        sex = self._normalized_sex(user)
        if sex not in table:
            sex = "other"
        age_group = self.get_age_group(user.age)
        weight = user.weight if user.weight and user.weight > 0 else 70.0
        
        if nutrient == 'protein':
            activity = self._normalized_activity(user)
            if activity not in table[sex]:
                activity = "moderate"
            rdi_per_kg = table[sex][activity]
            return rdi_per_kg * weight

        if nutrient == "vitamin_d":
            vd_key = "70+" if (user.age or 0) >= 70 else "18-70"
            branch = table[sex]
            return branch.get(vd_key, list(branch.values())[0])

        if nutrient == "folate" and self._user_likely_pregnant(user) and sex == "F":
            branch = table[sex]
            if "pregnancy" in branch:
                return float(branch["pregnancy"])

        if nutrient == "iron" and self._user_likely_pregnant(user) and sex == "F":
            return 27.0

        if 'all' in table[sex]:
            return table[sex]['all']
        if age_group in table[sex]:
            return table[sex][age_group]
        return list(table[sex].values())[0]
    
    def estimate_current_intake(self, nutrient: str, user: UserProfile) -> float:
        estimates = {
            'iron': {
                'omnivore': 12,
                'vegetarian': 8,
                'vegan': 6,
                'pescatarian': 10
            },
            'calcium': {
                'omnivore': 800,
                'vegetarian': 700,
                'vegan': 500,
                'pescatarian': 750
            },
            'vitamin_d': {
                'omnivore': 200,
                'vegetarian': 150,
                'vegan': 100,
                'pescatarian': 180
            },
            'vitamin_b12': {
                'omnivore': 4,
                'vegetarian': 2,
                'vegan': 0.5,
                'pescatarian': 3
            },
            'magnesium': {
                'omnivore': 300,
                'vegetarian': 280,
                'vegan': 250,
                'pescatarian': 290
            },
            'protein': {
                'omnivore': 70,
                'vegetarian': 60,
                'vegan': 50,
                'pescatarian': 65
            },
            'zinc': {
                'omnivore': 10,
                'vegetarian': 8,
                'vegan': 6,
                'pescatarian': 9
            },
            'folate': {
                'omnivore': 300,
                'vegetarian': 280,
                'vegan': 250,
                'pescatarian': 290
            },
            'vitamin_a': {
                'omnivore': 600,
                'vegetarian': 500,
                'vegan': 400,
                'pescatarian': 550
            },
            'vitamin_c': {
                'omnivore': 80,
                'vegetarian': 75,
                'vegan': 70,
                'pescatarian': 77
            },
            'iodine': {
                'omnivore': 120,
                'vegetarian': 100,
                'vegan': 80,
                'pescatarian': 110
            },
            'vitamin_k': {
                'omnivore': 80,
                'vegetarian': 70,
                'vegan': 60,
                'pescatarian': 75
            },
            'potassium': {
                'omnivore': 2500,
                'vegetarian': 2800,
                'vegan': 3000,
                'pescatarian': 2600
            }
        }
        
        if nutrient in estimates:
            diet = self._normalized_diet(user)
            return estimates[nutrient][diet]
        return 0
    
    def calculate_deficits(self, user: UserProfile, lab_results: Optional[LabResultItem] = None) -> Dict[str, float]:
        deficits = {}
        
        # Toți nutrienții conform tabelului de deficiențe nutriționale
        nutrients = [
            'iron', 'calcium', 'vitamin_d', 'vitamin_b12', 'magnesium', 
            'protein', 'zinc', 'folate', 'vitamin_a', 'vitamin_c', 
            'iodine', 'vitamin_k', 'potassium'
        ]
        
        # Extrage textul din observații pentru a detecta nutrienți preferați
        notes_text = ""
        if user and getattr(user, 'medical_conditions', None):
            notes_text = (user.medical_conditions or "").lower()
        if lab_results and getattr(lab_results, 'notes', None):
            notes_text = f"{notes_text} {lab_results.notes or ''}".lower()
        
        preferred_nutrients = self._parse_preferred_nutrients(notes_text)

        # Dacă nu există analize deloc SAU există un rând dar toate valorile sunt NULL,
        # nu calculăm deficite medicale estimate. În acest caz, recomandările vor merge
        # pe fallback de profil, fără mesaje de tip „deficit de X”.
        has_lab_panel = False
        if lab_results is not None:
            for nutrient in self.LAB_BACKED_NUTRIENTS:
                if nutrient == 'iron':
                    # Pentru fier, acceptăm panel valid dacă există fie ferritină, fie hemoglobină.
                    v = getattr(lab_results, 'ferritin', None)
                    if v is None:
                        v = getattr(lab_results, 'hemoglobin', None)
                else:
                    v = self._get_lab_value(nutrient, lab_results)
                if v is not None:
                    has_lab_panel = True
                    break
        if not has_lab_panel:
            # Dacă utilizatorul menționează explicit în observații nevoia de anumiți nutrienți,
            # păstrăm doar acele prioritizări minime.
            for nutrient in preferred_nutrients:
                if nutrient in nutrients:
                    rdi = self.get_rdi(nutrient, user)
                    deficits[nutrient] = max(deficits.get(nutrient, 0), 0.3 * rdi)
            return deficits
        
        for nutrient in nutrients:
            rdi = self.get_rdi(nutrient, user)
            
            if lab_results:
                # Tratament special pentru fier:
                # preferăm ferritina; dacă lipsește, folosim hemoglobina.
                if nutrient == 'iron':
                    if getattr(lab_results, 'ferritin', None) is not None:
                        lab_value = lab_results.ferritin
                        deficit = self._calculate_deficit_from_labs(nutrient, lab_value, rdi)
                        deficits[nutrient] = max(0, deficit)
                        continue
                    if getattr(lab_results, 'hemoglobin', None) is not None:
                        deficit = self._calculate_iron_deficit_from_hemoglobin(
                            lab_results.hemoglobin, user, rdi
                        )
                        deficits[nutrient] = max(0, deficit)
                        continue
                    deficits[nutrient] = 0
                    continue

                lab_value = self._get_lab_value(nutrient, lab_results)
                
                if lab_value is not None:
                    deficit = self._calculate_deficit_from_labs(nutrient, lab_value, rdi)
                    deficits[nutrient] = max(0, deficit)
                    continue
                # Dacă există analize, dar acest marker nu a fost completat (NULL),
                # nu presupunem deficit pe baza estimărilor din dietă/profil.
                if nutrient in self.LAB_BACKED_NUTRIENTS:
                    deficits[nutrient] = 0
                    continue
            
            current_intake = self.estimate_current_intake(nutrient, user)
            deficit = max(0, rdi - current_intake)
            deficits[nutrient] = deficit
        
        # Dacă utilizatorul menționează nevoie de nutrienți în observații,
        # adaugă un deficit minim pentru a prioritiza alimente bogate în ei
        for nutrient in preferred_nutrients:
            if nutrient in nutrients:
                rdi = self.get_rdi(nutrient, user)
                current = deficits.get(nutrient, 0)
                if current < 0.3 * rdi:
                    deficits[nutrient] = max(current, 0.3 * rdi)
        
        return deficits
    
    def _parse_preferred_nutrients(self, notes_text: str) -> set:
        """Detectează din observații nutrienți preferați pe baza unui set extins de pattern-uri."""
        preferred = set()
        if not notes_text:
            return preferred

        normalized = unicodedata.normalize("NFKD", notes_text.lower()).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"\s+", " ", normalized).strip()

        pattern_map = {
            'iron': [
                r"\banemi[eaic]\b", r"\bferipriv", r"\bfier\b", r"\bferitin", r"\bhemoglobin[ae]?\b",
                r"(deficienta|deficit|lipsa)\s+de\s+fier",
            ],
            'vitamin_d': [
                r"\bvit(?:amina)?\s*d\b", r"\b25\s*oh\s*d\b", r"\bhipovitaminoza d\b",
                r"(deficienta|deficit|lipsa)\s+de\s+vit(?:amina)?\s*d",
            ],
            'vitamin_b12': [
                r"\bb\s*12\b", r"\bcobalamin", r"\banemie megaloblastica\b",
                r"(deficienta|deficit|lipsa)\s+de\s+vit(?:amina)?\s*b\s*12",
            ],
            'magnesium': [
                r"\bmagneziu\b", r"\bmagnesium\b", r"\bhypomagnes", r"\bhipomagnez",
                r"(deficienta|deficit|lipsa)\s+de\s+magneziu",
            ],
            'calcium': [
                r"\bcalciu\b", r"\bcalcium\b", r"\bhipocalc", r"\bosteopen", r"\bosteopor",
                r"(deficienta|deficit|lipsa)\s+de\s+calciu",
            ],
            'zinc': [
                r"\bzinc\b", r"\bzn\b", r"\bhipozinc",
                r"(deficienta|deficit|lipsa)\s+de\s+zinc",
            ],
            'folate': [
                r"\bfolat\b", r"\bacid folic\b", r"\bvit(?:amina)?\s*b9\b",
                r"(deficienta|deficit|lipsa)\s+de\s+(folat|acid folic|vit(?:amina)?\s*b9)",
            ],
            'vitamin_a': [
                r"\bvit(?:amina)?\s*a\b", r"\bretinol\b",
                r"(deficienta|deficit|lipsa)\s+de\s+vit(?:amina)?\s*a",
            ],
            'vitamin_k': [
                r"\bvit(?:amina)?\s*k\b", r"\bcoagulare\b",
                r"(deficienta|deficit|lipsa)\s+de\s+vit(?:amina)?\s*k",
            ],
            'iodine': [
                r"\biod\b", r"\biodine\b", r"\btiroid",
                r"(deficienta|deficit|lipsa)\s+de\s+iod",
            ],
            'potassium': [
                r"\bpotasiu\b", r"\bpotassium\b", r"\bhipokaliem",
                r"(deficienta|deficit|lipsa)\s+de\s+potasiu",
            ],
            'protein': [
                r"\bproteine?\b", r"\bhipoprotein", r"\bsarcopen",
                r"(deficienta|deficit|lipsa)\s+de\s+proteine?",
            ],
            'vitamin_c': [
                r"\bvit(?:amina)?\s*c\b", r"\bscorbut\b",
                r"(deficienta|deficit|lipsa)\s+de\s+vit(?:amina)?\s*c",
            ],
        }

        for nutrient, regexes in pattern_map.items():
            if any(re.search(rx, normalized, re.IGNORECASE) for rx in regexes):
                preferred.add(nutrient)
        
        return preferred
    
    def _get_lab_value(self, nutrient: str, lab_results: LabResultItem) -> Optional[float]:
        mapping = {
            'iron': lab_results.ferritin,  # Ferritin este indicator pentru fier
            'calcium': lab_results.calcium,
            'vitamin_d': lab_results.vitamin_d,
            'vitamin_b12': lab_results.vitamin_b12,
            'magnesium': lab_results.magnesium,
            'protein': lab_results.protein,
            'zinc': lab_results.zinc,
            'folate': lab_results.folate if hasattr(lab_results, 'folate') else None,
            'vitamin_a': lab_results.vitamin_a if hasattr(lab_results, 'vitamin_a') else None,
            'iodine': lab_results.iodine if hasattr(lab_results, 'iodine') else None,
            'vitamin_k': lab_results.vitamin_k if hasattr(lab_results, 'vitamin_k') else None,
            'potassium': lab_results.potassium if hasattr(lab_results, 'potassium') else None,
            'vitamin_c': None  # Nu este în modelul LabResult, va folosi estimare
        }
        return mapping.get(nutrient)
    
    def _calculate_deficit_from_labs(self, nutrient: str, lab_value: float, rdi: float) -> float:
        clinical_thresholds = {
            'iron': {'threshold': 30.0, 'unit': 'ferritin_ng_ml'},
            'calcium': {'threshold': 8.5, 'unit': 'mg_dl'},
            'vitamin_d': {'threshold': 20.0, 'unit': 'ng_ml'},
            'vitamin_b12': {'threshold': 200.0, 'unit': 'pg_ml'},
            'magnesium': {'threshold': 1.7, 'unit': 'mg_dl'},
            'protein': {'threshold': 6.0, 'unit': 'g_dl'},
            'zinc': {'threshold': 70.0, 'unit': 'mcg_dl'},
            'folate': {'threshold': 3.0, 'unit': 'ng_ml'},
            'vitamin_a': {'threshold': 20.0, 'unit': 'mcg_dl'},
            'iodine': {'threshold': 100.0, 'unit': 'mcg_l'},
            'potassium': {'threshold': 3.5, 'unit': 'mmol_l'},
        }
        
        if nutrient not in clinical_thresholds:
            return 0
        
        threshold = clinical_thresholds[nutrient]['threshold']
        
        if lab_value < threshold:
            deficit_ratio = (threshold - lab_value) / threshold
            normalized_deficit = min(1.5, max(0.3, deficit_ratio))
            return rdi * normalized_deficit
        else:
            return 0

    def _calculate_iron_deficit_from_hemoglobin(self, hemoglobin: float, user: UserProfile, rdi: float) -> float:
        """
        Fallback pentru fier când ferritina nu este disponibilă:
        estimează severitatea pe baza hemoglobinei.
        """
        sex = self._normalized_sex(user)
        if sex == "M":
            threshold = 13.5  # g/dL — prag orientativ adult
        elif sex == "F":
            threshold = 12.0  # g/dL — prag orientativ adult (non-gravidă; sarcina modifică interpretarea clinică)
        else:
            threshold = 12.5  # g/dL — medie conservatoare dacă sexul e neclar

        if hemoglobin < threshold:
            deficit_ratio = (threshold - hemoglobin) / threshold
            normalized_deficit = min(1.5, max(0.3, deficit_ratio))
            return rdi * normalized_deficit
        return 0

