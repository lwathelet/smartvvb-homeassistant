# SmartVVB pour Home Assistant

*[English](README.md) · Français · [Nederlands](README.nl.md)*

[![Validate](https://github.com/lwathelet/smartvvb-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/lwathelet/smartvvb-homeassistant/actions/workflows/validate.yml)

Surveillez et contrôlez votre chauffe-eau [SmartVVB](https://smartvvb.no) depuis Home Assistant.

Ceci est l'équivalent Home Assistant de l'application SmartVVB pour Homey : même backend, mêmes fonctionnalités.

## Fonctionnalités

**Chauffe-eau** (un par appareil) :
- Température actuelle de l'eau et consigne réglée sur le potentiomètre du chauffe-eau (lecture seule)
- Mode de fonctionnement et mode absence

**Capteurs :**
- Température de l'eau, puissance instantanée, énergie consommée aujourd'hui, coût du jour (NOK)
- Eau chaude disponible et eau utilisée aujourd'hui, en litres
- Force du signal WiFi (désactivé par défaut, à activer dans les paramètres de l'entité)

« Énergie aujourd'hui » peut être ajouté au **tableau de bord Énergie** de Home Assistant.

**Capteurs binaires :**
- Chauffe en cours : actif lorsque le chauffe-eau consomme de l'énergie
- Sécurité de l'eau : Sûr / Dangereux (indicateur anti-légionellose)

**Contrôle :**
- Sélecteur de mode : Off, Away, Economy, Standard, Comfort, Auto, Always on
- Boutons Forcer la marche / Forcer l'arrêt (dérogation temporaire de 2 heures, voir remarque ci-dessous)
- Énergie maximale par heure (désactivé par défaut, à activer dans les paramètres de l'entité)

**Action `smartvvb.set_max_energy_schedule` :** définit une puissance maximale (W) pour chacune des 24 heures de la journée, 0 bloquant une heure. Pratique avec une intégration de prix de l'électricité pour éviter les heures chères :

```yaml
action: smartvvb.set_max_energy_schedule
data:
  device_id: <votre appareil SmartVVB>
  hours: [2000, 2000, 2000, 2000, 2000, 2000, 0, 0, 0, 2000, 2000, 2000,
          2000, 2000, 2000, 2000, 0, 0, 0, 0, 2000, 2000, 2000, 2000]
```

**Diagnostics :** page de l'appareil → ⋮ → Télécharger les diagnostics (les identifiants sont retirés).

**Mises à jour :** interrogation (polling) du cloud SmartVVB toutes les minutes (le backend enregistre un échantillon par minute). Aucun webhook ni accès externe à Home Assistant n'est nécessaire.

## Important : Forcer marche/arrêt est une dérogation de 2 heures, pas un interrupteur

Le point d'accès `/ForceDevice` du backend est documenté comme « force device for 2 hours ». Il s'agit d'une dérogation temporaire par-dessus le mode actif, pas d'un état marche/arrêt permanent. C'est pourquoi cette intégration l'expose sous forme de deux **boutons**, et non d'une entité `switch` : un interrupteur implique un état stable et lisible, ce qui n'est pas le cas ici.

## Installation

### HACS (recommandé)

[![Ouvrez votre instance Home Assistant et ce dépôt dans HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lwathelet&repository=smartvvb-homeassistant&category=integration)

Ou manuellement dans HACS :
1. HACS → ⋮ → Dépôts personnalisés → ajoutez `https://github.com/lwathelet/smartvvb-homeassistant`, type « Intégration ».
2. Recherchez « SmartVVB », téléchargez-la, puis redémarrez Home Assistant.

### Manuelle
Copiez `custom_components/smartvvb` dans le dossier `custom_components` de votre Home Assistant, puis redémarrez.

## Configuration
Paramètres → Appareils et services → Ajouter une intégration → SmartVVB → saisissez votre nom d'utilisateur et mot de passe SmartVVB.

Seul le jeton d'accès obtenu est enregistré (le jeton du backend n'expire pas) ; votre mot de passe n'est jamais stocké.

## Plusieurs appareils
Si votre compte possède plusieurs appareils SmartVVB, chacun reçoit automatiquement son propre jeu d'entités après la configuration. Inutile d'ajouter l'intégration plusieurs fois.

## Assistance
Signalez les problèmes dans les [issues GitHub](https://github.com/lwathelet/smartvvb-homeassistant/issues). Joindre le fichier de diagnostics aide beaucoup.
