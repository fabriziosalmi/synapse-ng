# 🎨 UI Refactor - Console Operativa Synapse-NG

## 📋 Sommario delle Modifiche

Questo documento descrive il refactoring completo dell'interfaccia utente di Synapse-NG, trasformandola da un semplice visualizzatore 3D a una **Console Operativa di Rete** interattiva e ricca di insight.

---

## 🔧 FASE 1: Backend - Nuove Metriche

### 1.1 Nuovo Endpoint `/network/stats`

**File:** `app/main.py` (linee 150-209)

**Scopo:** Fornire metriche di rete in tempo reale separate dallo stato CRDT persistente.

**Struttura Risposta:**
```json
{
  "timestamp": "2025-10-02T...",
  "webrtc_connections": {
    "total_established": 3,
    "total_connecting": 1,
    "peers": {
      "peer_id_1": {
        "state": "connected",
        "ice_state": "completed",
        "data_channel": "open",
        "latency_ms": 50
      }
    }
  },
  "synapsesub_stats": {
    "total_subscriptions": 2,
    "topics": {
      "channel:sviluppo_ui:state": {
        "mesh_size": 3,
        "messages_seen": 150
      }
    },
    "total_messages_seen": 300
  },
  "network_topology": {
    "total_nodes": 4,
    "connected_direct": 3,
    "discovered_only": 1
  }
}
```

**Metriche Chiave:**
- **WebRTC**: Stato connessioni, latenza (simulata per ora), stato ICE
- **PubSub**: Dimensione mesh per topic, messaggi visti
- **Topologia**: Nodi totali, connessi direttamente, solo scoperti

---

### 1.2 WebSocket Arricchito

**File:** `app/main.py` (linee 711-737)

**Modifiche:**
- Il WebSocket ora invia un messaggio aggregato che include **sia** lo stato CRDT **sia** le statistiche di rete
- Formato messaggio:
```json
{
  "type": "full_update",
  "timestamp": "...",
  "state": { /* stato CRDT completo */ },
  "network_stats": { /* da /network/stats */ }
}
```

**Vantaggi:**
- Un solo flusso di dati per la UI
- Sincronizzazione garantita tra stato e statistiche
- Aggiornamento ogni secondo (configurabile)

---

## 🎨 FASE 2: Frontend - Visualizzazione 3D Avanzata

### 2.1 Gerarchia dei Link

**File:** `app/templates/index.html` (funzione `updateGraph`, linee 519-593)

**Implementazione:**

#### **Link WebRTC Diretti** (linee 522-569)
- **WebRTC + In Mesh**: Ciano brillante (`0x00ffff`), solido
  - Rappresenta la "autostrada" della comunicazione
  - Mostra le connessioni P2P attive tra partecipanti dello stesso canale
- **WebRTC Fuori Mesh**: Verde (`0x00ff88`), semi-trasparente (opacità 0.6)
  - Connessione disponibile ma non usata nel canale corrente
- **In Connessione**: Arancione tratteggiato (`0xffaa00`), opacità 0.4
  - Visualizza lo stato "connecting" delle connessioni WebRTC

#### **Link "Scoperto"** (linee 571-593)
- Grigio scuro tratteggiato (`0x333333`), opacità 0.2
- Indica nodi conosciuti ma non connessi via WebRTC
- Mostra la "conoscenza" senza connessione diretta

**Logica:**
```javascript
// Per ogni peer nelle connessioni WebRTC
if (isOpen && isInMesh) {
    // Link brillante e spesso
    material = new THREE.LineBasicMaterial({ color: 0x00ffff, ... });
} else if (isOpen) {
    // Link WebRTC ma fuori mesh
    material = new THREE.LineBasicMaterial({ color: 0x00ff88, opacity: 0.6 });
} else {
    // Connessione in corso
    material = new THREE.LineDashedMaterial({ color: 0xffaa00, ... });
}
```

---

### 2.2 Nodi Dinamici

**File:** `app/templates/index.html` (funzione `updateGraph`, linee 434-517)

#### **Dimensione Basata su Reputazione** (linee 501-505)
```javascript
const baseScale = 1.0;
const repScale = Math.min(node.reputation / 100, 2.0); // Max 2x size
const targetScale = baseScale + repScale;
sphere.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
```
- Nodi con più reputazione sono visibilmente più grandi (max 2x)
- Animazione smooth con `lerp` per transizioni fluide

#### **Altezza Basata su Reputazione** (linee 507-509)
```javascript
const targetY = -150 + Math.min(node.reputation * 5, 400);
sphere.position.y += (targetY - sphere.position.y) * 0.05;
```
- Crea una "stratificazione verticale" della rete
- Nodi più importanti "salgono" visivamente

#### **Colore e Trasparenza per Focus Canale** (linee 478-499)
```javascript
if (node.id === window.LOCAL_NODE_ID) {
    // Nodo locale: sempre bianco brillante
    sphere.material.color.setHex(0xffffff);
} else if (isChannelFocused && !isParticipant) {
    // Nodi non partecipanti: grigi e semi-trasparenti
    sphere.material.color.setHex(0x444444);
    sphere.material.opacity = 0.3;
    sphere.material.transparent = true;
} else {
    // Nodi partecipanti: verde normale
    sphere.material.color.setHex(0x00ff88);
}
```

---

### 2.3 Selettore Canali con Focus Visivo

**File:** `app/templates/index.html` (linee 690-724)

**UI Element:**
```html
<div id="channel-selector">
    <label for="channel-select">🔍 Canale Focus:</label>
    <select id="channel-select">
        <option value="global">🌐 Global (Tutti)</option>
        <!-- Popolato dinamicamente -->
    </select>
</div>
```

**Comportamento:**
1. **Global Mode** (`selectedChannel === 'global'`):
   - Tutti i nodi visibili normalmente
   - Tutti i link WebRTC mostrati

2. **Channel Focus Mode** (es. `selectedChannel === 'sviluppo_ui'`):
   - Nodi partecipanti: Verde brillante, opachi
   - Nodi non partecipanti: Grigio, semi-trasparenti (opacità 0.3)
   - Link: Solo tra partecipanti al canale
   - Effetto "isolamento visivo" del contesto

**Logica di Filtraggio:**
```javascript
const isChannelFocused = selectedChannel !== 'global';
const participantsInChannel = isChannelFocused
    ? (currentState.state[selectedChannel]?.participants || [])
    : allNodeIds;

const isParticipant = participantsInChannel.includes(node.id);
// Applica stili in base a isParticipant
```

---

### 2.4 Activity Glows (Preparato)

**File:** `app/templates/index.html` (linee 462-475, 257-266)

**Implementazione:**
- Ogni nodo ha un "ring glow" associato (`nodeActivityGlows`)
- Nascosto di default (`glow.visible = false`)
- Animato nel loop di rendering: espansione + dissolvenza
- **Pronto per future integrazioni**: Attivare il glow quando un nodo pubblica un messaggio

```javascript
// Activity glow (nascosto di default)
const glowGeometry = new THREE.RingGeometry(20, 30, 32);
const glowMaterial = new THREE.MeshBasicMaterial({
    color: 0x00ff88,
    transparent: true,
    opacity: 0.8
});
const glow = new THREE.Mesh(glowGeometry, glowMaterial);
glow.visible = false; // Attivare quando necessario
```

**Future Enhancement:**
```javascript
// Quando un nodo pubblica un messaggio PubSub
nodeActivityGlows[nodeId].visible = true;
nodeActivityGlows[nodeId].scale.set(1, 1, 1);
nodeActivityGlows[nodeId].material.opacity = 0.8;
```

---

## 📊 FASE 3: HUD Dinamico

### 3.1 Pannello Nodo Locale (Top-Left)

**File:** `app/templates/index.html` (linee 142-149)

**Metriche Visualizzate:**
- **ID**: Abbreviato (primi 8 caratteri)
- **Nodi Attivi**: Totale nodi nella rete
- **Connessioni Dirette**: `webrtc_connections.total_established` ⭐ **NUOVO**
- **Reputazione**: Del nodo locale ⭐ **NUOVO**

**Codice Update:**
```javascript
const localNode = state.global.nodes[window.LOCAL_NODE_ID];
if (localNode) {
    document.getElementById('reputation').textContent = localNode.reputation || 0;
}
document.getElementById('direct-connections').textContent = stats.webrtc_connections.total_established;
```

---

### 3.2 Pannello Analisi Canale (Bottom-Right)

**File:** `app/templates/index.html` (funzione `updateHUD`, linee 596-688)

#### **Modalità Global** (linee 615-635)
```
📊 Analisi Rete Globale
---
Nodi Totali: 4
Connessi Diretti: 3
Solo Scoperti: 1
---
Topic PubSub: 2
Messaggi Visti: 300
---
Canali Attivi:
• sviluppo_ui: 3 part., 5 task
• marketing: 2 part., 1 task
```

#### **Modalità Channel Focus** (linee 636-687)
```
🔍 Canale: sviluppo_ui
---
Partecipanti: 3
Task Attivi: 5
Proposte: 2
---
Salute Mesh:
Dimensione Mesh: 3
Messaggi Visti: 150
Latenza Media: 75 ms ⭐ **NUOVO**
```

**Calcolo Latenza Media:**
```javascript
let totalLatency = 0;
let connectedCount = 0;
channelData.participants.forEach(peerId => {
    if (peerId !== window.LOCAL_NODE_ID) {
        const peerWebRTC = stats.webrtc_connections.peers[peerId];
        if (peerWebRTC?.latency_ms) {
            totalLatency += peerWebRTC.latency_ms;
            connectedCount++;
        }
    }
});
const avgLatency = Math.round(totalLatency / connectedCount);
```

---

### 3.3 Pannello Ispettore Interattivo (Bottom-Left)

**File:** `app/templates/index.html` (linee 70-79, 308-403)

**Trigger:** Click su un nodo nella scena 3D

**Implementazione Raycasting:**
```javascript
function onNodeClick(event) {
    // Converti coordinate mouse in coordinate normalizzate
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(Object.values(nodeMeshes));

    if (intersects.length > 0) {
        const nodeId = Object.keys(nodeMeshes).find(id => nodeMeshes[id] === intersects[0].object);
        showInspector(nodeId);
    }
}
```

**Informazioni Visualizzate:**

1. **Header**
   - ID Completo (full base64)
   - Reputazione
   - URL del nodo

2. **Stato Connessione**
   - ✅ **Connessione Diretta (WebRTC)** - se `data_channel === 'open'`
   - ⚠️ **Connessione in Corso** - se connesso ma canale non aperto
   - 🔍 **Scoperto (Non Connesso)** - se non in `webrtc_connections.peers`
   - **Metriche**: Stato, ICE State, Latenza (se disponibile)

3. **Canali Sottoscritti**
   - Lista dinamica ottenuta cercando il `nodeId` nelle `participants` list

4. **Task Assegnati**
   - Ricerca in tutti i canali per `task.assignee === nodeId`
   - Visualizzazione con:
     - Nome canale
     - Titolo task
     - Status task

**Esempio Output:**
```
🔎 Ispettore Nodo                    [✕]

ID Completo:
JkN-5D2qxGet881Ux96P7F7zPtWjOLH5HKoGugWYQ38=

Reputazione: 120
URL: http://node-2:8000
---
✅ Connessione Diretta (WebRTC)
Stato: connected
ICE: completed
Latenza: 50 ms
---
📡 Canali Sottoscritti:
• sviluppo_ui
• marketing
---
📋 Task Assegnati (2):
  ┌ sviluppo_ui
  │ Fix bug login
  └ Status: in_progress

  ┌ marketing
  │ Update landing page
  └ Status: claimed
```

---

## 🎨 Design System

### Palette Colori

| Elemento | Colore | Hex | Significato |
|----------|--------|-----|-------------|
| Nodo Locale | Bianco | `0xffffff` | "Io" - Sempre riconoscibile |
| Nodi Partecipanti | Verde Cyber | `0x00ff88` | Attivi, parte della rete |
| Nodi Non Partecipanti | Grigio | `0x444444` | Fuori focus |
| Link WebRTC + Mesh | Ciano | `0x00ffff` | Connessione critica |
| Link WebRTC Normale | Verde | `0x00ff88` | Connessione disponibile |
| Link In Connessione | Arancione | `0xffaa00` | Stato transitorio |
| Link Scoperto | Grigio Scuro | `0x333333` | Solo conoscenza |
| Ispettore Border | Arancione | `0xffaa00` | Interattività |
| Accent UI | Verde Cyber | `0x00ff88` | Elementi attivi |

### Animazioni

1. **Node Scaling**: `lerp` con fattore 0.1 per smooth transitions
2. **Node Height**: Movimento verticale con damping 0.05
3. **Activity Glows**: Espansione 1.05x per frame, fade opacity 0.95x
4. **Label Billboarding**: Sempre di fronte alla camera

---

## 🚀 Guida all'Uso

### Navigazione 3D
- **Rotazione**: Drag con mouse sinistro
- **Zoom**: Scroll del mouse
- **Pan**: Drag con mouse destro
- **Ispeziona**: Click su un nodo

### Selettore Canali
1. Click sul dropdown "🔍 Canale Focus"
2. Seleziona "🌐 Global" per vista completa
3. Seleziona un canale specifico per focus mode:
   - Nodi non partecipanti diventano grigi e semi-trasparenti
   - Link visibili solo tra partecipanti
   - HUD mostra statistiche del canale

### Ispettore Nodo
1. Click su qualsiasi nodo nella scena 3D
2. Pannello appare in basso a sinistra
3. Mostra info complete: ID, connessione, canali, task
4. Chiudi con "✕" o selezionando un altro canale

---

## 📈 Metriche Chiave Visualizzate

### Real-Time
- ✅ **Connessioni WebRTC Attive** (nuova metrica critica)
- ✅ **Latenza P2P** (simulata, ready per implementazione reale)
- ✅ **Dimensione Mesh PubSub** per topic
- ✅ **Messaggi PubSub Visti**

### Per-Channel
- ✅ **Partecipanti al canale**
- ✅ **Task attivi**
- ✅ **Proposte di governance**
- ✅ **Latenza Media** con peer del canale

### Per-Node (Ispettore)
- ✅ **Stato connessione** (Diretta/Scoperto/In Corso)
- ✅ **Canali sottoscritti**
- ✅ **Task assegnati** con dettagli

---

## 🔮 Future Enhancements

### 1. Animated Message Flow
Visualizzare "pacchetti" di luce che viaggiano lungo i link quando vengono inviati messaggi PubSub.

**Implementazione suggerita:**
```javascript
// Nel websocket handler, quando arriva un nuovo messaggio
if (uiData.recent_message) {
    const fromNode = uiData.recent_message.from;
    const toNodes = uiData.recent_message.recipients;

    toNodes.forEach(toNode => {
        animateMessageFlow(fromNode, toNode);
    });
}

function animateMessageFlow(from, to) {
    // Crea una sfera piccola che si muove lungo il link
    const particle = new THREE.Mesh(
        new THREE.SphereGeometry(3),
        new THREE.MeshBasicMaterial({ color: 0x00ffff, emissive: 0x00ffff })
    );
    // Anima da from a to in 500ms
    // Rimuovi al termine
}
```

### 2. Real Latency Measurement
Sostituire la latenza simulata con misurazioni reali tramite messaggi PING/PONG nel protocollo SynapseSub.

**Implementazione suggerita:**
```python
# In synapsesub_protocol.py
class MessageType(str, Enum):
    PING = "PING"
    PONG = "PONG"
    # ... existing types

# In ConnectionManager
async def measure_latency(self, peer_id: str):
    start = time.time()
    await self.send_message(peer_id, {"type": "PING", "timestamp": start})
    # Attendi PONG e calcola RTT
    # Aggiorna self.peer_latencies[peer_id]
```

### 3. Historical Charts
Aggiungere grafici temporali per metriche chiave (connessioni, latenza, throughput).

**Libreria suggerita:** Chart.js o D3.js

### 4. Node Search/Filter
Barra di ricerca per trovare nodi per ID, URL o canali sottoscritti.

### 5. Task Management UI
Click su un task nell'ispettore per aprire un pannello di gestione (claim, progress, complete).

---

## 🐛 Debug & Testing

### Console Browser
La UI logga eventi importanti:
```javascript
console.warn('Formato messaggio WebSocket non riconosciuto', uiData);
console.error('WebSocket error:', error);
console.warn('WebSocket chiuso, tentativo di riconnessione...');
```

### Verifica WebSocket
```javascript
// In console browser
ws.readyState // 0: CONNECTING, 1: OPEN, 2: CLOSING, 3: CLOSED
```

### Verificare Metriche
```bash
# Test endpoint direttamente
curl http://localhost:8001/network/stats | jq .
```

---

## 📦 File Modificati

1. **`app/main.py`**
   - Nuovo endpoint `/network/stats` (linee 150-209)
   - WebSocket arricchito (linee 711-737)

2. **`app/templates/index.html`**
   - **Completamente riscritto** (767 linee)
   - Nuova architettura modular del codice JavaScript
   - 4 pannelli HUD + selettore canali + ispettore interattivo
   - Sistema di rendering avanzato con gerarchia link

---

## ✅ Checklist Implementazione

- [x] Backend: Endpoint `/network/stats`
- [x] Backend: WebSocket arricchito con stato + statistiche
- [x] Frontend: Gerarchia link (WebRTC vs Scoperto)
- [x] Frontend: Dimensione nodi basata su reputazione
- [x] Frontend: Focus canale con fade-out nodi
- [x] Frontend: Selettore canali dinamico
- [x] Frontend: HUD con metriche WebRTC/PubSub
- [x] Frontend: Pannello Ispettore con click detection
- [x] Frontend: Activity glows (preparati)
- [x] Design: Palette colori coerente
- [x] Design: Animazioni smooth
- [x] UX: Controlli intuitivi
- [x] Docs: Questo documento

---

## 🎉 Conclusioni

L'interfaccia di Synapse-NG è stata trasformata da un semplice visualizzatore 3D a una **Console Operativa completa** che permette di:

1. ✅ **Vedere il polso della rete** in tempo reale
2. ✅ **Capire la topologia** WebRTC e PubSub
3. ✅ **Navigare per contesto** con il focus canali
4. ✅ **Ispezionare nodi** con un click
5. ✅ **Monitorare performance** (latenza, mesh health)

La nuova UI rende **visibile** l'architettura avanzata di SynapseComms v2.0, trasformando dati complessi in insight immediati e actionable.

**La rete ora non è solo potente - è anche bella da vedere! 🧠✨**
