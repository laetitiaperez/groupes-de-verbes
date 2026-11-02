"""Retient les formes confirmées par les trois sites, découpe les temps simples et contrôle les familles.

Usage : construire_formes.py normal.json
Une forme n'entre dans donnees/formes.json que si les sites concordent ou si un écart
figure dans DECISIONS. Tout autre écart arrête le script.
"""
import json, re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
lu = json.loads(Path(sys.argv[1]).read_text(encoding="utf8"))["formes"]
familles = json.loads((RACINE / "donnees/familles.json").read_text(encoding="utf8"))
FAMILLE = {v: f for f in familles for v in f["verbes"]}

SIMPLES = ["ind-present", "ind-imparfait", "ind-ps", "ind-futur", "cond-present", "sub-present", "sub-imparfait", "imp-present"]
COMPOSES = ["ind-pc", "ind-pqp", "ind-pa", "ind-fa", "cond-passe", "sub-passe", "sub-pqp", "imp-passe"]
NON_PERSONNELS = ["inf-present", "inf-passe", "part-present", "part-passe"]
TOUS = SIMPLES + COMPOSES + NON_PERSONNELS
IMPERSONNELS = {"falloir", "pleuvoir"}
ENTIERS = {"être", "avoir", "aller"}  # Plus de trois radicaux : on ne découpe pas.

# Écarts tranchés. Chaque règle dit quel site suivre, ou quelles formes admettre.
SUIVRE = {
    "sortir": ("lemonde", "Être en emploi intransitif (il est sorti). Le Conjugueur montre l'emploi transitif, avec avoir (il a sorti le chien)."),
    "asseoir": ("lemonde", "Deux conjugaisons admises. Série en -ied- et -ey- d'après Le Monde et le Wiktionnaire, série en -oi- d'après Le Conjugueur."),
    "essayer": ("lemonde", "Deux graphies admises : essaie ou essaye. Série en -ai- d'après Le Conjugueur et Le Monde, série en -ay- d'après le Wiktionnaire."),
    "balayer": ("lemonde", "Deux graphies admises : balaie ou balaye. Série en -ai- d'après Le Conjugueur et Le Monde, série en -ay- d'après le Wiktionnaire."),
    "céder": ("lemonde", "Futur et conditionnel : céderai, ou cèderai depuis les rectifications de 1990."),
    "espérer": ("lemonde", "Futur et conditionnel : espérerai, ou espèrerai depuis les rectifications de 1990."),
    "préférer": ("lemonde", "Futur et conditionnel : préférerai, ou préfèrerai depuis les rectifications de 1990."),
    "répéter": ("lemonde", "Futur et conditionnel : répéterai, ou répèterai depuis les rectifications de 1990."),
    "plaire": ("lemonde", "Il plaît, ou il plait depuis les rectifications de 1990."),
    "vouloir": ("lemonde", "Impératif : veuille ou veux, veuillons ou voulons, veuillez ou voulez (Académie française). Subjonctif : voulions, vouliez."),
    "pouvoir": ("lemonde", "Pas d'impératif, d'après Le Conjugueur et Le Monde. Le Wiktionnaire donne un impératif passé, non retenu."),
    "falloir": ("lemonde", "Verbe impersonnel : troisième personne du singulier seulement."),
    "pleuvoir": ("lemonde", "Verbe impersonnel au sens propre : troisième personne du singulier seulement. Le Wiktionnaire ajoute des formes personnelles figurées, non retenues."),
}

def serie_ay(forme, verbe):
    """essaie -> essaye, pour les verbes en -ayer. Ne touche que le radical."""
    pre = verbe[:-4]
    return pre + "ay" + forme[len(pre) + 2:] if forme.startswith(pre + "ai") else forme

def variantes(verbe, temps, i, forme):
    if forme is None:
        return None
    r = [forme]
    if FAMILLE[verbe]["id"] == "g1-ayer" and serie_ay(forme, verbe) != forme:
        r.append(serie_ay(forme, verbe))
    if FAMILLE[verbe]["id"] == "g1-eaigu" and temps in ("ind-futur", "cond-present"):
        r.append(wikt_rect(verbe, temps, i))
    if verbe == "plaire" and temps == "ind-present" and i == 2:
        r.append("plait")
    if verbe == "asseoir" and temps in lu["asseoir"]["conjugueur"]:
        autre = lu["asseoir"]["conjugueur"][temps][i][0]
        if autre != forme and temps in SIMPLES + ["part-present"]:
            r.append(autre)
    if verbe == "vouloir" and temps == "imp-present":
        r.append(["veux", "voulons", "voulez"][i])
    return r

def wikt_rect(verbe, temps, i):
    return [x for x in lu[verbe]["wiktionnaire"][temps][i] if x not in lu[verbe]["lemonde"][temps][i]][0]

def retenir(verbe, temps):
    sites = lu[verbe]
    if verbe in SUIVRE:
        site = SUIVRE[verbe][0]
        l = sites[site].get(temps)
        if not l:
            l = sites["wiktionnaire"].get(temps)[:3] if temps == "imp-passe" else sites["wiktionnaire"].get(temps) if temps in ("inf-present", "inf-passe") else None
        if not l and verbe not in ("pouvoir",):
            l = sites["conjugueur"].get(temps)
        if not l:
            return None
    else:
        l = sites["conjugueur"][temps]
        for s in sites:
            autre = sites[s].get(temps)
            if autre and autre[: len(l)] != l:  # Le Wiktionnaire ajoute parfois des lignes après l'impératif.
                raise SystemExit(f"Écart non tranché : {verbe} {temps} {s}\n{autre}\n{l}")
    out = []
    for i, cell in enumerate(l):
        f = cell[0] if cell and cell[0] != "-" else None
        if verbe in IMPERSONNELS and temps not in NON_PERSONNELS and len(l) >= 3:
            f = f if i == 2 else None
        if (verbe == "pouvoir" or verbe in IMPERSONNELS) and temps.startswith("imp"):
            f = None
        out.append(f)
    return out

# Désinences admises pour le découpage, par personne.
PRESENT = [["e", "x", "s"], ["es", "x", "s"], ["e", "t", ""], ["ons"], ["ez", "es"], ["ent", "ont"]]
IMPARFAIT = ["ais", "ais", "ait", "ions", "iez", "aient"]
SERIES_PS = {
    "a": ["ai", "as", "a", "âmes", "âtes", "èrent"], "i": ["is", "is", "it", "îmes", "îtes", "irent"],
    "ï": ["ïs", "ïs", "ït", "ïmes", "ïtes", "ïrent"], "u": ["us", "us", "ut", "ûmes", "ûtes", "urent"],
    "in": ["ins", "ins", "int", "înmes", "întes", "inrent"],
}
SERIES_SI = {
    "a": ["asse", "asses", "ât", "assions", "assiez", "assent"], "i": ["isse", "isses", "ît", "issions", "issiez", "issent"],
    "ï": ["ïsse", "ïsses", "ït", "ïssions", "ïssiez", "ïssent"], "u": ["usse", "usses", "ût", "ussions", "ussiez", "ussent"],
    "in": ["insse", "insses", "înt", "inssions", "inssiez", "inssent"],
}
FUTUR = ["ai", "as", "a", "ons", "ez", "ont"]
COND = ["ais", "ais", "ait", "ions", "iez", "aient"]
SUBJ = ["e", "es", "e", "ions", "iez", "ent"]

def serie(ps3):
    for k, fin in (("in", "int"), ("ï", "ït"), ("a", "a"), ("i", "it"), ("u", "ut")):
        if ps3.endswith(fin):
            return k
    raise SystemExit(f"Passé simple inconnu : {ps3}")

def voyelle_futur(verbe, forme):
    """-e- au 1er groupe et pour cueillir, -i- pour les verbes en -ir réguliers, rien sinon."""
    fam = FAMILLE[verbe]
    if (fam["groupe"] == "g1" and fam["id"] != "g1-envoyer") or fam["id"] == "g3-cueillir":
        return "er"
    if verbe.endswith("ïr"):
        return "ïr"
    if verbe.endswith("ir") and not verbe.endswith("oir") and forme.endswith(("irai", "iras", "ira", "irons", "irez", "iront", "irais", "irait", "irions", "iriez", "iraient")):
        return "ir"
    return "r"

def couper(forme, fins):
    for fin in sorted(fins, key=len, reverse=True):
        if forme.endswith(fin):
            return forme[: len(forme) - len(fin)], fin
    raise SystemExit(f"Désinence introuvable : {forme} {fins}")

def decouper(verbe, temps, i, forme, tout):
    fam = FAMILLE[verbe]
    if temps == "ind-present" or temps == "imp-present":
        rang = i if temps == "ind-present" else [0, 3, 4][i]
        if fam["groupe"] == "g2" and rang < 3 and verbe != "haïr":
            return couper(forme, [["is", "is", "it"][rang]])
        if rang == 2:
            p1 = tout["ind-present"][0]
            if p1 and p1[0] == forme + "s":
                return forme, ""
        return couper(forme, PRESENT[rang])
    if temps == "ind-imparfait":
        return couper(forme, [IMPARFAIT[i]])
    if temps == "ind-ps":
        return couper(forme, [SERIES_PS[serie(tout["ind-ps"][2][0])][i]])
    if temps == "sub-imparfait":
        return couper(forme, [SERIES_SI[serie(tout["ind-ps"][2][0])][i]])
    if temps == "ind-futur":
        return couper(forme, [voyelle_futur(verbe, forme) + FUTUR[i]])
    if temps == "cond-present":
        return couper(forme, [voyelle_futur(verbe, forme) + COND[i]])
    if temps == "sub-present":
        return couper(forme, [SUBJ[i]])
    if temps == "part-present":
        return couper(forme, ["ant"])
    if temps == "part-passe":
        return couper(forme, ["é", "ï", "i", "u", "û", "s", "t"])
    if temps == "inf-present":
        return couper(forme, ["er", "ïr", "ir", "oir", "re"])
    raise SystemExit(temps)

def cellule(verbe, temps, i, forme, tout):
    """Une cellule : liste de graphies, découpées par | dans les temps simples."""
    vs = variantes(verbe, temps, i, forme)
    if vs is None:
        return None
    if verbe in ENTIERS or temps in COMPOSES or temps == "inf-passe":
        return vs
    r = []
    for v in vs:
        rad, des = decouper(verbe, temps, i, v, tout)
        r.append(f"{rad}|{des}")
    return r

sortie, patrons = {}, {}
for verbe in lu:
    tout = {t: retenir(verbe, t) for t in TOUS}
    tout = {t: (l if l else None) for t, l in tout.items()}
    tout = {t: [[x] if x else None for x in l] if l else None for t, l in tout.items()}
    formes = {}
    for t, l in tout.items():
        if l is None:
            continue
        formes[t] = [cellule(verbe, t, i, c[0] if c else None, tout) for i, c in enumerate(l)]
    aux = "être" if formes["ind-pc"][2][0].split()[0] == "est" else "avoir"
    sortie[verbe] = {"aux": aux, "formes": formes}

# Contrôle des familles : mêmes désinences, et mêmes cases pour chaque radical.
def patron(v):
    p, radicaux = {}, {}
    for t in SIMPLES + ["part-present", "part-passe", "inf-present"]:
        for i, c in enumerate(sortie[v]["formes"].get(t, [])):
            if c:
                rad, des = c[0].split("|")
                k = radicaux.setdefault(rad, len(radicaux))
                p[f"{t}:{i}"] = (k, des)
    return p, len(radicaux)

problemes = []
for fam in familles:
    if fam["id"].endswith("isoles") or fam["id"] in ("g3-aller", "g3-aux", "g3-impersonnels"):
        continue
    modele = fam["verbes"][0]
    pm, _ = patron(modele)
    for v in fam["verbes"][1:]:
        pv, _ = patron(v)
        d = [k for k in sorted(set(pm) | set(pv)) if pm.get(k, (None, None))[1] != pv.get(k, (None, None))[1]]
        # Même partition des cases entre radicaux.
        cases = sorted(set(pm) & set(pv))
        lien = {}
        partition = all(lien.setdefault(pm[k][0], pv[k][0]) == pv[k][0] for k in cases)
        inverse = len(set(lien.values())) == len(lien)
        if d or not partition or not inverse:
            problemes.append((fam["id"], v, d[:6], partition and inverse))

# Chaque temps composé doit redonner auxiliaire + participe passé, accordé avec être.
BASE = {"ind-pc": "ind-present", "ind-pqp": "ind-imparfait", "ind-pa": "ind-ps", "ind-fa": "ind-futur",
        "cond-passe": "cond-present", "sub-passe": "sub-present", "sub-pqp": "sub-imparfait", "imp-passe": "imp-present"}
composes = 0
for v, e in sortie.items():
    pp = e["formes"]["part-passe"][0][0].replace("|", "")
    for t, b in BASE.items():
        for i, c in enumerate(e["formes"].get(t, [])):
            if not c:
                continue
            base = sortie[e["aux"]]["formes"][b][i][0]
            pluriel = e["aux"] == "être" and (i >= 3 or t == "imp-passe" and i > 0) and not pp.endswith("s")
            attendu = f"{base} {pp}{'s' if pluriel else ''}"
            composes += 1
            if c[0] != attendu:
                raise SystemExit(f"Temps composé incohérent : {v} {t} {i} {c} {attendu}")
print(composes, "temps composés recalculés")

# Les séries en -ay- calculées doivent redonner les formes lues sur le Wiktionnaire.
for v in ("essayer", "balayer"):
    for t, l in sortie[v]["formes"].items():
        for i, c in enumerate(l):
            w = lu[v]["wiktionnaire"].get(t, [])
            if c and i < len(w) and t in SIMPLES and c[-1].replace("|", "") != w[i][0]:
                raise SystemExit(f"Série -ay- fausse : {v} {t} {i} {c} {w[i]}")

(RACINE / "donnees/formes.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")), encoding="utf8")
(RACINE / "donnees/decisions.json").write_text(json.dumps({v: r for v, (_, r) in SUIVRE.items()}, ensure_ascii=False, indent=1), encoding="utf8")
n = sum(1 for v in sortie.values() for l in v["formes"].values() for c in l if c)
print(len(sortie), "verbes,", n, "cases retenues,", len(problemes), "écarts de famille")
for p in problemes:
    print(p)
