from collections import deque

ETAT_INITIAL = [7, 0, 1,
                2, 3, 5,
                4, 8, 6]


ETAT_FINAL   = [1, 2,3,
                4, 5,6,
                7, 8,0]
# -------------------------------------------------------
# Fonction 1 : Vérifier si on a atteint l'état final
# -------------------------------------------------------
def est_but(etat):
    # On compare simplement la liste courante avec l'état final
    return etat == ETAT_FINAL


# -------------------------------------------------------
# Fonction 2 : Générer les successeurs d'un état
# -------------------------------------------------------
def successeurs(etat):
    """
    Trouve toutes les grilles qu'on peut obtenir en un seul mouvement.
    On localise le 0 (case vide), puis on essaie de le déplacer dans
    chacune des 4 directions. Si le déplacement reste dans la grille,
    on échange le 0 avec la case voisine → nouvel état successeur.
    """
    resultat = []

    # Trouver l'index du 0 dans la liste (ex: index 1 = ligne 0, colonne 1)
    pos_vide = etat.index(0)
    ligne    = pos_vide // 3   # numéro de ligne   (0, 1 ou 2)
    col      = pos_vide %  3   # numéro de colonne (0, 1 ou 2)

    # Les 4 déplacements : (nom, décalage_ligne, décalage_col)
    mouvements = [
        ("haut",    -1,  0),
        ("bas",     +1,  0),
        ("gauche",   0, -1),
        ("droite",   0, +1),
    ]

    for nom, dl, dc in mouvements:
        nouvelle_ligne = ligne + dl
        nouvelle_col   = col   + dc

        # Vérifier qu'on ne sort pas de la grille 3×3
        if 0 <= nouvelle_ligne < 3 and 0 <= nouvelle_col < 3:

            # Calculer l'index de la case cible dans la liste
            pos_cible = nouvelle_ligne * 3 + nouvelle_col

            # Copier l'état et échanger le 0 avec la case cible
            nouvel_etat = etat[:]
            nouvel_etat[pos_vide], nouvel_etat[pos_cible] = \
                nouvel_etat[pos_cible], nouvel_etat[pos_vide]

            resultat.append((nom, nouvel_etat))

    return resultat


# -------------------------------------------------------
# Fonction 3 : Recherche de la solution (BFS)
# -------------------------------------------------------
def recherche(etat_initial):
    """
    Explore les états un par un (en largeur) jusqu'à trouver l'état final.
    Chaque élément de la file contient :
      - l'état courant
      - la liste des actions effectuées depuis le début (le "chemin")
    """

    # Cas trivial : on est déjà au but
    if est_but(etat_initial):
        return []

    # File d'attente BFS : on commence avec l'état initial et un chemin vide
    file = deque()
    file.append((etat_initial, []))

    # Ensemble des états déjà visités (stockés comme tuples, immuables)
    visites = {tuple(etat_initial)}

    while file:
        etat_courant, chemin = file.popleft()   # prendre le premier de la file

        # Générer tous les états accessibles en un mouvement
        for action, etat_suivant in successeurs(etat_courant):

            if tuple(etat_suivant) not in visites:
                nouveau_chemin = chemin + [action]

                # Solution trouvée !
                if est_but(etat_suivant):
                    return nouveau_chemin

                # Sinon, marquer comme visité et ajouter à la file
                visites.add(tuple(etat_suivant))
                file.append((etat_suivant, nouveau_chemin))

    return None  # aucune solution (puzzle insolvable)


# -------------------------------------------------------
# Affichage
# -------------------------------------------------------
def afficher_grille(etat, titre=""):
    if titre:
        print(f"\n{titre}")
    print("+-------+")
    for ligne in range(3):
        cases = etat[ligne*3 : ligne*3+3]
        print("| " + " ".join(str(x) if x != 0 else " " for x in cases) + " |")
    print("+-------+")


# -------------------------------------------------------
# Programme principal
# -------------------------------------------------------
if __name__ == "_main_":
    print("========================================")
    print("   Puzzle 8 — Recherche BFS")
    print("========================================")

    afficher_grille(ETAT_INITIAL, "État initial :")
    afficher_grille(ETAT_FINAL,   "État final   :")

    print("\nRecherche en cours…")
    solution = recherche(ETAT_INITIAL)

    if solution:
        print(f"\n✔ Solution trouvée en {len(solution)} coups !")
        print("Actions :", " → ".join(solution))

        # Rejouer la solution pas à pas
        print("\n--- Déroulement de la solution ---")
        etat = ETAT_INITIAL[:]
        afficher_grille(etat, "Départ")

        delta = {"haut": (-1,0), "bas": (1,0), "gauche": (0,-1), "droite": (0,1)}
        for i, action in enumerate(solution, 1):
            p  = etat.index(0)
            dl, dc = delta[action]
            j  = (p//3 + dl)*3 + (p%3 + dc)
            etat[p], etat[j] = etat[j], etat[p]
            afficher_grille(etat, f"Coup {i} : {action}")
    else:
        print("✘ Aucune solution trouvée.")
