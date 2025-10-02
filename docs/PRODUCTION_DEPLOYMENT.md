# 🚀 Production Deployment Guide - Synapse-NG

Guida completa per il deployment di Synapse-NG in produzione con supporto completo per NAT traversal, mDNS discovery e monitoring.

---

## Table of Contents

1. [TURN Server Deployment](#1-turn-server-deployment)
2. [ICE Configuration](#2-ice-configuration)
3. [mDNS Discovery](#3-mdns-discovery)
4. [Monitoring & Metrics](#4-monitoring--metrics)
5. [Docker Deployment](#5-docker-deployment)
6. [Security Considerations](#6-security-considerations)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. TURN Server Deployment

### Perché serve un TURN server?

- **STUN** funziona per ~80% delle connessioni (NAT cone/restricted)
- **TURN** è necessario per NAT simmetrici (~20% dei casi)
- TURN fa da relay quando connessione P2P diretta fallisce

### Setup con Docker

```bash
# 1. Configura credenziali
cd turn-server
# Modifica turnserver.conf:
#   - Cambia user/password
#   - Imposta external-ip se dietro NAT

# 2. Avvia TURN server
docker-compose -f docker-compose.turn.yml up -d

# 3. Verifica funzionamento
docker-compose -f docker-compose.turn.yml logs -f turn-server

# 4. Test TURN server
docker exec -it synapse-turn turnutils_uclient -v -t -u synapse -w changeme123 127.0.0.1
```

### Configurazione Nodi per usare TURN

**Opzione 1: Variabile d'ambiente**

```bash
export ICE_SERVERS_JSON='[
  {"urls":"stun:stun.l.google.com:19302"},
  {"urls":"turn:your-turn-server.com:3478","username":"synapse","credential":"changeme123"}
]'

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Opzione 2: Docker Compose**

```yaml
environment:
  - ICE_SERVERS_JSON=[{"urls":"turn:turn-server:3478","username":"synapse","credential":"changeme123"}]
```

### TURN Server Pubblico (Deployment Cloud)

```bash
# AWS/GCP/Azure: Apri porte
# TCP/UDP 3478 (STUN/TURN)
# TCP/UDP 5349 (TURN over TLS)
# UDP 49152-65535 (relay range)

# Configura external-ip in turnserver.conf
external-ip=YOUR_PUBLIC_IP

# Se dietro load balancer
# external-ip=PUBLIC_IP/PRIVATE_IP
```

---

## 2. ICE Configuration

### Server ICE Raccomandati

```json
[
  {"urls": "stun:stun.l.google.com:19302"},
  {"urls": "stun:stun1.l.google.com:19302"},
  {"urls": "turn:your-turn.example.com:3478", "username": "user", "credential": "pass"}
]
```

### ICE Trickle

✅ **Già abilitato!** aiortc supporta ICE trickle nativamente.

**Vantaggi:**
- Connessioni più rapide (non aspetta tutti i candidati)
- Migliore UX (primi pacchetti trasmessi prima)
- Riduce latency di setup da ~3s a ~1s

**Log di Debug:**
```bash
# Abilita log dettagliati per vedere ICE candidates
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --log-level debug
```

Vedrai:
```
🧊 ICE candidate per abc123...: type=host, protocol=udp
🧊 ICE candidate per abc123...: type=srflx, protocol=udp
🧊 ICE candidate per abc123...: type=relay, protocol=udp
```

### Priorità ICE Candidates

1. **host**: IP locale (LAN) - latenza minima
2. **srflx**: Server reflexive (STUN) - IP pubblico
3. **relay**: TURN relay - fallback garantito

---

## 3. mDNS Discovery

### Quando usare mDNS?

✅ **Usa mDNS per:**
- Reti locali (conferenze, uffici, casa)
- Sviluppo/testing locale
- Ambienti offline

❌ **NON usare mDNS per:**
- Deploy su cloud pubblico
- Nodi distribuiti geograficamente
- Container isolati (a meno di rete custom)

### Setup mDNS su Docker

```bash
# Usa configurazione con rete custom
docker-compose -f docker-compose.mdns.yml up -d

# Verifica discovery
docker-compose -f docker-compose.mdns.yml logs | grep "mDNS"
```

**Output atteso:**
```
📡 mDNS: Servizio registrato come synapse-ng-abc123._synapse-ng._tcp.local.
🔍 mDNS: Browser avviato per servizi _synapse-ng._tcp.local.
🎯 mDNS: Nuovo peer scoperto! def456... (http://node-2:8000, canali: 2)
```

### Disabilitare mDNS

```bash
# Via env
export DISABLE_MDNS=true

# Via docker-compose
environment:
  - DISABLE_MDNS=true
```

---

## 4. Monitoring & Metrics

### Endpoint ICE Metrics

```bash
# Ottieni metriche ICE
curl http://localhost:8000/webrtc/ice-metrics | jq
```

**Output:**
```json
{
  "summary": {
    "total_attempted": 15,
    "total_established": 14,
    "total_failed": 1,
    "success_rate_percent": 93.33,
    "ice_candidates_sent": 45,
    "ice_candidates_received": 42
  },
  "connection_states": {
    "peer_abc123": [
      {"state": "connecting", "timestamp": 1234567890.123},
      {"state": "connected", "timestamp": 1234567892.456}
    ]
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Metriche Chiave

| Metrica | Buono | Warning | Critical |
|---------|-------|---------|----------|
| Success Rate | >90% | 70-90% | <70% |
| Avg Connection Time | <2s | 2-5s | >5s |
| Failed Connections | <10% | 10-30% | >30% |

### Dashboard Prometheus (opzionale)

Il TURN server coturn supporta Prometheus metrics:

```conf
# In turnserver.conf
prometheus
prometheus-port=9641
```

Poi scrape con Prometheus:
```yaml
scrape_configs:
  - job_name: 'synapse-turn'
    static_configs:
      - targets: ['turn-server:9641']
```

---

## 5. Docker Deployment

### Setup Produzione Completa

```bash
# 1. Clone repository
git clone https://github.com/your-org/synapse-ng
cd synapse-ng

# 2. Configura TURN server
cd turn-server
# Modifica turnserver.conf (credenziali, external-ip)

# 3. Avvia TURN
docker-compose -f docker-compose.turn.yml up -d

# 4. Configura nodi
export ICE_SERVERS_JSON='[...]'  # Include TURN

# 5. Avvia nodi
docker-compose up -d

# 6. Verifica
docker-compose logs -f
curl http://localhost:8001/webrtc/ice-metrics
```

### Multi-Host Deployment

**Host 1 (TURN Server):**
```bash
docker-compose -f docker-compose.turn.yml up -d
# Esponi porta 3478 pubblicamente
```

**Host 2-N (Nodi):**
```bash
export ICE_SERVERS_JSON='[{"urls":"turn:HOST1_IP:3478","username":"synapse","credential":"..."}]'
docker-compose up -d node-1
```

---

## 6. Security Considerations

### TURN Server

⚠️ **IMPORTANTE:**

1. **Cambia credenziali default:**
   ```conf
   # In turnserver.conf
   user=synapse:YOUR_STRONG_PASSWORD_HERE
   ```

2. **Usa TLS in produzione:**
   ```conf
   tls-listening-port=5349
   cert=/path/to/cert.pem
   pkey=/path/to/privkey.pem
   ```

3. **Limita bandwidth:**
   ```conf
   max-bps=500000  # 500 Kbps per client
   total-quota=100  # 100 MB per sessione
   ```

4. **Firewall:**
   ```bash
   # Permetti solo IP noti
   ufw allow from KNOWN_IP to any port 3478
   ```

### Nodi Synapse-NG

1. **HTTPS obbligatorio in produzione:**
   ```bash
   # Usa reverse proxy (nginx/caddy)
   # Termina TLS lì, non nell'app
   ```

2. **Variabili d'ambiente sensibili:**
   ```bash
   # Non committare .env con credenziali
   echo ".env" >> .gitignore
   ```

3. **Rate limiting:**
   ```python
   # In main.py (opzionale)
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

---

## 7. Troubleshooting

### Problema: Connessioni WebRTC Falliscono

**Diagnosi:**
```bash
# 1. Verifica ICE metrics
curl http://localhost:8000/webrtc/ice-metrics

# 2. Controlla log
docker-compose logs node-1 | grep -i "ice\|webrtc"

# 3. Test TURN server
docker exec -it synapse-turn turnutils_uclient -v -t -u synapse -w changeme123 127.0.0.1
```

**Soluzioni:**
- Success rate <70%? → Aggiungi TURN server
- "Connection timeout"? → Verifica firewall porte UDP
- "Authentication failed"? → Controlla credenziali TURN

---

### Problema: mDNS Non Scopre Peer

**Diagnosi:**
```bash
# Verifica servizio mDNS
docker-compose logs node-1 | grep mDNS

# Test manuale (su host)
avahi-browse -r _synapse-ng._tcp
# oppure
dns-sd -B _synapse-ng._tcp
```

**Soluzioni:**
- In Docker? → Usa `docker-compose.mdns.yml` (rete custom)
- Su macOS? → Funziona nativamente
- Su Linux? → Installa `avahi-daemon`
- Firewall? → Permetti multicast UDP 5353

---

### Problema: TURN Server Non Risponde

**Diagnosi:**
```bash
# Test connettività
nc -u turn-server.com 3478
# Invia qualsiasi byte, dovrebbe rispondere

# Test con turnutils
turnutils_uclient -v -t -u synapse -w changeme123 turn-server.com
```

**Soluzioni:**
- Porte chiuse? → Apri 3478 UDP/TCP, 49152-65535 UDP
- Firewall attivo? → Permetti traffico TURN
- external-ip errato? → Verifica in turnserver.conf

---

## 8. Best Practices

### Configurazione Ottimale

```bash
# Per deployment Internet (con TURN)
export ICE_SERVERS_JSON='[
  {"urls":"stun:stun.l.google.com:19302"},
  {"urls":"stun:stun1.l.google.com:19302"},
  {"urls":"turn:turn.mycompany.com:3478","username":"user","credential":"pass"}
]'

# Per LAN locale (solo mDNS)
export DISABLE_MDNS=false
export RENDEZVOUS_URL=""  # P2P mode

# Per ambienti ibridi (Internet + LAN)
# Usa entrambi: TURN + mDNS
```

### Monitoring Continuo

```bash
# Cronjob per check health
*/5 * * * * curl -s http://localhost:8000/webrtc/ice-metrics | jq '.summary.success_rate_percent' | awk '{if($1<80) print "WARNING: Low success rate"}'
```

### Backup & Recovery

```bash
# Backup identità nodi
tar -czf synapse-backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf synapse-backup-YYYYMMDD.tar.gz
```

---

## 9. Performance Tuning

### TURN Server

```conf
# turnserver.conf ottimizzato
max-bps=1000000          # 1 Mbps per client
total-quota=200          # 200 MB per sessione
user-quota=100           # 100 MB per user
stale-nonce=600          # 10 minuti
max-allocate-lifetime=3600  # 1 ora
```

### Nodi Synapse-NG

```bash
# Aumenta worker uvicorn per load
uvicorn app.main:app --workers 4 --host 0.0.0.0

# Usa Gunicorn per produzione
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 10. Esempi Deployment

### Scenario 1: Startup con 3-10 Nodi (LAN)

```bash
# SOLO mDNS, no server esterni
export DISABLE_MDNS=false
export RENDEZVOUS_URL=""
python -m uvicorn app.main:app --host 0.0.0.0
```

**Vantaggi:**
- Zero configurazione
- Zero costi server
- Funziona offline

---

### Scenario 2: Azienda Distribuita (Internet)

```bash
# Deploy TURN server centralizzato
docker-compose -f docker-compose.turn.yml up -d

# Nodi usano TURN
export ICE_SERVERS_JSON='[{"urls":"turn:turn.company.com:3478","username":"user","credential":"pass"}]'
docker-compose up -d
```

**Vantaggi:**
- Funziona attraverso qualsiasi NAT
- ~95% success rate connessioni
- Fallback garantito

---

### Scenario 3: Conferenza/Evento Temporaneo

```bash
# Organizzatore avvia rendezvous + node
docker-compose up -d rendezvous node-1

# Partecipanti (stessa rete Wi-Fi)
# mDNS li scopre automaticamente
export BOOTSTRAP_NODES=http://organizer-laptop:8001
python -m uvicorn app.main:app
```

**Vantaggi:**
- Setup veloce
- mDNS + bootstrap per robustezza
- Zero infrastruttura cloud

---

## Conclusione

Con questa configurazione, Synapse-NG è production-ready per:

✅ **Qualsiasi topologia di rete** (LAN, Internet, NAT simmetrico)
✅ **Monitoraggio completo** (ICE metrics, success rate)
✅ **Alta affidabilità** (STUN + TURN fallback)
✅ **Zero-config locale** (mDNS discovery)

**Success Rate Atteso:**
- Solo STUN: 70-85%
- STUN + TURN: 95-99%
- LAN + mDNS: ~100%

---

**Synapse-NG: "Funziona e basta", ovunque.** 🌐🚀
