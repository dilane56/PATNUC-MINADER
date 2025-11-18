{
    'name': "PATNUC MINADER Base",
    'version': '1.0',
    'summary': "Module de base contenant les données communes (zones géographiques)",
    'description': "Ce module définit les régions, départements et arrondissements du Cameroun à utiliser dans tous les modules MINADER.",
    'author': "PATNUC Team",
    'category': 'Base',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/location_views.xml',
        'data/location_data.xml',
    ],
    'installable': True,
    'application': False,
}
