# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FertilizerModReturnWizard(models.TransientModel):
    _name = 'fertilizer.mod.return.wizard'
    _description = 'Wizard de retour de demande de modification d\'homologation'

    mod_homologation_id = fields.Many2one('fertilizer.mod.homologation', string='Demande de modification', required=True)
    return_reason = fields.Text(string='Motif du retour', required=True)
    current_state = fields.Char(string='État actuel')
    target_state = fields.Char(string='État cible', default='draft')

    def action_confirm_return(self):
        """Confirmer le retour avec motif"""
        if not self.return_reason:
            raise ValidationError(_("Le motif du retour est obligatoire."))
        
        # Mise à jour de la demande
        self.mod_homologation_id.write({
            'state': self.target_state,
            'return_reason': self.return_reason,
            'returned_by_user_id': self.env.user.id,
            'returned_from_state': self.current_state
        })
        
        # Log dans le chatter
        target_label = 'au brouillon' if self.target_state == 'draft' else 'au dossier reçu'
        self.mod_homologation_id.message_post(
            body=_("Retour %s depuis l'étape %s - Motif: %s") % (target_label, self.current_state, self.return_reason)
        )
        
        # Notification au demandeur ou à l'utilisateur concerné
        if self.target_state == 'draft' and self.homologation_id.create_uid:
            # Notification au demandeur
            message = _("Votre demande de modification d'homologation %s a été retournée au brouillon.\n\nMotif: %s") % (
                self.mod_homologation_id.name, self.return_reason
            )
            partner_ids = [self.mod_homologation_id.create_uid.partner_id.id]
        elif self.target_state == 'recue':
            # Notification à l'utilisateur agissant à l'étape 'recue' (agent_SRE)
            message = _("La demande de modification d'homologation %s a été retournée à l'étape dossier reçu.\n\nMotif: %s") % (
                self.mod_homologation_id.name, self.return_reason
            )
            # Notifier tous les utilisateurs du groupe agent_SRE
            sre_group = self.env.ref('patnuc_minader_homologation_engrais_fertilisants.group_agent_SRE', raise_if_not_found=False)
            partner_ids = sre_group.users.mapped('partner_id.id') if sre_group else []
        elif self.target_state == 'verification':
            # Notification au groupe de vérification administrative (agent_SRE)
            message = _("La demande  de modification d'homologation %s a été retournée à l'étape de vérification administrative.\n\nMotif: %s") % (
                self.mod_homologation_id.name, self.return_reason
            )
            # Notifier tous les utilisateurs du groupe agent_SRE
            sre_group = self.env.ref('patnuc_minader_homologation_engrais_fertilisants.group_agent_SRE', raise_if_not_found=False)
            partner_ids = sre_group.users.mapped('partner_id.id') if sre_group else []
        else:
            message = _("Votre demande de modification d'homologation %s a été retournée.\n\nMotif: %s") % (
                self.mod_homologation_id.name, self.return_reason
            )
            partner_ids = [self.mod_homologation_id.create_uid.partner_id.id] if self.mod_homologation_id.create_uid else []
        if partner_ids:
            self.mod_homologation_id.message_post(
                body=message,
                partner_ids=partner_ids,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fertilizer.mod.homologation',
            'view_mode': 'form',
            'res_id': self.mod_homologation_id.id,
            'target': 'current',
        }