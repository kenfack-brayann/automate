// Affichage graphique de l'AFD avec Cytoscape.js (chargé globalement par index.html).
// Aucune donnée utilisateur n'est insérée via innerHTML : tout passe par textContent / Cytoscape.
let cy = null;          // graphe affiché (AFN, AFD ou AFD minimal selon la vue choisie)

// Palette alignée sur le site (fond clair du graphe : #faf9ff).
const STYLE = [
  { selector: 'node.state', style: {
      'background-color': '#ffffff', 'border-width': 2.5, 'border-color': '#6d50db',
      label: 'data(label)', 'text-valign': 'center', 'text-halign': 'center',
      color: '#222222', 'font-size': 15, 'font-weight': 600, width: 50, height: 50 } },
  { selector: 'node.final', style: { 'border-style': 'double', 'border-width': 8 } },
  { selector: 'node.visited', style: { 'background-color': '#e3dcff' } },
  { selector: 'node.current.accepted', style: { 'background-color': '#8fe0bd' } },
  { selector: 'node.current.rejected', style: { 'background-color': '#ffb3c2' } },
  { selector: 'node.start-marker', style: { width: 1, height: 1, 'background-opacity': 0, 'border-width': 0 } },
  { selector: 'edge', style: {
      'curve-style': 'bezier', 'control-point-step-size': 55, width: 2,
      'line-color': '#8c7fc9', 'target-arrow-color': '#8c7fc9', 'target-arrow-shape': 'triangle',
      label: 'data(label)', 'font-size': 15, 'font-weight': 600, color: '#222222',
      'text-background-color': '#faf9ff', 'text-background-opacity': 1, 'text-background-padding': 3,
      'loop-direction': '-90deg', 'loop-sweep': '40deg' } },
  { selector: 'edge.epsilon', style: { 'line-style': 'dashed' } },
  { selector: 'edge.start-edge', style: { label: '', width: 2.5, 'line-color': '#222222', 'target-arrow-color': '#222222' } },
];

/** Affiche un automate (AFN, AFD ou AFD minimal) et remplace le graphe précédent. */
export function renderAutomaton(container, automaton) {
  if (cy) { cy.destroy(); cy = null; }
  cy = buildGraph(container, automaton);
}

function buildGraph(container, dfa) {
  const finals = new Set(dfa.final_states);
  const elements = [];

  for (const s of dfa.states) {
    elements.push({ data: { id: s, label: s }, classes: finals.has(s) ? 'state final' : 'state' });
  }
  // Flèche entrante : petit nœud invisible relié à l'état initial.
  elements.push({ data: { id: '__start' }, classes: 'start-marker' });
  elements.push({ data: { id: '__start_edge', source: '__start', target: dfa.initial_state }, classes: 'start-edge' });

  // Plusieurs symboles entre les mêmes états -> une seule flèche "a, b".
  for (const from of dfa.states) {
    const grouped = new Map();
    // AFD : une cible par symbole (texte). AFN : une liste de cibles par symbole.
    for (const [symbol, targets] of Object.entries(dfa.transitions[from] || {})) {
      for (const to of [].concat(targets)) {
        if (!grouped.has(to)) grouped.set(to, []);
        grouped.get(to).push(symbol);
      }
    }
    for (const [to, symbols] of grouped) {
      const onlyEpsilon = symbols.length === 1 && symbols[0] === dfa.epsilon;     // transition ε : en pointillés
      elements.push({
        data: { id: `e_${from}_${to}`, source: from, target: to, label: symbols.join(', ') },
        classes: onlyEpsilon ? 'transition epsilon' : 'transition',
      });
    }
  }

  const cy = window.cytoscape({ container, elements, style: STYLE, minZoom: 0.3, maxZoom: 2.5 });

  // Disposition en arbre (breadthfirst) : on la lance sans animation, puis on
  // échange x/y pour que les niveaux se lisent de gauche à droite.
  cy.elements('.state, .transition').layout({
    name: 'breadthfirst', directed: true, roots: '#' + dfa.initial_state,
    spacingFactor: 1.5, padding: 40, animate: false,
  }).run();
  cy.nodes('.state').positions((node) => ({ x: node.position('y'), y: node.position('x') }));
  const p = cy.getElementById(dfa.initial_state).position();
  cy.getElementById('__start').position({ x: p.x - 75, y: p.y });
  cy.fit(undefined, 40);
  return cy;
}

/** Met en évidence le parcours d'un mot (état courant coloré selon le verdict). */
export function highlightPath(path, accepted) {
  if (!cy) return;
  clearHighlight();
  for (const s of path) cy.getElementById(s).addClass('visited');
  cy.getElementById(path[path.length - 1]).addClass('current').addClass(accepted ? 'accepted' : 'rejected');
}

export function clearHighlight() {
  if (cy) cy.nodes().removeClass('visited current accepted rejected');
}

export function renderTable(table, dfa) {
  table.replaceChildren();
  const finals = new Set(dfa.final_states);
  const head = table.createTHead().insertRow();
  head.appendChild(cell('th', 'État'));
  const columns = dfa.epsilon ? [...dfa.alphabet, dfa.epsilon] : dfa.alphabet;     // l'AFN a une colonne ε
  for (const a of columns) head.appendChild(cell('th', a));
  const body = table.createTBody();
  for (const s of dfa.states) {
    const row = body.insertRow();
    const mark = (s === dfa.initial_state ? '→ ' : '') + (finals.has(s) ? '* ' : '');
    const th = cell('th', mark + s);
    th.scope = 'row';
    row.appendChild(th);
    for (const a of columns) {
      const targets = [].concat((dfa.transitions[s] || {})[a] || []);
      row.appendChild(cell('td', targets.join(', ') || '—'));
    }
  }
}

function cell(tag, text) {
  const el = document.createElement(tag);
  el.textContent = text;
  return el;
}

// Le graphe suit la taille de la fenêtre (rotation du téléphone, redimensionnement).
window.addEventListener('resize', () => {
  if (cy) { cy.resize(); cy.fit(undefined, 40); }
});
