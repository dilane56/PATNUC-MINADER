# (Q) Wizard créé pour gérer le retour des demandes à l'étape vérification
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class InfrastructureReturnWizard(models.TransientModel):
    _name = 'infrastructure.return.wizard'
    _description = 'Wizard de retour de demande'

    # (Q) Champs du wizard pour le retour
    request_id = fields.Many2one('infrastructure.financing.request', string='Demande', required=True)
    return_reason = fields.Text(string='Motif du retour', required=True)
    current_state = fields.Char(string='État actuel', help='État de la demande avant retour')

    # (Q) Action de validation du retour modifiée pour retourner à l'étape précédente
    def action_confirm_return(self):
        """Confirmer le retour avec motif vers l'étape précédente"""
        if not self.return_reason:
            raise ValidationError(_("Le motif du retour est obligatoire."))
        
        # Déterminer l'étape de retour selon l'étape actuelle
        current_state = self.current_state or self.request_id.state
        if current_state == 'technical_support':
            return_to_state = 'verification'
        elif current_state == 'verification':
            return_to_state = 'draft'
        elif current_state == 'final_decision':
            return_to_state = 'review'
        else:
            return_to_state = 'draft'
        
        # Mise à jour de la demande
        self.request_id.write({
            'state': return_to_state,
            'return_reason': self.return_reason,
            'returned_by_user_id': self.env.user.id,
            'returned_from_state': current_state
        })
        
        # Log dans le chatter avec le motif
        self.request_id._log_action(f"Retour depuis l'étape {current_state} vers {return_to_state} - Motif: {self.return_reason}")
        
        # (Q) Notification au demandeur
        self.request_id._send_notification('return_verification')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Demande retournée"),
                'message': _("La demande a été retournée au demandeur pour correction."),
                'type': 'warning',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'infrastructure.financing.request',
                    'view_mode': 'form',
                    'views': [[False, 'form']],
                    'res_id': self.request_id.id,
                    'target': 'current',
                },
            }
        }