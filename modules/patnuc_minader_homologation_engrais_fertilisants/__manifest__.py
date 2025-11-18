{
    'name': 'Gestion de l\'Homologation des Engrais et Fertilisants',
    'version': '1.7',
    'summary': 'Module pour gérer la procédure d\'homologation des engrais et fertilisants',
    'description': """
        Ce module permet de gérer l'ensemble du processus d'homologation des engrais et fertilisants
        conformément à la réglementation camerounaise.
    """,
    'author': 'Francesca MBOUEMBE',
    'website': 'https://www.iccsoft.com',
    'category': 'Agriculture',
    'depends': ['base', 'mail'],
    'data': [
        #security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        #data
        'data/fertilizer_homologation_data.xml',
        
        #views
        'views/fertilizer_product_views.xml',
        'views/laboratory_analysis_views.xml',
        'views/field_test_views.xml',
        'views/economic_evaluation_views.xml',
        'views/fertilizer_homologation_views.xml',
        'views/fertilizer_mod_homologation_views.xml',
        'views/fertilizer_renew_homologation_views.xml',
        'views/fertilizer_suspend_views.xml',
        'views/arrete_homologation_views.xml',
        'views/menu_views.xml',
        
        #wizard
        'wizard/document_preview_wizard_views.xml',
        'wizard/return_wizard_views.xml',
        'wizard/return_mod_wizard_views.xml',
        'wizard/return_renew_wizard_views.xml',
        'wizard/rejection_wizard_views.xml',
        'wizard/rejection_mod_wizard_views.xml',
        'wizard/rejection_renew_wizard_views.xml',
        'wizard/certificate_wizard_view.xml',
        
        #reports
        'reports/homologation_certificate_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}