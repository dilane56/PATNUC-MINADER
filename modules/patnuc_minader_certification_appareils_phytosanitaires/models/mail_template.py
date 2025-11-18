from odoo import models, api

class MailTemplate(models.Model):
    _inherit = 'mail.template'
    
    @api.model
    def _get_phytosanitary_context(self):
        """Contexte spécifique pour les templates phytosanitaires"""
        return {
            'company_name': 'MINADER',
            'department': 'DRIPA',
            'contact_email': 'dripa@minader.cm',
            'contact_phone': '+237 222 23 45 67'
        }