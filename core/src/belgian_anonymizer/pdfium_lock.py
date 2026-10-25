import threading

# PDFium is not thread-safe, and FastAPI runs sync endpoints in a thread pool: every pypdfium2 call
# (opening, reading, rendering, closing) must hold this lock
PDFIUM_LOCK = threading.RLock()
