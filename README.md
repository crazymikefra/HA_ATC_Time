# ATC Time Sync

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Validate](https://github.com/crazymikefra/HA_ATC_Time/actions/workflows/validate.yml/badge.svg)](https://github.com/crazymikefra/HA_ATC_Time/actions/workflows/validate.yml)

Intégration Home Assistant qui met à l'heure les capteurs Bluetooth sous firmware ATC / pvvx (LYWSD03MMC, etc.).

La connexion passe par la pile Bluetooth de Home Assistant : un adaptateur local ou un proxy Bluetooth ESPHome fonctionnent indifféremment.

## Prérequis

- Home Assistant 2024.8 ou plus récent
- L'intégration **Bluetooth** active, avec au moins un adaptateur ou un proxy capable de se connecter (proxy ESPHome en mode `active: true`)

## Installation

### Avec HACS (recommandé)

1. Dans HACS, menu ⋮ → **Dépôts personnalisés**
2. Ajoutez `https://github.com/crazymikefra/HA_ATC_Time`, catégorie **Intégration**
3. Installez **ATC Time Sync**, puis redémarrez Home Assistant

### Manuelle

Copiez le dossier `custom_components/atc_time` dans `config/custom_components/`, puis redémarrez Home Assistant.

## Configuration

Ajoutez dans `configuration.yaml` :

```yaml
atc_time:
```

puis redémarrez Home Assistant.

## Actions

### `atc_time.set_atc_time`

Envoie l'heure locale de Home Assistant au capteur.

```yaml
action: atc_time.set_atc_time
data:
  device_address: A4:C1:38:63:21:1D
  wait_time: 30   # optionnel, délai maximal en secondes
```

Exemple d'automatisation, mise à l'heure chaque nuit :

```yaml
automation:
  - alias: Mise à l'heure du capteur salon
    triggers:
      - trigger: time
        at: "03:00:00"
    actions:
      - action: atc_time.set_atc_time
        data:
          device_address: A4:C1:38:63:21:1D
```

### `atc_time.get_characteristics`

Liste les services et caractéristiques GATT du capteur et renvoie leurs valeurs (utile pour le diagnostic). À lancer depuis **Outils de développement → Actions** pour voir la réponse.

## Licence

Distribué sous licence MIT, voir [LICENSE](LICENSE).
