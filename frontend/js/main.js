import { parseAlphabet, validateRegex, validateWord } from './validation.js';
import { generateAutomaton, checkWord, ApiError } from './api.js';
import { renderAutomaton, renderTable, highlightPath, clearHighlight } from './automate.js';
import { addResult, clearResults } from './simulation.js';

const $ = (id) => document.getElementById(id);
const el = {
  defForm: $('definition-form'), alphabet: $('alphabet'), regex: $('regex'),
  alphabetError: $('alphabet-error'), regexError: $('regex-error'), defError: $('definition-error'),
  generate: $('generate-btn'),
  viz: $('visualisation'), view: $('view'), summary: $('summary'), graph: $('graph'),
  table: $('transition-table'), tableTitle: $('table-title'),
  sim: $('simulation'), wordForm: $('word-form'), word: $('word'), wordError: $('word-error'),
  test: $('test-btn'), history: $('history'),
};

// Automate courant : identifiant temporaire, alphabet figé à la génération,
// les trois vues (AFN, AFD, AFD minimale) et le dernier mot testé.
let current = null;

// Vocabulaire de chaque vue (le texte des options est dans index.html).
const VIEWS = {
  nfa: { graph: 'Graphe de l\'AFN', table: 'Table de transitions de l\'AFN' },
  dfa: { graph: 'Graphe de l\'AFD', table: 'Table de transitions de l\'AFD' },
  min: { graph: 'Graphe de l\'AFD minimale', table: 'Table de transitions de l\'AFD minimale' },
};

function setError(input, errorEl, message) {
  errorEl.textContent = message || '';
  if (input) input.classList.toggle('invalid', Boolean(message));
}

function summarize(view, data) {
  const base = `${data.states.length} état(s) · état initial : ${data.initial_state} · ` +
    `état(s) final(aux) : ${data.final_states.join(', ') || 'aucun'}`;
  if (view === 'nfa') return `${base} · les transitions ε sont en pointillés`;
  if (view === 'dfa') return `${base} · mot vide ${data.accepts_empty_word ? 'accepté' : 'rejeté'}`;
  const before = current.views.dfa.states.length;
  return `${base} · ` + (data.states.length === before
    ? 'l\'AFD était déjà minimal'
    : `réduit de ${before} à ${data.states.length} états`);
}

/** Affiche la vue choisie (une seule à la fois) : résumé, graphe et table de transitions. */
function showView(view) {
  const data = current.views[view];
  if (!data) return;
  el.summary.textContent = summarize(view, data);
  el.graph.setAttribute('aria-label', VIEWS[view].graph);
  el.tableTitle.textContent = VIEWS[view].table;
  renderAutomaton(el.graph, data);
  renderTable(el.table, data);
  // Le parcours d'un mot est calculé sur l'AFD : on ne le surligne que dans cette vue.
  if (view === 'dfa' && current.lastResult) highlightPath(current.lastResult.path, current.lastResult.accepted);
}

el.view.addEventListener('change', () => { if (current) showView(el.view.value); });

// Bouton d'insertion de ε à la position du curseur.
document.querySelectorAll('[data-insert]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const input = el.regex;
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? start;
    input.setRangeText(btn.dataset.insert, start, end, 'end');
    input.focus();
  });
});

el.defForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  setError(el.alphabet, el.alphabetError, '');
  setError(el.regex, el.regexError, '');
  setError(null, el.defError, '');

  const alpha = parseAlphabet(el.alphabet.value);
  if (!alpha.ok) return setError(el.alphabet, el.alphabetError, alpha.error);
  const check = validateRegex(el.regex.value, alpha.symbols);
  if (!check.ok) return setError(el.regex, el.regexError, check.error);

  el.generate.disabled = true;
  try {
    const dfa = await generateAutomaton(alpha.symbols, el.regex.value.trim());
    current = {
      id: dfa.automate_id, alphabet: dfa.alphabet, lastResult: null,
      views: { nfa: dfa.nfa, dfa, min: dfa.minimal_dfa },
    };
    el.viz.hidden = false;
    el.sim.hidden = false;
    el.view.value = 'nfa';          // l'AFN est toujours affiché en premier
    showView('nfa');
    clearResults(el.history);
    el.word.value = '';
    setError(el.word, el.wordError, '');
  } catch (err) {
    if (!(err instanceof ApiError)) console.error(err);
    setError(null, el.defError, err instanceof ApiError ? err.message : 'Une erreur interne est survenue. Veuillez réessayer.');
  } finally {
    el.generate.disabled = false;
  }
});

el.wordForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  setError(el.word, el.wordError, '');
  if (!current) return;

  const word = el.word.value;            // surtout pas de trim, ni de "required" : "" = mot vide
  const check = validateWord(word, current.alphabet);
  if (!check.ok) return setError(el.word, el.wordError, check.error);

  el.test.disabled = true;
  try {
    const result = await checkWord(current.id, word);
    addResult(el.history, result);
    current.lastResult = result;
    if (el.view.value === 'dfa') highlightPath(result.path, result.accepted);
  } catch (err) {
    if (!(err instanceof ApiError)) console.error(err);
    clearHighlight();
    setError(el.word, el.wordError, err instanceof ApiError ? err.message : 'Une erreur interne est survenue. Veuillez réessayer.');
  } finally {
    el.test.disabled = false;
  }
});
