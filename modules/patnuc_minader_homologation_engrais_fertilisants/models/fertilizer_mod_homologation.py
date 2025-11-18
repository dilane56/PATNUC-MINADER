# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FertilizerModHomologation(models.Model):
    _name = 'fertilizer.mod.homologation'
    _description = 'Procédure de modification d\'homologation des engrais et fertilisants'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    
    #reference demande homolog init 
    arrete_id = fields.Many2one('fertilizer.decree', 
                                 string='reference de l\'arrêté', required=True)
    
    #related reference 
    applicant_id = fields.Many2one(
        related='arrete_id.applicant_id',
        string="Demandeur",
        store=True,
        readonly=True,
    )
    
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
    
    #date de soumission et de livrance
    submission_date = fields.Datetime(string='Date de soumission',default=fields.Datetime.now, readonly=True, tracking=True)
    date_delivrance = fields.Date(string='Date delivrance', readonly=True, tracking=True)
    expiry_date = fields.Date(string='Date d\'expiration', tracking=True)
    
    # (Q) Modification de la séquence des états selon les nouvelles spécifications
    state = fields.Selection([
        ('draft', 'Dépôt du dossier'),
        ('verification', 'Reception'),
        ('analysis', 'Analyses chimiques et microbiologiques'),
        ('field_test', 'Tests agronomiques'),
        ('economic_eval', 'Évaluation agro-économique'), 
        ('synthesis', 'Verification administrative'),
        ('validation', 'Validation conformité du dossier'),
        ('decision', 'Décision d\'homologation'),
        ('approved', 'Signature'),
        ('signed', 'Terminer'),
        ('rejected', 'Rejeté'),  
    ], string='État', default='draft', tracking=True)
    
    # Documents requis
    official_request_letter = fields.Binary(string='Lettre de demande officielle')
    official_request_letter_filename = fields.Char(string="Nom du fichier")

    homologation_certificate = fields.Binary(string='Attestation d\'homologation')
    homologation_certificate_filename = fields.Char(string="Nom du fichier")
    import_agreement_copy = fields.Binary(string='Copie de l\'agrément d\'importation')
    import_agreement_copy_filename = fields.Char(string="Nom du fichier")
    identity_document_copy = fields.Binary(string='Photocopie pièce d\'identité')
    identity_document_copy_filename = fields.Char(string="Nom du fichier")
    
    # Documents générés
    completeness_report = fields.Binary(string='Rapport de vérification de complétude')
    completeness_report_filename = fields.Char(string="Nom du fichier")
    chemical_analysis_report = fields.Binary(string='Rapport d\'analyse chimique')
    chemical_analysis_report_filename = fields.Char(string="Nom du fichier")
    microbiological_analysis_report = fields.Binary(string='Rapport d\'analyse microbiologique')
    microbiological_analysis_report_filename = fields.Char(string="Nom du fichier")
    field_test_report = fields.Binary(string='Rapport des tests en champ')
    field_test_report_filename = fields.Char(string="Nom du fichier")
    economic_evaluation_report = fields.Binary(string='Rapport d\'évaluation économique')
    economic_evaluation_report_filename = fields.Char(string="Nom du fichier")
    # synthesis_report = fields.Binary(string='Rapport de synthèse')
    # synthesis_report_filename = fields.Char(string="Nom du fichier")
    homologation_decision = fields.Binary(string='Décision d\'homologation')
    homologation_decision_filename = fields.Char(string="Nom du fichier")
    homologation_certificate = fields.Binary(string='Certificat d\'homologation')
    homologation_certificate_filename = fields.Char(string="Nom du fichier")
    
    # Relations avec les autres modèles
    laboratory_analysis_id = fields.Many2one('laboratory.analysis', string='Analyse de laboratoire')
    field_test_id = fields.Many2one('field.test', string='Test en champ')
    economic_evaluation_id = fields.Many2one('economic.evaluation', string='Évaluation économique')
    
    # Champs related pour l'onglet analyse laboratoire
    laboratory_analysis_agent = fields.Many2one(related='laboratory_analysis_id.responsible_id', readonly=True)
    analysis_creation_date = fields.Datetime(related='laboratory_analysis_id.create_date', readonly=True)
    analysis_submission_date = fields.Date(related='laboratory_analysis_id.analysis_date', readonly=True)
    analysis_chemical_report = fields.Binary(related='laboratory_analysis_id.chemical_analysis_report', readonly=True)
    analysis_chemical_report_filename = fields.Char(related='laboratory_analysis_id.chemical_analysis_report_filename', readonly=True)
    analysis_microbiological_report = fields.Binary(related='laboratory_analysis_id.microbiological_analysis_report', readonly=True)
    analysis_microbiological_report_filename = fields.Char(related='laboratory_analysis_id.microbiological_analysis_report_filename', readonly=True)
    
    # # Champs related pour les résultats d'analyse

    # analysis_nitrogen_content = fields.Float(related='laboratory_analysis_id.nitrogen_content', readonly=True)
    # analysis_phosphorus_content = fields.Float(related='laboratory_analysis_id.phosphorus_content', readonly=True)
    # analysis_potassium_content = fields.Float(related='laboratory_analysis_id.potassium_content', readonly=True)
    # analysis_ph_level = fields.Float(related='laboratory_analysis_id.ph_level', readonly=True)
    # analysis_moisture_content = fields.Float(related='laboratory_analysis_id.moisture_content', readonly=True)
    # analysis_microbial_contamination = fields.Text(related='laboratory_analysis_id.microbial_contamination', readonly=True)
    # analysis_pathogen_presence = fields.Text(related='laboratory_analysis_id.pathogen_presence', readonly=True)
    # analysis_conform_to_specs = fields.Boolean(related='laboratory_analysis_id.conform_to_specs', readonly=True)
    # analysis_conclusion = fields.Text(related='laboratory_analysis_id.analysis_conclusion', readonly=True)
    

    
    # Champs related pour les documents de test en champ
    field_test_start_date = fields.Date(related='field_test_id.start_date', readonly=True)
    field_test_agent = fields.Many2one(related='field_test_id.responsible_id', readonly=True)
    field_test_results_file = fields.Binary(related='field_test_id.test_results_file', readonly=True)
    field_test_results_filename = fields.Char(related='field_test_id.test_results_filename', readonly=True)
    field_agronomic_test_report = fields.Binary(related='field_test_id.agronomic_test_report', readonly=True)
    field_agronomic_test_report_filename = fields.Char(related='field_test_id.agronomic_test_report_filename',readonly=True)

    
    # Champs related pour l'évaluation économique
    economic_evaluation_date = fields.Date(related='economic_evaluation_id.evaluation_date', readonly=True)
    # economic_product_price = fields.Float(related='economic_evaluation_id.product_price', readonly=True)
    # economic_application_cost = fields.Float(related='economic_evaluation_id.application_cost', readonly=True)
    # economic_yield_increase_value = fields.Float(related='economic_evaluation_id.yield_increase_value', readonly=True)
    # economic_net_benefit = fields.Float(related='economic_evaluation_id.net_benefit', readonly=True)
    # economic_benefit_cost_ratio = fields.Float(related='economic_evaluation_id.benefit_cost_ratio', readonly=True)
    # economic_payback_period = fields.Float(related='economic_evaluation_id.payback_period', readonly=True)
    economic_eval_agent = fields.Many2one(related='economic_evaluation_id.responsible_id', readonly=True)
    economic_eval_report = fields.Binary(related='economic_evaluation_id.economic_evalutation_report', readonly=True)
    economic_eval_report_filename = fields.Char(related='economic_evaluation_id.economic_evalutation_report_filename', readonly=True)

    # Vérification administrative et recption du dossier
    admin_check_agent = fields.Many2one('res.users', string='Agent de vérification', tracking=True)
    admin_check_date = fields.Datetime(string='Date de vérification', tracking=True)
    reception_agent = fields.Many2one('res.users', string='Agent de réception', tracking=True)
    reception_date = fields.Datetime(string='Date de réception', tracking=True)
    official_request_letter_verified = fields.Boolean(string='Lettre de demande officielle vérifiée')
    homologation_certificate_verified = fields.Boolean(string='Attestation d\'homologation vérifiée')
    import_agreement_copy_verified = fields.Boolean(string='Copie de l\'agrément d\'importation vérifiée')
    identity_document_copy_verified = fields.Boolean(string='Photocopie pièce d\'identité vérifiée')
    verification_note = fields.Text(string='Note de vérification', tracking=True)
    all_documents_verified = fields.Boolean(string='Tous documents vérifiés', compute='_compute_all_documents_verified')
    analysis_complete = fields.Boolean(string='Analyse complète', compute='_compute_analysis_complete')
    field_test_complete = fields.Boolean(string='Test en champ complet', compute='_compute_field_test_complete')
    economic_evaluation_complete = fields.Boolean(string='Évaluation économique complète', compute='_compute_economic_evaluation_complete')
    conformity_complete = fields.Boolean(string='Conformité complète', compute='_compute_conformity_complete')
    # date_verification_admin =fields.Datetime(string="Date de verfication")
    
    # Suivi
    assigned_to = fields.Many2one('res.users', string='Assigné à', tracking=True)
    notes = fields.Text(string='Notes')
    administrative_note = fields.Text(string='Note administrative', tracking=True)
    reception_note = fields.Text(string='Note de réception', tracking=True)
    
    # Conformité
    conformity_check_agent = fields.Many2one('res.users', string='Agent de vérification', tracking=True)
    conformity_check_date = fields.Datetime(string='Date de vérification', tracking=True)
    conformity_report = fields.Binary(string='Rapport de conformité')
    conformity_report_filename = fields.Char(string="Nom du fichier")
    conformity_note = fields.Text(string='Note de conformité', tracking=True)

    #decision
    decision_agent = fields.Many2one('res.users', string='Agent de décision', tracking=True)
    decision_date = fields.Datetime(string='Date de décision', tracking=True)
    decision_note = fields.Text(string='Note de décision', tracking=True)
    reception_pv = fields.Binary(string='PV de réception')
    reception_pv_filename = fields.Char(string="Nom du fichier")
    homologation_arretement = fields.Binary(string='Arrêté d\'homologation')
    homologation_arretement_filename = fields.Char(string="Nom du fichier")
    
    # Vérification administrative (synthèse)
    admin_check_official_request_letter = fields.Boolean(string='Lettre de demande officielle vérifiée')
    admin_check_homologation_certificate = fields.Boolean(string='Attestation d\'homologation vérifiée')
    admin_check_import_agreement_copy = fields.Boolean(string='Copie agrément d\'importation vérifiée')
    admin_check_identity_document_copy = fields.Boolean(string='Photocopie pièce d\'identité vérifiée')
    admin_check_chemical_report = fields.Boolean(string='Rapport d\'analyse chimique vérifié')
    admin_check_microbiological_report = fields.Boolean(string='Rapport d\'analyse microbiologique vérifié')
    admin_check_field_test_results = fields.Boolean(string='Résultats de test en champ vérifiés')
    admin_check_agronomic_test_report = fields.Boolean(string='Rapport de test agronomique vérifié')
    admin_check_economic_eval_report = fields.Boolean(string='Rapport d\'évaluation économique vérifié')
    admin_verification_note = fields.Text(string='Note de vérification administrative', tracking=True)
    check_agent = fields.Many2one('res.users', string='Agent de vérification', tracking=True)
    check_date = fields.Datetime(string='Date de vérification', tracking=True)
    
    # Certificat et signature
    homologation_document = fields.Binary(string='Certificat d\'homologation signé par le Ministre')
    homologation_document_filename = fields.Char(string="Nom du fichier")
    signature_agent = fields.Many2one('res.users', string='Personnel du cabinet du Ministre', tracking=True)
    date_signature = fields.Datetime(string='Date d\'insertion de l\'arêté signé', tracking=True)
    
    # (Q) Champs pour gérer le retour avec motif
    return_reason = fields.Text(string='Motif du retour', tracking=True)
    returned_by_user_id = fields.Many2one('res.users', string='Retourné par')
    returned_from_state = fields.Char(string='Retourné depuis l\'étape')
    
    # (Q) Champs pour gérer le rejet avec motif
    rejection_reason = fields.Text(string='Motif du rejet', tracking=True)
    rejected_by_user_id = fields.Many2one('res.users', string='Rejeté par')
    rejected_from_state = fields.Char(string='Rejeté depuis l\'étape')
    
    @api.depends('official_request_letter_verified', 'homologation_certificate_verified', 'import_agreement_copy_verified', 'identity_document_copy_verified')
    def _compute_all_documents_verified(self):
        for record in self:
            record.all_documents_verified = all([record.official_request_letter_verified, record.homologation_certificate_verified, 
                                               record.import_agreement_copy_verified, record.identity_document_copy_verified])
    
    @api.depends(  'laboratory_analysis_id.chemical_analysis_report', 'laboratory_analysis_id.microbiological_analysis_report')
    def _compute_analysis_complete(self):
        for record in self:
            if record.laboratory_analysis_id:
                analysis = record.laboratory_analysis_id
                record.analysis_complete = all([
                    # analysis.nitrogen_content is not None,
                    # analysis.phosphorus_content is not None,
                    # analysis.potassium_content is not None,
                    # analysis.microbial_contamination,
                    # analysis.pathogen_presence,
                    analysis.chemical_analysis_report,
                    analysis.microbiological_analysis_report,
                    # analysis.analysis_conclusion
                ])
            else:
                record.analysis_complete = False
    
    @api.depends('field_agronomic_test_report', 'field_test_id.test_results_file')
    def _compute_field_test_complete(self):
        for record in self:
            if record.field_test_id:
                test = record.field_test_id
                record.field_test_complete = all([
                    test.agronomic_test_report,
                    test.test_results_file
                ])
            else:
                record.field_test_complete = False
    
    @api.depends('economic_evaluation_id.economic_evalutation_report')
    def _compute_economic_evaluation_complete(self):
        for record in self:
            if record.economic_evaluation_id:
                eval = record.economic_evaluation_id
                record.economic_evaluation_complete = all([
                    # eval.benefit_cost_ratio is not None,
                    # eval.payback_period is not None,
                    eval.economic_evalutation_report

                ])
            else:
                record.economic_evaluation_complete = False
    
    @api.depends('conformity_report', 'conformity_note')
    def _compute_conformity_complete(self):
        for record in self:
            record.conformity_complete = all([
                record.conformity_report,
                record.conformity_note
            ])

    @api.depends('official_request_letter')
    def _compute_document_url(self):
        """Génère l'URL pour la prévisualisation du document.
           Note: L'URL doit pointer vers le contrôleur /web/content.
        """
        for record in self:
            if record.official_request_letter:
                # Modèle: /web/content/<model>/<id>/<champ_binaire>/<nom_fichier>
                # Nous utilisons 'raw_data' pour éviter le téléchargement forcé
                url_base = f"/web/content/{record._name}/{record.id}/official_request_letter"

                # Le nom de fichier est facultatif ici mais peut améliorer l'affichage
                if record.official_request_letter_filename:
                    url_base += f"/{record.official_request_letter_filename}"

                record.official_request_letter_url = url_base
            else:
                record.official_request_letter_url = False

    # (Q) Méthodes pour gérer les noms de fichiers
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        binary_fields = {
            'official_request_letter': 'official_request_letter_filename',
            'homologation_certificate': 'homologation_certificate_filename',
            'import_agreement_copy': 'import_agreement_copy_filename',
            'identity_document_copy': 'identity_document_copy_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field]:
                if filename_field not in vals or not vals[filename_field]:
                    filename = None
                    
                    # Essayer de récupérer depuis le contexte
                    filename = self.env.context.get(f'{binary_field}_filename')
                    
                    if not filename:
                        for key in [f'default_{filename_field}', filename_field, f'{binary_field}_name']:
                            filename = self.env.context.get(key)
                            if filename:
                                break
                    
                    # Depuis la requête HTTP
                    if not filename and hasattr(self.env, 'request') and self.env.request:
                        request_files = getattr(self.env.request, 'httprequest', None)
                        if request_files and hasattr(request_files, 'files'):
                            for file_key, file_obj in request_files.files.items():
                                if binary_field in file_key and hasattr(file_obj, 'filename'):
                                    filename = file_obj.filename
                                    break
                    
                    # Nom par défaut
                    if not filename:
                        default_names = {
                            'official_request_letter': 'lettre_demande_officielle.pdf',
                            'homologation_certificate': 'attestation_homologation.pdf',
                            'import_agreement_copy': 'copie_agrement_importation.pdf',
                            'identity_document_copy': 'photocopie_piece_identite.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename
    
    def action_update_filenames(self):
        """Action pour mettre à jour les noms de fichiers depuis les attachements"""
        for record in self:
            record._update_filename_from_attachment()
        return True
    
    def _update_filename_from_attachment(self):
        """Récupérer les noms de fichiers depuis les attachements"""
        binary_fields = {
            'official_request_letter': 'official_request_letter_filename',
            'homologation_certificate': 'homologation_certificate_filename',
            'import_agreement_copy': 'import_agreement_copy_filename',
            'identity_document_copy': 'identity_document_copy_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if getattr(self, binary_field):
                attachment = self.env['ir.attachment'].search([
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
                    ('res_field', '=', binary_field)
                ], limit=1, order='id desc')
                
                if attachment and attachment.name:
                    setattr(self, filename_field, attachment.name)          
    
    # (Q) Fonctions de workflow mises à jour selon la nouvelle séquence
    def action_submit(self):
        for record in self:

            if record.state == 'draft':
                if not all([record.official_request_letter, record.homologation_certificate, 
                           record.import_agreement_copy, record.identity_document_copy]):
                    raise ValidationError(_("Tous les documents requis doivent être vérifiés avant de passer à l'étape suivante."))
                record.submission_date = fields.Date.today()
                record.state = 'verification'
                # Effacer le motif de retour et réinitialiser les vérifications lors de la nouvelle soumission
                record.return_reason = False
                record.official_request_letter_verified = False
                record.homologation_certificate_verified = False
                record.import_agreement_copy_verified = False
                record.identity_document_copy_verified = False
                record.verification_note = False
                record.message_post(body=_("Le dossier est en cours de vérification administrative."))
    

    
    def action_start_analysis(self):
        for record in self:
            if record.state == 'verification':
                # Vérifier que tous les documents sont vérifiés
                if not all([record.official_request_letter_verified, record.homologation_certificate_verified, 
                           record.import_agreement_copy_verified, record.identity_document_copy_verified]):
                    raise ValidationError(_("Tous les documents requis doivent être vérifiés avant de passer à l'étape suivante."))
                
                # Vérifier que la note de vérification est renseignée
                if not record.verification_note:
                    raise ValidationError(_("Vous devez renseigner une note de vérification avant de passer à l'étape suivante."))


                record.reception_agent = self.env.user.id
                record.reception_date = fields.Date.today()
                
                record.state = 'analysis'
                record.message_post(body=_("Le dossier passe à l'étape d'analyses chimiques et microbiologiques."))
                
                # Notifier le groupe LNAD
                lnad_group = self.env.ref('patnuc_minader_homologation_engrais_fertilisants.group_agent_LNAD', raise_if_not_found=False)
                if lnad_group:
                    partner_ids = lnad_group.users.mapped('partner_id.id')
                    if partner_ids:
                        record.message_post(
                            body=_("Le dossier %s est maintenant à l'étape d'analyses chimiques et microbiologiques.") % record.name,
                            partner_ids=partner_ids,
                            message_type='comment'
                        )
    
    def action_create_analysis(self):
        for record in self:
            if record.state == 'analysis':
                # Créer une analyse de laboratoire associée
                analysis = self.env['laboratory.analysis'].create({
                    'mod_homologation_id': record.id,
                    'product_id': record.product_id.id,
                })
                record.laboratory_analysis_id = analysis.id
                record.message_post(body=_("Une analyse de laboratoire a été créée."))
                
                # Retourner le formulaire d'analyse
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Analyse de laboratoire',
                    'res_model': 'laboratory.analysis',
                    'view_mode': 'form',
                    'res_id': analysis.id,
                    'target': 'new',
                    'context': {
                        'default_request_id': record.id,
                        'form_view_initial_mode': 'edit',
                    },
                    'flags': {
                        'mode': 'edit'
                    }
                }
    
    def action_start_field_test(self):
        for record in self:
            if record.state == 'analysis':
                record.state = 'field_test'
                record.message_post(body=_("Le dossier passe à l'étape des tests agronomiques."))
                
                # Notifier le groupe des tests agronomiques
                field_test_group = self.env.ref('patnuc_minader_homologation_engrais_fertilisants.group_agent_LNAD', raise_if_not_found=False)
                if field_test_group:
                    partner_ids = field_test_group.users.mapped('partner_id.id')
                    if partner_ids:
                        record.message_post(
                            body=_("Le dossier %s est maintenant à l'étape des tests agronomiques.") % record.name,
                            partner_ids=partner_ids,
                            message_type='comment'
                        )
    
    def action_create_field_test(self):
        for record in self:
            if record.state == 'field_test':
                # Créer un test en champ associé
                field_test = self.env['field.test'].create({
                    'mod_homologation_id': record.id,
                    'product_id': record.product_id.id,
                })
                record.field_test_id = field_test.id
                record.message_post(body=_("Un test agronomique a été créé."))
                
                # Retourner le formulaire de test en champ
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Test en champ',
                    'res_model': 'field.test',
                    'view_mode': 'form',
                    'res_id': field_test.id,
                    'target': 'new',
                    'context': {
                        'default_request_id': record.id,
                        'form_view_initial_mode': 'edit',
                    },
                    'flags': {
                        'mode': 'edit'
                    }
                }
    
    def action_start_economic_evaluation(self):
        for record in self:
            if record.state == 'field_test':
                record.state = 'economic_eval'
                record.message_post(body=_("Le dossier passe à l'étape d'évaluation économique."))
                
                # Notifier le groupe SRC
                src_group = self.env.ref('patnuc_minader_homologation_engrais_fertilisants.group_agent_SRC', raise_if_not_found=False)
                if src_group:
                    partner_ids = src_group.users.mapped('partner_id.id')
                    if partner_ids:
                        record.message_post(
                            body=_("Le dossier %s est maintenant à l'étape d'évaluation économique.") % record.name,
                            partner_ids=partner_ids,
                            message_type='comment'
                        )
    
    def action_create_economic_evaluation(self):
        for record in self:
            if record.state == 'economic_eval':
                # Créer une évaluation économique associée
                economic_eval = self.env['economic.evaluation'].create({
                    'mod_homologation_id': record.id,
                    'product_id': record.product_id.id,
                })
                record.economic_evaluation_id = economic_eval.id
                record.message_post(body=_("Une évaluation économique a été créée."))
                
                # Retourner le formulaire d'évaluation économique
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Évaluation économique',
                    'res_model': 'economic.evaluation',
                    'view_mode': 'form',
                    'res_id': economic_eval.id,
                    'target': 'new',
                    'context': {
                        'default_request_id': record.id,
                        'form_view_initial_mode': 'edit',
                    },
                    'flags': {
                        'mode': 'edit'
                    }
                }

    def action_preview_document(self):
        """Créer un wizard de prévisualisation et l'afficher dans une popup."""
        self.ensure_one()
        if not self.official_request_letter:
            raise UserError(_("Aucun document à prévisualiser."))

        wizard = self.env['document.preview.wizard'].create({
            'name': self.official_request_letter_filename or 'document.pdf',
            'pdf_data': self.official_request_letter,
        })

        return {
            'name': _('Prévisualisation du document'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.preview.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',  # ouvre dans une popup
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
    
    def action_prepare_synthesis(self):
        for record in self:
            if record.state == 'economic_eval':
                record.state = 'synthesis'
                record.message_post(body=_("La synthèse des résultats est en préparation."))
    
    def action_validate_regulatory(self):
        for record in self:

                # Vérifier que tous les documents ont été vérifiés
                missing_checks = []
                if not record.admin_check_official_request_letter:
                    missing_checks.append("Lettre de demande officielle")
                if not record.admin_check_homologation_certificate:
                    missing_checks.append("Attestation d'homologation")
                if not record.admin_check_import_agreement_copy:
                    missing_checks.append("Copie agrément d'importation")
                if not record.admin_check_identity_document_copy:
                    missing_checks.append("Photocopie pièce d'identité")
                if not record.admin_check_chemical_report:
                    missing_checks.append("Rapport d'analyse chimique")
                if not record.admin_check_microbiological_report:
                    missing_checks.append("Rapport d'analyse microbiologique")
                if not record.admin_check_field_test_results:
                    missing_checks.append("Résultats de test en champ")
                if not record.admin_check_agronomic_test_report:
                    missing_checks.append("Rapport de test agronomique")
                if not record.admin_check_economic_eval_report:
                    missing_checks.append("Rapport d'évaluation économique")
                
                if missing_checks:
                    raise ValidationError(_("Vous devez vérifier tous les documents suivants avant de passer à l'étape suivante : %s") % ", ".join(missing_checks))
                
                if not record.admin_verification_note:
                    raise ValidationError(_("Vous devez renseigner une note de vérification administrative avant de passer à l'étape suivante."))

                record.check_agent = self.env.user.id
                record.check_date = fields.Datetime.today()
                record.state = 'validation'
                record.message_post(body=_("La validation conformité du dossier est en cours."))  # (Q) Message mis à jour
    
    # (Q) Nouvelle méthode pour l'étape décision finale
    def action_final_decision(self):
        for record in self:
            if record.state == 'validation':
                missing_fields = []
                if not record.conformity_report:
                    missing_fields.append("Rapport de conformite")
                if not record.conformity_note:
                    missing_fields.append("Note de conformité")
                
                if missing_fields:
                    raise ValidationError(_("Vous devez renseigner les champs suivants avant de passer à l'étape suivante : %s") % ", ".join(missing_fields))
                
                record.conformity_check_date = fields.Datetime.today().now()
                record.conformity_check_agent = self.env.user.id
                record.state = 'decision'
                record.message_post(body=_("Le dossier est à l'étape de décision finale."))
    
    def action_generate_certificate(self):
        """Générer le certificat d'homologation"""
        for record in self:
            if record.state == 'approved' and record.certificate_signature:
                # Marquer le certificat comme généré
                record.certificate_generated = True
                record.message_post(body=_("Le certificat d'homologation a été généré."))
                
                # Générer et retourner le rapport PDF du certificat
                return self.env.ref('patnuc_minader_homologation_engrais_fertilisants.action_report_homologation_certificate').report_action(record)
    
    def action_approve(self):
        for record in self:

            if not record.decision_note:
                raise ValidationError(_("Vous devez renseigner une note de décision avant d'approver le produit."))
            if not (record.reception_pv or record.homologation_arretement):
                raise ValidationError(_("Vous devez renseigner au moins un des champs 'Reception PV' ou 'Homologation arrêté' avant d'approver le produit."))
            if record.state == 'decision':
                record.decision_date = fields.Datetime.today().now()
                record.decision_agent = self.env.user.id
                record.state = 'approved'
                record.message_post(body=_("Le produit a été homologué avec succès."))

    def action_sign(self):
        for record in self:
            if record.state == 'approved':
                if not record.homologation_document:
                    raise ValidationError(_("Vous devez renseigner le document d'homologation avant de signer."))
                if not record.arrete_id :
                    raise ValidationError(_("Impossible de signer. Cette demande de modification n'est liée à aucun Arrêté d'Homologation actif."))
                if record.product_id : 
                    new_product = record.product_id
                    update_data = {
                    # Copie du Nom Commercial du nouveau produit 
                    'commercial_name': new_product.id,
                    # Copie du Nom Technique du nouveau produit 
                    'technical_name': new_product.technical_name,
                    # Copie du Fabricant 
                    'manufacturer_id': new_product.manufacturer_id.id 
                    }
                    # Écriture des nouvelles données dans l'Arrêté d'Homologation
                    record.arrete_id.write(update_data)
                #enregistremnt agent et date insert sign_doc
                record.signature_agent = self.env.user.id
                record.date_signature = fields.Datetime.today().now()
                record.state = 'signed'
                


                record.message_post(body=_("L'Homologation a été et signé."))
    
    # (Q) Méthode pour rejeter avec motif
    def action_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rejeter la demande',
            'res_model': 'fertilizer.mod.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state
            }
        }
    
    def _notify_applicant_approval(self):
        """Notifier le demandeur de l'approbation"""
        if self.applicant_id:
            self.message_post(
                body=_("Votre demande d'homologation %s a été approuvée.") % self.name,
                partner_ids=[self.applicant_id.id],
                message_type='comment'
            )
    
    def _notify_applicant_rejection(self):
        """Notifier le demandeur du rejet"""
        if self.applicant_id:
            self.message_post(
                body=_("Votre demande de modification d'homologation %s a été rejetée.") % self.name,
                partner_ids=[self.applicant_id.id],
                message_type='comment'
            )
    
    # Méthode pour retourner au dépôt depuis la vérification
    def action_return_to_draft(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retourner au dépôt',
            'res_model': 'fertilizer.mod.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'draft'
            }
        }

    # Méthode pour retourner a l'analyse chimique
    def action_return_to_lab_analysis(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Retourner a l'analyse",
            'res_model': 'fertilizer.mod.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'analysis'
            }
        }

     # Méthode pour retourner aux tests agronomique
    def action_return_to_field_test(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Retourner aux Test",
            'res_model': 'fertilizer.mod.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'field_test'
            }
        }

    # Méthode pour retourner a l'evaluation agro-economique
    def action_return_to_economic_eval(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Retourner a l'evaluation agro-economique",
            'res_model': 'fertilizer.mod.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'economic_eval'
            }
        }

    # Méthode pour retourner a la verification administrative
    def action_return_to_admin_check(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Retourner a la verification administrative",
            'res_model': 'fertilizer.mod.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'synthesis'
            }
        }

    # Méthode pour retourner a la validation de conformite
    def action_return_to_conformity_check(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Retourner a la validation de conformite",
            'res_model': 'fertilizer.mod.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mod_homologation_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'validation'
            }
        }

    # Méthode pour retourner à la vérification depuis l'analyse
    def action_return_to_verification(self):
        for record in self:
            if record.state == 'analysis':
                record.state = 'verification'
                record.message_post(body=_("Le dossier est retourné à l'étape de vérification administrative."))

    
    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'
            record.message_post(body=_("Le dossier a été réinitialisé à l'état brouillon."))
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('fertilizer.mod.homologation') or _('New')
        self._capture_filenames(vals)
        return super(FertilizerModHomologation, self).create(vals)
    
    def write(self, vals):
        self._capture_filenames(vals)
        result = super(FertilizerModHomologation, self).write(vals)
        
        # Forcer la récupération des noms de fichiers après l'upload
        binary_fields = ['official_request_letter', 'homologation_certificate', 'import_agreement_copy', 'identity_document_copy']
        if any(field in vals for field in binary_fields):
            self._update_filename_from_attachment()
        
        return result
    
    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'rejected']:
                raise UserError(_('Vous ne pouvez pas supprimer un dossier qui n\'est pas en brouillon ou rejeté.'))
        return super(FertilizerModHomologation, self).unlink()