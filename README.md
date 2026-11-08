# Générateur d'AFD à partir d'une expression régulière

Application web (Flask + HTML/CSS/JS + Cytoscape.js) qui construit, à partir d'une expression
régulière, l'**AFN** (méthode de Thompson), l'**automate fini déterministe** (AFD) et l'**AFD minimale**,
et permet de tester des mots (mot vide inclus). Un champ « Affichage » choisit ce qui est montré :
l'AFN (par défaut), l'AFD ou l'AFD minimale.

## Installation

Prérequis : Python 3.9 ou plus récent.

```bash
cd afd-regex-app
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Exécution

```bash
cd backend
python app.py
```

Ouvrir <http://127.0.0.1:5000>. Flask sert aussi le frontend : aucun autre serveur n'est nécessaire.
Cytoscape.js est fourni dans `frontend/js/vendor/` (fonctionne hors connexion).

## Utilisation

1. Alphabet : `{a,b}` ou `a,b` (lettres ou chiffres, un caractère chacun).
2. Expression : `(a|b)*abb`. Opérateurs : `|`, `*`, `( )`, concaténation. `ε` = mot vide
   (bouton d'insertion fourni). `ε` est le **seul** élément neutre : `€` n'a aucun rôle particulier
   et est refusé comme tout symbole absent de l'alphabet.
3. « Générer l'automate » affiche d'abord l'**AFN**. Le champ **Affichage** permet de passer à
   « Voir l'AFD » ou « Voir l'AFD minimale » (une seule vue à la fois). Les transitions ε de l'AFN sont
   en pointillés.
4. Tester des mots : le test s'exécute sur l'AFD ; son parcours est surligné quand la vue « AFD » est affichée.
   **Champ vide = mot vide.**

## Tests

```bash
cd backend
python -m pytest -v
```

## Structure

```
backend/
  app.py, config.py            application Flask, limites de sécurité
  routes/automate_routes.py    endpoints API
  core/                        alphabet, lexer, parser, nfa, dfa, minimizer, simulation, serializer, pipeline
  validators/                  validation alphabet / regex / mot / requête
  utils/                       erreurs, stockage temporaire, limiteur de débit, helpers texte
  tests/                       tests pytest
frontend/
  index.html, css/, js/        interface (js/vendor/ = Cytoscape.js)
docs/API.md                    documentation des endpoints
docs/RAPPORT.md                choix algorithmiques et résultats des tests
```

## Limites connues

- Les automates sont stockés **en mémoire** (30 min) : un redémarrage ou plusieurs workers les perdent.
  Lancez un seul processus (ex. `gunicorn -w 1 --threads 4 "app:create_app()"`) ou ajoutez Redis.
- Derrière un proxy inverse, le limiteur de débit voit l'IP du proxy (utiliser `ProxyFix`).
- Les AFD (complet de sous-ensembles et minimal) n'ont pas d'état puits : une transition absente
  signifie « rejet ».
