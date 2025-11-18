from odoo import models, fields, api

class MassValidationWizard(models.TransientModel):
    _name = 'phytosanitary.mass.validation.wizard'
    _description = 'Assistant de Validation en Masse'

    # request_ids = fields.Many2many('phytosanitary.certification.request', 
    #                                string='Demandes à valider')
    
    request_ids = fields.Many2many(
        'phytosanitary.certification.request',
        'phyto_certif_request_mass_wizard_rel',  # 🔧 nom de table plus court
        'wizard_id', 'request_id',
        string="Demandes"
    )
    
    
    action_type = fields.Selection([
        ('approve', 'Approuver'),
        ('reject', 'Rejeter'),
        ('move_next_stage', 'Passer à l\'étape suivante')
    ], string='Action', required=True, default='move_next_stage')
    
    comments = fields.Text('Commentaires')
    
    def action_apply(self):
        """Appliquer l'action sur toutes les demandes sélectionnées"""
        for request in self.request_ids:
            if self.action_type == 'approve':
                if request.state == 'admin_check':
                    request.action_technical_review()
                elif request.state == 'technical_review':
                    request.action_technical_evaluation()
                # etc.
            elif self.action_type == 'reject':
                request.write({
                    'state': 'rejected',
                    'rejection_reason': self.comments
                })
            elif self.action_type == 'move_next_stage':
                request._move_to_next_stage()
        
        return {'type': 'ir.actions.act_window_close'}