# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CertificationReturnWizard(models.TransientModel):
    _name = 'certification.return.wizard'
    _description = 'Wizard de retour '

    certification_request_id = fields.Many2one('certification.request', string='Demande', required=True)
    return_reason = fields.Text(string='Motif du retour', required=True)
    current_state = fields.Char(string='État actuel')
    target_state = fields.Char(string='État cible', default='draft')

    def action_confirm_return(self):
        """Confirmer le retour avec motif"""
        if not self.return_reason:
            raise ValidationError(_("Le motif du retour est obligatoire."))
        
        # Mise à jour de la demande
        self.certification_request_id.write({
            'state': self.target_state,
            'return_reason': self.return_reason,
            'retuned_by': self.env.user.id,
            'returned_from_state': self.current_state,
            'return_date': fields.Datetime.now()
        })
        
        # Log dans le chatter
        target_label = 'au brouillon' if self.target_state == 'draft' else 'au dossier reçu'
        self.certification_request_id.message_post(
            body=_("Retour %s depuis l'étape %s - Motif: %s") % (target_label, self.current_state, self.return_reason)
        )
        
        # Notification au demandeur ou à l'utilisateur concerné

       # partner_ids = []
        if self.target_state == 'draft' and self.certification_request_id.create_uid:
            # Notification au demandeur
            message = _("Votre demande d'homologation %s a été retournée au brouillon.\n\nMotif: %s") % (
                self.certification_request_id.name, self.return_reason
            )
            partner_ids = [self.certification_request_id.create_uid.partner_id.id]
        elif self.target_state == 'doc_verification':
            # Notification à l'utilisateur agissant à l'étape 'recue' (agent_SRE)
            message = _("La demande d'homologation %s a été retournée à l'étape de verification de document.\n\nMotif: %s") % (
                self.certification_request_id.name, self.return_reason
            )
            partner_ids = [self.certification_request_id.create_uid.partner_id.id]
        else:
            message = _("Votre demande d'homologation %s a été retournée.\n\nMotif: %s") % (
                self.certification_request_id.name, self.return_reason
            )
            partner_ids = [self.certification_request_id.create_uid.partner_id.id] if self.certification_request_id.create_uid else []

        if partner_ids:
            self.certification_request_id.message_post(
                body=message,
                partner_ids=partner_ids,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'certification.request',
            'view_mode': 'form',
            'res_id': self.certification_request_id.id,
            'target': 'current',
        }