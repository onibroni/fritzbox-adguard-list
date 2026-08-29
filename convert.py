import ipaddress
import re
import urllib.request

SOURCES = [
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_2.txt",
]

OUTPUT = "fritzbox.txt"

DOMAIN_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$",
    re.IGNORECASE
)


def normalize_domain(domain):
    domain = domain.strip().lower().rstrip(".")

    if domain.startswith("*."):
        domain = domain[2:]

    if not domain or "." not in domain:
        return None

    try:
        ipaddress.ip_address(domain)
        return None
    except ValueError:
        pass

    if not DOMAIN_RE.fullmatch(domain):
        return None

    return domain


def parse_line(line):
    line = line.strip()

    # Leerzeilen und Kommentare ignorieren
    if not line or line.startswith(("!", "#", "[")):
        return None

    # AdGuard-Ausnahmen nicht blockieren
    if line.startswith("@@"):
        return None

    # AdGuard / Adblock:
    # ||example.com^
    if line.startswith("||"):
        domain = line[2:]
        domain = domain.split("^", 1)[0]
        domain = domain.split("$", 1)[0]
        domain = domain.split("/", 1)[0]

        return normalize_domain(domain)

    # HOSTS-Format:
    # 0.0.0.0 example.com
    # 127.0.0.1 example.com
    parts = line.split()

    if len(parts) >= 2:
        try:
            ipaddress.ip_address(parts[0])
            return normalize_domain(parts[1])
        except ValueError:
            pass

    # Bereits reine Domain
    if len(parts) == 1:
        return normalize_domain(parts[0])

    return None


domains = set()

for url in SOURCES:
    print(f"Lade: {url}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "fritzbox-adguard-list/1.0"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8", errors="ignore")

    for line in text.splitlines():
        domain = parse_line(line)

        if domain:
            domains.add(domain)


with open(OUTPUT, "w", encoding="utf-8", newline="\n") as file:
    for domain in sorted(domains):
        file.write(domain + "\n")


print(f"Fertig: {len(domains)} Domains in {OUTPUT}")
