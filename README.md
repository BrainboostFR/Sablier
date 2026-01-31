# Hourglass Overlay

Une application de sablier élégante et minimaliste développée avec Python et PySide6. Cet outil crée une fenêtre flottante semi-transparente sur votre écran qui s'écoule en temps réel.

## Fonctionnalités

- Toujours au-dessus : Le sablier reste visible au-dessus des autres fenêtres.
- Interactif : Cliquez sur le sablier pour le retourner et réinitialiser le temps.
- Mobile : Faites glisser le sablier n'importe où sur votre écran (la position est sauvegardée).
- Personnalisable : Réglez la taille (32px à 128px) et la durée via le menu des réglages.
- Intégration Système : Icône dans la barre des tâches pour accéder aux réglages ou quitter proprement.
- Animations Fluides : Rotation animée lors du retournement et système de particules pour le sable.

## Installation

### Prérequis
* Python 3.8 ou supérieur

1. Installez les dépendances :
   pip install -r requirements.txt

2. Lancez l'application :
   python main.py

## Utilisation

- Déplacer : Clic gauche maintenu pour glisser l'objet.
- Retourner : Clic gauche simple pour inverser le sablier.
- Réglages : Faites un clic droit sur l'icône de l'application dans la zone de notification (System Tray) et sélectionnez "Réglages".