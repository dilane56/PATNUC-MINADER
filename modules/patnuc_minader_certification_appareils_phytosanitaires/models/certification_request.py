from odoo import models, fields, api, _
from odoo.exceptions import UserError , ValidationError
from datetime import datetime, timedelta

class CertificationRequest(models.Model):
    _name = 'phytosanitary.certification.request'
    _description = 'Demande de Certification Appareils Phytosanitaires'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Numéro de demande', required=True, copy=False, default=lambda self: _('Nouveau'))
    state = fields.Selection([
        ('draft', 'Déposée'),  
        ('reception', 'Reception'),
        ('technical_review', 'Instruction Technique'),
        ('technical_eval', 'Évaluation Technique'),
        ('admin_check', 'Traitement du dossier'),
        ('final_decision', 'Décision Finale'),
        ('certificate_signed', 'Signature du certificat'),
        ('approved','Certificat approuvé'),
        ('rejected', 'Rejetée'),
        ('cancelled', 'Annulée'),
        ('expired', 'expiré'),
    ], string='État', default='draft', tracking=True)

    user_id = fields.Many2one('res.users', string='Demandeur', required=True, tracking=True)
    #company_type = fields.Selection(related='partner_id.company_type', tracking=True)
    legal_representative = fields.Char('Représentant légal', tracking=True)
    
    equipment_id = fields.Many2one('phytosanitary.equipment', string='Appareil', required=True, tracking=True)
    #date automatique date.now
    submission_date = fields.Datetime('Date de soumission', default=fields.Datetime.now, tracking=True)
    
    #expected_completion_date = fields.Date('Date prévue de fin', compute='_compute_expected_date', tracking=True)
    #actual_completion_date = fields.Date('Date réelle de fin', tracking=True)
    
    # Documents requis
    official_request_letter = fields.Binary('Lettre de demande officielle')
    official_request_letter_filename = fields.Char('Nom du fichier')
    homologation_certificate = fields.Binary('Attestation d\'homologation')
    homologation_certificate_filename = fields.Char('Nom du fichier')
    import_agreement_copy = fields.Binary('Copie de l\'agrément d\'importation')
    import_agreement_copy_filename = fields.Char('Nom du fichier')
    identity_document_copy = fields.Binary('Photocopie pièce d\'identité')
    identity_document_copy_filename = fields.Char('Nom du fichier')
    #*recu de paiement des frais de dossier
    invoice_payment_cert_atp = fields.Binary('Reçu de paiement des frais de traitement du dossier')
    invoice_payment_cert_atp_filename = fields.Char('Nom du fichier')
   
    
    # Champs temporaires pour compatibilité
    technical_sheet_file = fields.Binary('Fiche technique (déprécié)', deprecated=True, tracking=True)
    technical_sheet_filename = fields.Char('Nom fichier technique (déprécié)', deprecated=True, tracking=True)
    
    # Champs de vérification des documents
    official_request_letter_verified = fields.Boolean('Lettre de demande officielle vérifiée', tracking=True)
    homologation_certificate_verified = fields.Boolean('Attestation homologation vérifiée',tracking=True)
    import_agreement_copy_verified = fields.Boolean('Agrément importation vérifié',  tracking=True)
    identity_document_copy_verified = fields.Boolean('Pièce d\'identité vérifiée', tracking=True)
    
    #* agent de reception & date reception 
    reception_agent = fields.Many2one('res.users', string='Agent de réception', tracking=True)
    reception_date = fields.Datetime(string='Date de réception', tracking=True)

    #* agent instruction technique 
    instruction_technical_agent = fields.Many2one('res.users', string='Agent instruction technique', tracking=True)
    instruction_technical_date = fields.Datetime(string='Date instruction technique', tracking=True)
    
    #*
    invoice_payment_copy_verified = fields.Boolean('Recu de paiement des frais de traitement du dossier', tracking=True)
    
    #commentaire de reception
    admin_verification_comment = fields.Text('Commentaire de vérification', tracking=True)
    
    # Champs instruction technique
    technical_instruction_note = fields.Text('Note d\'instruction technique', tracking=True)
    
    #* rapport d'instruction technique
    technical_instruction_doc = fields.Binary('Rapport d\'instruction technique')
    technical_instruction_doc_filename = fields.Char('Nom du fichier du rapport')
    """proceed_to_technical_evaluation = fields.Selection([
        ('yes', 'Oui'),
        ('no', 'Non')
    ], string='Instruction à l\'évaluation technique', tracking=True)"""
    
    # Champs évaluation technique
    
    technical_evaluation_notes = fields.Text('Notes d\'évaluation technique', tracking=True)
    """technical_evaluation_result = fields.Selection([
        ('favorable', 'Favorable'),
        ('conditional', 'Favorable sous conditions'),
        ('unfavorable', 'Défavorable')
    ], string='Résultat de l\'évaluation technique', tracking=True)"""
    technical_report_file = fields.Binary('Rapport technique', tracking=True)
    technical_report_filename = fields.Char('Nom du fichier rapport', tracking=True)
    
    all_documents_verified = fields.Boolean('Tous documents vérifiés', compute='_compute_all_documents_verified', store=True, tracking=True)
    document_ids = fields.One2many('phytosanitary.document', 'request_id', string='Documents', tracking=True)
    required_documents_complete = fields.Boolean('Documents requis complets', compute='_compute_documents_status', tracking=True)
    
    admin_evaluation_id = fields.Many2one('phytosanitary.admin.evaluation', string='Évaluation Administrative', tracking=True)
    technical_evaluation_id = fields.Many2one('phytosanitary.technical.evaluation', string='Évaluation Technique', tracking=True)
    
    # Champs related pour afficher les informations de l'évaluation technique
    """
    tech_eval_overall_score = fields.Float('Score Global', related='technical_evaluation_id.overall_score', readonly=True, tracking=True)
    tech_eval_recommendation = fields.Selection(related='technical_evaluation_id.recommendation', readonly=True, tracking=True)
    tech_eval_functionality_score = fields.Float('Score Fonctionnalité', related='technical_evaluation_id.functionality_score', readonly=True, tracking=True)
    tech_eval_safety_score = fields.Float('Score Sécurité', related='technical_evaluation_id.safety_score', readonly=True, tracking=True)
    tech_eval_compliance_score = fields.Float('Score Conformité', related='technical_evaluation_id.compliance_score', readonly=True, tracking=True)
    """
    technical_report = fields.Text('Note d\'evaluation technique', related='technical_evaluation_id.technical_report', readonly=True)
    tech_eval_report_file = fields.Binary('Rapport Technique', related='technical_evaluation_id.technical_report_file', readonly=True)
    tech_eval_report_filename = fields.Char('Nom Fichier Rapport', related='technical_evaluation_id.technical_report_filename', readonly=True)
    overall_score =  fields.Float('Score d\'evaluation globale', related='technical_evaluation_id.overall_score', readonly=True)
    
    #* agent evaluation technique
    evaluator_id = fields.Many2one('res.users', string='Évaluateur (Technique)', related='technical_evaluation_id.evaluator_id', readonly=True,store=False)
    evaluation_date = fields.Date('Date d\'évaluation' , related='technical_evaluation_id.evaluation_date', readonly=True)

    #traitement du dossier 
    #add checklist files reception - instruction - evaluation 
    conformite_official_request_letter_verified = fields.Boolean('Lettre de demande officielle vérifiée',  tracking=True)
    conformite_homologation_certificate_verified = fields.Boolean('Attestation homologation vérifiée', tracking=True)
    conformite_import_agreement_copy_verified = fields.Boolean('Agrément importation vérifié',  tracking=True)
    conformite_identity_document_copy_verified = fields.Boolean('Pièce d\'identité vérifiée',  tracking=True)
    conformite_invoice_payment_copy_verified = fields.Boolean('Recu de paiement des frais de traitement du dossier', tracking=True)
    conformite_technical_report_verified  = fields.Boolean('Rapport d\'instruction technique',  tracking=True)
    conformite_technical_eval_report_verified  = fields.Boolean('Rapport d\'évaluation technique',  tracking=True)
    #doc conformite
    note_conformite = fields.Text('Note de conformité')
    conformite_report = fields.Binary('Rapport de conformité du dossier')
    conformite_report_filename = fields.Char('Nom du dossier')
    #*agent de conformité
    conformite_agent = fields.Many2one('res.users', string='Agent de traitement du dossier', tracking=True)
    conformite_date = fields.Datetime(string='Date de traitement du dossier', tracking=True)
    
    #decision finale 
    # PV de réception - Document uploadé à l'étape décision finale
    certificat_delivr_report= fields.Text('Note de décision')
    reception_pv= fields.Binary('PV de réception')
    reception_pv_filename= fields.Char('Nom du fichier')
    # certificat délivré 
    certificat_deliv= fields.Binary('Certificat délivré')
    certificat_deliv_filename= fields.Char('Nom du fichier')
    #* agent decision 
    decision_agent = fields.Many2one('res.users', string='Agent de décision', tracking=True)
    decision_date = fields.Datetime(string='Date de décision', tracking=True)

    #signature du certificat
    certificate_number = fields.Char('Numéro de certificat', tracking=True)
    certificate_validity_start = fields.Date('Début validité certificat', tracking=True)
    certificate_validity_end = fields.Date('Fin validité certificat', tracking=True)
    rejection_reason = fields.Text('Motif de rejet', tracking=True)
    #* agent signature 
    signature_agent = fields.Many2one('res.users', string='Personnel du cabinet du ministre', tracking=True)
    signature_date = fields.Datetime(string='Date d\'insertion de l\'arêté signé', tracking=True)

    return_reason = fields.Text(string="Raison du Retour/Rejet", readonly=True, tracking=True)
    
    #fees_amount = fields.Float('Montant des frais', tracking=True)
    #fees_paid = fields.Boolean('Frais payés', default=False, tracking=True)
    payment_receipt = fields.Binary('Reçu de paiement', tracking=True)
    
    #responsible_agent_id = fields.Many2one('res.users', string='Agent responsable', tracking=True)
    #dripa_validator_id = fields.Many2one('res.users', string='Validateur DRIPA', tracking=True)
    #minister_signer_id = fields.Many2one('res.users', string='Signataire Ministre', tracking=True)
    
    # Champs de signature
    """
    signature_draw = fields.Binary('Signature dessinée', tracking=True)
    signature_image = fields.Binary('Signature', tracking=True)
    signature_filename = fields.Char('Nom fichier signature', tracking=True)
    """
    is_signed = fields.Boolean('Signé', compute='_compute_is_signed', store=True)
    
    certificat_signed= fields.Binary('Certificat signé par le Ministre')
    certificat_signed_filename = fields.Char('Nom du fichier')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('phytosanitary.certification.request') or 'Nouveau'
        return super().create(vals)

    @api.depends('submission_date')
    def _compute_expected_date(self):
        for record in self:
            if record.submission_date:
                record.expected_completion_date = record.submission_date.date() + timedelta(days=30)
            else:
                record.expected_completion_date = False

    @api.depends('official_request_letter', 'homologation_certificate', 'import_agreement_copy', 'identity_document_copy')
    def _compute_documents_status(self):
        for record in self:
            record.required_documents_complete = all([
                record.official_request_letter,
                record.homologation_certificate,
                record.import_agreement_copy,
                record.identity_document_copy
            ])
    
    @api.depends('official_request_letter_verified', 'homologation_certificate_verified', 'import_agreement_copy_verified', 'identity_document_copy_verified')
    def _compute_all_documents_verified(self):
        for record in self:
            record.all_documents_verified = all([
                record.official_request_letter_verified,
                record.homologation_certificate_verified,
                record.import_agreement_copy_verified,
                record.identity_document_copy_verified,
                record.invoice_payment_copy_verified
            ])

    def action_submit(self):
        """
        Vérifie si tous les documents requis sont chargés avant de passer à l'état reception'.
        """
        # Liste des champs binaires obligatoires à vérifier
        required_files = [
            self.official_request_letter,
            self.homologation_certificate,
            self.import_agreement_copy,
            self.identity_document_copy,
            self.invoice_payment_cert_atp
        ]

        # Utilisation de la fonction all() pour vérifier si tous les champs sont non-vides
        if not all(required_files):
            # Si un ou plusieurs fichiers sont manquants, lever une erreur
            raise ValidationError(
                _("Veuillez charger tous les documents requis (Lettre officielle, Attestation d'homologation, Agrément d'importation, Pièce d'identité, et Reçu de paiement des frais de dossier) avant de soumettre la demande.")
            )

        # Si tous les fichiers sont présents, effectuer la transition d'état
        self.write({'state': 'reception', 'submission_date': fields.Datetime.now()})
    
    def action_reception(self):
        for record in self : 
            if not all([    record.official_request_letter_verified,
                            record.homologation_certificate_verified,
                            record.import_agreement_copy_verified,
                            record.identity_document_copy_verified,
                            record.invoice_payment_copy_verified,
                            ]):
                raise ValidationError(_("Tous les documents requis doivent être vérifiés avant de passer à l'étape suivante."))
            
            if not record.admin_verification_comment:
                raise ValidationError(_("Le commentaire de vérification est obligatoire avant de passer à l'instruction technique."))
            #define agent & date reception
            record.reception_agent = self.env.user.id
            record.reception_date = fields.Datetime.now()
            record.state = 'technical_review'
    
    def action_technical_evaluation(self):
        for record in self : 

            if not record.technical_instruction_note or not record.technical_instruction_doc:
                raise ValidationError(_("La note d'instruction technique et le rapport d'instruction technique sont obligatoires."))
            #define agent instruction & date 
            record.instruction_technical_agent = self.env.user.id 
            record.instruction_technical_date = fields.Datetime.now()
            record.state = 'technical_eval'
    
    def action_launch_technical_evaluation(self):
        return {
            'name': 'Évaluation Technique',
            'type': 'ir.actions.act_window',
            'res_model': 'phytosanitary.technical.evaluation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_equipment_id': self.equipment_id.id,
                'default_evaluator_id': self.env.user.id,
                'default_evaluation_date': fields.Date.today()
            }
        }
    

    def action_final_decision(self):
        for record in self : 
            if not all([    record.conformite_official_request_letter_verified,
                            record.conformite_homologation_certificate_verified,
                            record.conformite_import_agreement_copy_verified,
                            record.conformite_identity_document_copy_verified,
                            record.conformite_invoice_payment_copy_verified,
                            record.conformite_technical_report_verified,
                            record.conformite_technical_eval_report_verified,
                            ]):
                raise ValidationError(_("Veuillez confirmer la conformité de chaque document du dossier avant de passer à l'étape suivante. Bien vouloir cocher si un document est conforme. Pour consultation des dits documents allez sur l'onget (Document requis)"))  
            if not record.conformite_report or not record.note_conformite:
                raise ValidationError(("Le rapport et la note de confomité sont obligatoires avant de passer à la décision finale"))
            record.conformite_agent = self.env.user.id 
            record.conformite_date = fields.Datetime.now()
            record.state='final_decision'
    
    def action_approve_decision(self):
        for record in self : 
            if not record.reception_pv  : 
             raise ValidationError(_("Le PV de réception est obligatoire pour approuver la décision finale."))
            if not record.certificat_deliv : 
                raise ValidationError(_("Le certificat delivré est obligatoire pour approuver la décision finale."))
            record.decision_agent=self.env.user.id 
            record.decision_date=fields.Datetime.now()
            record.state='certificate_signed'
       
        
    
    def action_notify_decision(self):
        #notifier la décision a l'usager 
        pass
        
    def action_reject(self):
        return {
            'name': 'Motif de rejet',
            'type': 'ir.actions.act_window',
            'res_model': 'phytosanitary.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    def action_view_documents(self):
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'phytosanitary.document',
            'domain': [('request_id', '=', self.id)],
            'context': {'default_request_id': self.id}
        }
    
    @api.depends('certificat_signed')
    def _compute_is_signed(self):
        """
        Définit 'is_signed' à True si le fichier 'certificat_signed' est présent.
        """
        for record in self:
            record.is_signed = bool(record.certificat_signed)
    
    def action_confirm_signed(self):
        """
        Passe la demande à l'état 'Approuvée' après la vérification du certificat signé.
        """
        for record in self : 
            if not record.certificat_signed:
                raise ValidationError("Veuillez d'abord uploader le certificat signé par le Ministre.")
            record.signature_agent = self.env.user.id 
            record.signature_date = fields.Datetime.now()
            record.state='approved'
    
        
    
    def action_check_admin(self):
        for record in self : 
            if not record.technical_report or not record.tech_eval_report_file: 
                raise ValidationError(_("Le document et la note technique sont obligatoires avant de passer à l'étape suivante."))
            record.evaluator_id = self.env.user.id 
            record.evaluation_date = fields.Datetime.now()
            record.state='admin_check'
            
    # La méthode générique pour ouvrir le wizard, que vous avez fournie
    def _open_return_wizard(self, target_state):
        """
        Ouvre le wizard de retour de demande avec l'état de destination spécifié.
        :param target_state: Le nom technique de l'état de destination (ex: 'reception').
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retour de la Demande',
            # Changer le modèle résolu pour notre nouveau modèle de wizard
            'res_model': 'certification.return.wizard', 
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_current_state': self.state,
                # Clé critique: passer l'état de destination au wizard
                'target_state': target_state, 
            }
        }
    # Retour depuis technical_review (Instruction Technique) vers reception
    def action_return_to_reception(self):
        """Retourne de l'instruction technique à la réception du dossier."""
        return self._open_return_wizard(target_state='reception')

    # Retour depuis technical_eval (Évaluations) vers technical_review
    def action_return_to_technical_review(self):
        """Retourne des évaluations à l'instruction technique."""
        return self._open_return_wizard(target_state='technical_review')
        
    # Retour depuis admin_check (Traitement du dossier) vers technical_eval
    def action_return_to_technical_eval(self):
        """Retourne du traitement du dossier à l'étape d'évaluation technique."""
        return self._open_return_wizard(target_state='technical_eval')

    # Retour depuis final_decision vers admin_check
    def action_return_to_admin_check(self):
        """Retourne de la décision finale à l'étape de traitement du dossier."""
        return self._open_return_wizard(target_state='admin_check')

    # Retour vers draft (brouillon) — souvent utilisé depuis reception
    def action_return_to_draft(self):
        """Retourne à l'état brouillon (pour les erreurs de soumission initiales)."""
        return self._open_return_wizard(target_state='draft')
    
    # methode de previsualisation des documents
    def action_preview_document(self):
        """Action pour prévisualiser un document"""
        field_name = self.env.context.get('field_name')
        filename_field = self.env.context.get('filename_field')
        
        if not field_name or not hasattr(self, field_name):
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
                'message': 'Document non trouvé',
                'type': 'warning'
            }}
        
        file_content = getattr(self, field_name)
        filename = getattr(self, filename_field) if filename_field and hasattr(self, filename_field) else 'document.pdf'
        
        if not file_content:
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
                'message': 'Aucun document à prévisualiser',
                'type': 'warning'
            }}
        
        # Créer un attachment temporaire pour la prévisualisation
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': file_content,
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=false',
            'target': 'new',
        }
    def preview_document(self):
        """Ouvrir le document dans un modal pour prévisualisation"""
        document_field = self.env.context.get('document_field')
        if not document_field:
            raise UserError(_("Aucun document spécifié pour la prévisualisation."))
        
        document_data = getattr(self, document_field)
        if not document_data:
            raise UserError(_("Le document n'existe pas ou n'a pas été uploadé."))
        
        filename_field = f"{document_field}_filename"
        filename = getattr(self, filename_field, f"{document_field}.pdf")
        
        # Créer un wizard pour la prévisualisation
        wizard = self.env['document.preview.wizard'].create({
            'name': filename,
            'pdf_data': document_data,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prévisualisation du document',
            'res_model': 'document.preview.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': 'large'},
        }


