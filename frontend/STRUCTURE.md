# Structura Modulară - VitaBalance

## Organizare Proiect

Proiectul este organizat într-o structură modulară, scalabilă și ușor de întreținut.

```
src/
├── features/                    # Feature modules (funcționalități specifice)
│   ├── auth/                    # Modul de autentificare
│   │   ├── pages/              # Pagini: LoginPage, RegisterPage
│   │   └── components/         # Componente specifice auth (dacă sunt)
│   ├── medical/                # Modul medical
│   │   ├── pages/              # Pagini: MedicalProfilePage, MedicalLabResultsPage
│   │   └── components/        # Componente specifice medical (dacă sunt)
│   └── recommendations/       # Modul recomandări
│       ├── components/         # Recommendations, RecommendationCard, NutrientChart
│       └── types.ts           # Tipuri specifice recomandărilor
│
├── shared/                      # Cod partajat între features
│   ├── components/             # Componente reutilizabile
│   │   ├── ui/                 # UI primitives (GlassCard, InputField, PrimaryButton, SelectField)
│   │   ├── layout/             # Layout components (Layout)
│   │   └── common/             # Componente comune (Disclaimer)
│   ├── hooks/                  # Custom hooks partajate
│   │   └── useAppNavigation.ts # Hook pentru navigare și state management
│   ├── contexts/               # React contexts
│   │   └── ThemeContext.tsx    # Context pentru theme (dark mode)
│   ├── types/                  # Tipuri TypeScript partajate
│   │   └── index.ts            # User, AuthUser, Route
│   ├── constants/              # Constante
│   │   └── routes.ts           # Constante pentru rute
│   └── utils/                  # Funcții utilitare (dacă sunt)
│
├── services/                    # API services
│   └── api.ts                  # Servicii pentru API calls (profileService, labResultsService, etc.)
│
├── contexts/                    # (Legacy - va fi mutat în shared/contexts)
│
├── App.tsx                      # Componenta principală - orchestrator
└── main.tsx                     # Entry point
```

## Principii de Organizare

### 1. **Feature-Based Structure**
- Fiecare feature (auth, medical, recommendations) este izolat în propriul folder
- Fiecare feature poate avea propriile componente, pagini, hooks și tipuri
- Facilitează dezvoltarea paralelă și testarea

### 2. **Shared Code**
- Componente UI reutilizabile în `shared/components/ui/`
- Layout și componente comune în `shared/components/`
- Hooks partajate în `shared/hooks/`
- Tipuri comune în `shared/types/`

### 3. **Services Layer**
- Toate API calls-urile sunt centralizate în `services/api.ts`
- Facilitează mock-ul și testarea
- Ușor de înlocuit cu un backend real

### 4. **Separation of Concerns**
- **Pages**: Componente de nivel superior care orchestrează UI-ul
- **Components**: Componente reutilizabile și specifice feature-ului
- **Hooks**: Logică de business reutilizabilă
- **Services**: Comunicare cu API-ul
- **Types**: Definiții TypeScript

## Beneficii

✅ **Scalabilitate**: Ușor de adăugat noi features fără a afecta cele existente
✅ **Mentenabilitate**: Cod organizat logic, ușor de găsit și modificat
✅ **Reutilizare**: Componente și hooks partajate reduc duplicarea
✅ **Testare**: Structură clară facilitează testarea izolată
✅ **Colaborare**: Echipe diferite pot lucra pe features diferite simultan

## Conventii

- **Naming**: PascalCase pentru componente, camelCase pentru funcții/hooks
- **Exports**: Folosim `index.ts` pentru exporturi barrel
- **Imports**: Importuri absolute din `shared/` și `features/`
- **Types**: Tipurile sunt exportate din `shared/types` sau din feature-ul specific

## Exemple de Importuri

```typescript
// Componente shared
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components'

// Hooks shared
import { useAppNavigation } from '../../../shared/hooks'

// Types shared
import type { User, AuthUser } from '../../../shared/types'

// Services
import { profileService } from '../../../services/api'

// Features
import { LoginPage } from '../../../features/auth/pages'
```

