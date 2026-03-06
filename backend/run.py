"""
Script pentru rularea serverului FastAPI
"""
import uvicorn
import os

if __name__ == "__main__":
    # reload=True pornește 2 procese și poate păstra cod vechi în caz de conflicte.
    # Pentru debug stabil (și ca să nu mai vezi eroarea cu rule_results dintr-un proces vechi),
    # rulează fără reload.
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

