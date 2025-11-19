{
    'name': 'PATNUC - MINADER_Certification Appareils Phytosanitaires',
    'version': '17.0.1.0.0',
    'category': 'Agriculture',
    'summary': 'Gestion de la certification des appareils de traitement phytosanitaire',
    'description': """
        Module pour digitaliser la procédure de certification des appareils 
        de traitement phytosanitaire selon les normes du MINADER.
        
        Fonctionnalités:
        - Gestion des demandes de certification
        - Workflow de validation en 8 étapes
        - Documents requis et générés
        - Notifications automatiques
        - Rapports et certificats
    """,
    'author': 'Francesca MBOUEMBE - MFD',
    'website': 'https://www.iccsoft.cm',
    'depends': ['base', 'mail', 'portal'],
    'data': [
        #security
        'security/security.xml',
        'security/ir.model.access.csv',
        
        #reports
        'reports/certificate_report.xml',
        'reports/technical_report.xml',
        
        #data

        'data/sequence.xml',
        'data/mail_templates.xml',
        
        #views
        'views/certification_request_views.xml',
        'views/equipment_views.xml',
        'views/technical_evaluation_views.xml',
        'views/document_views.xml',
        'views/operator_views.xml',
        'views/agreement_views.xml',
        'views/portal_templates.xml',
        'views/menu_views.xml',
                
        #wizards
        'wizards/mass_validation_wizard_views.xml',
        'wizards/rejection_wizard_views.xml',
        'wizards/return_wizard_view.xml',
        'wizards/document_preview_wizard_views.xml',
        
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}