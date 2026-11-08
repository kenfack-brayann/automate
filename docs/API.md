# Documentation de l'API

Toutes les réponses sont en JSON. En cas d'erreur : `{"success": false, "error": "<message>"}`.
Les corps de requête doivent être du JSON (`Content-Type: application/json`) avec **exactement**
les propriétés listées (toute propriété en trop ou manquante → 400). Taille max : 4 Ko.

## POST /api/automate — génération de l'AFD

Requête :
```json
{ "alphabet": ["a", "b"], "regex": "(a|b)*abb" }
```
- `alphabet` : liste de 1 à 26 symboles distincts, chacun une lettre ASCII ou un chiffre.
  `ε` est interdit (et `€`, qui n'est ni lettre ni chiffre).
- `regex` : 1 à 200 caractères, `ε` accepté comme mot vide. `€` n'est pas un élément neutre :
  il est refusé comme tout symbole absent de l'alphabet.

Réponse 200 (états et transitions calculés par l'algorithme) :
```json
{
  "success": true,
  "automate_id": "Qx7...",
  "alphabet": ["a", "b"],
  "initial_state": "q0",
  "states": ["q0", "q1", "q2", "q3", "q4"],
  "final_states": ["q4"],
  "transitions": { "q0": {"a": "q1", "b": "q2"}, "q1": {"a": "q1", "b": "q3"} },
  "accepts_empty_word": false,
  "minimal_dfa": {
    "alphabet": ["a", "b"],
    "initial_state": "q0",
    "states": ["q0", "q1", "q2", "q3"],
    "final_states": ["q3"],
    "transitions": { "q0": {"a": "q1", "b": "q0"}, "q1": {"a": "q1", "b": "q2"} },
    "accepts_empty_word": false
  },
  "nfa": {
    "alphabet": ["a", "b"],
    "epsilon": "ε",
    "initial_state": "q0",
    "states": ["q0", "q1", "q2", "..."],
    "final_states": ["q13"],
    "transitions": { "q0": {"ε": ["q1", "q2"]}, "q3": {"a": ["q6"]} }
  }
}
```
`nfa` est l'AFN de Thompson de l'expression (états `q0, q1…` en parcours en largeur). Contrairement à
l'AFD, chaque symbole mène à une **liste** d'états, et les transitions epsilon sont présentes sous la
clé `epsilon` (« ε »). Il n'a qu'un état final. Il sert uniquement à l'affichage.

`minimal_dfa` est l'AFD minimal de la même expression (même langage, nombre d'états minimal, états
renommés `q0, q1…` en parcours en largeur) ; il a les mêmes champs que l'AFD, sans `success` ni
`automate_id`. Une transition absente signifie rejet (pas d'état puits). Les AFD ne contiennent jamais
de transition epsilon. Le test de mots (`/api/automate/check`) s'exécute sur l'AFD d'origine.

## POST /api/automate/check — test d'un mot

Requête :
```json
{ "automate_id": "Qx7...", "word": "abb" }
```
`word` peut être `""` (mot vide). `ε` est refusé dans un mot (réservé aux expressions) ; `€` est refusé
comme tout symbole absent de l'alphabet.

Réponse 200 :
```json
{ "success": true, "accepted": true, "message": "Mot accepté",
  "word": "abb", "path": ["q0", "q1", "q3", "q4"], "blocked": false }
```
`blocked` vaut `true` si une transition manquait pendant la lecture (mot rejeté, sans erreur serveur).

## Codes HTTP

| Code | Cas |
|------|-----|
| 200 | Succès |
| 400 | JSON invalide, propriété manquante/inattendue, mauvais type |
| 404 | Automate introuvable ou expiré (30 min) ; route inconnue |
| 405 | Méthode non autorisée |
| 413 | Requête trop volumineuse (> 4 Ko) |
| 422 | Règle métier violée : alphabet, syntaxe de l'expression, symbole inconnu, mot invalide, automate trop volumineux ou trop long à calculer |
| 429 | Trop de requêtes (60 par minute et par IP) |
| 500 | Erreur interne (message générique, détails dans les journaux serveur) |

Exemple d'erreur :
```json
{ "success": false, "error": "Le symbole c ne figure pas dans l'alphabet déclaré." }
```
