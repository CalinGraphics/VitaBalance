# Validare clinică și limitări

## Rolul aplicației

VitaBalance oferă **sugestii nutriționale orientative** bazate pe reguli și pe datele introduse de utilizator. **Nu înlocuiește** consultul medical, interpretarea analizelor de către medic sau planul terapeutic personalizat.

## Ce ar trebui validat extern

- **Setul de reguli** din `ScopedRulesEngine` / `NutritionalRuleEngine` față de ghiduri clinice actuale (RDI, praguri de laborator) — cu input de la medic sau nutriționist.
- **Scorurile și porțiile** — calibrate pe cazuri reale (personae din README secțiunea licență).
- **Comportamentul OpenFoodFacts** (mod non-blocant): poate exclude alimente procesate când verdictul API nu confirmă siguranța; echilibru între siguranță și diversitate.

## Recomandări pentru lucrarea de licență

Documentează explicit limitările, sursele de reguli (fișiere JSON / cod), și pașii pentru audit ulterior al catalogului (`docs/CATALOG_AUDIT_CHECKLIST.md`).
