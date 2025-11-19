from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class PhytosanitaryReturnWizard(models.TransientModel):
    _name = 'phytosanitary.return.wizard'
    _description = 'Wizard de retour de demande de certification phytosanitaire'
    _transient_max_hours = 1  # Suppression automatique après 1 heure

    certification_request_id = fields.Many2one('phytosanitary.certification.request', string='Demande', required=True)
    return_reason = fields.Text(string='Motif du retour', required=True)
    current_state = fields.Char(string='État actuel', help='État de la demande avant retour')
    
    # Champ pour stocker l'état de destination, utile pour le log
    target_state = fields.Char(string='État de destination')

    def action_confirm_return(self):
        """
        Confirmer le retour avec motif vers l'étape précédente.
        Action mise à jour pour fermer le wizard après exécution et utiliser une notification Odoo standard.
        """
        self.ensure_one()
        
        if not self.return_reason:
            raise ValidationError(_("Le motif du retour est obligatoire."))
        
        # Récupération de l'état cible via le contexte ou le champ
        target_state = self.env.context.get('target_state') or self.target_state
        current_state = self.current_state

        if not target_state:
             raise ValidationError(_("L'état de destination du retour n'a pas été spécifié. Contactez l'administrateur."))

        # Mappage des états techniques vers les libellés en français pour l'affichage utilisateur
        STATE_LABELS = {
            'draft': _('Dépôt du dossier'),
            'reception': _('Réception'),
            'technical_review': _('Instruction Technique'),
            'technical_eval': _('Évaluation Technique'),
            'admin_check': _('Traitement du dossier'),
            'final_decision': _('Décision Finale'),
            'certificate_signed': _('Signature du certificat'),
        }
        # Récupération du libellé, ou utilisation du nom technique par défaut
        target_state_label = STATE_LABELS.get(target_state, target_state)

        # 1. Mise à jour de la demande (changement d'état et motif de retour)
        self.certification_request_id.write({
            'state': target_state,
            'return_reason': self.return_reason,
        })
        
        # 2. Log dans le chatter
        message = _(f"La demande a été **retournée** depuis l'état '{current_state}' vers l'état '{target_state}' pour correction. **Motif:** {self.return_reason}")
        self.certification_request_id.message_post(body=message)

        # 3. ACTION : Notifications et Fermeture du Wizard
        # On retourne une action client combinée. Odoo va exécuter la notification PUIS fermer la fenêtre.
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Demande retournée"),
                'message': _(f"La demande a été retournée à l'étape '{target_state_label}'."),
                'type': 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}, # Fermeture après la notification
            }
        }
