// Validation côté navigateur (confort utilisateur uniquement : le backend revalide TOUT).
export const LIMITS = { alphabetSize: 26, alphabetText: 80, regex: 200, word: 1000 };
export const EPSILONS = ['ε'];     // seul ε est l'élément neutre ('€' est un caractère ordinaire)

const SYMBOL = /^[A-Za-z0-9]$/;

/** "{a,b}" ou "a,b" -> { ok, symbols } ou { ok:false, error } */
export function parseAlphabet(text) {
  let t = text.trim();
  if (t.startsWith('{') || t.endsWith('}')) {
    if (!(t.startsWith('{') && t.endsWith('}'))) return fail('Les accolades de l\'alphabet ne sont pas équilibrées.');
    t = t.slice(1, -1).trim();
  }
  if (t === '') return fail('L\'alphabet ne peut pas être vide.');
  if (text.length > LIMITS.alphabetText) return fail('L\'alphabet est trop long.');
  const symbols = [];
  for (const raw of t.split(',')) {
    const s = raw.trim();
    if (s === '') return fail('Séparateur incorrect : symbole manquant entre deux virgules.');
    if (EPSILONS.includes(s)) return fail('Le caractère epsilon ne peut pas appartenir à l\'alphabet.');
    if ([...s].length !== 1) return fail(`Chaque symbole doit être un seul caractère (élément invalide : « ${s} »).`);
    if (!SYMBOL.test(s)) return fail(`Le symbole « ${s} » n'est pas autorisé : utilisez des lettres ou des chiffres.`);
    if (symbols.includes(s)) return fail(`Le symbole ${s} est en double dans l'alphabet.`);
    symbols.push(s);
  }
  if (symbols.length > LIMITS.alphabetSize) return fail(`L'alphabet est trop grand (maximum ${LIMITS.alphabetSize} symboles).`);
  return { ok: true, symbols };
}

/** Vérifie la syntaxe de l'expression par un petit automate d'état (mêmes règles que le backend). */
export function validateRegex(text, symbols) {
  const regex = text.trim();
  if (regex === '') return fail('L\'expression régulière ne peut pas être vide.');
  if (regex.length > LIMITS.regex) return fail(`L'expression régulière est trop longue (maximum ${LIMITS.regex} caractères).`);

  // prev : START | OPEN | UNION | ATOM (symbole, epsilon, ')') | STAR
  let prev = 'START';
  let depth = 0;
  const syntax = (msg, i) => fail(`L'expression régulière contient une erreur de syntaxe : ${msg} (position ${i + 1}).`);
  const chars = [...regex];
  for (let i = 0; i < chars.length; i++) {
    const c = chars[i];
    if (/\s/.test(c)) return fail(`L'expression régulière contient un caractère interdit (espace) à la position ${i + 1}.`);
    if (c === '(') { depth++; prev = 'OPEN'; }
    else if (c === ')') {
      if (depth === 0) return syntax('parenthèse fermante sans parenthèse ouvrante', i);
      if (prev === 'OPEN') return syntax('parenthèses vides', i);
      if (prev === 'UNION') return syntax('alternative vide avant \')\'', i);
      depth--; prev = 'ATOM';
    } else if (c === '|') {
      if (prev !== 'ATOM' && prev !== 'STAR') return syntax('\'|\' mal placé (alternative vide)', i);
      prev = 'UNION';
    } else if (c === '*') {
      if (prev === 'STAR') return syntax('opérateurs \'*\' consécutifs', i);
      if (prev !== 'ATOM') return syntax('\'*\' mal placé (rien à répéter)', i);
      prev = 'STAR';
    } else if (EPSILONS.includes(c)) { prev = 'ATOM'; }
    else {
      if (!symbols.includes(c)) return fail(`Le symbole ${c} ne figure pas dans l'alphabet déclaré.`);
      prev = 'ATOM';
    }
  }
  if (depth > 0) return syntax('parenthèse ouvrante non fermée', chars.length);
  if (prev === 'UNION') return syntax('alternative vide après \'|\'', chars.length);
  return { ok: true };
}

/** Un mot vide est VALIDE (mot vide). ε est interdit dans les mots. */
export function validateWord(word, symbols) {
  if (word.length > LIMITS.word) return fail(`Le mot est trop long (maximum ${LIMITS.word} caractères).`);
  for (const c of word) {
    if (EPSILONS.includes(c)) {
      return fail('Le mot contient un symbole non autorisé : ε est réservé aux expressions. Laissez le champ vide pour tester le mot vide.');
    }
    if (!symbols.includes(c)) return fail(`Le mot contient un symbole non autorisé : « ${c === ' ' ? 'espace' : c} » ne figure pas dans l'alphabet.`);
  }
  return { ok: true };
}

function fail(error) { return { ok: false, error }; }
