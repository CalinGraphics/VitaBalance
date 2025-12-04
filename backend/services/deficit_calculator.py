from typing import Dict, Optional
from models import User, LabResult

class DeficitCalculator:
    """Calculează deficiențele nutriționale bazate pe profilul utilizatorului și analizele medicale"""
    
    # RDI (Recommended Daily Intake) pe categorii
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
        }
    }
    
    def get_age_group(self, age: int) -> str:
        """Determină grupa de vârstă"""
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
        """Obține RDI pentru un nutrient specific"""
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
        """Estimează aportul curent bazat pe tipul de dietă"""
        # Estimări bazate pe tipul de dietă (valori medii)
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
            }
        }
        
        if nutrient in estimates:
            diet = user.diet_type if user.diet_type in estimates[nutrient] else 'omnivore'
            return estimates[nutrient][diet]
        return 0
    
    def calculate_deficits(self, user: User, lab_results: Optional[LabResult] = None) -> Dict[str, float]:
        """
        Calculează deficiențele pentru toți nutrienții
        Prioritizează rezultatele analizelor medicale când sunt disponibile
        """
        deficits = {}
        
        nutrients = ['iron', 'calcium', 'vitamin_d', 'vitamin_b12', 'magnesium', 'protein', 'zinc']
        
        for nutrient in nutrients:
            rdi = self.get_rdi(nutrient, user)
            
            # Verifică dacă există analize medicale
            if lab_results:
                lab_value = self._get_lab_value(nutrient, lab_results)
                
                if lab_value is not None:
                    # Folosește valoarea din analize și compară cu referințele medicale
                    deficit = self._calculate_deficit_from_labs(nutrient, lab_value, rdi)
                    deficits[nutrient] = max(0, deficit)
                    continue
            
            # Dacă nu există analize, estimează aportul curent
            current_intake = self.estimate_current_intake(nutrient, user)
            deficit = max(0, rdi - current_intake)
            deficits[nutrient] = deficit
        
        return deficits
    
    def _get_lab_value(self, nutrient: str, lab_results: LabResult) -> Optional[float]:
        """Extrage valoarea din analize pentru un nutrient specific"""
        mapping = {
            'iron': lab_results.ferritin,  # Ferritin este indicator pentru fier
            'calcium': lab_results.calcium,
            'vitamin_d': lab_results.vitamin_d,
            'vitamin_b12': lab_results.vitamin_b12,
            'magnesium': lab_results.magnesium,
            'protein': lab_results.protein,
            'zinc': lab_results.zinc
        }
        return mapping.get(nutrient)
    
    def _calculate_deficit_from_labs(self, nutrient: str, lab_value: float, rdi: float) -> float:
        """
        Calculează deficitul bazat pe valorile din analize
        Folosește referințe medicale standard
        """
        # Referințe medicale pentru valori normale
        normal_ranges = {
            'iron': {'min': 15, 'optimal': 50},  # Ferritin ng/mL
            'calcium': {'min': 8.5, 'optimal': 10.5},  # mg/dL
            'vitamin_d': {'min': 20, 'optimal': 30},  # ng/mL
            'vitamin_b12': {'min': 200, 'optimal': 400},  # pg/mL
            'magnesium': {'min': 1.7, 'optimal': 2.2},  # mg/dL
            'protein': {'min': 6.0, 'optimal': 8.0},  # g/dL
            'zinc': {'min': 70, 'optimal': 100}  # mcg/dL
        }
        
        if nutrient not in normal_ranges:
            return 0
        
        normal = normal_ranges[nutrient]
        
        if lab_value < normal['min']:
            # Deficit sever - calculează cât lipsește până la optim
            deficit_ratio = (normal['optimal'] - lab_value) / (normal['optimal'] - normal['min'])
            return rdi * deficit_ratio * 1.5  # Multiplicator pentru deficit sever
        elif lab_value < normal['optimal']:
            # Deficit moderat
            deficit_ratio = (normal['optimal'] - lab_value) / (normal['optimal'] - normal['min'])
            return rdi * deficit_ratio
        else:
            # Valori normale sau optime
            return 0

