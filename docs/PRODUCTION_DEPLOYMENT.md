# 🚀 Production Deployment Guide - Synapse-NG

Complete guide for deploying Synapse-NG in production with full support for NAT traversal, mDNS discovery, and monitoring.

---

## Table of Contents

1. [TURN Server Deployment](#1-turn-server-deployment)
2. [ICE Configuration](#2-ice-configuration)
3. [mDNS Discovery](#3-mdns-discovery)
4. [Monitoring & Metrics](#4-monitoring--metrics)
5. [Docker Deployment](#5-docker-deployment)
6. [Security Considerations](#6-security-considerations)
7. [Troubleshooting](#7-troubleshooting)
8. [Best Practices](#8-best-practices)
9. [Performance Tuning](#9-performance-tuning)
10. [Deployment Examples](#10-deployment-examples)

---

## 1. TURN Server Deployment

### Why is a TURN server needed?

- **STUN** works for ~80% of connections (cone/restricted NAT)
- **TURN** is necessary for symmetric NATs (~20% of cases)
- TURN acts as relay when direct P2P connection fails

### Docker Setup

\`\`\`bash
# 1. Configure credentials
cd turn-server
# Edit turnserver.conf:
#   - Change user/password
#   - Set external-ip if behind NAT

# 2. Start TURN server
docker-compose -f docker-compose.turn.yml up -d

# 3. Verify functionality
docker-compose -f docker-compose.turn.yml logs -f turn-server

# 4. Test TURN server
docker exec -it synapse-turn turnutils_uclient -v -t -u synapse -w changeme123 127.0.0.1
\`\`\`

### Configure Nodes to Use TURN

**Option 1: Environment Variable**

\`\`\`bash
export ICE_SERVERS_JSON='[
  {"urls":"stun:stun.l.google.com:19302"},
  {"urls":"turn:your-turn-server.com:3478","username":"synapse","credential":"changeme123"}
]'

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
\`\`\`

**Option 2: Docker Compose**

\`\`\`yaml
environment:
  - ICE_SERVERS_JSON=[{"urls":"turn:turn-server:3478","username":"synapse","credential":"changeme123"}]
\`\`\`

### Public TURN Server (Cloud Deployment)

\`\`\`bash
# AWS/GCP/Azure: Open ports
# TCP/UDP 3478 (STUN/TURN)
# TCP/UDP 5349 (TURN over TLS)
# UDP 49152-65535 (relay range)

# Configure external-ip in turnserver.conf
external-ip=YOUR_PUBLIC_IP

# If behind load balancer
# external-ip=PUBLIC_IP/PRIVATE_IP
\`\`\`

---

## 2. ICE Configuration

### Recommended ICE Servers

\`\`\`json
[
  {"urls": "stun:stun.l.google.com:19302"},
  {"urls": "stun1.l.google.com:19302"},
  {"urls": "turn:your-turn.example.com:3478", "username": "user", "credential": "pass"}
]
\`\`\`

### ICE Trickle

✅ **Already enabled!** aiortc supports ICE trickle natively.

**Advantages:**
- Faster connections (doesn't wait for all candidates)
- Better UX (first packets transmitted earlier)
- Reduces setup latency from ~3s to ~1s

**Debug Logs:**
\`\`\`bash
# Enable detailed logs to see ICE candidates
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --log-level debug
\`\`\`

You'll see:
\`\`\`
🧊 ICE candidate for abc123...: type=host, protocol=udp
🧊 ICE candidate for abc123...: type=srflx, protocol=udp
�� ICE candidate for abc123...: type=relay, protocol=udp
\`\`\`

### ICE Candidate Priority

1. **host**: Local IP (LAN) - minimum latency
2. **srflx**: Server reflexive (STUN) - public IP
3. **relay**: TURN relay - guaranteed fallback

---

## 3. mDNS Discovery

### When to Use mDNS?

✅ **Use mDNS for:**
- Local networks (conferences, offices, home)
- Local development/testing
- Offline environments

❌ **DON'T use mDNS for:**
- Public cloud deployment
- Geographically distributed nodes
- Isolated containers (unless custom network)

### mDNS Setup on Docker

\`\`\`bash
# Use configuration with custom network
docker-compose -f docker-compose.mdns.yml up -d

# Verify discovery
docker-compose -f docker-compose.mdns.yml logs | grep "mDNS"
\`\`\`

**Expected output:**
\`\`\`
📡 mDNS: Service registered as synapse-ng-abc123._synapse-ng._tcp.local.
🔍 mDNS: Browser started for _synapse-ng._tcp.local. services
🎯 mDNS: New peer discovered! def456... (http://node-2:8000, channels: 2)
\`\`\`

### Disable mDNS

\`\`\`bash
# Via env
export DISABLE_MDNS=true

# Via docker-compose
environment:
  - DISABLE_MDNS=true
\`\`\`

---

## 4. Monitoring & Metrics

### ICE Metrics Endpoint

\`\`\`bash
# Get ICE metrics
curl http://localhost:8000/webrtc/ice-metrics | jq
\`\`\`

**Output:**
\`\`\`json
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
\`\`\`

### Key Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Success Rate | >90% | 70-90% | <70% |
| Avg Connection Time | <2s | 2-5s | >5s |
| Failed Connections | <10% | 10-30% | >30% |

### Prometheus Dashboard (optional)

The coturn TURN server supports Prometheus metrics:

\`\`\`conf
# In turnserver.conf
prometheus
prometheus-port=9641
\`\`\`

Then scrape with Prometheus:
\`\`\`yaml
scrape_configs:
  - job_name: 'synapse-turn'
    static_configs:
      - targets: ['turn-server:9641']
\`\`\`

---

## 5. Docker Deployment

### Complete Production Setup

\`\`\`bash
# 1. Clone repository
git clone https://github.com/your-org/synapse-ng
cd synapse-ng

# 2. Configure TURN server
cd turn-server
# Edit turnserver.conf (credentials, external-ip)

# 3. Start TURN
docker-compose -f docker-compose.turn.yml up -d

# 4. Configure nodes
export ICE_SERVERS_JSON='[...]'  # Include TURN

# 5. Start nodes
docker-compose up -d

# 6. Verify
docker-compose logs -f
curl http://localhost:8001/webrtc/ice-metrics
\`\`\`

### Multi-Host Deployment

**Host 1 (TURN Server):**
\`\`\`bash
docker-compose -f docker-compose.turn.yml up -d
# Expose port 3478 publicly
\`\`\`

**Host 2-N (Nodes):**
\`\`\`bash
export ICE_SERVERS_JSON='[{"urls":"turn:HOST1_IP:3478","username":"synapse","credential":"..."}]'
docker-compose up -d node-1
\`\`\`

---

## 6. Security Considerations

### TURN Server

⚠️ **IMPORTANT:**

1. **Change default credentials:**
   \`\`\`conf
   # In turnserver.conf
   user=synapse:YOUR_STRONG_PASSWORD_HERE
   \`\`\`

2. **Use TLS in production:**
   \`\`\`conf
   tls-listening-port=5349
   cert=/path/to/cert.pem
   pkey=/path/to/privkey.pem
   \`\`\`

3. **Limit bandwidth:**
   \`\`\`conf
   max-bps=500000  # 500 Kbps per client
   total-quota=100  # 100 MB per session
   \`\`\`

4. **Firewall:**
   \`\`\`bash
   # Allow only known IPs
   ufw allow from KNOWN_IP to any port 3478
   \`\`\`

### Synapse-NG Nodes

1. **HTTPS mandatory in production:**
   \`\`\`bash
   # Use reverse proxy (nginx/caddy)
   # Terminate TLS there, not in the app
   \`\`\`

2. **Sensitive environment variables:**
   \`\`\`bash
   # Don't commit .env with credentials
   echo ".env" >> .gitignore
   \`\`\`

3. **Rate limiting:**
   \`\`\`python
   # In main.py (optional)
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   \`\`\`

---

## 7. Troubleshooting

### Problem: WebRTC Connections Fail

**Diagnosis:**
\`\`\`bash
# 1. Check ICE metrics
curl http://localhost:8000/webrtc/ice-metrics

# 2. Check logs
docker-compose logs node-1 | grep -i "ice\|webrtc"

# 3. Test TURN server
docker exec -it synapse-turn turnutils_uclient -v -t -u synapse -w changeme123 127.0.0.1
\`\`\`

**Solutions:**
- Success rate <70%? → Add TURN server
- "Connection timeout"? → Check firewall UDP ports
- "Authentication failed"? → Check TURN credentials

---

### Problem: mDNS Doesn't Discover Peers

**Diagnosis:**
\`\`\`bash
# Check mDNS service
docker-compose logs node-1 | grep mDNS

# Manual test (on host)
avahi-browse -r _synapse-ng._tcp
# or
dns-sd -B _synapse-ng._tcp
\`\`\`

**Solutions:**
- In Docker? → Use \`docker-compose.mdns.yml\` (custom network)
- On macOS? → Works natively
- On Linux? → Install \`avahi-daemon\`
- Firewall? → Allow multicast UDP 5353

---

### Problem: TURN Server Not Responding

**Diagnosis:**
\`\`\`bash
# Test connectivity
nc -u turn-server.com 3478
# Send any byte, should respond

# Test with turnutils
turnutils_uclient -v -t -u synapse -w changeme123 turn-server.com
\`\`\`

**Solutions:**
- Ports closed? → Open 3478 UDP/TCP, 49152-65535 UDP
- Firewall active? → Allow TURN traffic
- Wrong external-ip? → Check in turnserver.conf

---

## 8. Best Practices

### Optimal Configuration

\`\`\`bash
# For Internet deployment (with TURN)
export ICE_SERVERS_JSON='[
  {"urls":"stun:stun.l.google.com:19302"},
  {"urls":"stun:stun1.l.google.com:19302"},
  {"urls":"turn:turn.mycompany.com:3478","username":"user","credential":"pass"}
]'

# For local LAN (mDNS only)
export DISABLE_MDNS=false
export RENDEZVOUS_URL=""  # P2P mode

# For hybrid environments (Internet + LAN)
# Use both: TURN + mDNS
\`\`\`

### Continuous Monitoring

\`\`\`bash
# Cronjob for health check
*/5 * * * * curl -s http://localhost:8000/webrtc/ice-metrics | jq '.summary.success_rate_percent' | awk '{if($1<80) print "WARNING: Low success rate"}'
\`\`\`

### Backup & Recovery

\`\`\`bash
# Backup node identities
tar -czf synapse-backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf synapse-backup-YYYYMMDD.tar.gz
\`\`\`

---

## 9. Performance Tuning

### TURN Server

\`\`\`conf
# Optimized turnserver.conf
max-bps=1000000          # 1 Mbps per client
total-quota=200          # 200 MB per session
user-quota=100           # 100 MB per user
stale-nonce=600          # 10 minutes
max-allocate-lifetime=3600  # 1 hour
\`\`\`

### Synapse-NG Nodes

\`\`\`bash
# Increase uvicorn workers for load
uvicorn app.main:app --workers 4 --host 0.0.0.0

# Use Gunicorn for production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
\`\`\`

---

## 10. Deployment Examples

### Scenario 1: Startup with 3-10 Nodes (LAN)

\`\`\`bash
# mDNS ONLY, no external servers
export DISABLE_MDNS=false
export RENDEZVOUS_URL=""
python -m uvicorn app.main:app --host 0.0.0.0
\`\`\`

**Advantages:**
- Zero configuration
- Zero server costs
- Works offline

---

### Scenario 2: Distributed Company (Internet)

\`\`\`bash
# Deploy centralized TURN server
docker-compose -f docker-compose.turn.yml up -d

# Nodes use TURN
export ICE_SERVERS_JSON='[{"urls":"turn:turn.company.com:3478","username":"user","credential":"pass"}]'
docker-compose up -d
\`\`\`

**Advantages:**
- Works through any NAT
- ~95% connection success rate
- Guaranteed fallback

---

### Scenario 3: Conference/Temporary Event

\`\`\`bash
# Organizer starts rendezvous + node
docker-compose up -d rendezvous node-1

# Participants (same Wi-Fi network)
# mDNS discovers them automatically
export BOOTSTRAP_NODES=http://organizer-laptop:8001
python -m uvicorn app.main:app
\`\`\`

**Advantages:**
- Quick setup
- mDNS + bootstrap for robustness
- Zero cloud infrastructure

---

## Conclusion

With this configuration, Synapse-NG is production-ready for:

✅ **Any network topology** (LAN, Internet, symmetric NAT)
✅ **Complete monitoring** (ICE metrics, success rate)
✅ **High reliability** (STUN + TURN fallback)
✅ **Zero-config local** (mDNS discovery)

**Expected Success Rate:**
- STUN only: 70-85%
- STUN + TURN: 95-99%
- LAN + mDNS: ~100%

---

**Synapse-NG: "It just works", everywhere.** 🌐🚀
