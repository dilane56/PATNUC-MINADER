# -*- coding: utf-8 -*-
{
    'name': "Minader Financement Infrastructures Routiere",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """Gestion des demandes de financement pour infrastructures routières""",

    'author': "PATNUC",
    'website': "https://www.patnuc.cm",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Custom',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','patnuc_minader_base'],

    # always loaded
    'data': [
        
        'security/security.xml',
        'views/infrastructure_financing_request_view.xml',
        'views/infrastructure_technical_support_view.xml',
        'views/infrastructure_document_view.xml',
        'views/Infrastructure_road_view.xml',
        'views/Infrastructure_artwork_view.xml',
        'views/Infrastructure_mini_view.xml',
        'views/commune_view.xml',
        'views/delegation_view.xml',
        'views/document_preview_wizard_view.xml',
        'wizard/rejection_wizard_view.xml',  # (Q) Vue wizard ajoutée
        'wizard/return_wizard_view.xml',  # (Q) Vue wizard de retour ajoutée

        'views/menu.xml',
        'views/templates.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

