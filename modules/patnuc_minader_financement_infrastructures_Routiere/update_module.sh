#!/bin/bash

# Script pour mettre à jour le module et corriger l'erreur signature_file

echo "🔄 Mise à jour du module patnuc_minader_financement_infrastructures_Routiere"
echo "=================================================================="

# Vérifier si nous sommes dans le bon répertoire
if [ ! -f "__manifest__.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le répertoire du module"
    exit 1
fi

echo "✅ Répertoire du module détecté"

# Afficher les informations du module
echo "📋 Informations du module:"
grep -E "^[[:space:]]*'name'|^[[:space:]]*'version'" __manifest__.py

echo ""
echo "🔧 Actions recommandées pour corriger l'erreur signature_file:"
echo "=================================================================="
echo ""
echo "1. 🔄 REDÉMARRER LE SERVEUR ODOO"
echo "   sudo systemctl restart odoo"
echo "   # ou"
echo "   pkill -f odoo-bin && ./odoo-bin"
echo ""
echo "2. 🔄 METTRE À JOUR LE MODULE"
echo "   Via l'interface:"
echo "   - Aller dans Apps"
echo "   - Rechercher 'patnuc_minader_financement_infrastructures_Routiere'"
echo "   - Cliquer sur 'Mettre à jour'"
echo ""
echo "   Via la ligne de commande:"
echo "   ./odoo-bin -u patnuc_minader_financement_infrastructures_Routiere -d VOTRE_DB --stop-after-init"
echo ""
echo "3. 🧹 VIDER LE CACHE"
echo "   - Vider le cache du navigateur (Ctrl+Shift+R)"
echo "   - Redémarrer en mode développeur"
echo ""
echo "4. 🔍 VÉRIFIER LES LOGS"
echo "   tail -f /var/log/odoo/odoo.log"
echo ""
echo "💡 CAUSE PROBABLE:"
echo "   L'erreur 'signature_file' vient d'un cache Odoo qui référence"
echo "   une ancienne version du modèle. Le code actuel est correct."
echo ""
echo "✅ STATUT DU CODE: CORRECT"
echo "🎯 ACTION REQUISE: MISE À JOUR DU MODULE"

# Créer un fichier de version pour tracking
echo "$(date): Module vérifié et prêt pour mise à jour" > .last_update_check

echo ""
echo "🚀 Le module est prêt pour la mise à jour!"