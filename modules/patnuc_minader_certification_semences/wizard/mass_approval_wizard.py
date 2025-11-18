from odoo import models, fields, api

class MassApprovalWizard(models.TransientModel):
    _name = 'certification.mass.approval.wizard'
    _description = 'Assistant d\'approbation en masse'
    
    request_ids = fields.Many2many('certification.request', string='Demandes à approuver')
    approval_notes = fields.Text('Notes d\'approbation')
    
    def action_approve_all(self):
        """Approuver toutes les demandes sélectionnées"""
        for request in self.request_ids:
            if request.state == 'technical_review':
                request.write({
                    'state': 'approved',
                    'completion_date': fields.Datetime.now(),
                    'notes': self.approval_notes
                })
                request._generate_certificate()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': f'{len(self.request_ids)} demandes approuvées avec succès.',
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }