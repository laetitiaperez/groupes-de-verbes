"""Assemble la page et contrôle les fiches : parents, liens, sources, formes citées."""
import json
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
fiches = (RACINE / "donnees/fiches.js").read_text(encoding="utf8")
formes = json.loads((RACINE / "donnees/formes.json").read_text(encoding="utf8"))
familles = json.loads((RACINE / "donnees/familles.json").read_text(encoding="utf8"))
decisions = json.loads((RACINE / "donnees/decisions.json").read_text(encoding="utf8"))
page = (RACINE / "src/page.html").read_text(encoding="utf8")
app = (RACINE / "src/app.js").read_text(encoding="utf8")

CONTROLE = r"""
const assert = (c, m) => { if (!c) { console.error(m); process.exitCode = 1; } };
const ids = new Set(FICHES.map(f => f.id));
assert(ids.size === FICHES.length, "identifiant en double");
const verbes = Object.keys(FORMES);
const lues = new Set(verbes);
for (const e of Object.values(FORMES)) for (const l of Object.values(e.formes)) for (const c of l) for (const g of c || []) lues.add(g.replace("|", ""));
const cite = (o, t) => { for (const m of t.matchAll(/<i>(.*?)<\/i>/g)) {
  const x = m[1].toLowerCase();
  assert(lues.has(x) || HORS_TABLEAUX.map(h => h.toLowerCase()).includes(x), `forme citée inconnue : ${o} -> ${m[1]}`);
} };
for (const f of FICHES) {
  if (f.p) assert(ids.has(f.p), `parent inconnu : ${f.id} -> ${f.p}`);
  for (const l of f.l || []) assert(ids.has(l), `lien inconnu : ${f.id} -> ${l}`);
  assert(f.s && f.s.length, `sans source : ${f.id}`);
  for (const [k] of f.s || []) assert(SOURCES[k], `source inconnue : ${f.id} -> ${k}`);
  for (const t of [f.d, f.n || "", ...(f.f || [])]) cite(f.id, t);
}
for (const fam of FAMILLES) { assert(ids.has(fam.id), `famille sans fiche : ${fam.id}`); }
for (const [b] of BRANCHES) assert(ids.has(b), `branche inconnue : ${b}`);
for (const [v, t] of Object.entries(NOTES)) { assert(FORMES[v], `note sans verbe : ${v}`); cite(v, t); }
console.log(`${FICHES.length} fiches, ${verbes.length} verbes, ${FAMILLES.length} familles, ${lues.size} formes différentes`);
"""
J = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))
donnees = f"{fiches}\nconst FAMILLES = {J(familles)};\nconst FORMES = {J(formes)};\nconst DECISIONS = {J(decisions)};\n"
essai = subprocess.run(["node", "-e", donnees + CONTROLE], capture_output=True, text=True)
print(essai.stdout.strip(), essai.stderr.strip())
if essai.returncode:
    sys.exit(1)

sortie = page.replace("/*DONNEES*/", donnees).replace("/*APP*/", app)
(RACINE / "carte-groupes.html").write_text(sortie, encoding="utf8")
titre = re.search(r"<title>.*?</title>", sortie).group(0)
site = f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">{sortie}'
(RACINE / "index.html").write_text(site, encoding="utf8")
print(titre, f"{len(sortie.encode()) // 1024} Ko")
