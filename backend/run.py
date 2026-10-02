"""
Script pentru rularea serverului FastAPI
"""
import logging
import os

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    # reload=True pornește două procese, ceea ce poate servi cod dintr-un proces vechi.
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

