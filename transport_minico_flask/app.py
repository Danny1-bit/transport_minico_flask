from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os

app = Flask(__name__)

# ✅ Nouvelle route pour la page de MENU principal
@app.route('/')
def menu():
    return render_template("index.html")  # Ce sera ta page avec les hexagones

# ✅ Route pour afficher ton formulaire (bouton dans le menu)
@app.route('/formulaire')
def formulaire():
    return render_template("formulaire.html")

# Route pour saisir le tableau des coûts
@app.route('/saisie_tableau', methods=['POST'])
def saisie_tableau():
    nb_fournisseurs = int(request.form['fournisseurs'])
    nb_clients = int(request.form['clients'])
    return render_template("saisie_tableau.html", fournisseurs=nb_fournisseurs, clients=nb_clients)

# Route pour afficher les résultats
@app.route('/resultat', methods=['POST'])
def resultat():
    nb_fournisseurs = int(request.form['fournisseurs'])
    nb_clients = int(request.form['clients'])

    couts = []
    for i in range(nb_fournisseurs):
        ligne = []
        for j in range(nb_clients):
            val = float(request.form.get(f'cout_{i}_{j}', 0))
            ligne.append(val)
        couts.append(ligne)

    offres = [float(request.form.get(f'offre_{i}', 0)) for i in range(nb_fournisseurs)]
    demandes = [float(request.form.get(f'demande_{j}', 0)) for j in range(nb_clients)]

    couts = np.array(couts)
    allocation = np.zeros_like(couts)
    offres_restantes = offres.copy()
    demandes_restantes = demandes.copy()

    # Méthode MINICO
    for j in range(len(demandes_restantes)):
        colonne_temp = couts[:, j].copy()
        while demandes_restantes[j] > 0:
            i = np.argmin(colonne_temp)
            qte = min(offres_restantes[i], demandes_restantes[j])
            allocation[i][j] += qte
            offres_restantes[i] -= qte
            demandes_restantes[j] -= qte
            if offres_restantes[i] == 0:
                colonne_temp[i] = np.inf

    cout_total = np.sum(allocation * couts)
    graph_img = generate_graph(nb_fournisseurs, nb_clients, allocation)

    return render_template("resultat.html", couts=couts, offres=offres, demandes=demandes, allocation=allocation, cout_total=cout_total, graph_img=graph_img)

def generate_graph(nb_fournisseurs, nb_clients, allocation):
    G = nx.DiGraph()
    for i in range(nb_fournisseurs):
        G.add_node(f'F{i+1}', type='fournisseur')
    for j in range(nb_clients):
        G.add_node(f'C{j+1}', type='client')

    for i in range(nb_fournisseurs):
        for j in range(nb_clients):
            if allocation[i][j] > 0:
                G.add_edge(f'F{i+1}', f'C{j+1}', weight=allocation[i][j])

    plt.figure(figsize=(12, 8))
    pos = {}
    for i in range(nb_fournisseurs):
        pos[f'F{i+1}'] = (-1, i)
    for j in range(nb_clients):
        pos[f'C{j+1}'] = (1, j)

    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=10, font_weight='bold', edge_color='gray')
    plt.gca().invert_yaxis()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_img = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return graph_img

def stepping_stone_optimisation(couts, allocation):
    import copy
    alloc = allocation.copy()
    n, m = couts.shape
    max_iter = 1000
    for it in range(max_iter):
        # 1. Calcul des potentiels u, v
        u = [None] * n
        v = [None] * m
        u[0] = 0
        base = [(i, j) for i in range(n) for j in range(m) if alloc[i, j] > 0]
        for _ in range(n + m):
            for (i, j) in base:
                if u[i] is not None and v[j] is None:
                    v[j] = couts[i, j] - u[i]
                elif v[j] is not None and u[i] is None:
                    u[i] = couts[i, j] - v[j]
        # 2. Calcul des coûts marginaux
        delta = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                if alloc[i, j] == 0 and u[i] is not None and v[j] is not None:
                    delta[i, j] = couts[i, j] - u[i] - v[j]
        # 3. Chercher la case vide avec le coût marginal le plus négatif
        min_delta = 0
        min_pos = None
        for i in range(n):
            for j in range(m):
                if alloc[i, j] == 0 and delta[i, j] < min_delta:
                    min_delta = delta[i, j]
                    min_pos = (i, j)
        print(f"[SteppingStone] Iter {it}: min_delta={min_delta} at {min_pos}")
        # ✅ Correction : on ne continue que si min_delta < 0
        if min_pos is None or min_delta >= 0:
            print(f"[SteppingStone] Iter {it}: optimalité atteinte ou pas d'amélioration possible. Coût actuel = {np.sum(alloc * couts)}")
            break  # Optimalité atteinte ou pas d'amélioration possible
        # 4. Construire le cycle fermé alterné (+/-) passant par min_pos
        def build_cycle(start, base):
            from collections import deque
            stack = [(start, [start], set([start]), True)]  # (pos, path, visited, is_row)
            while stack:
                (i, j), path, visited, is_row = stack.pop()
                if len(path) > 3 and (i, j) == start:
                    return path
                if is_row:
                    for jj in range(m):
                        if jj != j and ((i, jj) in base or (i, jj) == start):
                            next_pos = (i, jj)
                            if next_pos not in visited or next_pos == start:
                                stack.append((next_pos, path + [next_pos], visited | {next_pos}, not is_row))
                else:
                    for ii in range(n):
                        if ii != i and ((ii, j) in base or (ii, j) == start):
                            next_pos = (ii, j)
                            if next_pos not in visited or next_pos == start:
                                stack.append((next_pos, path + [next_pos], visited | {next_pos}, not is_row))
            return None
        cycle = build_cycle(min_pos, set(base))
        if not cycle:
            print(f"[SteppingStone] Iter {it}: pas de cycle trouvé. Coût actuel = {np.sum(alloc * couts)}")
            break  # Pas de cycle trouvé
        # 5. Trouver la plus petite allocation sur les positions - du cycle (hors la case vide)
        minus_indices = [idx for idx in range(1, len(cycle), 2)]
        min_qte = min([alloc[cycle[idx][0], cycle[idx][1]] for idx in minus_indices])
        if min_qte <= 0:
            print(f"[SteppingStone] Iter {it}: min_qte <= 0. Coût actuel = {np.sum(alloc * couts)}")
            break  # Sécurité
        # 6. Appliquer le transfert sur le cycle
        old_cost = np.sum(alloc * couts)
        for idx, (i, j) in enumerate(cycle):
            if idx % 2 == 0:
                alloc[i, j] += min_qte
            else:
                alloc[i, j] -= min_qte
                if alloc[i, j] < 1e-8:
                    alloc[i, j] = 0
        new_cost = np.sum(alloc * couts)
        print(f"[SteppingStone] Iter {it}: transfert effectué, coût avant = {old_cost}, coût après = {new_cost}")
        if new_cost > old_cost + 1e-6:
            print(f"[SteppingStone] Iter {it}: ERREUR - le coût a augmenté après transfert ! Annulation et arrêt.")
            # Annuler le transfert
            for idx, (i, j) in enumerate(cycle):
                if idx % 2 == 0:
                    alloc[i, j] -= min_qte
                else:
                    alloc[i, j] += min_qte
            break
    return alloc

@app.route('/stepping_stone', methods=['POST'])
def stepping_stone():
    nb_fournisseurs = int(request.form['fournisseurs'])
    nb_clients = int(request.form['clients'])

    couts = []
    allocation = []
    for i in range(nb_fournisseurs):
        ligne_cout = []
        ligne_alloc = []
        for j in range(nb_clients):
            ligne_cout.append(float(request.form.get(f'cout_{i}_{j}', 0)))
            ligne_alloc.append(float(request.form.get(f'allocation_{i}_{j}', 0)))
        couts.append(ligne_cout)
        allocation.append(ligne_alloc)

    offres = [float(request.form.get(f'offre_{i}', 0)) for i in range(nb_fournisseurs)]
    demandes = [float(request.form.get(f'demande_{j}', 0)) for j in range(nb_clients)]

    couts = np.array(couts)
    allocation = np.array(allocation)

    # Vérification : coût de départ transmis à Stepping Stone
    cout_depart = np.sum(allocation * couts)
    # Pour comparaison, on peut aussi recalculer la solution Minico ici si besoin
    # (mais on suppose qu'elle est bien transmise)

    # Appliquer Stepping Stone
    allocation_opt = stepping_stone_optimisation(couts, allocation)
    cout_optimise = np.sum(allocation_opt * couts)

    graph_img = generate_graph(nb_fournisseurs, nb_clients, allocation_opt)

    # Message d'alerte si le coût de départ ne correspond pas à la solution Minico
    alerte = None
    if 'cout_minico' in request.form:
        cout_minico = float(request.form['cout_minico'])
        if abs(cout_depart - cout_minico) > 1e-6:
            alerte = f"Alerte : le coût de départ transmis à Stepping Stone ({cout_depart}) est différent du coût Minico ({cout_minico}) ! Vérifiez la transmission de l'allocation."
    else:
        alerte = "Alerte : le coût Minico n'a pas été transmis à la page Stepping Stone."

    message = None
    if abs(cout_optimise - cout_depart) < 1e-6:
        message = "La solution de base (Minico) est déjà optimale."

    return render_template("optimale.html", 
                           cout_optimise=cout_optimise,
                           allocation=allocation_opt,
                           couts=couts,
                           offres=offres,
                           demandes=demandes,
                           graph_img=graph_img,
                           cout_depart=cout_depart,
                           alerte=alerte,
                           message=message)

@app.route('/minico_guide')
def minico_guide():
    return render_template("minico_guide.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
