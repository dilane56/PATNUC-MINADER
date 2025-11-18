# Modification du Workflow - Suppression de l'étape "Reçue"

## Changements apportés

### Ancien workflow :
1. **Dépôt du dossier** (draft)
2. ~~**Reçue** (submitted)~~ ← **SUPPRIMÉE**
3. **Vérification & Conformité** (verification)
4. **Appui Technique** (technical_support)
5. **Revue et Compilation** (review)
6. **Décision Finale** (final_decision)
7. **Approuvée** (approuvee)
8. **Rejetée** (rejected)

### Nouveau workflow :
1. **Dépôt du dossier** (draft)
2. **Vérification & Conformité** (verification) ← **DIRECTEMENT**
3. **Appui Technique** (technical_support)
4. **Revue et Compilation** (review)
5. **Décision Finale** (final_decision)
6. **Approuvée** (approuvee)
7. **Rejetée** (rejected)

## Modifications techniques

### Dans le modèle (`infrastructure_financing_request.py`) :
- **Suppression de l'état** `('submitted', 'Reçue')` de la sélection `state`
- **Modification de `action_submit()`** : passe directement à l'état `'verification'`
- **Suppression de `action_verification()`** : méthode devenue inutile
- **Nettoyage des références** à `'submitted'` dans les méthodes de retour

### Dans les vues (`infrastructure_financing_request_view.xml`) :
- **Suppression des boutons** :
  - `action_verification` (passer à la vérification)
  - `action_return_to_draft` (retourner au dépôt depuis reçue)
- **Nettoyage des conditions** de visibilité dans l'onglet Appui Technique
- **Pas de filtre de recherche** pour l'état "Reçue" (déjà absent)

## Impact sur l'utilisation

### Nouveau comportement :
1. **Création de la demande** : État = "Dépôt du dossier"
2. **Clic sur "Soumettre"** : État passe directement à "Vérification & Conformité"
3. **Plus d'étape intermédiaire** : Gain de temps dans le processus

### Avantages :
- **Simplification du workflow** : Une étape en moins
- **Gain de temps** : Pas d'action manuelle supplémentaire
- **Logique métier** : La vérification commence dès la soumission

### Boutons disponibles après soumission :
- **"passer a l'Appui Technique"** : Pour continuer le processus
- **"Retourner"** : Pour retourner au dépôt (avec wizard)
- **"Rejeter"** : Pour rejeter la demande (avec wizard)

## Compatibilité

### Données existantes :
- Les demandes existantes avec l'état `'submitted'` devront être mises à jour manuellement
- Recommandation : Exécuter une requête SQL pour migrer les états :
  ```sql
  UPDATE infrastructure_financing_request 
  SET state = 'verification' 
  WHERE state = 'submitted';
  ```

### Tests recommandés :
1. Créer une nouvelle demande
2. Vérifier que "Soumettre" passe directement à "Vérification"
3. Tester les boutons de retour et rejet
4. Vérifier que le workflow continue normalement

## Notes importantes

- **Aucun impact** sur les autres étapes du workflow
- **Aucun impact** sur les droits d'accès et groupes de sécurité
- **Aucun impact** sur les documents requis et la logique métier
- **Amélioration** de l'expérience utilisateur par simplification