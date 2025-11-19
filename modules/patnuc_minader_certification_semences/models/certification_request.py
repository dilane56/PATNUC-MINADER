from odoo import models, fields, api, _
from odoo.exceptions import UserError 
import logging
import base64
from datetime import datetime, timedelta


_logger = logging.getLogger(__name__)

class CertificationRequest(models.Model):
    _name = 'certification.request'
    _description = 'Demande de Certification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char('Référence', required=True, copy=False, readonly=True,
                      default=lambda self: self.env['ir.sequence'].next_by_code('certification.request'))
    
    # Informations générales
    operator_id = fields.Many2one('certification.operator', string='Opérateur',required=True, tracking=True)
    
    # Informations automatiques de l'opérateur (res.partner)
    operator_name = fields.Char(related='operator_id.partner_name', string='Nom complet', readonly=True)
    operator_email = fields.Char(related='operator_id.partner_email', string='Email', readonly=True)
    operator_phone = fields.Char(related='operator_id.partner_phone', string='Téléphone', )
    operator_statut= fields.Selection([
        ('personne morale','personne morale'),
        ('personne physique','personne physique'),
    ],string='Statut',)
    operator_raison_sociale = fields.Selection([
        ('sa','sa'),
        ('sarl','sarl'),
        ('association','association'),
        ('coopérative','coopérative'),
        ('gic','gic'),
    ], string='Raison sociale')


    # Informations complémentaires
    agricole_campain = fields.Char(string="Campagne agricole")
    encadrement_structure = fields.Char(string="Structure d'encadrement et/ou d'appui")


    # Champs related de la parcelle
    parcelle_espece = fields.Selection(related='parcelle_id.espece', string='Espèce de semence', readonly=True)
    parcelle_variete = fields.Selection(related='parcelle_id.variete', string='Variété de semence', readonly=True)
    parcelle_superficie = fields.Float(related='parcelle_id.superficie', string='Superficie (ha)', readonly=True)
    parcelle_frais = fields.Float(related='parcelle_id.frais_redevance', string='Frais de redevance (FCFA)', readonly=True)
    parcelle_qte_sem_meres = fields.Float(related='parcelle_id.quantite_semences_meres', string='Quantité de célèves mères', readonly=True)
    parcelle_production = fields.Float(related='parcelle_id.production_attendue', string='Production attendue (ha)', readonly=True)
    parcelle_origine = fields.Text(related='parcelle_id.origine_semence_mere', string='Origine de la semence mère',
                                   readonly=True)

    parcelle_categorie = fields.Selection(related='parcelle_id.categorie', string='Catégorie', readonly=True)

    parcelle_region = fields.Many2one(related='parcelle_id.region_id', string='Région', readonly=True)

    parcelle_departement = fields.Many2one(related='parcelle_id.departement_id', string='Département', readonly=True)

    parcelle_arrondissement = fields.Many2one(related='parcelle_id.arrondissement_id', string='Arrondissement',
                                              readonly=True)

    parcelle_support_structure = fields.Char(related='parcelle_id.encadrement_structure',
                                             string="Structure d'encadrement ou d'appui", readonly=True)
    
    parcelle_categorie = fields.Selection(related='parcelle_id.categorie', string='Catégorie', readonly=True)


    # Documents requis
    declaration_activite_semenciere_timbre = fields.Binary('Déclaration d\'activité semencière', required=True)
    declaration_activite_semenciere_timbre_filename = fields.Char('Nom du timbre')
    redevance_semenciere_payement_receipt = fields.Binary('Relevé de paiement des frais de redevance', required=True)
    redevance_semenciere_payement_receipt_filename = fields.Char('Nom du timbre')


    # Vérification de documents
    declaration_activite_semenciere_verified = fields.Boolean(string='Déclaration d\'activité semencière vérifiée')
    payement_receipt_verified = fields.Boolean(string='Relevé de paiement des frais de redevance vérifié')
    documents_verfication_comment = fields.Text(string="Commentaire de l'agent", tracking=True)
    documents_verfication_agent = fields.Many2one('res.users', string='Agent de vérification', tracking=True)
    documents_verfication_date = fields.Datetime('Date de vérification', tracking=True)

    #Inspection des champs
    lot_ids = fields.One2many(
        'certification.parcelle.lot',
        'request_id',
        string="Lots de production"
    )

    inspection_ids = fields.One2many(
        'certification.inspection',
        'request_id',  # on doit ajouter ce champ dans le modèle inspection aussi
        string="Inspections"
    )

    inspections_done_count = fields.Integer(
        string="Inspections terminées",
        compute="_compute_inspections"
    )
    # Minimum 3 inspections requises par lot
    min_inspections_required = fields.Integer(string="Inspections minimales requises", default=3)
    lots_ready = fields.Boolean(string="Lots prêts", compute="_compute_lots_ready")
    
    # Nouveaux champs pour un meilleur résumé
    total_lots_count = fields.Integer(string="Nombre total de lots", compute="_compute_inspection_summary")
    lots_with_enough_inspections = fields.Integer(string="Lots avec ≥3 inspections", compute="_compute_inspection_summary")
    lots_completed = fields.Integer(string="Lots terminés", compute="_compute_inspection_summary")
    inspection_progress = fields.Char(string="Progression", compute="_compute_inspection_summary")
    all_lots_inspection_complete = fields.Boolean(string="Toutes inspections terminées", compute="_compute_inspection_summary")
    all_documents_verified = fields.Boolean(string='Tous documents vérifiés', compute='_compute_all_documents_verified')

    
    #champs pour l'analyse en laboratoire
    analysis_done_count = fields.Integer(string="Prélèvements terminés", compute="_compute_lab_analysis_summary")
    analysis_summary_compliant_lots = fields.Integer(string="Lots conformes à l'analyse", compute="_compute_lab_analysis_summary")
    analysis_lots_progress = fields.Char(string="Progression analyse lots", compute="_compute_lab_analysis_summary")
    all_lots_analysis_complete = fields.Boolean(string="Tous lots analysés", compute="_compute_lab_analysis_summary")
    has_lab_report = fields.Boolean('Rapport labo créé', compute='_compute_has_lab_report')
    
    # champs calculés pour les prelevements d'analyses des lotq
    prelevement_lot_analysis_ids = fields.One2many(
        comodel_name='prelevement.lot.certification',
        inverse_name='request_id', # Non stocké, juste pour lier
        string='Détail des Analyses de Prélèvement',
        compute='_compute_prelevement_lot_analysis_ids',
        store=False, # Important, car c'est un champ calculé
    )
    
    # Workflow et suivi
    state = fields.Selection([
        ('draft', 'Declaration des cultures'),
        ('doc_verification', 'Verification des documents'),
        ('inspection', 'Inspection des champ Semencier'),
        ('sampling', 'Echantillonage et Analyse'),
        ('certification', 'Certification des lots de semences'),
        ('labelling', 'Certificat délivré'),
        ('approved', 'Certificat Approuvé'),
        ('rejected', 'Rejetée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    # Dates importantes
    submission_date = fields.Datetime('Date de soumission', tracking=True, default=fields.Datetime.today().now())
    # reception_date = fields.Datetime('Date de réception', tracking=True)
    # expected_completion_date = fields.Date('Date prévue de finalisation')
    # completion_date = fields.Datetime('Date de finalisation')
    
    
    # Assignations
    regional_officer_id = fields.Many2one('res.users', string='Agent régional assigné')
    technical_reviewer_id = fields.Many2one('res.users', string='Réviseur technique')
    
    # Relations
    parcelle_id = fields.Many2one('certification.parcelle', string='Parcelle déclarée', required=True)
    field_control_ids = fields.One2many('certification.field.control', 'request_id',
       
       
                                    string='Contrôles terrain')
    
    # Informations de localisation
    region_id = fields.Many2one("minader.region", string="Région", related='parcelle_id.region_id', readonly=True,store=True)
    departement_id = fields.Many2one("minader.departement", string="Département",related='parcelle_id.departement_id',readonly=True,store=True )
    arrondissement_id = fields.Many2one("minader.arrondissement", string="Arrondissement",related='parcelle_id.arrondissement_id',readonly=True,store=True)
    localite_id = fields.Char(string="Localité", related='parcelle_id.localite_id',readonly=True,store=True)
    
    
    
    # elements de labo 
    laboratory_analysis_ids = fields.One2many('certification.laboratory.analysis', 'request_id',
                                            string='Analyses laboratoire')
    
    
    technical_exam_ids = fields.One2many('certification.technical.review', 'request_id', string='Technical exam')
    certificate_id = fields.Many2one('certification.certificate', string='Certificat')
    
    #rapport d'analyse en labo
    labo_report_pdf = fields.Binary(
        string='PDF du rapport final',
        compute='_compute_latest_analysis_details', 
        # related ne fonctionne pas sur One2many. On utilise compute pour trouver le dernier rapport.
    )
    
    labo_report_pdf_filename = fields.Char(
        string='Nom du PDF',
        compute='_compute_latest_analysis_details',
    )
    
    note_labo_final = fields.Text(
        string='Avis technique',
        compute='_compute_latest_analysis_details',
    )
    # Commentaires et observations
    notes = fields.Text('Notes internes')
    rejection_reason = fields.Text('Motif de rejet')

    # champs pour le retour a l'etape precedente
    return_reason = fields.Text('Motif de retour')
    retuned_by = fields.Many2one('res.users', 'Retourné par')
    return_date = fields.Datetime('Date de retour')
    returned_from_state = fields.Char(string='Retourné depuis l\'étape')
    
    # Rapport final d'inspection (relation avec le modèle existant)
    final_inspection_report_id = fields.Many2one('certification.inspection.final', string='Rapport final d\'inspection')
    has_final_report = fields.Boolean('Rapport final créé', compute='_compute_has_final_report')
    
    # Champs pour affichage rapide des informations du rapport final
    final_report_summary = fields.Text(related='final_inspection_report_id.summary', string='Synthèse du rapport final', readonly=True)
    final_report_decision = fields.Selection(related='final_inspection_report_id.decision', string='Décision finale', readonly=True)
    final_report_pdf = fields.Binary(related='final_inspection_report_id.final_report', string='PDF du rapport final', readonly=True)
    final_report_pdf_filename = fields.Char(related='final_inspection_report_id.final_report_filename', string='Nom du PDF', readonly=True)
    final_report_created_by = fields.Many2one(related='final_inspection_report_id.created_by', string='Rapport créé par', readonly=True)
    final_report_created_date = fields.Datetime(related='final_inspection_report_id.created_date', string='Date de création du rapport', readonly=True)

    # champs calculés lot certification
    
    certification_progress = fields.Float(
        string="Progression de la certification (%)",
        compute='_compute_certification_progress',
        store=True, # Optionnel : stocker la valeur pour des recherches ou des graphiques
        digits=(16, 2)
    )
    nombre_lots_demandes = fields.Integer(
        string="Nombre de lots demandés",
        default=1, # Assure une valeur par défaut pour éviter la division par zéro dans le calcul de progression
        help="Nombre total de lots pour lesquels la certification est demandée."
    )
    cert_final_decision = fields.Selection([
        ('pending', 'En attente de décision'),
        ('certified', 'Certifié'),
        ('refused', 'Refusé'),
    ], string="Décision Finale de Certification", default='pending', copy=False, readonly=True,
       help="Décision finale prise par l'organisme de certification.")
    
    #champ certificat
    cert_report = fields.Binary(string="certifiat délivré et signé", required=True)
    cert_report_filename = fields.Char(string="Nom du fichier PDF")
    
     #champs calculés lots 
    compliant_lots_ids = fields.Many2many(
        comodel_name='certification.parcelle.lot',
        string="Lots Conformés (Analyses Terminées et Conformes)",
        compute='_compute_compliant_lots_ids',
        store=False 
    )
    # arrete final 
    # --- Avis final ---
    certificate_document = fields.Binary(
    string="Certificat signé ",
    help="Copie PDF ou image du certificat délivré."
    )
    certificate_document_filename = fields.Char(
    string="Nom du fichier " )
    
    final_comment = fields.Text(
        string="Commentaire final",
        help="Observations et recommandations formulées lors de la décision finale."
    )

    final_decision_date = fields.Date(
        string="Date de décision finale",
        help="Date de la réunion ou de la validation de l'avis final."
    )

    final_decision_by = fields.Many2one(
        'res.users',
        string="Décision prise par",
        help="Responsable ayant émis l'avis final."
    )
    def action_approve(self):
        for record in self:
            record.state = 'approved'
            record.final_decision_by= self.env.user
            record.final_decision_date = fields.Datetime.now()
        
    @api.depends('lot_ids')
    def _compute_compliant_lots_ids(self):
        """
        Calcule les lots qui ont au moins une analyse de prélèvement terminée et conforme.
        C'est le champ qui répond spécifiquement à la demande.
        """
        for record in self:
            compliant_lot_set = set()
            lot_ids = record.lot_ids.ids
            
            if lot_ids:
                # Recherche des analyses terminées et conformes
                compliant_analyses = self.env['prelevement.lot.certification'].search([
                    ('lot_id', 'in', lot_ids),
                    ('state', '=', 'done'),
                    ('result', '=', 'compliant')
                ])
                
                # Collecte les IDs de lots uniques qui sont considérés comme conformes
                compliant_lot_set = {analysis.lot_id.id for analysis in compliant_analyses}
                
            record.compliant_lots_ids = [(6, 0, list(compliant_lot_set))]
    
    
    
    def action_open_certification_lots(self):
        """
        Ouvre une vue (action de fenêtre) affichant tous les Arrêtés de Certification
        Générale (certification.lots) liés à la demande actuelle.
        """
        # Cible le modèle des Arrêtés Généraux (certification.lots)
        lot_model_name = 'certification.lots' 

        # Récupération des IDs des vues Tree et Form du modèle 'certification.lots'
        # Ces IDs correspondent exactement à ceux de votre fichier XML
        tree_view_id = self.env.ref('patnuc_minader_certification_semences.view_certification_lots_tree').id
        form_view_id = self.env.ref('patnuc_minader_certification_semences.view_certification_lots_form').id

        return {
            # Nom plus précis pour l'action de fenêtre
            'name': 'Arrêtés de Certification Générale',
            'type': 'ir.actions.act_window',
            'res_model': lot_model_name,
            'view_mode': 'tree,form',
            
            # Utilisation des IDs de vue corrects
            'views': [
                (tree_view_id, 'tree'),
                (form_view_id, 'form'),
            ],
            
            'target': 'current',
            # Filtre pour n'afficher que les Arrêtés liés à la Demande (self.id)
            'domain': [('request_id', '=', self.id)], 
            'context': {
                # Passe l'ID par défaut si l'utilisateur clique sur 'Créer'
                'default_request_id': self.id, 
            }
        }
    
    def _compute_lot_certification_count(self):
        """
        Calcule le nombre de lots de certification associés à la demande.
        Nous supposons que le modèle de lot s'appelle 'certification.by.lot'
        et qu'il a un champ 'request_id' qui pointe vers la demande en cours.
        """
        # Récupère l'ID des demandes en cours de traitement
        request_ids = self.ids 

        # Effectue une recherche groupée pour compter les lots par demande (request_id)
        lots_data = self.env['certification.by.lot'].read_group(
            [('request_id', 'in', request_ids)],
            ['request_id'],
            ['request_id']
        )
        
        # Mappe les résultats du compteur
        count_map = {
            data['request_id'][0]: data['request_id_count'] 
            for data in lots_data
        }

        # Assigne le résultat à chaque enregistrement
        for record in self:
            record.lot_certification_count = count_map.get(record.id, 0)
    
    @api.depends('laboratory_analysis_ids.prelevement_lots')
    def _compute_prelevement_lot_analysis_ids(self):
        """Calcule tous les enregistrements de prélèvement de lots associés à cette demande via les fiches d'analyse laboratoire."""
        for record in self:
            all_prelevements = self.env['prelevement.lot.certification']
            # Utiliser l'opérateur union (|) pour agréger les records
            for lab_analysis in record.laboratory_analysis_ids:
                all_prelevements |= lab_analysis.prelevement_lots
            record.prelevement_lot_analysis_ids = all_prelevements
            
    @api.depends('laboratory_analysis_ids.analysis_report', 
                 'laboratory_analysis_ids.analysis_report_filename', 
                 'laboratory_analysis_ids.technical_opinion')
    def _compute_latest_analysis_details(self):
        """
        Calcule les détails du rapport de laboratoire en trouvant la dernière analyse effectuée.
        Ceci est nécessaire car 'related' n'est pas supporté sur les champs One2many.
        """
        for request in self:
            # Recherche la dernière analyse créée pour cette demande
            latest_analysis = self.env['certification.laboratory.analysis'].search([
                ('request_id', '=', request.id)
            ], order='create_date desc', limit=1)

            if latest_analysis:
                # Assignation des valeurs du dernier enregistrement d'analyse
                request.labo_report_pdf = latest_analysis.analysis_report
                request.labo_report_pdf_filename = latest_analysis.analysis_report_filename
                request.note_labo_final = latest_analysis.technical_opinion
            else:
                # Valeurs par défaut si aucune analyse n'existe
                request.labo_report_pdf = False
                request.labo_report_pdf_filename = False
                request.note_labo_final = False

    # Commentaires et observations
    notes = fields.Text('Notes internes')
    rejection_reason = fields.Text('Motif de rejet')

    @api.depends('inspection_ids.state')
    def _compute_inspections(self):
        for rec in self:
            rec.inspections_done_count = len(
                rec.inspection_ids.filtered(lambda i: i.state == 'done')
            )
    
    @api.depends('lot_ids', 'inspection_ids.state')
    def _compute_lots_ready(self):
        for rec in self:
            if not rec.lot_ids:
                rec.lots_ready = False
                continue
            
            all_lots_ready = True
            for lot in rec.lot_ids:
                lot_inspections = rec.inspection_ids.filtered(
                    lambda i: i.lot_id.id == lot.id and i.state == 'done'
                )
                if len(lot_inspections) < rec.min_inspections_required:
                    all_lots_ready = False
                    break
            
            rec.lots_ready = all_lots_ready
    
    @api.depends('lot_ids', 'inspection_ids.state')
    def _compute_inspection_summary(self):
        for rec in self:
            total_lots = len(rec.lot_ids)
            lots_with_enough = 0
            lots_completed = 0
            
            for lot in rec.lot_ids:
                lot_inspections = rec.inspection_ids.filtered(lambda i: i.lot_id.id == lot.id)
                done_inspections = lot_inspections.filtered(lambda i: i.state == 'done')
                
                if len(done_inspections) >= rec.min_inspections_required:
                    lots_with_enough += 1
                    lots_completed += 1
                elif len(lot_inspections) >= rec.min_inspections_required:
                    lots_with_enough += 1
            
            rec.total_lots_count = total_lots
            rec.lots_with_enough_inspections = lots_with_enough
            rec.lots_completed = lots_completed
            rec.all_lots_inspection_complete = (lots_completed == total_lots and total_lots > 0)
            
            if total_lots == 0:
                rec.inspection_progress = "Aucun lot créé"
            else:
                rec.inspection_progress = f"{lots_completed}/{total_lots} lots terminés"
    
    @api.depends('final_inspection_report_id')
    def _compute_has_final_report(self):
        for rec in self:
            rec.has_final_report = bool(rec.final_inspection_report_id)

    @api.onchange('operator_id')
    def _onchange_operator_id(self):
        """Filtrer les parcelles selon l'opérateur sélectionné"""
        if self.operator_id:
            return {'domain': {'parcelle_id': [('operator_id', '=', self.operator_id.id)]}}
        else:
            return {'domain': {'parcelle_id': []}}
    
    @api.depends('declaration_activite_semenciere_verified','payement_receipt_verified')
    def _compute_all_documents_verified(self):
        for rec in self:
            rec.all_documents_verified = all([rec.payement_receipt_verified, rec.declaration_activite_semenciere_verified])
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('certification.request') or 'New'
        return super(CertificationRequest, self).create(vals)

    def action_submit(self):
        if not self.parcelle_id:
            raise UserError("Veuillez sélectionner une parcelle avant de soumettre la demande.")
        if self.return_reason:
            self.return_reason = ''
        # Ne pas lier la parcelle pour permettre la réutilisation
        self.write({'state': 'doc_verification', 'submission_date': fields.Datetime.now()})
        self.message_post(body="Demande soumise , en attente de vérification des documents.")


    def action_verified_documents(self):
        if not self.all_documents_verified:
            raise UserError("Veuillez vérifier tous les documents avant de continuer.")
        if not self.documents_verfication_comment:
            raise UserError("Veuillez ajouter un commentaire de vérification des documents.")
        if self.return_reason:
            self.return_reason = ''
        self.documents_verfication_date = fields.Datetime.now()
        self.documents_verfication_agent = self.env.user.id
        self.write({'state': 'inspection'})
        self.message_post(body="Documents vérifiés, en attente d'inspection des champ Semencier.")

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

    #fonction pour demarer l'inspection des champs
    def action_start_field_inspection(self):
        for rec in self:
            if not rec.lot_ids:
                raise UserError("Veuillez d'abord découper la parcelle en lots.")
            rec.state = 'inspection'
            rec.message_post(body="Inspection des champs lancée.")

    def action_open_lot_form(self):
        self.ensure_one()
        if not self.parcelle_id:
            raise UserError("Veuillez d'abord sélectionner une parcelle avant de créer des lots.")

        return {
            'name': "Créer un lot",
            'type': 'ir.actions.act_window',
            'res_model': 'certification.parcelle.lot',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_parcelle_id': self.parcelle_id.id,
            }
        }
    
    def action_create_final_report(self):
        """Créer le rapport final d'inspection"""
        self.ensure_one()
        if not self.all_lots_inspection_complete:
            raise UserError("Toutes les inspections doivent être terminées avant de créer le rapport final.")
        
        if self.final_inspection_report_id:
            # Ouvrir le rapport existant
            return {
                'name': 'Rapport final d\'inspection',
                'type': 'ir.actions.act_window',
                'res_model': 'certification.inspection.final',
                'res_id': self.final_inspection_report_id.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            # Créer un nouveau rapport
            return {
                'name': 'Créer rapport final d\'inspection',
                'type': 'ir.actions.act_window',
                'res_model': 'certification.inspection.final',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_request_id': self.id,
                    'default_inspection_ids': [(6, 0, self.inspection_ids.ids)],
                }
            }
    def action_start_sampling_form(self):
        """
        Action du bouton pour démarrer ou visualiser le formulaire d'analyse Laboratoire.
        
        Cette version ajoute la logique pour forcer le mode d'édition lors de l'ouverture
        modale (target: 'new') si l'analyse n'est pas terminée/validée.
        """
        self.ensure_one()
        
        AnalysisModel = self.env['certification.laboratory.analysis']
        
        # 1. Rechercher l'analyse la plus récente pour cette demande.
        lab_analysis_record = AnalysisModel.search([
            ('request_id', '=', self.id)
        ], order='create_date desc', limit=1)

        # 2. Si aucune analyse n'existe, on en crée une nouvelle.
        if not lab_analysis_record:
            lab_analysis_record = AnalysisModel.create({
                'request_id': self.id,
                'name': f"Analyse Labo - {self.name}", 
            })
            # Si c'est un nouvel enregistrement, il doit être éditable
            initial_mode = 'edit' 
        else:
            # Si l'enregistrement existe, on vérifie son état
            if lab_analysis_record.state in ('pending', 'in_progress'):
                initial_mode = 'edit'
            else:
                initial_mode = 'readonly'
                
        try:
            # Utilisez l'ID XML corrigé
            view_id = self.env.ref('patnuc_minader_certification_semences.view_form_laboratory_analysis').id
        except ValueError:
            view_id = False
        
        return {
            'name': ("Analyse Laboratoire"),
            'type': 'ir.actions.act_window',
            'res_model': 'certification.laboratory.analysis',
            'res_id': lab_analysis_record.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new', # Conserver target: 'new' comme demandé
            'context': {
                'form_view_initial_mode': initial_mode, # Force le mode d'édition/readonly initial
            }
        }

    #fonction pour valider l'inspection et passera l'etape suivante
    def action_complete_field_inspection(self):
        for rec in self:
            # 1. Vérifier qu'il y a au moins un lot créé
            if not rec.lot_ids:
                raise UserError("Aucun lot n'a été créé. Veuillez d'abord découper la parcelle en lots.")
            
            # 2. Vérifier que chaque lot a >= 3 inspections terminées
            for lot in rec.lot_ids:
                inspections_done = lot.inspection_ids.filtered(lambda i: i.state == 'done')
                if len(inspections_done) < 3:
                    raise UserError(
                        f"Le lot {lot.name} a seulement {len(inspections_done)} inspections terminées. "
                        "Minimum requis : 3 inspections terminées par lot."
                    )
            
            # 3. Vérifier qu'un rapport final d'inspection existe
            if not rec.final_inspection_report_id:
                raise UserError(
                    "Aucun rapport final d'inspection n'a été créé. "
                    "Veuillez créer le rapport final avant de terminer l'inspection."
                )
            
            # 4. Vérifier que le rapport final a une décision
            if not rec.final_inspection_report_id.decision:
                raise UserError(
                    "Le rapport final d'inspection doit contenir une décision (Valide/Rejeté) "
                    "avant de pouvoir terminer l'inspection."
                )

            rec.state = 'sampling'
            rec.message_post(body="Inspection des champs terminée et validée avec rapport final.")



    def action_complete_inspection(self):
        self.ensure_one()
        if not self.regional_officer_id:
            raise UserError("Veuillez renseigner l'agent régional assigné avant de finaliser l'inspection.")
        self.write({'state': 'sampling'})
        self._create_activity('Inspection terminée - Échantillonnage et analyse')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouveau Contrôle Terrain',
            'res_model': 'certification.field.control',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_request_id': self.id,
            },
            'target': 'new',
        }
    def action_return_to_draft(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retourner au dépôt',
            'res_model': 'certification.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_certification_request_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'draft'
            }
        }


    def action_back_to_doc_verification(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Retourner ala verification de documents',
            'res_model': 'certification.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_certification_request_id': self.id,
                'default_current_state': self.state,
                'default_target_state': 'doc_verification'
            }
        }
        
    def action_back_to_inspection(self):
        self.write({'state': 'inspection'})
    
    def action_complete_sampling(self):
        self.ensure_one()
        
        # Règle 1 : Vérifier que tous les lots ont été analysés
        if not self.all_lots_analysis_complete:
            raise UserError(
                "L'analyse de tous les lots n'est pas terminée. "
                f"Actuellement : {self.analysis_lots_progress}. "
                "Chaque lot doit avoir au moins une analyse de prélèvement marquée 'Terminée'."
            )
        
        # Règle 2 : Vérifier qu'un rapport général d'analyse laboratoire a été fourni
        # On suppose qu'une seule fiche d'analyse générale est créée (laboratory_analysis_ids)
        if not self.laboratory_analysis_ids:
            raise UserError("Veuillez créer et compléter la fiche d'Analyse Laboratoire générale.")
            
        lab_analysis = self.laboratory_analysis_ids[0]

        # Règle 3 : Vérifier que le rapport final est attaché et qu'un résultat global est donné
        if lab_analysis.state != 'completed' or not lab_analysis.result or not lab_analysis.analysis_report:
            raise UserError(
                "La fiche d'Analyse Laboratoire doit être marquée 'Terminé', "
                "contenir le Résultat global (Conforme/Non conforme) et avoir le Rapport final d'analyse attaché."
            )

        # Si toutes les règles sont remplies
        self.write({'state': 'certification'})
        self._create_activity('Échantillonnage et analyse terminés - Certification des lots')
       
        
    def action_back_to_sampling(self):
        self.write({'state': 'sampling'})
    
    def action_complete_certification(self):
        self.ensure_one()
        self.write({'state': 'labelling'})
        self._create_activity('Certification des lots terminée - Délivrance du certificat')
        
    
    # methodes calculés pour les analyses en laboratoires 

    @api.depends('laboratory_analysis_ids.prelevement_lots.state', 'laboratory_analysis_ids.prelevement_lots.result', 'lot_ids')
    def _compute_lab_analysis_summary(self):
        """Calcule le résumé de l'état d'analyse des échantillons de lots."""
        for rec in self:
            total_lots = len(rec.lot_ids)
            lots_analyzed = 0
            lots_compliant = 0
            
            # Collecter toutes les analyses de lots terminées pour cette demande
            # Note: laboratory_analysis_ids est un O2M vers la fiche générale d'analyse, 
            # et prelevement_lots est un O2M de cette fiche vers les analyses de lots.
            done_lot_analyses = rec.laboratory_analysis_ids.prelevement_lots.filtered(
                lambda l: l.state == 'done'
            )
            
            # Dictionnaire pour suivre les lots qui ont été analysés (par ID)
            analyzed_lot_ids = set()

            for lot in rec.lot_ids:
                # Chercher si ce lot spécifique a une analyse terminée
                analysis_for_lot = done_lot_analyses.filtered(
                    lambda l: l.lot_id.id == lot.id
                )
                
                if analysis_for_lot:
                    # On compte le lot comme analysé si au moins une analyse est done
                    lots_analyzed += 1
                    analyzed_lot_ids.add(lot.id)

                    # Vérifier la conformité du dernier résultat d'analyse pour ce lot
                    if analysis_for_lot[-1].result == 'compliant':
                        lots_compliant += 1

            rec.analysis_done_count = len(done_lot_analyses)
            rec.analysis_summary_compliant_lots = lots_compliant
            
            rec.all_lots_analysis_complete = (lots_analyzed == total_lots and total_lots > 0)
            
            if total_lots == 0:
                rec.analysis_lots_progress = "Aucun lot à analyser"
            else:
                rec.analysis_lots_progress = f"{lots_analyzed}/{total_lots} lots analysés"

    @api.depends('laboratory_analysis_ids.analysis_report')
    def _compute_has_lab_report(self):
        """Vérifie si un rapport général d'analyse laboratoire a été soumis."""
        for rec in self:
            # On vérifie si une analyse labo existe et si elle a un rapport (analysis_report)
            rec.has_lab_report = bool(rec.laboratory_analysis_ids and rec.laboratory_analysis_ids[0].analysis_report)

    # ------------------------------------------
        
    def action_back_to_certification(self):
        self.write({'state': 'certification'})
    
    def action_issue_certificate(self):
        self.write({
            'state': 'labelling',
            # 'completion_date': fields.Datetime.now()
        })
        self._generate_certificate()
        self._create_activity('Certificat délivré')
    
    def action_start_inspection(self):
        """Démarrer l'inspection des champs semenciers"""
        self.ensure_one()
        # if not self.regional_officer_id:
        #     raise UserError("Veuillez renseigner l'agent régional assigné avant de démarrer l'inspection.")
        self._create_field_control_record()
        self._create_activity('Inspection des champs semenciers démarrée')
    
    def action_start_sampling(self):
        """Échantillonnage et analyse"""
        self.ensure_one()
        self._create_laboratory_analysis_record()
        self._create_activity('Échantillonnage et analyse démarrés')
    
    def action_start_certification(self):
        """Démarrer la certification des lots"""
        self.ensure_one()
        self._create_activity('Certification des lots démarrée')
    
    def action_get_certificat(self):
        """
        Fonction permettant d'imprimer le certificat de semence
        """
        return self.env['ir.actions.report']._get_report_from_name(
            'patnuc_minader_certification_semences.report_certificate_document'
            ).report_action(self)
    
    def action_reject(self):
        """Rejeter la demande de certification"""
        if not self.rejection_reason:
            raise UserError("Veuillez saisir le motif de rejet avant de rejeter la demande.")
        self.write({
            'state': 'rejected',
            # 'completion_date': fields.Datetime.now()
        })
        self._create_activity(f'Demande rejetée: {self.rejection_reason}')
        
    def action_cancel(self):
        """Annuler la demande de certification"""
        self.write({
            'state': 'cancelled',
            # 'completion_date': fields.Datetime.now()
        })
        self._create_activity('Demande annulée')
    
    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        self.write({
            'state': 'draft',
            # 'completion_date': False,
            'rejection_reason': False
        })
        self._create_activity('Demande remise en brouillon')
    
    def _update_filename_from_attachment(self, binary_field, filename_field):
        """Méthode utilitaire pour récupérer le nom de fichier depuis les attachments"""
        if self.id:
            # Rechercher l'attachment le plus récent pour ce champ
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('res_field', '=', binary_field)
            ], order='id desc', limit=1)
            
            if attachment and attachment.name:
                # Mettre à jour le nom de fichier directement sans déclencher write à nouveau
                self.env.cr.execute(
                    f"UPDATE {self._table} SET {filename_field} = %s WHERE id = %s",
                    (attachment.name, self.id)
                )
                # Invalider le cache pour ce champ
                self.invalidate_cache([filename_field])
                return attachment.name
        return None
    
    def action_update_filenames(self):
        """Action pour forcer la mise à jour des noms de fichiers"""
        binary_fields = {
            'request_form': 'request_form_filename',
            'professional_card': 'professional_card_filename',
            'cultivation_plan_doc': 'cultivation_plan_doc_filename',
            'soil_analysis': 'soil_analysis_filename',
            'seed_origin_certificate': 'seed_origin_certificate_filename',
            'cni_copy': 'cni_copy_filename',
            'location_proof': 'location_proof_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if getattr(self, binary_field):
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def create(self, vals):
        # Capturer les noms de fichiers depuis le contexte lors de la création
        self._capture_filenames(vals)
        return super(CertificationRequest, self).create(vals)
    
    def write(self, vals):
        # Capturer les noms de fichiers depuis le contexte lors de la modification
        self._capture_filenames(vals)
        result = super(CertificationRequest, self).write(vals)
        
        # Après l'écriture, essayer de récupérer les noms de fichiers depuis les attachments
        binary_fields = {
            'request_form': 'request_form_filename',
            'professional_card': 'professional_card_filename',
            'cultivation_plan_doc': 'cultivation_plan_doc_filename',
            'soil_analysis': 'soil_analysis_filename',
            'seed_origin_certificate': 'seed_origin_certificate_filename',
            'cni_copy': 'cni_copy_filename',
            'location_proof': 'location_proof_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field]:
                # Si un fichier a été uploadé, essayer de récupérer son nom
                if not vals.get(filename_field):
                    self._update_filename_from_attachment(binary_field, filename_field)
        
        return result
    
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        # Mapping des champs Binary vers leurs champs filename correspondants
        binary_fields = {
            'request_form': 'request_form_filename',
            'professional_card': 'professional_card_filename',
            'cultivation_plan_doc': 'cultivation_plan_doc_filename',
            'soil_analysis': 'soil_analysis_filename',
            'seed_origin_certificate': 'seed_origin_certificate_filename',
            'cni_copy': 'cni_copy_filename',
            'location_proof': 'location_proof_filename',
        }
        
        # Vérifier chaque champ Binary pour capturer le nom de fichier
        for binary_field, filename_field in binary_fields.items():
            # Si un fichier est uploadé
            if binary_field in vals and vals[binary_field]:
                # Vérifier si le nom de fichier n'est pas déjà fourni
                if filename_field not in vals or not vals[filename_field]:
                    # Essayer plusieurs méthodes pour récupérer le nom
                    filename = None
                    
                    # 1. Depuis le contexte direct
                    filename = self.env.context.get(f'{binary_field}_filename')
                    
                    # 2. Depuis le contexte avec différentes clés possibles
                    if not filename:
                        for key in [f'default_{filename_field}', filename_field, f'{binary_field}_name']:
                            filename = self.env.context.get(key)
                            if filename:
                                break
                    
                    # 3. Depuis les paramètres de la requête HTTP si disponible
                    if not filename and hasattr(self.env, 'request') and self.env.request:
                        request_files = getattr(self.env.request, 'httprequest', None)
                        if request_files and hasattr(request_files, 'files'):
                            for file_key, file_obj in request_files.files.items():
                                if binary_field in file_key and hasattr(file_obj, 'filename'):
                                    filename = file_obj.filename
                                    break
                    
                    # 4. Si toujours pas de nom, utiliser un nom par défaut descriptif
                    if not filename:
                        default_names = {
                            'request_form': 'formulaire_demande.pdf',
                            'professional_card': 'carte_professionnelle.pdf',
                            'cultivation_plan_doc': 'plan_culture.pdf',
                            'soil_analysis': 'analyse_sol.pdf',
                            'seed_origin_certificate': 'attestation_origine.pdf',
                            'cni_copy': 'copie_cni.pdf',
                            'location_proof': 'preuve_localisation.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename

    def _create_activity(self, summary):
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=summary,
            user_id=self.regional_officer_id.id or self.env.user.id
        )
        
    
    def _create_field_control_record(self):
        self.env['certification.field.control'].create({
            'request_id': self.id,
            'scheduled_date': fields.Date.today(),
            # 'inspector_id': self.regional_officer_id.id
        })
    
    def _create_laboratory_analysis_record(self):
        self.env['certification.laboratory.analysis'].create({
            'request_id': self.id,
            'analysis_date': fields.Date.today(),
            'laboratory_id': self.env.ref('patnuc_minader_certification_semences.lnad_lab').id
        })
        
    def action_generate_certificate(self):
        """ Méthode publique appelée par le bouton """
        self.ensure_one()
        # Générer un nom de fichier unique avec un horodatage
        now = fields.Datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f'Certificat_de_Semence_{self.name}_{now}.pdf'
        report_action= self.env.ref('patnuc_minader_certification_semences.report_certificat_document_action').report_action(self)
        report_action['name'] = report_name
        return report_action
        # return self._generate_certificate()
        
    
    def _generate_certificate(self):
        certificate = self.env['certification.certificate'].create({
            'request_id': self.id,
            'operator_id': self.operator_id.id,
            'issue_date': fields.Date.today(),
            'name': self.env['ir.sequence'].next_by_code('certification.certificate')
        })
        self.certificate_id = certificate.id
        self.state = 'labelling'