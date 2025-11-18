# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PhytosanitaryRejectionWizard(models.TransientModel):
    _name = 'phytosanitary.rejection.wizard'
    _description = 'Assistant de Rejet de Demande'

    request_id = fields.Many2one('phytosanitary.certification.request', 
                                 string='Demande', required=True)
    rejection_reason = fields.Text('Motif de rejet', required=True)
    
    def action_confirm_rejection(self):
        self.request_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'actual_completion_date': fields.Date.today()
        })
        
        # Envoyer notification de rejet
        template = self.env.ref('patnuc_minader_certification_appareils_phytosanitaires.phytosanitary_certification_rejected')
        template.send_mail(self.request_id.id, force_send=True)
        
        return {'type': 'ir.actions.act_window_close'}