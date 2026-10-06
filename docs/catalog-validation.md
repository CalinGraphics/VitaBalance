# Validarea catalogului vechi de alimente

Generat de `backend/scripts/validate_legacy_catalog.py`. Rânduri vechi: **591**. Niciunul nu mai e recomandat (motorul folosește doar catalogul validat din USDA).

- În afara toleranței energetice (±15%) sau cu date lipsă: **21**
- Cu o cantitate în nume (valori probabil per porție, nu la 100 g): **273**

Verificarea energiei nu prinde valorile per porție: ele sunt consistente intern (vezi docs/audit.md §4.0).

## Rânduri în afara toleranței

| id | aliment | kcal declarat | kcal din macronutrienți | probleme |
|---|---|---|---|---|
| 107 | Sandviș cu Chiftele (15cm) | 580 | 563 | macros_over_100g |
| 118 | Pad Thai cu Pui | 550 | 528 | macros_over_100g |
| 149 | Paste Alfredo cu Pui | 680 | 654 | macros_over_100g |
| 169 | Sandviș Reuben | 650 | 602 | macros_over_100g |
| 176 | Vodcă cu Sifon (1 cocktail) | 100 | 0 | atwater_out_of_tolerance:+100% |
| 240 | Jicama (bețișoare) | 46 | 35 | atwater_out_of_tolerance:+23% |
| 250 | Club Sandviș | 580 | 560 | macros_over_100g |
| 259 | Burrito cu Carne de Vită (mare) | 650 | 632 | macros_over_100g |
| 279 | Gyros (1 sandviș) | 600 | 580 | macros_over_100g |
| 287 | Sandviș Pui Parmezan | 650 | 638 | macros_over_100g |
| 313 | Whisky (shot) | 105 | 0 | atwater_out_of_tolerance:+100% |
| 371 | Biryani cu Pui | 520 | 504 | macros_over_100g |
| 388 | Vită Wellington (1 felie) | 600 | 594 | macros_over_100g |
| 412 | Paella cu Fructe de Mare | 550 | 550 | macros_over_100g |
| 427 | Lomo Saltado | 500 | 508 | macros_over_100g |
| 451 | Carbonara | 650 | 647 | macros_over_100g |
| 461 | Tagliatelle al Ragù Bolognese | 550 | 538 | macros_over_100g |
| 487 | Gin | 70 | 0 | atwater_out_of_tolerance:+100% |
| 511 | Cacio e Pepe | 500 | 495 | macros_over_100g |
| 540 | Vodcă | 97 | 0 | atwater_out_of_tolerance:+100% |
| 550 | Shawarma de Pui (1 wrap) | 550 | 533 | macros_over_100g |
