# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FertilizerRenewHomologation(models.Model):
    _name = 'fertilizer.renew.homologation'
    _description = 'Procédure de renouvellement de l\'homologation des engrais et fertilisants'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
      
    #reference demande homolog init 
    arrete_id = fields.Many2one('fertilizer.decree', 
                                 string='reference de l\'arrêté', required=True)
   #product agricole : intrants agricole
    old_product_hom = fields.Many2one(
        'fertilizer.product',
        string="Produit homologué",
        related='arrete_id.commercial_name',
        readonly=True,
        store=True
    )
    # nouveau produit a homologuer/modifier
    product_id = fields.Many2one('fertilizer.product', 
                                 string='Nouveau produit à homologuer', 
                                 required=False, tracking=True)
    
     # Champs liés
    applicant_id = fields.Many2one(
        related='arrete_id.applicant_id',
        string="Demandeur",
        store=True,
        readonly=True,
    )
    
    #date de delivrance et de soumission
    submission_date = fields.Datetime(string='Date de soumission',default=fields.Datetime.now, readonly=True, tracking=True)
    date_delivrance = fields.Date(string='Date delivrance initiale',readonly=True, tracking=True)
    expiry_date = fields.Date(string='Date d\'expiration', tracking=True)
    #assigned_to = fields.Many2one('res.users', string='Responsable', tracking=True, default=lambda self: self.env.user)
    
    # Séquence des états simplifiée
    state = fields.Selection([
        ('draft', 'Dépôt du dossier'),
        ('verification', 'reception'),
        ('validation', 'Vérification de Conformité'),
        ('decision', 'Décision de renouvellement'),
        ('approved', 'Arrêté de renouvellement Signé'),
        ('signed', 'Terminer'),
        ('rejected', 'Rejeté'),  
    ], string='État', default='draft', tracking=True)
 
    # Documents Requis pour le Renouvellement (Accent sur le suivi)
   

    official_request_letter = fields.Binary(string="Lettre de demande officielle de renouvellement", required=True)
    official_request_letter_filename = fields.Char(string="Nom du fichier de la lettre")

    # Données et rapport de suivi post-homologation (différent de la modification/initiale)
    data_toxicity = fields.Text(string="Données de la toxicité mises à jour", required=True)
    data_environnment = fields.Text(string="Données environnementales mises à jour", required=True)
    data_limit_max = fields.Text(string="Données des limites maximales des contaminants mises à jour", required=True)
    report_suivi =  fields.Binary(string="Rapport de suivi de l'utilisation (post-homologation)", required=True)
    report_suivi_filename = fields.Char(string="Nom du fichier de suivi")

   
    # Reception (Réception - State 'verification')
 

    reception_agent = fields.Many2one('res.users', string='Agent de réception', tracking=True)
    reception_date = fields.Datetime(string='Date de réception', tracking=True)
    reception_note = fields.Text(string='Note de réception', tracking=True)
    reception_pv = fields.Binary(string='PV de réception')
    reception_pv_filename = fields.Char(string="Nom du fichier PV")

    data_toxicity_verified = fields.Boolean(string="Données de la toxicité vérifiées")
    data_environnment_verified = fields.Boolean(string="Données environnementales vérifiées")
    data_limit_max_verified = fields.Boolean(string="Données des limites vérifiées")
    report_suivi_verified =  fields.Boolean(string="Rapport de suivi vérifié")

    all_documents_verified = fields.Boolean(
        string="Tous les documents administratifs vérifiés",
        compute='_compute_all_documents_verified',
        store=True,
    )

    # Vérification de Conformité (Validation - State 'validation')
 
    conformity_check_agent = fields.Many2one('res.users', string='Agent de vérification conformité', tracking=True)
    conformity_check_date = fields.Datetime(string='Date de vérification conformité', tracking=True)
    conformity_report = fields.Binary(string='Rapport de vérification de conformité')
    conformity_report_filename = fields.Char(string="Nom du fichier rapport")
    conformity_note = fields.Text(string='Note de conformité', tracking=True)

    conformity_complete = fields.Boolean(
        string="Rapport de conformité complet",
        compute='_compute_conformity_complete',
        store=True,
    )
    
    # Décision et Finalisation
  

    decision_agent = fields.Many2one('res.users', string='Agent de décision', tracking=True)
    decision_date = fields.Datetime(string='Date de décision', tracking=True)
    decision_note = fields.Text(string='Note de décision', tracking=True)
    homologation_arretement = fields.Binary(string='Arrêté de renouvellement de l\'homologation')
    homologation_arretement_filename = fields.Char(string="Nom du fichier Arrêté")
    
    homologation_document = fields.Binary(string='Certificat d\'homologation signé')
    homologation_document_filename = fields.Char(string="Nom du fichier Certificat")
    signature_agent = fields.Many2one('res.users', string='Personnel du cabinet du Ministre', tracking=True)
    date_signature = fields.Datetime(string='Date de signature', tracking=True)

   
    # Champs de gestion du Rejet)
   
    return_reason = fields.Text(string='Motif du retour', tracking=True)
    rejected_by_user_id = fields.Many2one('res.users', string='Rejeté par')
    rejection_reason = fields.Text(string='Motif du rejet', tracking=True)
    rejected_from_state = fields.Char(
        string="État de Rejet Précédent", 
        tracking=False, 
        copy=False,
        help="Stocke l'état technique de l'homologation avant le rejet (utilisé pour le retour en arrière)."
    )

    # champs de gestion du retour 
    returned_by_user_id = fields.Many2one('res.users', string='Retourné par')
    returned_from_state = fields.Char(string='Retourné depuis l\'étape')
    return_date = fields.Datetime(
        string="Date de Retour",
        readonly=True,
        copy=False,
    )
    
    # Fonctions calculées (simples)

    @api.depends('data_toxicity_verified', 'data_environnment_verified', 'data_limit_max_verified', 'report_suivi_verified')
    def _compute_all_documents_verified(self):
        """Calcule si tous les documents de réception ont été cochés."""
        for record in self:
            record.all_documents_verified = all([
                record.data_toxicity_verified,
                record.data_environnment_verified,
                record.data_limit_max_verified,
                record.report_suivi_verified
            ])

    @api.depends('conformity_report', 'conformity_note')
    def _compute_conformity_complete(self):
        """Calcule si le rapport de conformité est prêt."""
        for record in self:
            record.conformity_complete = bool(record.conformity_report and record.conformity_note)

  
    # Fonctions de workflow (Avancement)
   
    def action_submit(self):
        """Passe de Brouillon à Réception/Vérif. Admin"""
        for record in self:
            if not record.official_request_letter or not record.report_suivi or not record.data_toxicity or not record.data_environnment or not record.data_limit_max:
                raise ValidationError(_("Tous les documents et données mis à jour requis doivent être définis."))
            record.submission_date = fields.Datetime.now()
            record.state = 'verification'
            record.message_post(body=_("Le dossier est soumis pour réception et vérification administrative."))
    
    def action_validate_admin(self):
        """Passe de Réception à Vérification de Conformité"""
        for record in self:
            if not record.all_documents_verified:
                raise ValidationError(_("Tous les documents administratifs doivent être vérifiés avant de passer à l'étape suivante."))
            if not record.reception_note:
                raise ValidationError(_("Veuillez renseigner une note de réception."))

            record.reception_agent = self.env.user.id
            record.reception_date = fields.Datetime.now()
            record.state = 'validation'
            record.message_post(body=_("La vérification administrative est terminée. Le dossier est passé à l'étape de vérification de conformité."))
            
    def action_start_decision(self):
        """Passe de Vérification de Conformité à Décision"""
        for record in self:
            # J'utilise conformity_complete pour simplifier, mais vous pouvez ajuster la vérification des champs ici.
            if not record.conformity_complete:
                raise ValidationError(_("Le Rapport de vérification de conformité et la Note de conformité sont obligatoires."))

            record.conformity_check_agent = self.env.user.id
            record.conformity_check_date = fields.Datetime.now()
            record.state = 'decision'
            record.message_post(body=_("La vérification de conformité est terminée. Le dossier est à l'étape de décision."))

    def action_approve(self):
        """Passe de Décision à Approuvé (Arrêté Signé)"""
        for record in self:
            if not record.decision_note or not record.homologation_arretement:
                 raise ValidationError(_("Veuillez renseigner la Note de Décision et l'Arrêté de renouvellement avant d'approuver."))

            record.decision_agent = self.env.user.id
            record.decision_date = fields.Datetime.now()
            record.state = 'approved'
            record.message_post(body=_("Décision de renouvellement approuvée. Le dossier est en attente de signature."))

    def action_sign(self):
        """Passe de Approuvé à Terminé"""
        for record in self:
            if not record.homologation_document:
                raise ValidationError(_("Veuillez télécharger le Certificat d'homologation signé."))
            #user & date signature 
            record.signature_agent = self.env.user.id
            record.date_signature = fields.Datetime.now()
            record.state = 'signed'
            #update date_renouvellement 
            renew_arrete =  {
                'delivery_date' : record.date_signature,
                'state' : 'actif'
            }
            record.arrete_id.write(renew_arrete)
            record.message_post(body=_("Le processus de renouvellement est terminé."))


    # Fonctions de workflow (Retour)

    def _open_return_wizard(self, target_state, wizard_name):
        """Fonction utilitaire pour ouvrir le wizard de retour."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': wizard_name,
            'res_model': 'fertilizer.renew.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_renew_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': target_state
            }
        }
    def _notify_applicant_rejection(self):
        """Notifier le demandeur du rejet"""
        if self.applicant_id:
            self.message_post(
                body=_("Votre demande de modification d'homologation %s a été rejetée.") % self.name,
                partner_ids=[self.applicant_id.id],
                message_type='comment'
            )

    def action_reject(self):
        """Ouvre le wizard de rejet (nécessite le modèle 'fertilizer.rejection.wizard')"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rejeter la demande',
            'res_model': 'fertilizer.renew.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_renew_homologation_id': self.id,
                'default_current_state': self.state
            }
        }
    
    def action_return_to_draft(self):
        """Retour vers Dépôt (draft) - depuis vérification"""
        return self._open_return_wizard('draft', 'Retourner au dépôt')

    def action_return_to_verification(self):
        """Retour vers Vérification Administrative (verification) - depuis validation"""
        return self._open_return_wizard('verification', 'Retourner à la Vérification Administrative')

    def action_return_to_validation(self):
        """Retour vers Vérification de Conformité (validation) - depuis décision"""
        return self._open_return_wizard('validation', 'Retourner à la Vérification de Conformité')
    
    def action_return_to_decision(self):
        """Retour vers Décision (decision) - depuis approuvé"""
        return self._open_return_wizard('decision', 'Retourner à l\'étape de Décision')
    
    # Séquence, création et écriture (simplifié)
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('fertilizer.renew.homologation') or _('New')
        return super(FertilizerRenewHomologation, self).create(vals)
    
    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'rejected']:
                raise UserError(_('Vous ne pouvez pas supprimer un dossier qui n\'est pas en brouillon ou rejeté.'))
        return super(FertilizerRenewHomologation, self).unlink()
