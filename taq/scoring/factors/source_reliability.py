RELIABILITY = {
    "virustotal": 0.95, "shodan": 0.9, "censys": 0.9, "abuseipdb": 0.85,
    "bgpview": 0.85, "securitytrails": 0.8, "crt.sh": 0.85,
    "haveibeenpwned": 0.9, "dehashed": 0.7, "github": 0.7,
    "linkedin": 0.6, "twitter": 0.5, "reddit": 0.4, "instagram": 0.4,
    "mitre_attck": 0.95, "otx": 0.8, "malwarebazaar": 0.85, "urlhaus": 0.8,
    "whois": 0.75, "dns": 0.8, "web_scrape": 0.5, "paste_monitor": 0.6,
    "darkweb": 0.5, "unknown": 0.4,
}

def score_source(source_name: str | None) -> float:
    if not source_name:
        return RELIABILITY["unknown"]
    key = source_name.lower().strip().replace(" ", "_")
    if key in RELIABILITY:
        return RELIABILITY[key]
    for k, v in RELIABILITY.items():
        if k in key or key in k:
            return v
    return RELIABILITY["unknown"]
