# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PhytosanitaryRejectionWizard(models.TransientModel):
    _name = 'phytosanitary.rejection.wizard'
    _description = 'Assistant de Rejet'

    request_id = fields.Many2one('phytosanitary.certification.request', string='Demande', required=True)
    rejection_reason = fields.Text('Motif de rejet', required=True)

    def action_confirm_rejection(self):
        if not self.rejection_reason:
            raise ValidationError("Le motif de rejet est obligatoire.")
        
        self.request_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason
        })
        
        return {'type': 'ir.actions.act_window_close'}