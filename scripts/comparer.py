"""Lit les pages enregistrées des trois sites et compare chaque forme de chaque verbe.

Usage : comparer.py pages sortie.json
Écrit les formes lues par site, puis un rapport des désaccords.
"""
import html, json, re, sys, unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
pages, sortie = Path(sys.argv[1]), Path(sys.argv[2])

TEMPS = {
    "indicatif:présent": "ind-present", "indicatif:passé composé": "ind-pc", "indicatif:imparfait": "ind-imparfait",
    "indicatif:plus-que-parfait": "ind-pqp", "indicatif:passé simple": "ind-ps", "indicatif:passé antérieur": "ind-pa",
    "indicatif:futur simple": "ind-futur", "indicatif:futur": "ind-futur", "indicatif:futur antérieur": "ind-fa",
    "subjonctif:présent": "sub-present", "subjonctif:passé": "sub-passe", "subjonctif:imparfait": "sub-imparfait",
    "subjonctif:plus-que-parfait": "sub-pqp",
    "conditionnel:présent": "cond-present", "conditionnel:passé": "cond-passe",
    "conditionnel:passé première forme": "cond-passe", "conditionnel:passé 1ère forme": "cond-passe",
    "impératif:présent": "imp-present", "impératif:passé": "imp-passe", "imperatif:présent": "imp-present", "imperatif:passé": "imp-passe",
    "participe:présent": "part-present", "participe:passé": "part-passe",
    "infinitif:présent": "inf-present", "infinitif:passé": "inf-passe",
}
PRONOM = re.compile(r"^(que |qu')?(j'|je |tu |il |elle |on |nous |vous |ils |elles |qu'il |qu'elle )")

def ascii_(v):
    return "".join(c for c in unicodedata.normalize("NFD", v) if not unicodedata.combining(c))

def texte(b):
    b = re.sub(r"<(sup|style|script)\b.*?</\1>", "", b, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", b)).replace("\xa0", " ").replace("’", "'")).strip()

def nettoie(f):
    f = f.lower().strip()
    f = re.sub(r"^(qu'|que )?(il/elle/on|ils/elles) ", "", f)
    f = re.sub(r"^\((tu|nous|vous)\) ", "", f)
    f = re.sub(r"\((e|s|e?s)\)|·e?s?|\[.*?\]", "", f).strip(" .,;")
    f = f.split("/")[0].strip()
    for _ in range(2):
        f = PRONOM.sub("", f)
    return f

def variantes(f):
    return sorted({nettoie(x) for x in re.split(r"\s+ou\s+|\s*,\s*", f) if nettoie(x) and nettoie(x) != "—"})

def conjugueur(t):
    MODES = {"ind": "indicatif", "sub": "subjonctif", "cnd": "conditionnel", "imp": "impératif", "par": "participe", "inf": "infinitif"}
    t = t[t.find("<body"):]
    pos = [(m.start(), m.group(1)) for m in re.finditer(r'<h2 class="modeBloc" id="(\w+)"', t)]
    fin = t.find('<h2 class="modeBloc">R')
    r = {}
    for i, (p, code) in enumerate(pos):
        if code not in MODES:
            continue
        q = pos[i + 1][0] if i + 1 < len(pos) else fin
        q = min(x for x in (q, fin) if x > p)
        for b in re.split(r'<div class="conjugBloc">', t[p:q])[1:]:
            b = re.sub(r"<br\s*/?>", "\n", b)
            b = re.sub(r"</(div|p|h\d)>", "\n", b)
            ls = [texte(l) for l in b.split("\n")]
            ls = [l for l in ls if l]
            if len(ls) >= 2:
                c = TEMPS.get(f"{MODES[code]}:{ls[0].lower()}")
                if c:
                    r[c] = [variantes(l) for l in ls[1:]]
    return r

def wiktionnaire(t):
    t = t[t.find("mw-content-text"):]
    fin = t.find('id="Modes_impersonnels_2"')
    if fin > 0:
        t = t[:fin]
    r = {}
    ids = ["Modes_impersonnels", "Indicatif", "Subjonctif", "Conditionnel", "Impératif"]
    for k, sec in enumerate(ids):
        i = t.find(f'id="{sec}"')
        if i < 0:
            continue
        j = t.find(f'id="{ids[k + 1]}"', i) if k + 1 < len(ids) else len(t)
        s = t[i:j]
        lignes = [[texte(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)] for tr in re.findall(r"<tr.*?</tr>", s, re.S)]
        if sec == "Modes_impersonnels":
            for l in lignes:
                if l and l[0] == "Infinitif":
                    r["inf-present"], r["inf-passe"] = [variantes(l[2])], [variantes(f"{l[4]} {l[5]}")]
                if l and l[0] == "Participe":
                    r["part-present"], r["part-passe"] = [variantes(l[2])], [variantes(l[5])]
            continue
        mode = sec.lower()
        courant = None
        for l in lignes:
            if len(l) == 1:
                courant = TEMPS.get(f"{mode}:{l[0].lower()}")
                if courant:
                    r[courant] = []
            elif courant and len(l) >= 2:
                sujet, forme = l[0], l[1]
                simple = courant in ("ind-present", "ind-imparfait", "ind-ps", "ind-futur", "sub-present", "sub-imparfait", "cond-present", "imp-present")
                r[courant].append(variantes(forme if simple else f"{sujet} {forme}"))
    return r

def participes(r):
    """Sépare le masculin singulier, commun aux trois sites, des autres formes."""
    if "part-passe" in r:
        l = [x for v in r["part-passe"] for x in v if not x.startswith(("ayant ", "étant "))]
        r["part-passe"], r["part-passe-formes"] = [l[:1]], [sorted(set(l))]
    return r

def lemonde(t):
    r = {}
    i = t.find("vtfc-verbs-conjugation")
    t = t[i:]
    blocs = re.split(r'<div class="vtfc-verbs-mode">', t)[1:]
    for b in blocs:
        mode = texte(b[:b.find("</div>")]).lower()
        for k in re.split(r'<span class="vtfc-verbs-tense">', b)[1:]:
            nom = texte(k[:k.find("</span>")]).lower()
            c = TEMPS.get(f"{mode}:{nom}")
            if c:
                r[c] = [variantes(texte(li)) for li in re.findall(r"<li>(.*?)</li>", k, re.S)]
            else:
                inconnus.add(f"{mode}:{nom}")
    return r

inconnus = set()
LECTEURS = {"conjugueur": conjugueur, "wiktionnaire": wiktionnaire, "lemonde": lemonde}
familles = json.loads((RACINE / "donnees/familles.json").read_text(encoding="utf8"))
tout, manquants, ecarts = {}, [], []
CLES = sorted(set(TEMPS.values())) + ["part-passe-formes"]
RARES = {"part-passe-formes": ("wiktionnaire",), "inf-present": ("lemonde",), "inf-passe": ("lemonde",), "imp-passe": ("lemonde",)}
for fam in familles:
    for verbe in fam["verbes"]:
        lu = {}
        for site, lecteur in LECTEURS.items():
            p = pages / site / f"{ascii_(verbe)}.html"
            lu[site] = participes(lecteur(p.read_text(encoding="utf8", errors="ignore"))) if p.exists() else {}
        tout[verbe] = lu
        for c in CLES:
            tailles = {s: len(lu[s].get(c, [])) for s in lu}
            for s, n in tailles.items():
                if not n and s not in RARES.get(c, ()):
                    manquants.append((verbe, s, c))
            for i in range(max(tailles.values())):
                vals = {s: tuple(lu[s][c][i]) for s in lu if i < len(lu[s].get(c, [])) and s not in RARES.get(c, ())}
                if len(set(vals.values())) > 1:
                    ecarts.append({"verbe": verbe, "temps": c, "rang": i, "valeurs": vals})

sortie.write_text(json.dumps({"formes": tout, "ecarts": ecarts}, ensure_ascii=False), encoding="utf8")
print(len(tout), "verbes,", len(ecarts), "écarts,", len(manquants), "tableaux manquants")
print("intitulés inconnus :", sorted(inconnus))
parsite = {}
for v, s, c in manquants:
    parsite.setdefault(s, []).append(f"{v}:{c}")
for s, l in parsite.items():
    print(s, len(l), l[:12])
