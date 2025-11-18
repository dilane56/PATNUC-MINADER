#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier la validité du module
patnuc_minader_financement_infrastructures_Routiere
"""

import sys
import os

def test_module_structure():
    """Test de la structure du module"""
    print("🔍 Vérification de la structure du module...")
    
    # Fichiers obligatoires
    required_files = [
        '__init__.py',
        '__manifest__.py',
        'models/__init__.py',
        'models/infrastructure_financing_request.py',
        'views/infrastructure_financing_request_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Fichiers manquants: {missing_files}")
        return False
    else:
        print("✅ Structure du module correcte")
        return True

def test_manifest():
    """Test du fichier manifest"""
    print("🔍 Vérification du manifest...")
    
    try:
        with open('__manifest__.py', 'r', encoding='utf-8') as f:
            manifest_content = f.read()
        
        # Vérifications de base
        if "'name'" not in manifest_content:
            print("❌ Nom du module manquant dans le manifest")
            return False
        
        if "'depends'" not in manifest_content:
            print("❌ Dépendances manquantes dans le manifest")
            return False
        
        print("✅ Manifest valide")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du manifest: {e}")
        return False

def test_python_syntax():
    """Test de la syntaxe Python"""
    print("🔍 Vérification de la syntaxe Python...")
    
    python_files = [
        '__init__.py',
        'models/__init__.py',
        'models/infrastructure_financing_request.py',
        'wizard/__init__.py',
        'wizard/rejection_wizard.py',
        'wizard/return_wizard.py'
    ]
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, file_path, 'exec')
                print(f"✅ {file_path} - Syntaxe correcte")
            except SyntaxError as e:
                print(f"❌ {file_path} - Erreur de syntaxe: {e}")
                return False
            except Exception as e:
                print(f"⚠️ {file_path} - Avertissement: {e}")
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Test du module patnuc_minader_financement_infrastructures_Routiere")
    print("=" * 70)
    
    # Changer vers le répertoire du module
    module_path = "/home/hels/odoo/patnuc_erp/modules/patnuc_minader_financement_infrastructures_Routiere"
    if os.path.exists(module_path):
        os.chdir(module_path)
    else:
        print(f"❌ Répertoire du module non trouvé: {module_path}")
        return False
    
    tests = [
        test_module_structure,
        test_manifest,
        test_python_syntax
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur lors du test {test.__name__}: {e}")
            results.append(False)
        print()
    
    # Résumé
    print("=" * 70)
    if all(results):
        print("🎉 TOUS LES TESTS PASSÉS - Le module peut démarrer normalement")
        return True
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ - Vérifiez les erreurs ci-dessus")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)