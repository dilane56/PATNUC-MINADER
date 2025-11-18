# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FertilizerRejectionWizard(models.TransientModel):
    _name = 'fertilizer.rejection.wizard'
    _description = 'Wizard de rejet de demande d\'homologation'

    homologation_id = fields.Many2one('fertilizer.homologation', string='Demande', required=True)
    rejection_reason = fields.Text(string='Motif du rejet', required=True)
    current_state = fields.Char(string='État actuel')

    def action_confirm_rejection(self):
        """Confirmer le rejet avec motif"""
        if not self.rejection_reason:
            raise ValidationError(_("Le motif du rejet est obligatoire."))
        
        # Mise à jour de la demande
        self.homologation_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'rejected_by_user_id': self.env.user.id,
            'rejected_from_state': self.current_state
        })
        
        # Log dans le chatter
        self.homologation_id.message_post(
            body=_("Rejet depuis l'étape %s - Motif: %s") % (self.current_state, self.rejection_reason)
        )
        
        # Notification au demandeur
        self.homologation_id._notify_applicant_rejection()
        if self.homologation_id.create_uid:
            message = _("Votre demande d'homologation %s a été rejetée.\n\nMotif: %s") % (
                self.homologation_id.name, self.rejection_reason
            )
            self.homologation_id.message_post(
                body=message,
                partner_ids=[self.homologation_id.create_uid.partner_id.id],
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fertilizer.homologation',
            'view_mode': 'form',
            'res_id': self.homologation_id.id,
            'target': 'current',
        }