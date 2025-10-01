"""
Gestione identità crittografica per nodi Synapse-NG
Usa Ed25519 per firme digitali veloci e sicure
"""

import os
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
import base64


class NodeIdentity:
    """Identità crittografica persistente di un nodo"""

    def __init__(self, key_path: str = None):
        self.key_path = key_path or os.getenv("KEY_PATH", "/app/data/node.key")
        self.private_key = None
        self.public_key = None
        self.node_id = None

        # Carica o genera identità
        if os.path.exists(self.key_path):
            self._load_identity()
        else:
            self._generate_identity()

    def _generate_identity(self):
        """Genera nuova identità Ed25519"""
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

        # ID del nodo = base64 della chiave pubblica
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.node_id = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')

        # Salva chiave privata
        self._save_identity()

        print(f"🔐 Nuova identità generata: {self.node_id[:16]}...")

    def _save_identity(self):
        """Salva chiave privata su disco"""
        # Crea directory se non esiste
        key_dir = Path(self.key_path).parent
        key_dir.mkdir(parents=True, exist_ok=True)

        # Serializza chiave privata
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Salva in modo atomico
        temp_path = f"{self.key_path}.tmp"
        with open(temp_path, 'wb') as f:
            f.write(private_pem)
        os.replace(temp_path, self.key_path)

        # Set permissions (solo owner può leggere)
        os.chmod(self.key_path, 0o600)

    def _load_identity(self):
        """Carica identità esistente"""
        with open(self.key_path, 'rb') as f:
            private_pem = f.read()

        self.private_key = serialization.load_pem_private_key(
            private_pem,
            password=None
        )
        self.public_key = self.private_key.public_key()

        # Ricalcola ID
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self.node_id = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')

        print(f"🔓 Identità caricata: {self.node_id[:16]}...")

    def sign_data(self, data: dict) -> str:
        """Firma dati con chiave privata"""
        # Serializza deterministicamente
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        message = canonical.encode('utf-8')

        # Firma
        signature = self.private_key.sign(message)

        # Ritorna in base64
        return base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    def verify_signature(self, data: dict, signature_b64: str, public_key_b64: str) -> bool:
        """Verifica firma di dati"""
        try:
            # Decodifica chiave pubblica
            pub_bytes = base64.urlsafe_b64decode(public_key_b64 + '==')
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)

            # Decodifica firma
            signature = base64.urlsafe_b64decode(signature_b64 + '==')

            # Serializza dati
            canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
            message = canonical.encode('utf-8')

            # Verifica
            public_key.verify(signature, message)
            return True

        except (InvalidSignature, Exception) as e:
            print(f"⚠️  Verifica firma fallita: {e}")
            return False

    def get_public_key_b64(self) -> str:
        """Ottieni chiave pubblica in base64"""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')

    def __repr__(self):
        return f"NodeIdentity(id={self.node_id[:16]}...)"
