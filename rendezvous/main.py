
import asyncio
import time
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Set

app = FastAPI()

# --- Struttura Dati ---
# Usiamo un dizionario per mappare l'URL del peer al timestamp dell'ultima registrazione.
# Esempio: { "http://node-1:8000": 1678886400.0 }
active_peers = {}
PEER_TIMEOUT_SECONDS = 60  # Un peer viene considerato inattivo dopo 60 secondi

class PeerRegistration(BaseModel):
    url: str

# --- Endpoint ---

@app.post("/register", status_code=200)
async def register_peer(payload: PeerRegistration):
    """
    Registra un peer nella lista di quelli attivi o aggiorna il suo timestamp.
    """
    peer_url = payload.url
    if not peer_url:
        raise HTTPException(status_code=400, detail="URL non può essere vuoto")
    
    active_peers[peer_url] = time.time()
    print(f"✅ Peer registrato/aggiornato: {peer_url}")
    return {"message": f"Peer {peer_url} registrato con successo."}

@app.get("/get_peers", response_model=List[str])
async def get_peers(limit: int = 5):
    """
    Restituisce una lista casuale di peer attivi.
    """
    # Filtra i peer ancora validi (non scaduti)
    current_time = time.time()
    valid_peers = [
        url for url, last_seen in active_peers.items() 
        if current_time - last_seen < PEER_TIMEOUT_SECONDS
    ]
    
    # Scegli un campione casuale fino al limite specificato
    num_to_return = min(len(valid_peers), limit)
    random_peers = random.sample(valid_peers, num_to_return)
    
    print(f"ℹ️  Richiesta peer. Peer attivi: {len(valid_peers)}. Restituiti: {len(random_peers)}.")
    return random_peers

# --- Task in Background ---

async def cleanup_inactive_peers():
    """
    Task periodico che rimuove i peer inattivi dalla lista.
    """
    while True:
        await asyncio.sleep(PEER_TIMEOUT_SECONDS / 2) # Esegui la pulizia ogni 30 secondi
        
        current_time = time.time()
        # È necessario creare una copia delle chiavi per iterare,
        # poiché non si può modificare un dizionario mentre lo si itera.
        peers_to_check = list(active_peers.keys())
        
        cleaned_count = 0
        for peer_url in peers_to_check:
            if current_time - active_peers.get(peer_url, 0) > PEER_TIMEOUT_SECONDS:
                try:
                    del active_peers[peer_url]
                    cleaned_count += 1
                except KeyError:
                    # Il peer potrebbe essere stato rimosso da un'altra operazione, ignora.
                    pass
        
        if cleaned_count > 0:
            print(f"🧹 Puliti {cleaned_count} peer inattivi.")

@app.on_event("startup")
async def on_startup():
    """
    All'avvio del server, avvia il task di pulizia in background.
    """
    print("🚀 Rendezvous Server avviato. In attesa di peer...")
    asyncio.create_task(cleanup_inactive_peers())

