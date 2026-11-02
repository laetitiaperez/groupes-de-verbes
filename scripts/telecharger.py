"""Enregistre les pages de conjugaison de chaque verbe sur trois sites, pour les comparer.

Les pages restent hors du dépôt : elles servent seulement au contrôle.
Usage : telecharger.py dossier
"""
import json, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sortie = Path(sys.argv[1])
GROUPE = {"g1": "premier-groupe", "g2": "deuxieme-groupe", "g3": "troisieme-groupe"}

def ascii_(v):
    return "".join(c for c in unicodedata.normalize("NFD", v) if not unicodedata.combining(c))

def adresses(verbe, groupe):
    q = urllib.parse.quote(verbe)
    return {
        "conjugueur": [f"https://leconjugueur.lefigaro.fr/conjugaison/verbe/{ascii_(verbe)}.html"],
        "wiktionnaire": [f"https://fr.wiktionary.org/wiki/Conjugaison:fran%C3%A7ais/{q}"],
        "lemonde": [f"https://conjugaison.lemonde.fr/conjugaison/{GROUPE[groupe]}/{ascii_(verbe)}/"],
    }

def lire(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

familles = json.loads((RACINE / "donnees/familles.json").read_text(encoding="utf8"))
for famille in familles:
    for verbe in famille["verbes"]:
        for site, urls in adresses(verbe, famille["groupe"]).items():
            cible = sortie / site / f"{ascii_(verbe)}.html"
            if cible.exists():
                continue
            cible.parent.mkdir(parents=True, exist_ok=True)
            for url in urls:
                try:
                    cible.write_bytes(lire(url))
                    break
                except Exception as e:
                    print("ÉCHEC", site, verbe, url, e, flush=True)
            time.sleep(1)
    print(famille["id"], "fait", flush=True)
print("terminé", flush=True)
