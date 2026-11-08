# Rapport : choix algorithmiques et résultats des tests

## 1. Chaîne de traitement

```
saisie -> validation -> normalisation -> lexer -> parser (AST) -> AFN (Thompson) -> AFD (sous-ensembles) -> AFD minimal (Moore) -> simulation
```

| Étape | Module | Choix |
|-------|--------|-------|
| Alphabet | `validators/alphabet_validator.py` | Symboles = lettres ASCII ou chiffres uniquement. Cela exclut par construction opérateurs, accolades, espaces, caractères de contrôle et caractères Unicode ambigus (epsilon grec, euro, caractères d'aspect similaire). `ε` donne une erreur dédiée ; `€` est refusé comme tout symbole non alphanumérique. |
| Lexer | `core/lexer.py` | Normalisation NFC. Seul `ε` produit le token `EPSILON` ; `€` est un caractère ordinaire (token `CHAR`), donc refusé s'il ne figure pas dans l'alphabet. |
| Parser | `core/parser.py` | Descente récursive sur la grammaire `expr ::= term ('\|' term)*`, `term ::= factor+`, `factor ::= atom '*'?`, `atom ::= CHAR \| ε \| '(' expr ')'`. Produit un arbre (dataclasses). Aucune évaluation de la saisie, jamais de `eval`/`exec`. |
| AFN | `core/nfa.py` | Construction de Thompson (symbole, ε, concaténation, union, étoile). Sérialisé par `core/serializer.py` (clé `nfa`) : états renommés `s0, s1…` en parcours en largeur (ordre déterministe), transitions ε notées « ε » et passant après les symboles ; une transition a une liste de cibles. Affiché comme première vue. |
| AFD | `core/dfa.py` | Sous-ensembles avec ε-fermeture. État final si l'ensemble contient l'état d'acceptation de l'AFN. Les états sont nommés `q0, q1…` dans l'ordre de découverte (parcours en largeur, alphabet trié) : résultat déterministe et reproductible. Pas d'état puits : une transition absente = rejet. |
| AFD minimal | `core/minimizer.py` | Raffinement de partition (Moore) : l'AFD est complété en interne par un état puits, partitionné (finals / non finals, puis raffinement par signature des classes cibles) jusqu'à stabilité. Le puits et les états équivalents à lui (aucun final atteignable) sont retirés, pour respecter la convention « pas d'état puits ». États renommés `q0, q1…` en parcours en largeur (alphabet trié) : résultat déterministe. Complexité O(n²·\|Σ\|), avec n ≤ 300. |
| Simulation | `core/simulation.py` | Part de l'état initial ; le mot vide n'est accepté que si l'état initial est final. Transition manquante = rejet, sans exception. |

Comme `(a|b)*abb` donne 5 états (q0..q4), on retrouve l'AFD classique des manuels ; sa version minimale en compte 4 (deux états équivalents sont fusionnés).

## 2. Sécurité

- Validation **systématique** côté serveur (schéma JSON strict : propriétés exactes, types, tailles).
- Limites dans `config.py` : requête 4 Ko, alphabet 26 symboles, regex 200 caractères, mot 1000 caractères,
  imbrication 50, AFD 300 états, calcul 2 s.
- Identifiants d'automates : `secrets.token_urlsafe(16)`, durée de vie 30 min, 500 automates maximum.
- Limiteur de débit : 60 requêtes/minute/IP → 429.
- Erreurs : messages contrôlés pour l'utilisateur ; les exceptions inattendues sont journalisées et
  renvoyées en message générique (500), sans chemin ni trace.
- Frontend : aucun `innerHTML`, tout passe par `textContent` ; en-têtes `Content-Security-Policy`,
  `X-Content-Type-Options`, `X-Frame-Options`.
- Le module `re` de Python n'est utilisé **que dans les tests**, comme oracle de comparaison ; jamais sur une saisie utilisateur.

## 3. Résultats des tests (`python -m pytest`)

**211 tests** (à lancer avec `python -m pytest` ; les tests d'API de `test_security.py` nécessitent Flask).

| Fichier | Tests | Contenu |
|---------|------:|---------|
| `test_alphabet.py` | 30 | vide, doublons, séparateurs, caractères interdits, taille max, ε et € refusés, formats `{a,b}` / `a,b` |
| `test_regex.py` | 40 | arbre syntaxique, priorités, parenthèses, opérateurs mal placés, symbole absent, longueur, expressions epsilon mal formées |
| `test_epsilon.py` | 35 | tableau du cahier (§7.3) restreint à ε, ε seul élément neutre, `€` refusé (expression, alphabet, mot), absence de transition ε, état initial final ssi mot vide accepté, comparaison au moteur `re` sur tous les mots de longueur ≤ 7 pour 13 expressions |
| `test_minimal.py` | 40 | nombre d'états minimal attendu, même langage que l'AFD (mots ≤ 8), minimalité (états deux à deux distinguables, aucun état mort, idempotence), nommage, absence d'état puits, sérialisation |
| `test_dfa.py` | 8 | AFD de `(a|b)*abb`, déterminisme, ε-fermetures, absence d'état puits, sérialisation de l'AFD, limites d'états et de temps |
| `test_nfa.py` | 13 | structure de l'AFN sérialisé, AFN d'un symbole, transitions ε, numérotation déterministe, cibles valides et triées, AFN simulé directement = moteur `re` (mots ≤ 6, 7 expressions), réponse d'API avec `nfa`, `dfa` et `minimal_dfa` |
| `test_simulation.py` | 12 | tableau du cahier (§7.5), symbole inconnu, mot vide, transition manquante, tests multiples |
| `test_security.py` | 33 | JSON mal formé, propriété manquante/inattendue, mauvais types, code malveillant, `€` refusé, `minimal_dfa` dans la réponse, 413, 404, expiration, 429, erreur 500 sans fuite, en-têtes de sécurité |

Vérification manuelle dans Chromium : génération de `(a|b)*abb`, affichage du graphe (flèche entrante,
double cercle final), table de transitions, champ « Affichage » (AFN par défaut, puis AFD et AFD minimale, y compris sur mobile), retour à l'AFN à chaque nouvelle génération, tests `abb` (accepté), `aba` (rejeté), mot vide (rejeté),
`abc` (erreur de symbole), `a**` et `ε` dans l'alphabet (erreurs affichées près des champs), aucune erreur console.

## 4. Améliorations possibles

- Remplacer Moore par Hopcroft (O(n·|Σ|·log n)) si les limites d'états étaient relevées.
- Stockage partagé (Redis) pour plusieurs processus.
- Opérateurs supplémentaires (`+`, `?`, classes de caractères).
