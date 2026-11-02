"""Vérifie sur les formes retenues les règles énoncées dans les fiches."""
import json, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
F = json.loads((RACINE / "donnees/formes.json").read_text(encoding="utf8"))
fam = json.loads((RACINE / "donnees/familles.json").read_text(encoding="utf8"))
FAM = {f["id"]: f for f in fam}
SIMPLES = ["ind-present", "ind-imparfait", "ind-ps", "ind-futur", "cond-present", "sub-present", "sub-imparfait", "imp-present"]
ENTIERS = {"être", "avoir", "aller"}
erreurs, regles = [], 0

def regle(nom, ok, detail=""):
    global regles
    regles += 1
    if not ok:
        erreurs.append(f"{nom} : {detail}")

def formes(v, t):
    return [c[0].replace("|", "") if c else None for c in F[v]["formes"].get(t, [])]

def cases(v):
    for t in SIMPLES + ["part-present", "part-passe", "inf-present"]:
        for i, c in enumerate(F[v]["formes"].get(t, [])):
            for g in c or []:
                yield t, i, g.replace("|", "")

def muet(t, i):
    """Cases où le radical est suivi d'une syllabe à e muet."""
    return (t in ("ind-present", "sub-present") and i in (0, 1, 2, 5)) or (t == "imp-present" and i == 0) or t in ("ind-futur", "cond-present")

for v in FAM["g1-cer"]["verbes"]:
    for t, i, f in cases(v):
        rad = v[:-3]
        suite = f[len(rad) + 1:len(rad) + 2]
        regle("cédille devant a, o", ("ç" in f) == (suite in ("a", "o", "â")), f"{v} {t} {f}")
for v in FAM["g1-ger"]["verbes"]:
    for t, i, f in cases(v):
        rad = v[:-3]
        suite = f[len(rad) + 1:len(rad) + 2]
        regle("e après g devant a, o", (f.startswith(rad + "ge") and f[len(rad) + 2:len(rad) + 3] in ("a", "o", "â")) or suite in ("e", "i", "é", "è"), f"{v} {t} {f}")
for v in FAM["g1-double"]["verbes"]:
    c = v[-3]
    for t, i, f in cases(v):
        regle("consonne double devant e muet", (c + c in f) == muet(t, i), f"{v} {t} {f}")
for v in FAM["g1-e"]["verbes"]:
    for t, i, f in cases(v):
        regle("è devant e muet", ("è" in (f.removesuffix("èrent") if t == "ind-ps" else f)) == muet(t, i), f"{v} {t} {f}")
for v in FAM["g1-eaigu"]["verbes"]:
    for t, i, c in ((t, i, c) for t in SIMPLES for i, c in enumerate(F[v]["formes"].get(t, [])) if c):
        f = c[0].replace("|", "")
        ouvert = t in ("ind-present", "sub-present") and i in (0, 1, 2, 5) or t == "imp-present" and i == 0
        regle("è devant terminaison muette", ("è" in (f.removesuffix("èrent") if t == "ind-ps" else f)) == ouvert, f"{v} {t} {f}")
for v in FAM["g1-oyer"]["verbes"] + ["envoyer"]:
    for t, i, f in cases(v):
        if v == "envoyer" and t in ("ind-futur", "cond-present"):
            continue
        rad = v[:-3]
        regle("y devient i devant e muet", (f.startswith(rad + "i")) == muet(t, i), f"{v} {t} {f}")
for g in fam:
    for v in g["verbes"]:
        pp = F[v]["formes"]["part-present"][0]
        if pp is None:
            continue
        p = pp[0].replace("|", "")
        regle("participe en -issant au 2e groupe seulement", p.endswith(("issant", "ïssant")) == (g["groupe"] == "g2") or v in ("connaître", "reconnaître", "paraître", "disparaître", "naître"), f"{v} {p}")
        if g["groupe"] == "g1":
            regle("infinitif en -er", v.endswith("er"), v)
            regle("impératif sans s", not formes(v, "imp-present")[0].endswith("s"), v)
            regle("participe passé en -é", formes(v, "part-passe")[0].endswith("é"), v)

# Le conditionnel présent se forme sur le futur, à toutes les personnes.
for v in F:
    fu, co = formes(v, "ind-futur"), formes(v, "cond-present")
    for i, (a, b) in enumerate(zip(fu, co)):
        if a:
            fin = ("rai", "ras", "ra", "rons", "rez", "ront")[i]
            regle("même base au futur et au conditionnel", a.endswith(fin) and b.startswith(a[: -len(fin)] + "r"), f"{v} {a} {b}")
    im = formes(v, "ind-imparfait")
    if v not in ENTIERS and im[3] and v not in FAM["g1-cer"]["verbes"] + FAM["g1-ger"]["verbes"]:
        regle("imparfait sur le radical de nous", formes(v, "ind-present")[3][:-3] == im[3][:-4], f"{v} {im[3]}")
    # Passé simple : l'accent de nous et vous, jamais au singulier sauf le tréma de haïr.
    ps = formes(v, "ind-ps")
    if ps[3]:
        regle("accent à nous et vous au passé simple", any(x in ps[3] for x in "âîûï") and any(x in ps[4] for x in "âîûï"), f"{v} {ps}")
    si = formes(v, "sub-imparfait")
    if si[2] and v != "haïr" and ps[2]:
        regle("circonflexe au subjonctif imparfait", any(x in si[2] for x in "âîû"), f"{v} {si[2]}")

print(regles, "contrôles,", len(erreurs), "erreurs")
for e in erreurs[:40]:
    print(" ", e)
sys.exit(1 if erreurs else 0)
