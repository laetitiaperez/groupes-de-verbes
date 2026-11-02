const VERBE = "v:";
const TEMPS = {
  "ind-present": "Présent", "ind-imparfait": "Imparfait", "ind-ps": "Passé simple", "ind-futur": "Futur simple", "cond-present": "Conditionnel présent",
  "ind-pc": "Passé composé", "ind-pqp": "Plus-que-parfait", "ind-pa": "Passé antérieur", "ind-fa": "Futur antérieur", "cond-passe": "Conditionnel passé",
  "sub-present": "Subjonctif présent", "sub-imparfait": "Subjonctif imparfait", "sub-passe": "Subjonctif passé", "sub-pqp": "Subjonctif plus-que-parfait",
  "imp-present": "Impératif présent", "imp-passe": "Impératif passé",
  "inf-present": "Infinitif présent", "inf-passe": "Infinitif passé", "part-present": "Participe présent", "part-passe": "Participe passé"
};
const MODES = [
  ["Indicatif, temps simples", ["ind-present", "ind-imparfait", "ind-ps", "ind-futur", "cond-present"]],
  ["Indicatif, temps composés", ["ind-pc", "ind-pqp", "ind-pa", "ind-fa", "cond-passe"]],
  ["Subjonctif", ["sub-present", "sub-imparfait", "sub-passe", "sub-pqp"]],
  ["Impératif", ["imp-present", "imp-passe"]],
  ["Modes non personnels", ["inf-present", "inf-passe", "part-present", "part-passe"]]
];
const SIMPLES = ["ind-present", "ind-imparfait", "ind-ps", "ind-futur", "cond-present", "sub-present", "sub-imparfait", "imp-present"];
const SUJETS = ["je", "tu", "il", "nous", "vous", "ils"];
const SANS_ELISION = new Set(["haïr"]);

// L'arbre : les fiches, puis un nœud par verbe sous sa famille.
const NOEUDS = [...FICHES];
const FAMILLE = {};
FAMILLES.forEach(f => f.verbes.forEach(v => { FAMILLE[v] = f; NOEUDS.push({ id: VERBE + v, p: f.id, t: v, verbe: v }); }));
const parId = Object.fromEntries(NOEUDS.map(f => [f.id, f]));
const enfants = {};
NOEUDS.forEach(f => { if (f.p) (enfants[f.p] ??= []).push(f.id); });
const DROITE = ["g1", "g2", "apart"], GAUCHE = ["g3-ir", "g3-oir", "g3-re", "reperes"];
const COUL = Object.fromEntries(BRANCHES.map(([id], i) => [id, `var(--c${i + 1})`]));
const NOM_GROUPE = { g1: "1er groupe", g2: "2e groupe", g3: "3e groupe" };

const etat = { ouverts: new Set(["groupes"]), choisi: "groupes", vue: "carte", masque: false, temps: "ind-present", desinence: null, revelees: new Set(), modele: "ind-present" };
const $ = id => document.getElementById(id);
const etroit = matchMedia("(max-width: 900px)");
const sansAcc = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const ancetres = id => { const r = []; for (let f = parId[id]; f && f.p; f = parId[f.p]) r.push(f.p); return r; };
const branche = id => id === "groupes" ? null : parId[id].p === "groupes" ? id : branche(parId[id].p);
const descendants = id => (enfants[id] || []).reduce((n, e) => n + 1 + descendants(e), 0);
const verbeModele = fam => fam.verbes[0];

function creerNoeud(f) {
  const b = document.createElement("button");
  const prof = ancetres(f.id).length, haut = branche(f.id);
  b.className = "noeud" + (f.id === "groupes" ? " racine" : prof === 1 ? " n1" : "") + (f.id === etat.choisi ? " choisi" : "") + (f.verbe ? " verbe-noeud" : "");
  if (haut) b.style.setProperty("--c", COUL[haut]);
  b.textContent = f.t;
  b.dataset.id = f.id;
  const n = descendants(f.id);
  if (n && !etat.ouverts.has(f.id)) {
    const c = document.createElement("span"); c.className = "compte"; c.textContent = "+" + n; b.append(c);
  }
  b.onclick = () => choisir(f.id, true);
  return b;
}

function dessinerCarte() {
  const can = $("canevas"), svg = can.querySelector("svg");
  can.querySelectorAll(".noeud").forEach(n => n.remove());
  const lignes = [], ligneH = 34, ecartX = 44;
  const places = {};
  function visibles(id, prof, cote, liste) {
    liste.push({ id, prof, cote });
    if (etat.ouverts.has(id)) (enfants[id] || []).forEach(e => visibles(e, prof + 1, cote, liste));
    return liste;
  }
  const tous = [{ id: "groupes", prof: 0, cote: 0 }];
  DROITE.forEach(b => visibles(b, 1, 1, tous));
  GAUCHE.forEach(b => visibles(b, 1, -1, tous));
  tous.forEach(n => { const el = creerNoeud(parId[n.id]); can.append(el); n.el = el; n.l = el.offsetWidth; n.h = el.offsetHeight; places[n.id] = n; });
  // Largeur de chaque colonne, par côté et par profondeur.
  const col = { "1": [], "-1": [] };
  tous.forEach(n => { if (n.prof) { const c = col[n.cote]; c[n.prof] = Math.max(c[n.prof] || 0, n.l); } });
  const hauteur = id => {
    const e = etat.ouverts.has(id) ? enfants[id] || [] : [];
    return places[id].H = Math.max(ligneH, e.reduce((s, x) => s + hauteur(x), 0));
  };
  const totalD = DROITE.reduce((s, b) => s + hauteur(b) + 10, 0), totalG = GAUCHE.reduce((s, b) => s + hauteur(b) + 10, 0);
  const H = Math.max(totalD, totalG, 300) + 32;
  const largeurCote = c => col[c].reduce((s, w) => s + (w || 0) + ecartX, 0);
  const racine = places.groupes;
  const cx = largeurCote(-1) + racine.l / 2 + 28;
  const W = cx + racine.l / 2 + largeurCote(1) + 28;
  const xCol = (c, p) => { let d = racine.l / 2 + ecartX; for (let i = 1; i < p; i++) d += col[c][i] + ecartX; return d; };
  function poser(id, y0) {
    const n = places[id];
    n.y = y0 + n.H / 2;
    n.x = n.cote > 0 ? cx + xCol(1, n.prof) : cx - xCol(-1, n.prof) - n.l;
    let y = y0;
    if (etat.ouverts.has(id)) (enfants[id] || []).forEach(e => { poser(e, y); y += places[e].H; });
  }
  let y = (H - totalD) / 2; DROITE.forEach(b => { poser(b, y); y += places[b].H + 10; });
  y = (H - totalG) / 2; GAUCHE.forEach(b => { poser(b, y); y += places[b].H + 10; });
  racine.x = cx - racine.l / 2; racine.y = H / 2;
  can.style.width = W + "px"; can.style.height = H + "px";
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  tous.forEach(n => {
    n.el.style.transform = `translate(${n.x}px, ${n.y - n.h / 2}px)`;
    const f = parId[n.id];
    if (!f.p) return;
    const p = places[f.p];
    const x1 = n.cote > 0 ? p.x + p.l : p.x, x2 = n.cote > 0 ? n.x : n.x + n.l, m = (x1 + x2) / 2;
    lignes.push(`<path d="M${x1} ${p.y}C${m} ${p.y} ${m} ${n.y} ${x2} ${n.y}" stroke="${COUL[branche(n.id)]}"/>`);
  });
  svg.innerHTML = lignes.join("");
  return places;
}

function dessinerPlan() {
  const plan = $("plan"); plan.textContent = "";
  const branche_ = (id, parent) => {
    const li = document.createElement("li");
    li.append(creerNoeud(parId[id]));
    const e = enfants[id] || [];
    if (e.length && etat.ouverts.has(id)) {
      const ul = document.createElement("ul");
      ul.style.setProperty("--c", COUL[branche(e[0])]);
      e.forEach(x => branche_(x, ul));
      li.append(ul);
    }
    parent.append(li);
  };
  branche_("groupes", plan);
  plan.querySelector("button").style.display = "inline-block";
  const racine = plan.firstElementChild;
  const ul = document.createElement("ul"); ul.style.border = "0"; ul.style.padding = "0";
  const liste = racine.querySelector("ul");
  if (liste) { ul.append(...liste.children); liste.remove(); racine.append(ul); }
}

// Une graphie découpée « chant|ais » devient radical + désinence.
function graphie(g, cle) {
  if (!g.includes("|")) return g;
  const [r, d] = g.split("|");
  if (!d) return `<span class="rad">${r}</span>`;
  const cachee = etat.masque && !etat.revelees.has(cle);
  return `<span class="rad">${r}</span><span class="${cachee ? "des cache" : "des"}" data-cle="${cle}">${cachee ? "?" : d}</span>`;
}
const texteForme = c => c[0].replace("|", "");

function sujet(verbe, t, i, forme) {
  const lettre = sansAcc(forme)[0];
  const voyelle = "aeiouy".includes(lettre) || (lettre === "h" && !SANS_ELISION.has(verbe));
  const subj = t.startsWith("sub-");
  if (i === 0) return (subj ? "que " : "") + (voyelle ? "j'" : "je ");
  if (subj && (i === 2 || i === 5)) return `qu'${SUJETS[i]} `;
  return (subj ? "que " : "") + SUJETS[i] + " ";
}

function blocTemps(verbe, t) {
  const l = FORMES[verbe].formes[t];
  if (!l || !l.some(Boolean)) return `<div class="bloc"><h4>${TEMPS[t]}</h4><div class="suj">Pas de forme retenue</div></div>`;
  const impers = t.startsWith("imp-") || t.startsWith("inf-") || t.startsWith("part-");
  const lignes = l.map((c, i) => {
    if (!c) return "";
    const rendu = c.map((g, n) => graphie(g, `${verbe}/${t}/${i}/${n}`)).join(" <span class=\"suj\">ou</span> ");
    return `<div>${impers ? "" : `<span class="suj">${sujet(verbe, t, i, texteForme(c))}</span>`}${rendu}</div>`;
  }).join("");
  return `<div class="bloc"><h4>${TEMPS[t]}</h4>${lignes}</div>`;
}

function radicaux(verbe) {
  const r = new Map();
  for (const t of [...SIMPLES, "part-present", "part-passe", "inf-present"]) {
    (FORMES[verbe].formes[t] || []).forEach(c => {
      if (!c || !c[0].includes("|")) return;
      const k = c[0].split("|")[0];
      if (!r.has(k)) r.set(k, new Set());
      r.get(k).add(TEMPS[t]);
    });
  }
  return r;
}

function formesProches(verbe) {
  const par = new Map(), f = FORMES[verbe].formes;
  for (const t of [...SIMPLES, "part-passe"]) (f[t] || []).forEach(c => {
    if (!c) return;
    c.forEach(g => { const x = g.replace("|", ""); if (!par.has(x)) par.set(x, new Set()); par.get(x).add(TEMPS[t]); });
  });
  const identiques = [...par].filter(([, s]) => s.size > 1).map(([x, s]) => `<li><b>${x}</b> : ${[...s].join(", ")}</li>`);
  const groupes = new Map();
  for (const x of par.keys()) { const k = sansAcc(x); if (!groupes.has(k)) groupes.set(k, []); groupes.get(k).push(x); }
  const accents = [...groupes.values()].filter(l => l.length > 1).map(l => `<li>${l.map(x => `<b>${x}</b> (${[...par.get(x)].join(", ")})`).join(" et ")}</li>`);
  const bords = [];
  const paire = (a, ta, b, tb) => { if (a && b) { const x = texteForme(a), y = texteForme(b); if (y === x + "s") bords.push(`<li><b>${x}</b> (${TEMPS[ta]}) et <b>${y}</b> (${TEMPS[tb]})</li>`); } };
  paire(f["ind-ps"]?.[0], "ind-ps", f["ind-imparfait"]?.[0], "ind-imparfait");
  paire(f["ind-futur"]?.[0], "ind-futur", f["cond-present"]?.[0], "cond-present");
  return { identiques, proches: [...accents, ...bords] };
}

function ficheVerbe(f) {
  const v = f.verbe, e = FORMES[v], fam = FAMILLE[v];
  const entier = v === "être" || v === "avoir" || v === "aller";
  let h = `<p><b>${NOM_GROUPE[fam.groupe]}</b>, famille <button class="lien" data-va="${fam.id}">${fam.titre}</button>. Auxiliaire : ${e.aux}.</p>`;
  if (NOTES[v]) h += `<p>${NOTES[v]}</p>`;
  if (DECISIONS[v]) h += `<div class="attention">${DECISIONS[v]}</div>`;
  if (!entier) {
    const r = radicaux(v);
    h += `<h3>Radicaux de ce découpage</h3><ul class="radicaux">${[...r].map(([k, s]) => `<li><b>${k}-</b> : ${[...s].join(", ")}</li>`).join("")}</ul>`;
  }
  h += MODES.map(([nom, l]) => `<div class="mode">${nom}</div><div class="temps">${l.map(t => blocTemps(v, t)).join("")}</div>`).join("");
  const p = formesProches(v);
  if (p.identiques.length) h += `<details><summary>Formes identiques à plusieurs temps (${p.identiques.length})</summary><ul class="proches">${p.identiques.join("")}</ul></details>`;
  if (p.proches.length) h += `<details><summary>Formes proches (${p.proches.length})</summary><ul class="proches">${p.proches.join("")}</ul></details>`;
  const voisins = fam.verbes.filter(x => x !== v);
  if (voisins.length) h += `<h3>Même famille</h3><div class="liens">${voisins.map(x => `<button class="puce" data-va="${VERBE + x}">${x}</button>`).join("")}</div>`;
  h += `<h3>Sources</h3><ul class="sources"><li>Formes comparées sur <a href="${SOURCES.LC[2]}" target="_blank" rel="noopener">Le Conjugueur</a>, <a href="${SOURCES.LM[2]}" target="_blank" rel="noopener">Le Monde</a> et le Wiktionnaire.</li></ul>`;
  return h;
}

function dessinerFiche() {
  const a = $("fiche");
  if (etat.desinence) { ficheDesinence(a); return; }
  const f = parId[etat.choisi];
  const fil = ancetres(f.id).reverse().map(x => `<button data-va="${x}">${parId[x].t}</button>`).join(" › ");
  let h = `<button id="fermer">Fermer</button>${fil ? `<div class="fil">${fil}</div>` : ""}<h2>${f.t}</h2>`;
  if (f.verbe) h += ficheVerbe(f);
  else {
    h += `<p>${f.d}</p>`;
    if (f.f) h += `<ul>${f.f.map(x => `<li>${x}</li>`).join("")}</ul>`;
    if (f.n) h += `<div class="attention">${f.n}</div>`;
    const fam = FAMILLES.find(x => x.id === f.id);
    if (fam) {
      const m = verbeModele(fam);
      if (!fam.id.endsWith("isoles") && fam.id !== "g3-aux") {
        h += `<h3>Patron : ${m}</h3><div class="onglets">${SIMPLES.map(t => `<button class="puce" data-t="${t}" aria-pressed="${t === etat.modele}">${TEMPS[t]}</button>`).join("")}</div><div class="temps">${blocTemps(m, etat.modele)}</div>`;
      }
      h += `<h3>Verbes de la famille (${fam.verbes.length})</h3><div class="liens">${fam.verbes.map(x => `<button class="puce" data-va="${VERBE + x}">${x}</button>`).join("")}</div>`;
    }
    const e = (enfants[f.id] || []).filter(x => !parId[x].verbe);
    const suite = [...e, ...(f.l || []).filter(i => !e.includes(i))];
    if (suite.length) h += `<h3>Voir aussi</h3><div class="liens">${suite.map(i => `<button class="puce" data-va="${i}">${parId[i].t}</button>`).join("")}</div>`;
    h += `<h3>Sources</h3><ul class="sources">${f.s.map(([k, p]) => `<li><a href="${SOURCES[k][2]}" target="_blank" rel="noopener">${SOURCES[k][1]}</a>${p && p !== "tableaux" ? ", " + p : ""}</li>`).join("")}</ul>`;
  }
  a.innerHTML = h; a.scrollTop = 0;
  brancherFiche(a);
}

function brancherFiche(a) {
  a.querySelectorAll("[data-va]").forEach(b => b.onclick = () => { etat.desinence = null; choisir(b.dataset.va, false); });
  a.querySelectorAll("[data-t]").forEach(b => b.onclick = () => { etat.modele = b.dataset.t; dessinerFiche(); });
  const fermer = $("fermer"); if (fermer) fermer.onclick = () => { a.hidden = true; };
}

// Toutes les désinences, par temps et par personne.
function indexDesinences() {
  const ix = {};
  for (const [v, e] of Object.entries(FORMES)) for (const t of SIMPLES) (e.formes[t] || []).forEach((c, i) => {
    if (!c) return;
    c.forEach(g => {
      if (!g.includes("|")) return;
      const d = g.split("|")[1];
      const k = (ix[t] ??= {}), l = (k[i] ??= {});
      (l[d] ??= []).push([v, g]);
    });
  });
  return ix;
}
const INDEX = indexDesinences();
const nomDes = d => d ? "-" + d : "rien";

function dessinerDesinences() {
  const lignes = SIMPLES.map(t => {
    const cols = t === "imp-present" ? [null, 0, null, 1, 2, null] : [0, 1, 2, 3, 4, 5];
    return `<tr><td><b>${TEMPS[t]}</b></td>${cols.map(i => {
      if (i == null) return "<td></td>";
      const l = INDEX[t]?.[i] || {};
      return `<td>${Object.entries(l).sort((a, b) => b[1].length - a[1].length).map(([d, v]) => `<button class="puce" data-d="${t}/${i}/${d}" aria-pressed="${etat.desinence === `${t}/${i}/${d}`}">${nomDes(d)} <small>${v.length}</small></button>`).join("")}</td>`;
    }).join("")}</tr>`;
  }).join("");
  const t = $("tdes");
  t.innerHTML = `<thead><tr><th>Temps</th>${["je", "tu", "il", "nous", "vous", "ils"].map(p => `<th>${p}</th>`).join("")}</tr></thead><tbody>${lignes}</tbody>`;
  t.querySelectorAll("[data-d]").forEach(b => b.onclick = () => { etat.desinence = b.dataset.d; $("fiche").hidden = false; dessinerDesinences(); dessinerFiche(); });
}

function ficheDesinence(a) {
  const [t, i, d] = etat.desinence.split("/");
  const l = INDEX[t][i][d];
  const pers = t === "imp-present" ? ["2e du singulier", "1re du pluriel", "2e du pluriel"][i] : SUJETS[i];
  a.innerHTML = `<button id="fermer">Fermer</button><div class="fil">${TEMPS[t]}, ${pers}</div><h2>Désinence ${nomDes(d)}</h2>
  <p>${l.length} forme${l.length > 1 ? "s" : ""} dans les verbes de la carte. Aller, être et avoir ne sont pas découpés.</p>
  <div class="liens">${l.map(([v, g]) => `<button class="puce" data-va="${VERBE + v}">${graphie(g, "")}</button>`).join("")}</div>`;
  a.scrollTop = 0;
  brancherFiche(a);
}

function dessinerComparer() {
  const liste = [...SIMPLES, "part-present", "part-passe"];
  $("choix-temps").innerHTML = liste.map(t => `<button class="puce" data-c="${t}" aria-pressed="${t === etat.temps}">${TEMPS[t]}</button>`).join("");
  $("choix-temps").querySelectorAll("[data-c]").forEach(b => b.onclick = () => { etat.temps = b.dataset.c; dessinerComparer(); });
  const t = etat.temps, unique = t.startsWith("part-"), rangs = unique ? [0] : t === "imp-present" ? [0, 1, 2] : [0, 1, 2, 3, 4, 5];
  const tetes = unique ? ["Forme"] : t === "imp-present" ? ["2e sing.", "1re plur.", "2e plur."] : SUJETS;
  const ligne = v => `<tr data-id="${VERBE + v}"><td>${v}</td>${rangs.map(i => {
    const c = FORMES[v].formes[t]?.[i];
    return `<td>${c ? c.map(g => graphie(g, `${v}/${t}/${i}/c`)).join(" <span class=\"suj\">ou</span> ") : ""}</td>`;
  }).join("")}</tr>`;
  const corps = BRANCHES.filter(b => b[0] !== "reperes").map(([id, nom]) => {
    const fams = FAMILLES.filter(f => f.id !== "x" && ancetres(f.id).includes(id));
    return `<tr class="titre"><td colspan="${rangs.length + 1}">${nom}</td></tr>` + fams.map(f => {
      const isoles = f.id.endsWith("isoles") || ["g3-aux", "g3-impersonnels"].includes(f.id);
      return (isoles ? f.verbes : [verbeModele(f)]).map(ligne).join("");
    }).join("");
  }).join("");
  const table = $("comparaison");
  table.innerHTML = `<thead><tr><th>Verbe</th>${tetes.map(p => `<th>${p}</th>`).join("")}</tr></thead><tbody>${corps}</tbody>`;
  table.querySelectorAll("tr[data-id]").forEach(r => r.onclick = e => { if (!e.target.classList.contains("cache")) { etat.desinence = null; choisir(r.dataset.id, false); } });
}

function dessinerSources() {
  const n = Object.values(FORMES).reduce((s, e) => s + Object.values(e.formes).reduce((x, l) => x + l.filter(Boolean).length, 0), 0);
  const groupes = {};
  Object.values(SOURCES).forEach(s => (groupes[s[0]] ??= []).push(s));
  $("vue-sources").innerHTML = `
  <h2 style="margin-top:0">Comment les formes ont été vérifiées</h2>
  <p>La carte compte ${Object.keys(FORMES).length} verbes et ${n.toLocaleString("fr-FR")} cases de conjugaison. Chaque verbe a été lu sur trois sites : Le Conjugueur, Le Monde et le Wiktionnaire. Une forme n'entre que si les sites concordent, ou si l'écart est expliqué ci-dessous.</p>
  <ul>
    <li>Chaque temps composé a aussi été recalculé à partir de l'auxiliaire et du participe passé.</li>
    <li>Dans une famille, tous les verbes ont les mêmes désinences et la même répartition de radicaux que le modèle. Les familles de verbes isolés échappent à ce contrôle.</li>
    <li>Toutes les formes citées dans les fiches ont été comparées aux tableaux par un script.</li>
  </ul>
  <p>Ces trois sites ne sont pas des sources officielles, et leurs données peuvent avoir une origine commune. Leur accord réduit le risque d'erreur sans l'annuler.</p>
  <h2>Écarts entre les sites</h2>
  <p>${Object.keys(DECISIONS).length} verbes ont demandé une décision :</p>
  <ul>${Object.entries(DECISIONS).map(([v, t]) => `<li><b>${v}</b> : ${t}</li>`).join("")}</ul>
  <h2>Ordre de priorité</h2>
  <p>La Terminologie, les programmes et Éduscol définissent les notions. L'Office québécois de la langue française et l'Académie française précisent les règles. Les sites de conjugaison servent aux formes.</p>
  ${Object.entries(groupes).map(([g, l]) => `<h2>${g}</h2><ul>${l.map(s => `<li><a href="${s[2]}" target="_blank" rel="noopener">${s[1]}</a></li>`).join("")}</ul>`).join("")}`;
}

function centrer(id, places) {
  const s = $("scene"), n = places && places[id];
  if (!n || etroit.matches) return;
  s.scrollTo({ left: n.x + n.l / 2 - s.clientWidth / 2, top: n.y - s.clientHeight / 2, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

const VUES = ["carte", "comparer", "desinences", "sources"];
function dessiner() {
  const e = etroit.matches;
  $("canevas").hidden = e; $("plan").hidden = !e;
  VUES.forEach(v => { $("vue-" + v).hidden = etat.vue !== v; $("v-" + v).setAttribute("aria-selected", etat.vue === v); });
  $("deplier").hidden = $("replier").hidden = etat.vue !== "carte";
  let places = null;
  if (etat.vue === "carte") { if (e) dessinerPlan(); else places = dessinerCarte(); }
  if (etat.vue === "comparer") dessinerComparer();
  if (etat.vue === "desinences") dessinerDesinences();
  return places;
}

function choisir(id, depuisCarte) {
  if (depuisCarte && enfants[id]) {
    if (etat.ouverts.has(id) && id === etat.choisi && id !== "groupes") etat.ouverts.delete(id); else etat.ouverts.add(id);
  }
  etat.choisi = id; etat.desinence = null;
  ancetres(id).forEach(a => etat.ouverts.add(a));
  $("fiche").hidden = false;
  dessinerFiche();
  const places = dessiner();
  if (etat.vue === "carte") centrer(id, places);
}

// Recherche : un verbe, une fiche ou n'importe quelle forme conjuguée.
const FORMES_INDEX = new Map();
for (const [v, e] of Object.entries(FORMES)) for (const [t, l] of Object.entries(e.formes)) l.forEach(c => (c || []).forEach(g => {
  const k = sansAcc(g.replace("|", ""));
  if (!FORMES_INDEX.has(k)) FORMES_INDEX.set(k, new Map());
  const m = FORMES_INDEX.get(k);
  if (!m.has(v)) m.set(v, new Set());
  m.get(v).add(TEMPS[t]);
}));

function chercher() {
  const brut = $("q").value.trim();
  const r = $("resultats");
  if (!brut) { r.hidden = true; return; }
  const q = sansAcc(brut);
  const res = [];
  (FORMES_INDEX.get(q) || new Map()).forEach((s, v) => res.push([VERBE + v, v, "Forme : " + [...s].slice(0, 3).join(", ")]));
  NOEUDS.filter(f => sansAcc(f.t).includes(q) && !res.some(x => x[0] === f.id)).sort((a, b) => sansAcc(a.t).indexOf(q) - sansAcc(b.t).indexOf(q)).forEach(f => res.push([f.id, f.t, f.verbe ? "Verbe, " + FAMILLE[f.verbe].titre : "Fiche"]));
  const l = res.slice(0, 8);
  r.innerHTML = l.length ? l.map(([id, t, s]) => `<button data-id="${id}">${t}<small>${s}</small></button>`).join("") : `<button disabled>Aucun résultat</button>`;
  r.hidden = false;
  r.querySelectorAll("[data-id]").forEach(b => b.onclick = () => aller(b.dataset.id));
}
function aller(id) {
  $("q").value = ""; $("resultats").hidden = true;
  etat.vue = "carte";
  choisir(id, false);
}

function imprimable() {
  $("imprimable").innerHTML = BRANCHES.map(([id, t]) => {
    const liste = []; const f = i => { if (!parId[i].verbe) { liste.push(parId[i]); (enfants[i] || []).forEach(f); } }; f(id);
    return `<h2>${t}</h2><div class="cols">${liste.map(x => {
      const fam = FAMILLES.find(y => y.id === x.id);
      return `<article><h3>${x.t}</h3><p>${x.d}</p>${x.f ? `<p>${x.f.join(" ")}</p>` : ""}${x.n ? `<p><b>Attention :</b> ${x.n}</p>` : ""}${fam ? `<small>Verbes : ${fam.verbes.join(", ")}</small>` : ""}</article>`;
    }).join("")}</div>`;
  }).join("");
}

function revelerClic(e) {
  const c = e.target.closest?.(".cache");
  if (!c) return;
  e.stopPropagation();
  etat.revelees.add(c.dataset.cle);
  c.classList.remove("cache");
  const [v, t, i, n] = c.dataset.cle.split("/");
  c.textContent = FORMES[v].formes[t][i][n === "c" ? 0 : n].split("|")[1];
}

VUES.forEach(v => $("v-" + v).onclick = () => { etat.vue = v; const p = dessiner(); if (p) centrer(etat.choisi, p); });
$("deplier").onclick = () => { NOEUDS.forEach(f => { if (enfants[f.id]) etat.ouverts.add(f.id); }); dessiner(); };
$("replier").onclick = () => { etat.ouverts = new Set(["groupes"]); ancetres(etat.choisi).forEach(a => etat.ouverts.add(a)); dessiner(); };
$("masquer").onclick = () => {
  etat.masque = !etat.masque; etat.revelees.clear();
  $("masquer").setAttribute("aria-pressed", etat.masque);
  dessinerFiche(); dessiner();
};
$("fiche").addEventListener("click", revelerClic, true);
$("scene").addEventListener("click", revelerClic, true);
$("q").oninput = chercher;
$("q").onkeydown = e => {
  if (e.key === "Enter") { const b = $("resultats").querySelector("[data-id]"); if (b) aller(b.dataset.id); }
  if (e.key === "Escape") { $("q").value = ""; $("resultats").hidden = true; }
};
etroit.addEventListener("change", () => { $("fiche").hidden = etroit.matches; dessiner(); });
addEventListener("resize", () => { if (etat.vue === "carte" && !etroit.matches) dessiner(); });
document.fonts?.ready.then(() => { const p = dessiner(); centrer("groupes", p); });

dessinerSources(); imprimable(); dessinerFiche();
if (etroit.matches) $("fiche").hidden = true;
centrer("groupes", dessiner());
