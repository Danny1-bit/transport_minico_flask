# MiniCo - Optimisation du transport avec la méthode MINICO

MiniCo est une application web Flask permettant de résoudre des problèmes de transport par la méthode MINICO et d'optimiser la solution avec la méthode Stepping Stone.

## Fonctionnalités
- Saisie interactive des données de transport (fournisseurs, clients, coûts)
- Calcul automatique de la solution MINICO
- Optimisation par la méthode Stepping Stone
- Visualisation graphique des allocations
- Guide explicatif de la méthode MINICO

## Installation

1. **Cloner le dépôt**
```bash
git clone <url-du-repo>
cd transport_minico_flask
```

2. **Créer un environnement virtuel (optionnel mais recommandé)**
```bash
python -m venv env
source env/bin/activate  # Sur Windows : env\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install flask numpy networkx matplotlib
```

## Lancement de l'application

```bash
python transport_minico_flask/app.py
```

L'application sera accessible sur [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Structure du projet

- `transport_minico_flask/app.py` : Application Flask principale
- `transport_minico_flask/templates/` : Templates HTML (pages web)
- `transport_minico_flask/static/` : Fichiers statiques (CSS, images)

## Auteurs
- KEVIN ET DANNY

## Licence
Ce projet est proposé à des fins pédagogiques. 