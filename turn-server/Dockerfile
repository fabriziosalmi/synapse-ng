# Dockerfile per coturn (TURN/STUN server)
FROM coturn/coturn:latest

# Copia configurazione
COPY turnserver.conf /etc/coturn/turnserver.conf

# Esponi porte
# 3478: STUN/TURN TCP/UDP
# 5349: STUN/TURN over TLS
# 49152-65535: Range porte relay
EXPOSE 3478/tcp 3478/udp
EXPOSE 5349/tcp 5349/udp
EXPOSE 49152-65535/udp

# Avvia coturn
CMD ["turnserver", "-c", "/etc/coturn/turnserver.conf"]
