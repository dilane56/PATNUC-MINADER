# (Q) Wizard créé pour gérer le rejet des demandes à l'étape vérification
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class InfrastructureRejectionWizard(models.TransientModel):
    _name = 'infrastructure.rejection.wizard'
    _description = 'Wizard de rejet de demande'

    # (Q) Champs du wizard pour le rejet
    request_id = fields.Many2one('infrastructure.financing.request', string='Demande', required=True)
    rejection_reason = fields.Text(string='Motif du rejet', required=True)
    current_state = fields.Char(string='État actuel', help='État de la demande avant rejet')

    # (Q) Action de validation du rejet modifiée pour passer en état rejeté
    def action_confirm_rejection(self):
        """Confirmer le rejet avec motif et passage en état rejeté"""
        if not self.rejection_reason:
            raise ValidationError(_("Le motif du rejet est obligatoire."))
        
        # (Q) Mise à jour de la demande : passage en état rejeté avec sauvegarde de l'état précédent
        self.request_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'previous_state': self.current_state or self.request_id.state,
            'rejected_by_user_id': self.env.user.id,
            'rejected_from_state': self.current_state or self.request_id.state
        })
        
        # (Q) Log dans le chatter avec le motif
        self.request_id._log_action(f"Rejet depuis l'étape {self.current_state} - Motif: {self.rejection_reason}")
        
        # (Q) Notification au demandeur par message dans le chatter
        if self.request_id.create_uid:
            message = _("Votre demande %s a été rejetée.\n\nMotif: %s") % (self.request_id.name, self.rejection_reason)
            self.request_id.message_post(
                body=message,
                partner_ids=[self.request_id.create_uid.partner_id.id],
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Demande rejetée"),
                'message': _("La demande a été rejetée et le demandeur a été notifié."),
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