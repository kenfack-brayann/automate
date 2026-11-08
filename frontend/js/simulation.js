// Affichage des résultats de simulation (mot vide inclus). Uniquement textContent.
export function addResult(list, result) {
  const li = document.createElement('li');
  li.className = result.accepted ? 'accepted' : 'rejected';

  const verdict = document.createElement('span');
  verdict.className = 'verdict';
  verdict.textContent = result.accepted ? 'Mot accepté' : 'Mot rejeté';

  const word = document.createElement('span');
  word.className = 'word';
  word.textContent = result.word === '' ? 'ε (mot vide)' : '« ' + result.word + ' »';

  const path = document.createElement('span');
  path.className = 'path';
  path.textContent = 'Parcours dans l\'AFD : ' + result.path.join(' → ') +
    (result.blocked ? '  (blocage : aucune transition pour le symbole suivant)' : '');

  li.append(verdict, ' — ', word, path);
  list.prepend(li);      // le plus récent en premier
}

export function clearResults(list) { list.replaceChildren(); }
