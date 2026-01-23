# Conturi de Test - VitaBalance

## ⚠️ IMPORTANT: Repornește Backend-ul!

După ce am făcut fix-ul pentru eroarea `rule_results`, **trebuie să repornești backend-ul** pentru ca modificările să aibă efect:

```powershell
# Oprește backend-ul actual (Ctrl+C în terminalul unde rulează)
# Apoi repornește:
cd backend
.\venv\Scripts\activate
python run.py
```

---

## 📋 Conturi de Test

### Cont 1: Vegană cu Multiple Deficiențe

**Profil:**
- **Nume complet**: `Ana Ionescu`
- **Email**: `ana.vegan@test.vitabalance.ro`
- **Parolă**: `Test123!`
- **Vârstă**: `28`
- **Sex**: `Feminin`
- **Greutate**: `60` kg
- **Înălțime**: `165` cm
- **Nivel activitate**: `Moderată`
- **Tip de dietă**: `Vegan`
- **Alergii**: Selectează `Lactate`, `Gluten` (dacă sunt disponibile)
- **Condiții medicale**: `aport vegetal scăzut, expunere solară redusă`

**Analize Medicale:**
- **Hemoglobină**: `12.5` g/dL
- **Feritină**: `22` ng/mL ⚠️ (< 30 → deficit fier)
- **Vitamina D**: `15` ng/mL ⚠️ (< 20 → deficit vitamina D)
- **Vitamina B12**: `180` pg/mL ⚠️ (< 200 → deficit B12)
- **Calciu**: `8.2` mg/dL ⚠️ (< 8.5 → deficit calciu)
- **Magneziu**: `1.5` mg/dL ⚠️ (< 1.7 → deficit magneziu)
- **Zinc**: `65` mcg/dL ⚠️ (< 70 → deficit zinc)
- **Proteine**: `7.0` g/dL
- **Folat**: `2.5` ng/mL ⚠️ (< 3 → deficit folat)
- **Vitamina A**: `18` µg/dL ⚠️ (< 20 → deficit vit. A)
- **Vitamina C**: `20` mg/dL ⚠️ (< 23 → deficit vit. C)
- **Iod**: `85` µg/L ⚠️ (< 100 → deficit iod)
- **Potasiu**: `3.2` mmol/L ⚠️ (< 3.5 → deficit K)
- **Observații**: `Oboseală, dietă vegană recentă`

**Recomandări așteptate:**
- Linte, năut, spanac + vitamina C (fier vegan)
- Ciuperci expuse la UV, lapte vegetal fortificat (vitamina D vegan)
- Alimente fortificate, drojdie inactivă (B12 vegan)
- Avocado, portocale (folat)
- Kale, broccoli, migdale (calciu)
- Nuci, tărâțe de ovăz, frunze verzi (magneziu)
- Fasole, linte, semințe (zinc)
- Morcovi, spanac (vitamina A)
- Portocale, ardei gras, roșii (vitamina C)
- Alge marine (iod)
- Banane, cartofi (potasiu)

---

### Cont 2: Omnivor cu Deficit Fier și Vitamina D

**Profil:**
- **Nume complet**: `Dan Popescu`
- **Email**: `dan.omnivor@test.vitabalance.ro`
- **Parolă**: `Test123!`
- **Vârstă**: `35`
- **Sex**: `Masculin`
- **Greutate**: `80` kg
- **Înălțime**: `180` cm
- **Nivel activitate**: `Foarte activ`
- **Tip de dietă**: `Omnivor`
- **Alergii**: (nimic selectat)
- **Condiții medicale**: `ceai/cafea la masă`

**Analize Medicale:**
- **Feritină**: `25` ng/mL ⚠️ (< 30 → deficit fier)
- **Vitamina D**: `18` ng/mL ⚠️ (< 20 → deficit vitamina D)
- **Calciu**: `9.2` mg/dL (OK)
- **Magneziu**: `1.5` mg/dL ⚠️ (< 1.7 → ușor scăzut)
- **Restul**: Lasă gol sau valori normale

**Recomandări așteptate:**
- Carne roșie, ficat (fier omnivor)
- Expunere solară + alimente fortificate (vitamina D)
- Nuci, tărâțe de ovăz (magneziu)
- Mesaj despre evitarea ceaiului/cafelei la masă

---

### Cont 3: Sarcină + Risc Osteoporoză + Hipertensiune

**Profil:**
- **Nume complet**: `Maria Georgescu`
- **Email**: `maria.medical@test.vitabalance.ro`
- **Parolă**: `Test123!`
- **Vârstă**: `32`
- **Sex**: `Feminin`
- **Greutate**: `68` kg
- **Înălțime**: `162` cm
- **Nivel activitate**: `Sedentar`
- **Tip de dietă**: `Vegetarian`
- **Alergii**: `Lactate` (dacă disponibil)
- **Condiții medicale**: `sarcină, risc osteoporoză, hipertensiune`

**Analize Medicale:**
- **Folat**: `2.8` ng/mL ⚠️ (< 3 → deficit important în sarcină)
- **Calciu**: `8.3` mg/dL ⚠️ (< 8.5 → ușor sub prag)
- **Vitamina D**: `19` ng/mL ⚠️ (< 20 → ușor scăzut)
- **Potasiu**: `3.3` mmol/L ⚠️ (< 3.5 → sub prag pentru hipertensiune)
- **Restul**: Lasă gol sau valori normale

**Recomandări așteptate:**
- Frunze verzi, leguminoase (folat în sarcină)
- Calciu + vitamina D (profil osteoporoză)
- Banane, cartofi, alte alimente bogate în potasiu (hipertensiune)
- Kale, broccoli (vitamina K)

---

### Cont 4: Fără Analize - Doar Profil

**Profil:**
- **Nume complet**: `Alex FărăAnalize`
- **Email**: `alex.noLabs@test.vitabalance.ro`
- **Parolă**: `Test123!`
- **Vârstă**: `29`
- **Sex**: `Masculin`
- **Greutate**: `90` kg
- **Înălțime**: `182` cm
- **Nivel activitate**: `Sedentar`
- **Tip de dietă**: `Omnivor`
- **Alergii**: `Gluten`
- **Condiții medicale**: `IMC > 30, fumător, expunere solară redusă`

**Analize Medicale:**
- **Lasă toate câmpurile necompletate** (sari peste acest pas)

**Recomandări așteptate:**
- Recomandări generale influențate de:
  - Fumător → vitamina C
  - IMC > 30 + expunere solară redusă → vitamina D
  - Alergii gluten → exclude alimente cu gluten

---

## 🔍 Verificare După Creare Cont

1. **Creează contul** folosind datele de mai sus
2. **Completează profilul medical** cu toate informațiile
3. **Adaugă analizele** (sau sari peste pentru Cont 4)
4. **Accesează pagina de recomandări**

**Dacă vezi eroarea `rule_results` din nou:**
- Asigură-te că backend-ul a fost repornit după fix
- Verifică în consola backend dacă există alte erori
- Trimite-mi mesajul exact de eroare din UI și log-ul backend

---

## ✅ Ce Ar Trebui Să Funcționeze

- ✅ Generarea recomandărilor bazate pe deficiențe
- ✅ Aplicarea regulilor cu scop (scoped rules) din IMPLEMENTARE_PDF.md
- ✅ Explicații cu context (`[Context: ...] ...`)
- ✅ Excluderea alimentelor cu alergeni
- ✅ Respectarea tipului de dietă (vegan, vegetarian, omnivor)
- ✅ Considerarea condițiilor medicale (sarcină, osteoporoză, etc.)

---

## 🐛 Dacă Încă Apare Eroarea

**Eroarea**: `cannot access local variable 'rule_results' where it is not associated with a value`

**Soluție:**
1. Oprește complet backend-ul (Ctrl+C)
2. Repornește backend-ul:
   ```powershell
   cd backend
   .\venv\Scripts\activate
   python run.py
   ```
3. Reîncearcă generarea recomandărilor

Dacă problema persistă, verifică:
- Dacă există erori în consola backend
- Dacă fișierul `backend/services/rule_engine.py` a fost salvat corect
- Dacă există cache-uri Python (`__pycache__`) care trebuie șterse
