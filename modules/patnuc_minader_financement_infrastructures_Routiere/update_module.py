#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour forcer la mise à jour du module patnuc_minader_financement_infrastructures_Routiere
Exécuter ce script depuis l'interface Odoo ou via shell
"""

def update_module():
    """Force la mise à jour du module pour synchroniser les nouveaux champs"""
    try:
        # Rechercher le module
        module = env['ir.module.module'].search([
            ('name', '=', 'patnuc_minader_financement_infrastructures_Routiere')
        ])
        
        if module:
            # Forcer la mise à jour
            module.button_immediate_upgrade()
            print("✅ Module mis à jour avec succès")
            return True
        else:
            print("❌ Module non trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return False

# Exécuter si appelé directement
if __name__ == '__main__':
    update_module()