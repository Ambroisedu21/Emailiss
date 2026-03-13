# Emailiss

Application locale de monitoring email pour suivre :

- les gros volumes d'envoi
- la cadence d'envoi
- les performances par cible
- les performances par visuel / template

## Lancer l'application

```bash
python main.py
```

Puis ouvrir [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Ce que fait ce MVP

- dashboard de synthese
- filtres par cible et statut de campagne
- suivi des volumes, open rate, click rate, bounce rate, unsubscribe rate
- comparaison des templates email
- vue detaillee des campagnes

## Suite logique

- brancher vos vraies donnees ESP/CRM
- ajouter auth et gestion multi-comptes
- historiser les snapshots et alertes
- ajouter objectifs par cible et benchmark visuel
