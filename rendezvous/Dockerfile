# Usa un'immagine Python ufficiale e leggera.
FROM python:3.9-slim

# Imposta la directory di lavoro all'interno del container.
WORKDIR /app

# Installa le dipendenze necessarie.
# Non copiamo un file requirements.txt per questo semplice servizio,
# ma installiamo direttamente i pacchetti.
RUN pip install fastapi "uvicorn[standard]"

# Copia il codice dell'applicazione nella directory di lavoro.
COPY ./main.py .

# Esponi la porta su cui il server FastAPI ascolterà.
EXPOSE 8080

# Comando per avviare l'applicazione quando il container parte.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
