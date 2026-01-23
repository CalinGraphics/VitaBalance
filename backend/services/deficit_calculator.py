from typing import Dict, Optional
from models import User, LabResult

class DeficitCalculator:
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
    
    def get_age_group(self, age: int) -> str:
<<<<<<< Updated upstream
        """Determină grupa de vârstă"""
=======
        if age is None:
            return '18-50'  # Default pentru vârsta lipsă
>>>>>>> Stashed changes
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
    
    def get_rdi(self, nutrient: str, user: User) -> float:
        if nutrient not in self.RDI_TABLES:
            return 0
        
        table = self.RDI_TABLES[nutrient]
        sex = user.sex if user.sex in table else 'other'
        age_group = self.get_age_group(user.age)
        
        if nutrient == 'protein':
            # Pentru proteine, RDI este în g/kg corp
            activity = user.activity_level if user.activity_level in table[sex] else 'moderate'
            rdi_per_kg = table[sex][activity]
            return rdi_per_kg * user.weight
        else:
            # Pentru alți nutrienți, verifică grupa de vârstă
            if 'all' in table[sex]:
                return table[sex]['all']
            elif age_group in table[sex]:
                return table[sex][age_group]
            else:
                # Fallback la prima valoare disponibilă
                return list(table[sex].values())[0]
    
    def estimate_current_intake(self, nutrient: str, user: User) -> float:
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
            diet = user.diet_type if user.diet_type in estimates[nutrient] else 'omnivore'
            return estimates[nutrient][diet]
        return 0
    
    def calculate_deficits(self, user: User, lab_results: Optional[LabResult] = None) -> Dict[str, float]:
        deficits = {}
        
        # Toți nutrienții conform tabelului de deficiențe nutriționale
        nutrients = [
            'iron', 'calcium', 'vitamin_d', 'vitamin_b12', 'magnesium', 
            'protein', 'zinc', 'folate', 'vitamin_a', 'vitamin_c', 
            'iodine', 'vitamin_k', 'potassium'
        ]
        
        for nutrient in nutrients:
            rdi = self.get_rdi(nutrient, user)
            
            if lab_results:
                lab_value = self._get_lab_value(nutrient, lab_results)
                
                if lab_value is not None:
                    deficit = self._calculate_deficit_from_labs(nutrient, lab_value, rdi)
                    deficits[nutrient] = max(0, deficit)
                    continue
            
            current_intake = self.estimate_current_intake(nutrient, user)
            deficit = max(0, rdi - current_intake)
            deficits[nutrient] = deficit
        
        return deficits
    
    def _get_lab_value(self, nutrient: str, lab_results: LabResult) -> Optional[float]:
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

