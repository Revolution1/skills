---
name: enterprise-infrastructure-osint
description: Comprehensive methodology for mapping company infrastructure, technology stacks, and relationships through multi-layer OSINT and network reconnaissance. Includes passive DNS enumeration, port scanning, frontend stack fingerprinting, API extraction, certificate analysis, and confidence-tiered evidence framework.
allowed-tools:
  - "Bash"
  - "Read"
  - "Write"
  - "web_fetch"
---

# Enterprise Infrastructure Deep Reconnaissance

You are an infrastructure OSINT specialist. Your mission is to systematically map a company's digital footprint across DNS, network services, frontend technologies, backend patterns, and inter-infrastructure relationships. This skill captures a **proven two-phase methodology** from live enterprise investigation work, enabling reusable, confidence-aware reconnaissance.

---

## 🎯 Core Objectives

1. **Asset Inventory**: Discover all subdomains, IP addresses, and service endpoints.
2. **Technology Stack Profiling**: Identify frontend frameworks, backend patterns, cloud dependencies, and edge infrastructure.
3. **Relationship Mapping**: Connect public-facing surfaces to internal tooling, private networks, and organizational boundaries.
4. **Evidence Tiering**: Classify findings by confidence level to support prioritized investigation and reduce false positives.
5. **Audit Trail**: Create machine-readable evidence files linking conclusions to source probes.

---

## 📋 Prerequisites

- **Network connectivity**: Ability to run DNS queries and TCP probes from a control workstation.
- **Tools**: Core OSINT toolkit:
  - DNS: `dig`, `host`, `nslookup`
  - Reverse IP: `hackertarget.com` API or `crt.sh` (Certificate Transparency logs)
  - Network scanning: `nmap` (with service detection `-sV`, script scans `-sC`)
  - TLS/Certificate: `openssl s_client`, `curl --resolve`
  - Grep/text processing: `rg`, `grep`, `awk`, `sed`
  - Optional HTTP clients: `curl`, `wget`
- **Working directory**: A structured workspace with subdirectories for DNS, ports, HTTP headers, TLS, reports, and raw evidence.
- **Time investment**: ~2–4 hours for comprehensive enumeration depending on organization size and network complexity.

---

## 🔄 Two-Phase Methodology

### Phase 1: Asset Discovery & Technology Stack Fingerprinting

**Goal**: Build a complete inventory of domains, IPs, services, and identify frontend/backend technologies.

#### Step 1.1: DNS & Subdomain Enumeration

1. **Seed domain collection**:
   ```bash
   # List known parent domains (from WHOIS, initial investigation, or user input)
   dig +short <domain>
   dig +short www.<domain>
   dig +short api.<domain>
   ```

2. **Certificate Transparency (CT) log mining**:
   ```bash
   # Extract all registered certificates for the domain
   curl -s "https://crt.sh/?q=%.<domain>&output=json" | jq -r '.[].name_value' | sort -u
   ```

3. **Consolidate DNS records**:
   - Create a file `dns/all_domains_discovered.txt` listing all subdomains found.
   - Categorize by type: `app.*`, `api.*`, `cdn.*`, `admin.*`, `internal.*`, `dev.*`.

#### Step 1.2: Reverse-IP Aggregation

1. **Query each unique IP** for known hosting relationships:
   ```bash
   # Hackertarget API example (free tier limit ~100 queries/day)
   curl -s "https://api.hackertarget.com/reverseiplookup/?ip=<IP>" | head -20
   
   # Or manual nmap approach (slow but comprehensive)
   nmap --script hostmap-bfk.nse --script-args hostmap-bfk.prefix=<domain> <IP>
   ```

2. **Consolidate results** into `dns/reverseip_all_domains.txt`.
3. **Note**: Reverse-IP historical data is noisy (includes JavaScript tokens, CSS classes, unrelated domains). Mark as **Tier C (hint-only)** evidence.

#### Step 1.3: IP & Port Discovery

1. **Create IP list** from DNS + reverse-IP results.
   ```bash
   # Extract unique IPs into dns/unique_ips.txt
   grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' dns/* | cut -d: -f2 | sort -u > dns/unique_ips.txt
   ```

2. **Run tiered port scans**:
   ```bash
   # HTTP/HTTPS-focused (fast)
   nmap -p80,443,8080,8443 -sV -sC -oA ports/nmap_http_tls <target_list>
   
   # Service detection (slower)
   nmap -p- -sV --top-ports 1000 -oA ports/nmap_service <target_list>
   
   # Full scan (comprehensive but very slow)
   nmap -p- -sV -sC -oA ports/nmap_full <target_list>
   ```

3. **Parse output** into `ports/port_service_map.txt`:
   ```
   <IP>    <port>/tcp    <service>    <banner>
   ```

#### Step 1.4: Frontend Technology Stack Fingerprinting

For each HTTP/HTTPS endpoint (80, 443, 8080, 8443):

1. **Fetch homepage**:
   ```bash
   curl -s https://<domain>:<port> | head -1000 > raw/<domain>.html
   ```

2. **Identify frontend framework**:
   - **Vue.js** (Vue 2/3): Look for `<div id="app">`, `webpackJsonp`, `__NUXT__`, bundle patterns
   - **React**: Look for `<div id="root">`, `react`, `react-dom` in bundles
   - **Angular**: Look for `ng-app`, `angular` bundles
   - **Other SPA**: Vite (`import.meta`), Next.js (`_next/`), Remix, Svelte

   ```bash
   # Example: grep for Vue markers
   grep -i "vue\|vuex\|vue-router" raw/<domain>.html
   rg -i "from 'vue'|from \"vue\"" raw/<domain>.assets/ --type js
   ```

3. **Identify UI libraries**:
   - Vant, Element Plus, Ant Design, shadcn/ui, Bootstrap, Tailwind, Material-UI

4. **Identify backend HTTP client**:
   - Axios, fetch, jQuery, superagent, etc.

5. **Extract visible API endpoints** from bundle:
   ```bash
   # Look for API patterns in main bundle and chunks
   rg -i "https?://.*\.com/api/|'/api/|/v\d+/" raw/<domain>/ --type js | head -100
   ```

6. **Check for code splitting / dynamic chunks**:
   - Modern bundlers (Webpack, Vite) often hide business logic in dynamic chunks
   - Extract chunk filenames from main bundle HTML or manifest
   - Download each chunk file and grep for endpoints

7. **Document findings** in `report/<domain>_stack_analysis.md`:
   - Frontend framework + version (if detectable)
   - UI libraries
   - HTTP client
   - Observable endpoints
   - Code splitting patterns
   - Native bridge / hybrid app indicators

#### Step 1.5: TLS & Certificate Analysis

1. **Query each public endpoint**:
   ```bash
   openssl s_client -connect <IP>:443 -servername <domain> < /dev/null 2>/dev/null | openssl x509 -noout -text
   ```

2. **Extract and document**:
   - Certificate CN, SANs, issuer, validity dates
   - Observe certificate reuse across IPs/domains (SNI routing indicator)

3. **Create certificate matrix** in `raw/cert_matrix.txt`:
   ```
   <IP>    <SNI_domain>    <Cert_CN>    <Validity_Start>    <Validity_End>    <Issuer>
   ```

---

### Phase 2: Relationship Mapping & Infrastructure Boundary Detection

**Goal**: Map relationships between public edges, internal tooling, private networks, and identify organizational infrastructure boundaries.

#### Step 2.1: DNS Resolution Consolidation

1. **Create domain-to-IP mapping** (`dns/domain_ip_map.tsv`):
   ```
   domain    IP    record_type    cname_chain
   app.weicha88.com    139.224.204.241    A    pro-istio-external-slb.weicha88.com
   ```

2. **Create IP-to-domain reverse mapping** for quick lookup.

#### Step 2.2: Live DNS & SNI Probing

1. **Current DNS state**:
   ```bash
   for domain in $(cat dns/all_domains_discovered.txt); do
     echo "=== $domain ===" >> raw/live_dns_probe.txt
     dig +short $domain >> raw/live_dns_probe.txt
   done
   ```

2. **SNI certificate discovery** (multi-cert on shared IP):
   ```bash
   for ip in $(cat dns/unique_ips.txt); do
     for domain in $(cat dns/all_domains_discovered.txt); do
       echo "SNI=$domain on IP=$ip:"
       openssl s_client -connect $ip:443 -servername $domain < /dev/null 2>/dev/null \
         | openssl x509 -noout -text | grep -E "Subject:|CN=|DNS:"
     done
   done >> raw/sni_cert_matrix.txt
   ```

3. **Analyze results**:
   - **Single cert across multiple domains** → Virtual hosting
   - **Different certs per domain on same IP** → SNI routing
   - **Forced host headers** → Backend routing logic (see Step 2.3)

#### Step 2.3: Forced Host Routing & Load Balancer Fingerprinting

1. **Probe with forced host header**:
   ```bash
   # Force domain A to IP of domain B
   curl -vI -H "Host: <domain_A>" https://<ip_of_domain_B>:443 2>&1 | grep -E "HTTP|server:|x-powered-by|istio|envoy|nginx|tengine"
   
   # Shorter form with --resolve
   curl --resolve <domain_A>:443:<ip_of_domain_B> -vI https://<domain_A>/ 2>&1 | head -30
   ```

2. **Document response patterns**:
   - Application responds normally → Likely same backend
   - 502 Bad Gateway / TLS reset → Different backend / strict routing
   - Redirect or static page → Proxy behavior or misconfiguration

3. **Identify edge infrastructure**:
   - `server: istio-envoy` → Kubernetes ingress (likely Istio)
   - `server: tengine` → Alibaba Cloud or legacy on-premise
   - `server: nginx` → Common COTS load balancer
   - `server: Apache` → Traditional backend server

#### Step 2.4: Private Network Detection

1. **Check for RFC 1918 addresses** in DNS or reverse-IP results:
   ```bash
   # Private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
   rg '(10|192\.168|172\.1[6-9]|172\.2[0-9]|172\.3[0-1])\.' dns/
   ```

2. **Attempt connection** (usually fails from public internet):
   ```bash
   nmap -p22,80,443 <private_range> --max-retries 0 -T5
   ```

3. **Classify as**:
   - **Internal-only tooling**: Jenkins, GitLab, Nexus, Harbor, Kibana (development/CI/CD)
   - **Internal services**: Admin panels, monitoring, data processing
   - **No public exposure**: Expected, confirms organizational boundary

#### Step 2.5: Cross-Domain Artifact Collection

1. **Google Cloud / Alibaba Cloud / AWS indicators**:
   ```bash
   # Cloud storage links
   rg -i 'oss-cn-|aliyuncs|googleapis|amazonaws|storage.googleapis' raw/
   
   # Log aggregation endpoints
   rg -i 'log\.aliyuncs|cloudwatch|stackdriver|loggly' raw/
   ```

2. **Document** in `report/cloud_and_storage.md`.

#### Step 2.6: Evidence Consolidation & Confidence Tiering

Create a master relationship diagram in `report/infrastructure_relationships.md`:

```markdown
## Public Edges
- IP A (edge tech: Istio/Envoy) → domains: {app.company.com, api.company.com, ...}
- IP B (edge tech: Tengine) → domains: {partner.com, legacy.partner.com, ...}

## Private Tooling (RFC 1918)
- 10.10.1.x/24 (yapi, gitlab, harbor, nexus) → Internal-only dev/CI

## Evidence Confidence Tiers
- Tier A (high): live DNS dig, SNI probes, nmap scans
- Tier B (medium): consolidated mapping files from structured collection
- Tier C (hint-only): reverse-IP historical aggregation (noisy)
```

---

## 🛠️ Recommended Tools & Commands

| Task | Primary Tool | Backup |
|:---|:---|:---|
| DNS resolution | `dig` | `nslookup`, `host` |
| CT log mining | `curl + crt.sh` | Manual CT log browser |
| Reverse IP | `hackertarget.com` API | `nmap --script hostmap-bfk` |
| Port scanning | `nmap` | `masscan` (fast), `zmap` (research) |
| TLS certificate | `openssl s_client` | `curl -vI`, `testssl.sh` |
| Header inspection | `curl -I`, `curl -v` | `nc`, `telnet` |
| Grep/parsing | `rg` (ripgrep), `jq` | `grep`, `sed`, `awk` |
| Workflow automation | `bash` loops with file tracking | Python/Go scripts |

---

## 📊 Evidence Confidence Framework

Use this framework to classify every finding:

### Tier A: High Confidence (Direct/Live Evidence)
- **DNS**: Live `dig` output, current resolution state
- **Network**: `nmap` scan output with confirmed open ports
- **TLS**: `openssl s_client` certificate captures with timestamps
- **HTTP**: Live `curl` probes with response headers and status codes
- **Definition**: Directly observable in current time window, repeatable

### Tier B: Medium Confidence (Indirect but Structured)
- **Consolidated mappings**: Derived from Tier A sources, but requires aggregation logic
- **Multi-source correlation**: Same finding from ≥2 independent tools
- **Example**: `domain_ip_map.tsv` built from both DNS queries and nmap reverse scans
- **Definition**: Trustworthy but requires interpretation step

### Tier C: Hint-Only / Noisy (Historical Context)
- **Reverse-IP historical data**: Known to include stale records, false positives, CSS/JS tokens
- **Shared certificate issuer**: Weak signal for shared backend (many orgs share DigiCert, etc.)
- **Cached/archived data**: WHOIS history, old DNS records
- **Definition**: Useful for hints/context only; do NOT use alone to assert relationships

### False-Positive Controls

1. **Did NOT assume shared backend from**:
   - Shared certificate issuer (DigiCert issues millions)
   - Same CNAME prefix in DNS history
   - Reverse-IP co-location without current live probe confirmation

2. **DID require** at least one Tier A probe (SNI, host forcing, nmap) before asserting relationship

3. **DID test** both directions:
   - Can domain A reach IP of domain B? (host forcing)
   - Does TLS succeed? (SNI check)
   - Does application respond or error? (502 indicates separation)

---

## ⚠️ Common Pitfalls & Solutions

| Pitfall | Problem | Solution |
|:---|:---|:---|
| **Sourcemap endpoints** | Return 200 but serve SPA HTML fallback instead of JSON | Ignore `.js.map` URLs; use direct chunk file downloads instead |
| **Code splitting** | Modern SPAs hide ~90% of API logic in dynamic chunks | Extract chunk filenames from main bundle, batch-download via `/assets/*.js`, grep endpoints |
| **Virtual hosting overlap** | Same IP, different domains, multiple certs via SNI | Build SNI matrix; use forced host routing to test if backend routes or rejects |
| **Reverse-IP noise** | Aggregated historical data includes CSS tokens, JS keywords, unrelated domains | Filter by domain regex; mark as Tier C (hint-only); require Tier A confirmation |
| **TLS reset on port 443** | Ambiguous signal (no TLS, strict routing, DDoS protection) | Try different SNI values; check if IP + HTTP works; correlate with nmap -sV |
| **WHOIS privacy** | Registrant hidden behind privacy service | Skip; focus on DNS, certificates, network evidence instead |
| **Rate limiting** | Reverse-IP APIs and CT log bulk fetches may throttle | Use caching; space out requests; batch process results locally |
| **Cloud infrastructure** | AWS/Alibaba/GCP IPs are shared across many organizations | Correlate with DNS/certificate evidence; don't assume co-location = relationship |

---

## 📝 Output Deliverables Template

For each investigation, generate these artifacts:

### 1. **DNS & IP Inventory** (`dns/`)
```
all_domains_discovered.txt          # Cleaned subdomain list
domain_ip_map.tsv                   # domain, IP, record_type, CNAME chain
domain_cname_map.tsv                # CNAME resolution chains
reverseip_all_domains.txt           # Historical reverse-IP context (Tier C)
unique_ips.txt                      # IPs for scanning
```

### 2. **Port & Service Scan** (`ports/`)
```
nmap_http_tls.nmap                  # Fast: -p80,443 -sV
nmap_service.nmap                   # Medium: -p- -sV --top-ports
nmap_full.nmap                      # Full: -p- -sV -sC
port_service_map.txt                # Parsed table of open ports
```

### 3. **Technology Stack Report** (`report/`)
```
<domain>_stack_analysis.md          # Frontend/backend stack details
                                     # Includes: framework, UI libs, APIs, 
                                     # code splitting patterns, cloud deps
infrastructure_relationships.md      # Public edges, private tooling, boundaries
evidence_manifest.txt               # Traceability: conclusion → source file/line
```

### 4. **Raw Evidence** (`raw/`)
```
<domain>.html                       # Homepage HTML captures
<domain>_live_dns.txt              # Current DNS resolution
sni_cert_matrix.txt                # SNI probe results
ip_host_header_probe.txt           # Forced host routing results
live_probe_timeline.txt            # Timestamped probe sequence
```

### 5. **Confidence Audit Trail** (inline in reports)
```markdown
## Finding: app.example.com runs Vue 2
- **Confidence**: Tier A
- **Evidence**: 
  - grep result: `raw/app.example.com.html:123` (bundle mentions "vue" + "webpackJsonp")
  - Validation: curled homepage on 2026-05-13 07:15 UTC
- **Alternative hypotheses tested**: Angular (ruled out - no ng-app), React (ruled out - no #root)
```

---

## 🚀 Workflow: From Request to Deliverable

1. **Intake**: Receive target company/domain
2. **Phase 1a**: DNS enumeration → `all_domains_discovered.txt`
3. **Phase 1b**: Reverse-IP aggregation → `reverseip_all_domains.txt`
4. **Phase 1c**: Port scanning → `nmap_*.nmap` files
5. **Phase 1d**: Stack fingerprinting → `<domain>_stack_analysis.md` + raw HTML/chunks
6. **Phase 2a**: Consolidate DNS relationships → `domain_ip_map.tsv`
7. **Phase 2b**: Live SNI/TLS probing → `sni_cert_matrix.txt`
8. **Phase 2c**: Forced host routing → `ip_host_header_probe.txt`
9. **Phase 2d**: Private network detection → Note RFC 1918 ranges
10. **Phase 2e**: Create relationship diagram → `infrastructure_relationships.md`
11. **Deliverable**: Package all reports + evidence files with confidence tiers

---

## 💡 Key Insights from Field Work

- **Dynamic chunks are business logic**: Webpack/Vite code splitting often hides APIs in lazy-loaded chunks. Always extract and analyze chunk files, not just the main bundle.
  
- **SNI + virtual hosting = certificate multiplexing**: Modern infrastructure (Istio, tengine with SNI) routes different domains to different backends using the same IP. Use SNI probes to detect this.

- **Confidence matters more than volume**: 10 Tier A findings beat 1000 Tier C hints. False positives from historical reverse-IP data cost investigation time.

- **Timestamps enable timeline forensics**: Record when each probe ran. Compare cert issue/renewal dates to infrastructure migrations. Timeline + confidence tier = audit trail.

- **Live probe order matters**: DNS first (reveal IPs), then TLS/SNI (reveal certs), then forced host routing (reveal backend separation). Sequential probing clarifies ambiguous signals.

---

## 📚 Further Reading & References

- **OWASP Top 10 for APIs**: For backend API patterns
- **Kubernetes / Istio docs**: For edge gateway fingerprinting
- **Certificate Transparency (CT) logs**: crt.sh, censys.io
- **Reverse IP services**: hackertarget.com, shodan.io, ipqualityscore.com
- **IANA Private Ranges**: RFC 1918, RFC 6890

---

## 🎓 Example: Running the Full Methodology

```bash
# Directory setup
mkdir -p dns ports raw report http tls scripts

# Phase 1: Discovery
# (Follow Steps 1.1 – 1.5 above, collecting results into dns/, ports/, raw/, report/)

# Phase 2: Relationship Mapping
# (Follow Steps 2.1 – 2.6 above, consolidating into report/)

# Output: Comprehensive infrastructure map with confidence tiers and evidence trails
# Ready for: strategic planning, security assessment, due diligence, etc.
```

