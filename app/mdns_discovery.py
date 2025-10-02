"""
mDNS Discovery for Local Network

Questo modulo implementa il discovery automatico di peer Synapse-NG sulla stessa rete locale
usando mDNS/Zeroconf (DNS Service Discovery).

Funzionalità:
- Annuncio automatico del nodo sulla rete locale
- Discovery automatico di altri nodi Synapse-NG
- Zero configurazione: funziona "out of the box" senza server esterni
- Comunicazione tramite asyncio.Queue per integrazione con ConnectionManager
"""

import asyncio
import json
import logging
import socket
from typing import Optional, Dict, Set, Callable
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf, ServiceStateChange
from zeroconf.asyncio import AsyncZeroconf

logger = logging.getLogger(__name__)

# Service type per Synapse-NG (RFC 6763 format)
SERVICE_TYPE = "_synapse-ng._tcp.local."


class mDNSDiscovery:
    """
    Gestisce il discovery di nodi Synapse-NG sulla rete locale tramite mDNS/Zeroconf.

    Funziona in due modi:
    1. Annuncia questo nodo come servizio "_synapse-ng._tcp.local."
    2. Ascolta per altri nodi che annunciano lo stesso servizio

    Quando viene scoperto un nuovo peer, viene inserito in una asyncio.Queue
    che il ConnectionManager può monitorare per stabilire connessioni WebRTC.
    """

    def __init__(
        self,
        node_id: str,
        node_url: str,
        port: int,
        subscribed_channels: list,
        discovery_queue: asyncio.Queue
    ):
        """
        Args:
            node_id: ID univoco del nodo (base64)
            node_url: URL del nodo (es. http://node-1:8000)
            port: Porta HTTP su cui il nodo è in ascolto
            subscribed_channels: Lista dei canali a cui il nodo è iscritto
            discovery_queue: Queue asyncio dove inserire i peer scoperti
        """
        self.node_id = node_id
        self.node_url = node_url
        self.port = port
        self.subscribed_channels = subscribed_channels
        self.discovery_queue = discovery_queue

        # Zeroconf instance
        self.aiozc: Optional[AsyncZeroconf] = None
        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        self.browser: Optional[ServiceBrowser] = None

        # Traccia peer già scoperti (per evitare duplicati)
        self.discovered_peers: Set[str] = set()

        # Callback opzionale per notifiche custom
        self.on_peer_discovered_callback: Optional[Callable] = None

        # Task asyncio per gestione eventi
        self._running = False
        self._service_name = self._create_service_name()

    def _create_service_name(self) -> str:
        """
        Crea un nome univoco per il servizio mDNS.
        Formato: synapse-ng-{node_id_trunc}._synapse-ng._tcp.local.
        """
        # Usa i primi 8 caratteri del node_id per un nome leggibile
        node_id_short = self.node_id[:8].replace('/', '-').replace('+', '-')
        return f"synapse-ng-{node_id_short}.{SERVICE_TYPE}"

    def _create_service_info(self) -> ServiceInfo:
        """
        Crea un ServiceInfo per annunciare questo nodo sulla rete locale.

        Properties include:
        - node_id: ID completo del nodo
        - node_url: URL per HTTP bootstrap
        - channels: Lista canali sottoscritti (JSON)
        """
        # Ottieni indirizzo IP locale
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        # Properties (metadati chiave-valore)
        properties = {
            b"node_id": self.node_id.encode("utf-8"),
            b"node_url": self.node_url.encode("utf-8"),
            b"channels": json.dumps(self.subscribed_channels).encode("utf-8"),
        }

        service_info = ServiceInfo(
            type_=SERVICE_TYPE,
            name=self._service_name,
            port=self.port,
            properties=properties,
            addresses=[socket.inet_aton(local_ip)],
            server=f"{hostname}.local.",
        )

        return service_info

    async def start(self):
        """
        Avvia mDNS discovery:
        1. Annuncia questo nodo come servizio
        2. Inizia a cercare altri nodi
        """
        if self._running:
            logger.warning("mDNS discovery già in esecuzione")
            return

        self._running = True

        try:
            # Inizializza Zeroconf (async-safe)
            self.aiozc = AsyncZeroconf()
            self.zeroconf = self.aiozc.zeroconf

            # Crea e registra il servizio
            self.service_info = self._create_service_info()
            await self.aiozc.async_register_service(self.service_info)

            logger.info(f"📡 mDNS: Servizio registrato come {self._service_name}")

            # Inizia browser per scoprire altri nodi
            self.browser = ServiceBrowser(
                self.zeroconf,
                SERVICE_TYPE,
                handlers=[self._on_service_state_change]
            )

            logger.info(f"🔍 mDNS: Browser avviato per servizi {SERVICE_TYPE}")

        except Exception as e:
            logger.error(f"Errore avvio mDNS discovery: {e}")
            self._running = False
            raise

    async def stop(self):
        """
        Ferma mDNS discovery e de-registra il servizio.
        """
        if not self._running:
            return

        self._running = False

        try:
            # De-registra servizio
            if self.aiozc and self.service_info:
                await self.aiozc.async_unregister_service(self.service_info)
                logger.info(f"📡 mDNS: Servizio de-registrato")

            # Chiudi Zeroconf
            if self.aiozc:
                await self.aiozc.async_close()
                logger.info(f"🔍 mDNS: Zeroconf chiuso")

        except Exception as e:
            logger.error(f"Errore stop mDNS discovery: {e}")

    def _on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange
    ):
        """
        Callback chiamata quando cambia lo stato di un servizio mDNS.

        Args:
            zeroconf: Istanza Zeroconf
            service_type: Tipo di servizio (_synapse-ng._tcp.local.)
            name: Nome del servizio (es. synapse-ng-abc123._synapse-ng._tcp.local.)
            state_change: Tipo di cambiamento (Added, Removed, Updated)
        """
        if state_change == ServiceStateChange.Added:
            # Nuovo servizio scoperto
            asyncio.create_task(self._handle_service_added(zeroconf, service_type, name))
        elif state_change == ServiceStateChange.Removed:
            # Servizio rimosso (peer disconnesso)
            asyncio.create_task(self._handle_service_removed(name))

    async def _handle_service_added(self, zeroconf: Zeroconf, service_type: str, name: str):
        """
        Gestisce la scoperta di un nuovo servizio Synapse-NG.
        """
        try:
            # Ignora il nostro stesso servizio
            if name == self._service_name:
                logger.debug(f"mDNS: Ignorato servizio proprio ({name})")
                return

            # Ottieni informazioni complete sul servizio
            # IMPORTANTE: Usa to_thread per chiamata sincrona get_service_info
            service_info = await asyncio.to_thread(
                zeroconf.get_service_info,
                service_type,
                name,
                timeout=3000  # 3 secondi
            )

            if not service_info:
                logger.warning(f"mDNS: Impossibile ottenere info per {name}")
                return

            # Estrai properties
            properties = service_info.properties
            peer_id = properties.get(b"node_id", b"").decode("utf-8")
            peer_url = properties.get(b"node_url", b"").decode("utf-8")
            peer_channels_json = properties.get(b"channels", b"[]").decode("utf-8")

            if not peer_id or not peer_url:
                logger.warning(f"mDNS: Servizio {name} senza node_id o node_url")
                return

            # Verifica se già scoperto
            if peer_id in self.discovered_peers:
                logger.debug(f"mDNS: Peer {peer_id[:16]}... già scoperto")
                return

            # Segna come scoperto
            self.discovered_peers.add(peer_id)

            # Parse canali
            try:
                peer_channels = json.loads(peer_channels_json)
            except json.JSONDecodeError:
                peer_channels = []

            # Crea oggetto peer
            peer_info = {
                "peer_id": peer_id,
                "peer_url": peer_url,
                "channels": peer_channels,
                "discovery_method": "mdns",
                "service_name": name,
            }

            logger.info(
                f"🎯 mDNS: Nuovo peer scoperto! {peer_id[:16]}... "
                f"({peer_url}, canali: {len(peer_channels)})"
            )

            # Inserisci nella queue per il ConnectionManager
            await self.discovery_queue.put(peer_info)

            # Chiama callback opzionale
            if self.on_peer_discovered_callback:
                await self.on_peer_discovered_callback(peer_info)

        except Exception as e:
            logger.error(f"Errore gestione servizio mDNS aggiunto: {e}")

    async def _handle_service_removed(self, name: str):
        """
        Gestisce la rimozione di un servizio (peer disconnesso).
        """
        logger.info(f"📴 mDNS: Servizio rimosso: {name}")
        # Nota: Qui potremmo notificare il ConnectionManager della disconnessione,
        # ma per ora la mesh optimization gestirà le disconnessioni automaticamente

    def set_peer_discovered_callback(self, callback: Callable):
        """
        Imposta una callback opzionale per notifiche custom di peer scoperti.
        """
        self.on_peer_discovered_callback = callback

    def get_discovered_peers(self) -> Set[str]:
        """
        Ottiene l'insieme dei peer ID scoperti via mDNS.
        """
        return self.discovered_peers.copy()
