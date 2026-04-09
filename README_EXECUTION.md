# Guide d'execution - Frontend Localis

Ce fichier explique comment lancer le frontend en local.

## 1. Prerequis

- Node.js (version 18+ recommandee)
- npm (installe avec Node.js)

Verification rapide:

```bash
node -v
npm -v
```

## 2. Aller dans le dossier frontend

Depuis la racine du projet:

```bash
cd src/frontend
```

## 3. Installer les dependances

```bash
npm install
```

## 4. Lancer l'application

```bash
npm start
```

Le site sera accessible sur:

- http://localhost:5173

## 5. Generer la version production (optionnel)

```bash
npm run build
```

Le build sera genere dans le dossier `dist`.

## 6. Arreter le serveur

Dans le terminal ou l'application tourne:

- `Ctrl + C`

## Probleme frequent

Si le port 5173 est deja utilise, arretez le processus qui l'occupe ou relancez apres l'avoir libere.
