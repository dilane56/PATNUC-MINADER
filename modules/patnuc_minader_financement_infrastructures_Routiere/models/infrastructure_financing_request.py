from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

#Modèle principal de demande de financement
class InfrastructureFinancingRequest(models.Model):

    # (Q) Informations de base sur le modèle
    _name = 'infrastructure.financing.request'
    _description = "Demande de Financement d'Infrastructure Communale"

    # (Q) Héritage mail.thread et mail.activity.mixin pour le chatter
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # (Q) Configuration pour le chatter
    _mail_post_access = 'read'

    #Les enregistrements seront triés par date de création, de la plus récente à la plus ancienne
    _order = 'create_date desc'
    
    # (Q) Documents requis centralisés pour éviter la duplication
    REQUIRED_DOCUMENTS = [
        'official_request',
        'location_plan', 
        'communal_commitment',
        'environmental_impact'
    ]

    #Ce champ sert à identifier chaque demande de financement de façon unique.
    name = fields.Char(string="Référence/code de la demande", required=True, copy=False, readonly=True, default=lambda self: _('Nouveau'))

    # (Q) lien vers la commune qui fait la demande
    commune_id = fields.Many2one('infrastructure.commune', string='Commune', 
                                required=True, tracking=True)
    
    # (Q) Dates de traitement
    submission_date = fields.Datetime('Date de soumission', tracking=True)
    decision_date = fields.Date('Date Décision Finale', tracking=True)
    approval_date = fields.Date('Date d\'approbation', tracking=True)
    processing_days = fields.Integer('Jours de traitement', compute='_compute_processing_days', store=True)


    #État de la demande
    state = fields.Selection([
        ('draft', 'Dépôt du dossier'),
        ('verification', 'Vérification & Conformité'),
        ('technical_support', 'Appui Technique'),
        ('review','Revue et Compilation'),
        ('final_decision', 'Décision Finale'),
        ('approuvee', 'Approuvée'),
        ('rejected', 'Rejetée')
    ], string="État", default='draft', tracking=True)


    # Acteurs impliqués
    delegation_id = fields.Many2one('infrastructure.delegation', 
                                   string='Délégation Responsable')
    dgrcv_user_id = fields.Many2one('res.users', string='Responsable DGRCV')
    
    secretary_general_id = fields.Many2one('res.users', 
                                         string='Secrétaire Général/Cabinet')

########################

    infrastructure_type = fields.Selection([
        ('road', 'Infrastructure routière'),
        ('artwork', 'Ouvrage d’art'),
        ('mini_infra', 'Mini-infrastructure rurale / agricole /  communautaire'),
    ], string="Type d’infrastructure", required=True, tracking=True)

    road_id = fields.One2many('infrastructure.road', 'request_id', string="Fiche Route")
    artwork_id = fields.One2many('infrastructure.artwork', 'request_id', string="Fiche Ouvrage d’art")
    mini_id = fields.One2many('infrastructure.mini', 'request_id', string="Fiche Mini-infrastructure")

########################                                     

    #Informations sur le projet
    # (Q) Tracking ajouté sur project_title pour suivre les changements
    project_title = fields.Char(string="Titre du projet", required=True, tracking=True)
    project_description = fields.Text(string="Description du projet")


    #location = fields.Char(string="Localisation" , required=True)

    # Informations de localisation
    
    localite_id = fields.Char(string="Localité", required=True)


    # (Q) information sur les bénéficiaires
    estimated_budget = fields.Float(string="Budget estimé (FCFA)")
    currency_id = fields.Many2one('res.currency', string='Devise', 
                                 default=lambda self: self.env.company.currency_id)

    # Dates et délais - supprimé car déjà défini plus haut
    expected_completion_date = fields.Date('Date prévue de fin', compute='_compute_expected_date')
    actual_completion_date = fields.Date('Date réelle de fin')

    # Dates et notes de revue
    review_notes = fields.Text(string="Notes de revue")
    review_date = fields.Datetime(string="Date de revue", tracking=True)
    is_review_complete = fields.Boolean(string="Revue complète", default=False)


    # Documents requis
    official_request_file = fields.Binary('Lettre de demande officielle', required=True)
    official_request_filename = fields.Char('Nom du fichier')
    
    location_plan_file = fields.Binary('Plan de situation de l\'infrastructure', required=True)
    location_plan_filename = fields.Char('Nom du fichier')
    
    communal_commitment_file = fields.Binary('Approbation du conseil municipal', required=True)
    communal_commitment_filename = fields.Char('Nom du fichier')
    
    environmental_impact_file = fields.Binary("Évaluation de l'impact environnemental", required=True)
    environmental_impact_filename = fields.Char('Nom du fichier')
    
    # Champs pour compatibilité avec l'appui technique
    documents_ids = fields.One2many('infrastructure.document', 'request_id', string="Documents")
    documents_count = fields.Integer(string="Nombre de documents", compute='_compute_documents_count')
    required_documents_complete = fields.Boolean('Documents requis complets', compute='_compute_documents_status')


    # --- Statut des champs obligatoires ---
    required_fields_complete = fields.Boolean(
        string="Tous les champs requis remplis",
        compute="_compute_fields_status",
        store=True
    )

    # Lien vers le dossier d'appui technique
    # chaque  demande de financement est lié à un dossier d'appui technique
    technical_support_id = fields.Many2one(
        'infrastructure.technical.support',
        string="Appui Technique"
    )

    note = fields.Text(string="Remarques complémentaires")
    
    #  Champ ajouté pour les notes de conformité à l'étape de vérification
    conformity_notes = fields.Text(string="Note Conformité", tracking=True)
    
    # Champs de vérification des documents
    official_request_verified = fields.Boolean('Lettre de demande vérifiée', default=False)
    official_request_comment = fields.Text('Commentaire lettre de demande')
    location_plan_verified = fields.Boolean('Plan de situation vérifié', default=False)
    location_plan_comment = fields.Text('Commentaire plan de situation')
    communal_commitment_verified = fields.Boolean('Engagement conseil vérifié', default=False)
    communal_commitment_comment = fields.Text('Commentaire engagement conseil')
    environmental_impact_verified = fields.Boolean('Impact environnemental vérifié', default=False)
    environmental_impact_comment = fields.Text('Commentaire impact environnemental')
    
    # Champ calculé pour vérifier si tous les documents sont vérifiés
    all_documents_verified = fields.Boolean('Tous documents vérifiés', compute='_compute_all_documents_verified', store=True)
    
    # Champ calculé pour vérifier si l'appui technique est complet
    technical_support_complete = fields.Boolean('Appui technique complet', compute='_compute_technical_support_complete', store=True)
    
    #  Champ ajouté pour l'avis technique à l'étape d'appui technique - requis pour passer à l'étape suivante
    avis_technique = fields.Text(string="Avis Technique", tracking=True)
    
    #  Champ ajouté pour l'évaluation favorable/non favorable à l'étape d'appui technique
    technical_evaluation = fields.Selection([
        ('favorable', 'Favorable'),
        ('non_favorable', 'Non Favorable')
    ], string="Évaluation Technique", tracking=True)
    
    #  Champ ajouté pour la note de revue à l'étape de revue et compilation - requis pour passer à l'étape suivante
    note_revue = fields.Text(string="Note de Revue", tracking=True)
    
    #  Champs ajoutés pour l'onglet Revue à l'étape "revue & compilation"
    completude_dossier = fields.Selection([
        ('complet', 'Dossier complet'),
        ('incomplet', 'Dossier incomplet')
    ], string="Complétude du dossier", tracking=True)
    
    note_revue_onglet = fields.Text(string="Note de revue", tracking=True)
    
    # Rapport de revue - Document uploadé à l'étape revue
    review_report_file = fields.Binary('Rapport de revue')
    review_report_filename = fields.Char('Nom du fichier')
    
    # PV de réception - Document uploadé à l'étape décision finale
    reception_pv_file = fields.Binary('PV de réception')
    reception_pv_filename = fields.Char('Nom du fichier')
    
    # (Q) Champ ajouté pour stocker le motif de rejet lors de la vérification
    rejection_reason = fields.Text(string="Motif du rejet", tracking=True)
    
    # (Q) Champs ajoutés pour gérer le workflow de rejet définitif (state='rejected')
    previous_state = fields.Char(string="État précédent", help="État avant rejet")
    rejected_by_user_id = fields.Many2one('res.users', string="Rejeté par", help="Utilisateur qui a rejeté la demande")
    rejected_from_state = fields.Char(string="Rejeté depuis l'étape", help="Étape d'où la demande a été rejetée")
    
    # (Q) Champs ajoutés pour gérer le retour de demande (retour vers state='draft' pour correction)
    return_reason = fields.Text(string="Motif du retour", tracking=True)
    returned_by_user_id = fields.Many2one('res.users', string="Retourné par", help="Utilisateur qui a retourné la demande")
    returned_from_state = fields.Char(string="Retourné depuis l'étape", help="Étape d'où la demande a été retournée")
    

    
    # Champs related pour l'onglet Appui Technique
    tech_evaluation = fields.Selection(related='technical_support_id.technical_evaluation', readonly=True)
    tech_avis = fields.Text(related='technical_support_id.avis_technique', readonly=True)

    
    # Champs calculés pour Infrastructure Routière
    road_intervention_type = fields.Selection([
        ('ouverture', 'Ouverture'),
        ('rehabilitation', 'Réhabilitation'),
        ('entretien', 'Entretien'),
    ], string="Type d'intervention", compute='_compute_road_fields', readonly=True)
    road_linear_km = fields.Float(string="Linéaire (Km)", compute='_compute_road_fields', readonly=True)
    road_start_point = fields.Char(string="Point de départ", compute='_compute_road_fields', readonly=True)
    road_end_point = fields.Char(string="Point d'arrivée", compute='_compute_road_fields', readonly=True)
    road_villages_served = fields.Text(string="Villages desservis", compute='_compute_road_fields', readonly=True)
    road_soil_type = fields.Char(string="Type de sol", compute='_compute_road_fields', readonly=True)
    
    # Champs calculés pour Ouvrage d'Art
    artwork_work_type = fields.Selection([
        ('pont', 'Pont'),
        ('dalot', 'Dalot'),
        ('buse', 'Buse'),
        ('ponceau', 'Ponceau'),
        ('passerelle', 'Passerelle')
    ], string="Type d'ouvrage", compute='_compute_artwork_fields', readonly=True)
    artwork_dimensions = fields.Char(string="Dimensions principales", compute='_compute_artwork_fields', readonly=True)
    artwork_condition = fields.Text(string="État constaté", compute='_compute_artwork_fields', readonly=True)
    artwork_maintenance_urgency = fields.Selection([
        ('petit', 'Petit entretien'),
        ('gros', 'Gros entretien'),
        ('urgent', 'Intervention immédiate')
    ], string="Urgence des travaux", compute='_compute_artwork_fields', readonly=True)
    artwork_hydraulic_state = fields.Text(string="État hydraulique", compute='_compute_artwork_fields', readonly=True)
    artwork_structural_state = fields.Text(string="État structurel", compute='_compute_artwork_fields', readonly=True)
    
    # Champs calculés pour Mini-Infrastructure
    mini_mini_type = fields.Selection([
        ('poste_agricole', 'Poste Agricole'),
        ('daager', 'Délégation d\'Arrondissement'),
        ('ceac', 'CEAC'),
        ('case_communautaire', 'Case Communautaire'),
        ('hangar_marche', 'Hangar de Marché'),
        ('magasin', 'Magasin de Stockage'),
        ('aire_sechage', 'Aire de Séchage'),
        ('point_eau', 'Point d\'eau')
    ], string="Type de mini-infrastructure", compute='_compute_mini_fields', readonly=True)
    mini_localisation = fields.Char(string="Localisation", compute='_compute_mini_fields', readonly=True)
    mini_superficie = fields.Float(string="Superficie disponible (m²)", compute='_compute_mini_fields', readonly=True)
    mini_intervention_type = fields.Selection([
        ('construction', 'Construction'),
        ('rehabilitation', 'Réhabilitation'),
        ('entretien', 'Entretien / Équipement')
    ], string="Type d'intervention", compute='_compute_mini_fields', readonly=True)
    mini_soil_type = fields.Char(string="Type de sol", compute='_compute_mini_fields', readonly=True)
    mini_status = fields.Text(string="État actuel / Fonctionnalité", compute='_compute_mini_fields', readonly=True)
    
    # Champs related pour les documents techniques
    tech_plan_file = fields.Binary(related='technical_support_id.technical_plan_file', readonly=True)
    tech_plan_filename = fields.Char(related='technical_support_id.technical_plan_filename', readonly=True)
    tech_cost_estimate_file = fields.Binary(related='technical_support_id.cost_estimate_file', readonly=True)
    tech_cost_estimate_filename = fields.Char(related='technical_support_id.cost_estimate_filename', readonly=True)
    tech_feasibility_report_file = fields.Binary(related='technical_support_id.feasibility_report_file', readonly=True)
    tech_feasibility_report_filename = fields.Char(related='technical_support_id.feasibility_report_filename', readonly=True)
    tech_transmission_note_file = fields.Binary(related='technical_support_id.technical_transmission_note_file', readonly=True)
    tech_transmission_note_filename = fields.Char(related='technical_support_id.technical_transmission_note_filename', readonly=True)
    

    

    

    
    # (Q) Champs de messagerie automatiquement fournis par mail.thread et mail.activity.mixin
    # message_follower_ids, activity_ids, message_ids sont automatiquement disponibles


    def _capture_filenames(self, vals):
        """(Q) Méthode pour capturer automatiquement les noms de fichiers"""
        # Mapping des champs Binary vers leurs champs filename correspondants
        binary_fields = {
            'official_request_file': 'official_request_filename',
            'location_plan_file': 'location_plan_filename',
            'communal_commitment_file': 'communal_commitment_filename',
            'environmental_impact_file': 'environmental_impact_filename',
            'review_report_file': 'review_report_filename',
            'reception_pv_file': 'reception_pv_filename',
        }
        
        # Vérifier chaque champ Binary pour capturer le nom de fichier
        for binary_field, filename_field in binary_fields.items():
            # Si un fichier est uploadé
            if binary_field in vals and vals[binary_field]:
                # Vérifier si le nom de fichier n'est pas déjà fourni
                if filename_field not in vals or not vals[filename_field]:
                    # Essayer de récupérer le nom depuis le contexte
                    filename = self.env.context.get(f'{binary_field}_filename')
                    
                    # Si pas de nom, utiliser un nom par défaut descriptif
                    if not filename:
                        default_names = {
                            'official_request_file': 'lettre_demande_officielle.pdf',
                            'location_plan_file': 'plan_situation_infrastructure.pdf',
                            'communal_commitment_file': 'approbation_conseil_municipal.pdf',
                            'environmental_impact_file': 'evaluation_impact_environnemental.pdf',
                            'review_report_file': 'rapport_de_revue.pdf',
                            'reception_pv_file': 'pv_de_reception.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename

    # === s'exécute quand on crée un nouvelle demande de de financement ===
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('infrastructure.financing.request') or 'Nouveau'
        self._capture_filenames(vals)
        return super().create(vals)


    # === ACTION : Bouton "Soumettre" ===
    def action_submit(self):
        """Étape 1: Dépôt de la demande"""

        """Force recalcul des champs calculés"""
        self.invalidate_recordset() 

        # (Q) Vérifier si la demande a été retournée précédemment
        if self.returned_from_state:
            
            # (Q) Si la demande a été retournée, rediriger vers l'étape d'où elle a été retournée
            returned_by_user = self.returned_by_user_id
            returned_from_state = self.returned_from_state
            
            # (Q) Si retournée depuis vérification, effacer l'ancien avis de conformité
            vals_to_write = {
                'state': returned_from_state,
                'return_reason': False,
                'returned_by_user_id': False,
                'returned_from_state': False,
                'submission_date': fields.Datetime.now()
            }
            
            if returned_from_state == 'verification':
                vals_to_write['conformity_notes'] = False
            
            self.write(vals_to_write)
            
            # (Q) Log dans le chatter pour tracer la resoumission après retour
            self._log_action(f"Resoumission après correction - Retour à l'étape {returned_from_state}")
            
            # (Q) Notifier l'utilisateur qui avait retourné la demande
            if returned_by_user:
                self._notify_user_of_resubmission_after_return(returned_by_user)
            
            return self.notify(
                _("Demande resoumise avec succès après correction. Retour à l'étape de traitement."),
                type="success",
                title=_("Resoumission réussie 🎉"),
                sticky=False
            )

        # (Q) Workflow normal si la demande n'a pas été retournée
        """Vérification des documents requis"""
        # Vérifier les documents requis via les champs binaires
        missing_docs = []
        if not self.official_request_file:
            missing_docs.append("Lettre de demande officielle")
        if not self.location_plan_file:
            missing_docs.append("Plan de situation")
        if not self.communal_commitment_file:
            missing_docs.append("Engagement du conseil municipal")
        if not self.environmental_impact_file:
            missing_docs.append("Évaluation de l'impact environnemental")

        if missing_docs:
            """Message d'avertissement si des documents sont manquants"""
            return self.notify(
                _("Documents manquants :\n- %s") % "\n- ".join(missing_docs),
                type="warning",
                title=_("Soumission impossible"),
                sticky=False
            )
        
        """Vérification des informations techniques selon le type d'infrastructure"""
        if self.infrastructure_type == 'road' and not self.road_id:
            return self.notify(
                _("Veuillez ajouter les informations techniques pour l'infrastructure routière avant de soumettre."),
                type="warning",
                title=_("Informations techniques manquantes"),
                sticky=False
            )
        elif self.infrastructure_type == 'artwork' and not self.artwork_id:
            return self.notify(
                _("Veuillez ajouter les informations techniques pour l'ouvrage d'art avant de soumettre."),
                type="warning",
                title=_("Informations techniques manquantes"),
                sticky=False
            )
        elif self.infrastructure_type == 'mini_infra' and not self.mini_id:
            return self.notify(
                _("Veuillez ajouter les informations techniques pour la mini-infrastructure avant de soumettre."),
                type="warning",
                title=_("Informations techniques manquantes"),
                sticky=False
            )

        """Mettre à jour l'état et la date de soumission""" 
        self.write({
            'state': 'verification',
            'submission_date': fields.Datetime.now()
        })

        """Log dans le chatter pour garder une trace des actions"""
        self._log_action("Soumission de la demande")

        self._send_notification('verification')

        """Message de succès """
        return self.notify(
                ("Demande créée avec succès."),
            type="success",
            title=_("Succès 🎉"),
            sticky=False
        )


    # === ACTION : Bouton "Passer à l'appui technique" ===
    def action_technical_support(self):
        """Étape 2: Passer à l'appui technique après vérification"""

        # Vérifier que tous les documents sont vérifiés
        if not self.all_documents_verified:
            raise ValidationError(_("Veuillez vérifier tous les documents avant de passer à l'appui technique."))
        
        # Vérifier que le commentaire global est renseigné
        if not (self.conformity_notes or '').strip():
            raise ValidationError(_("Veuillez renseigner le commentaire global avant de passer à l'appui technique."))

        """Transition d'état"""
        self.write({'state': 'technical_support'})

        """Log interne dans le chatter"""
        self._log_action("Passage à l'étape appui technique")

        """Notification aux acteurs concernés"""
        self._send_notification('technical_support')

        return self.notify(
            _("Demande passée à l'étape appui technique avec succès."),
            type="success",
            title=_("Succès")
        )
    
    # === ACTION : Bouton "Lancer appui technique" ===
    def action_launch_technical_support(self):
        """À l'étape appui technique: Lancer le formulaire d'appui technique"""
        
        """Si un support technique existe déjà -> on le réutilise sinon on en crée un nouveau"""
        if self.technical_support_id:
            support = self.technical_support_id
        else:
            support = self._create_technical_support()
            self.technical_support_id = support.id

        # Retourne un formulaire d'appui technique
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appui Technique',
            'res_model': 'infrastructure.technical.support',
            'view_mode': 'form',
            'res_id': support.id,
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'form_view_initial_mode': 'edit',
            },
            'flags': {
                'mode': 'edit'
            }
        }


    # === ACTION : Bouton "Retourner" depuis l'appui technique ===
    def action_return_technical_support(self):
        """Retourner à l'étape précédente depuis l'appui technique"""
        return self._open_return_wizard()
    
    # === ACTION : Bouton "Retourner à l'Appui Technique" depuis la revue ===
    def action_return_to_technical_support(self):
        """Retourner à l'étape appui technique depuis la revue"""
        return self._open_return_wizard()
    
    # === ACTION : Bouton "Retourner à la Vérification" depuis l'appui technique ===
    def action_return_to_verification(self):
        """Retourner à l'étape vérification depuis l'appui technique"""
        return self._open_return_wizard()
    
    # === ACTION : Bouton "Retourner au Brouillon" depuis l'étape reçue ===
    def action_return_to_draft(self):
        """Retourner à l'étape brouillon depuis l'étape reçue"""
        return self._open_return_wizard()
    
    # === ACTION : Bouton "Rejeter" à l'étape vérification ===
    def action_reject_verification(self):
        """Rejeter la demande à l'étape vérification"""
        return self._open_rejection_wizard()
    
    # === ACTION : Bouton "Retourner" depuis la décision finale ===
    def action_return_final_decision(self):
        """Retourner à l'étape revue depuis la décision finale"""
        return self._open_return_wizard()

    # === ACTION : Bouton "review" ===
    def action_review(self):
        """Étape 3: Revue et Compilation - Vérification complète avant approbation"""

        """Forcer le recalcul des champs calculés"""
        self.invalidate_recordset()

        """Vérification d\'état"""
        if self.state != 'technical_support':
            return self.notify(
                _("La revue est uniquement possible après l'appui technique."),
                type="warning",
                title=_("Action impossible"),
                sticky=False
            )

        # Vérifier que l'évaluation technique et l'avis technique sont renseignés
        if not self.technical_support_id.technical_evaluation:
            return self.notify(
                _("Veuillez sélectionner une évaluation technique (Favorable/Non Favorable) dans l'appui technique avant de procéder à la revue."),
                type="warning",
                title=_("\u00c9valuation technique requise"),
                sticky=False
            )
        
        if not self.technical_support_id.avis_technique:
            return self.notify(
                _("Veuillez renseigner un avis technique dans l'appui technique avant de procéder à la revue."),
                type="warning",
                title=_("Avis technique requis"),
                sticky=False
            )
        
        # (Q) Vérifier que tous les documents techniques sont fournis
        if not self.technical_support_id:
            return self.notify(
                _("Aucun appui technique associé à cette demande."),
                type="warning",
                title=_("Appui technique manquant"),
                sticky=False
            )
        
        # Vérifier les 4 documents techniques requis
        missing_docs = []
        if not self.technical_support_id.technical_plan_file:
            missing_docs.append("Plan technique")
        if not self.technical_support_id.cost_estimate_file:
            missing_docs.append("Devis")
        if not self.technical_support_id.feasibility_report_file:
            missing_docs.append("Rapport de faisabilité")
        if not self.technical_support_id.technical_transmission_note_file:
            missing_docs.append("Note de transmission technique")

        if missing_docs:
            return self.notify(
                _("Documents techniques manquants :\n- %s") % "\n- ".join(missing_docs),
                type="warning",
                title=_("Documents manquants"),
                sticky=False
            )

        """Mettre à jour l'état et la date de revue"""
        now = fields.Datetime.now()
        self.write({
            'state': 'review',
            'review_date': now
        })

        # Log dans le chatter
        self._log_action("Revue et compilation")

        """Notifications (mail + bandeau vert sur l'interface de la demande )"""
        self._send_notification('review')
        return self.notify(
            _("Revue et compilation effectuées avec succès."),
            type="success",
            title=_("Succès")
        )




    # === ACTION : Bouton "decision finale" ===
    def action_final_decision(self):
        """Étape 4: Décision finale"""
        # (Q) Vérifier que les champs obligatoires de l'onglet Revue sont renseignés
        if not (self.note_revue_onglet or '').strip():
            return self.notify(
                _("Veuillez renseigner une note de revue avant de procéder à la décision finale."),
                type="warning",
                title=_("Note de revue requise"),
                sticky=False
            )
        
        if not self.review_report_file:
            return self.notify(
                _("Veuillez uploader le rapport de revue avant de procéder à la décision finale."),
                type="warning",
                title=_("Rapport de revue requis"),
                sticky=False
            )
        
        self.write({
            'state': 'final_decision',
            'decision_date': fields.Date.today()
        })

        # Log dans le chatter
        self._log_action("Décision finale")
        
        self._send_notification('final_decision')
        
        return self.notify(
            _("Décision finale enregistrée avec succès."),
            type="success",
            title=_("Succès")
        )
    
    # === ACTION : Bouton "Rejeter" à l'étape décision finale ===
    def action_reject_final_decision(self):
        """Ouvrir le wizard de rejet à l'étape décision finale"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Demande Rejetée',
            'res_model': 'infrastructure.rejection.wizard',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_current_state': self.state
            }
        }
    
    # === ACTION : Approuver la demande ===
    def action_approve(self):
        """Approuver la demande à l'étape décision finale"""
        if self.state != 'final_decision':
            return self.notify(
                _("L'approbation est uniquement possible à l'étape de décision finale."),
                type="warning",
                title=_("Action impossible"),
                sticky=False
            )
        
        if not self.reception_pv_file:
            return self.notify(
                _("Veuillez uploader le PV de réception avant d'approuver la demande."),
                type="warning",
                title=_("PV de réception requis"),
                sticky=False
            )
        
        self.write({
            'state': 'approuvee',
            'approval_date': fields.Date.today()
        })
        
        # Log dans le chatter
        self._log_action("Demande approuvée")
        
        self._send_notification('approuvee')
        
        return self.notify(
            _("Demande approuvée avec succès. La procédure est terminée."),
            type="success",
            title=_("Succès")
        )
    



    
    # (Q) Méthode ajoutée pour vérifier les droits d'écriture sur les demandes rejetées
    def write(self, vals):
        """Surcharge de write pour empêcher les modifications non autorisées sur les demandes rejetées"""
        self._capture_filenames(vals)
        
        # (Q) Vérifier les droits pour les champs de revue
        review_fields = {'completude_dossier', 'note_revue_onglet'}
        if any(field in vals for field in review_fields):
            agent_delegation_group = self.env.ref('patnuc_minader_financement_infrastructures_Routiere.agent_Delegation', raise_if_not_found=False)
            if not agent_delegation_group or agent_delegation_group not in self.env.user.groups_id:
                raise ValidationError(_("Seuls les agents de délégation peuvent modifier les champs de revue."))
        
        for record in self:
            if record.state == 'rejected' and vals:
                # (Q) Seul le demandeur peut modifier une demande rejetée
                if record.create_uid and record.create_uid.id != self.env.user.id:
                    # (Q) Exclure les champs système de la vérification
                    system_fields = {'message_follower_ids', 'activity_ids', 'message_ids', '__last_update'}
                    user_fields = set(vals.keys()) - system_fields
                    if user_fields:
                        raise ValidationError(_("Seul le demandeur peut modifier une demande rejetée."))
        return super().write(vals)


    @api.depends('documents_ids', 'official_request_file', 'location_plan_file', 'communal_commitment_file', 'environmental_impact_file')
    def _compute_documents_count(self):
        for record in self:
            required_docs_count = sum([
                1 if record.official_request_file else 0,
                1 if record.location_plan_file else 0,
                1 if record.communal_commitment_file else 0,
                1 if record.environmental_impact_file else 0
            ])
            other_docs_count = len(record.documents_ids)
            record.documents_count = required_docs_count + other_docs_count
    
    @api.depends('official_request_file', 'location_plan_file', 'communal_commitment_file', 'environmental_impact_file')
    def _compute_documents_status(self):
        for record in self:
            record.required_documents_complete = all([
                record.official_request_file,
                record.location_plan_file,
                record.communal_commitment_file,
                record.environmental_impact_file
            ])
    


    @api.depends('commune_id', 'project_title','localite_id')
    def _compute_fields_status(self):
        required_fields = ['commune_id', 'project_title','localite_id']
        for rec in self:
            rec.required_fields_complete = all(getattr(rec, f) for f in required_fields)
    
    @api.depends('submission_date', 'approval_date', 'decision_date', 'state')
    def _compute_processing_days(self):
        for record in self:
            if record.submission_date:
                # Utiliser la date d'approbation, sinon la date de décision, sinon la date actuelle
                if record.approval_date:
                    end_date = record.approval_date
                elif record.decision_date:
                    end_date = record.decision_date
                else:
                    end_date = fields.Date.today()
                
                start_date = record.submission_date.date()
                record.processing_days = (end_date - start_date).days
            else:
                record.processing_days = 0
    
    @api.depends('official_request_verified', 'location_plan_verified', 'communal_commitment_verified', 'environmental_impact_verified')
    def _compute_all_documents_verified(self):
        for record in self:
            record.all_documents_verified = all([
                record.official_request_verified,
                record.location_plan_verified,
                record.communal_commitment_verified,
                record.environmental_impact_verified
            ])
    
    @api.depends('technical_support_id.technical_evaluation', 'technical_support_id.avis_technique', 'technical_support_id.technical_plan_file', 'technical_support_id.cost_estimate_file', 'technical_support_id.feasibility_report_file', 'technical_support_id.technical_transmission_note_file')
    def _compute_technical_support_complete(self):
        for record in self:
            if record.technical_support_id:
                record.technical_support_complete = all([
                    record.technical_support_id.technical_evaluation,
                    record.technical_support_id.avis_technique,
                    record.technical_support_id.technical_plan_file,
                    record.technical_support_id.cost_estimate_file,
                    record.technical_support_id.feasibility_report_file,
                    record.technical_support_id.technical_transmission_note_file
                ])
            else:
                record.technical_support_complete = False
    

    

    
    @api.depends('road_id')
    def _compute_road_fields(self):
        for record in self:
            if record.road_id:
                road = record.road_id[0]  # Prendre le premier enregistrement
                record.road_intervention_type = road.intervention_type
                record.road_linear_km = road.linear_km
                record.road_start_point = road.start_point
                record.road_end_point = road.end_point
                record.road_villages_served = road.villages_served
                record.road_soil_type = road.soil_type
            else:
                record.road_intervention_type = False
                record.road_linear_km = 0.0
                record.road_start_point = False
                record.road_end_point = False
                record.road_villages_served = False
                record.road_soil_type = False
    
    @api.depends('artwork_id')
    def _compute_artwork_fields(self):
        for record in self:
            if record.artwork_id:
                artwork = record.artwork_id[0]  # Prendre le premier enregistrement
                record.artwork_work_type = artwork.work_type
                record.artwork_dimensions = artwork.dimensions
                record.artwork_condition = artwork.condition
                record.artwork_maintenance_urgency = artwork.maintenance_urgency
                record.artwork_hydraulic_state = artwork.hydraulic_state
                record.artwork_structural_state = artwork.structural_state
            else:
                record.artwork_work_type = False
                record.artwork_dimensions = False
                record.artwork_condition = False
                record.artwork_maintenance_urgency = False
                record.artwork_hydraulic_state = False
                record.artwork_structural_state = False
    
    @api.depends('mini_id')
    def _compute_mini_fields(self):
        for record in self:
            if record.mini_id:
                mini = record.mini_id[0]  # Prendre le premier enregistrement
                record.mini_mini_type = mini.mini_type
                record.mini_localisation = mini.localisation
                record.mini_superficie = mini.superficie
                record.mini_intervention_type = mini.intervention_type
                record.mini_soil_type = mini.soil_type
                record.mini_status = mini.status
            else:
                record.mini_mini_type = False
                record.mini_localisation = False
                record.mini_superficie = 0.0
                record.mini_intervention_type = False
                record.mini_soil_type = False
                record.mini_status = False



    @api.depends('submission_date')
    def _compute_expected_date(self):
        for record in self:
            if record.submission_date:
                # Calcul basé sur les délais de la procédure (environ 30 jours calendaires)
                submission_date = record.submission_date.date() if isinstance(record.submission_date, datetime) else record.submission_date
                record.expected_completion_date = submission_date + timedelta(days=30)
            else:
                record.expected_completion_date = False





    def _create_technical_support(self):

        """Création du dossier d'appui technique lié sans document par défaut"""

        support_obj = self.env['infrastructure.technical.support']
        now = fields.Datetime.now()

        # Création du support
        support = support_obj.create({
            'request_id': self.id,
        })

        # Les documents techniques seront ajoutés manuellement via l'interface

        # Lier le support à la demande
        self.technical_support_id = support.id

        return support



    # (Q) Action ajoutée pour le retour de demande depuis l'étape vérification
    def action_return_verification(self):
        """Ouvrir le wizard de retour pour l'étape vérification"""
        return self._open_return_wizard()
    
    # (Q) Méthode ajoutée pour ouvrir le wizard de retour
    def _open_return_wizard(self):
        """Méthode pour ouvrir le wizard de retour de demande"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Demande Retournée',
            'res_model': 'infrastructure.return.wizard',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_current_state': self.state
            }
        }
    
    # (Q) Méthode générique ajoutée pour ouvrir le wizard de rejet
    def _open_rejection_wizard(self):
        """Méthode générique pour ouvrir le wizard de rejet"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Demande Rejetée',
            'res_model': 'infrastructure.rejection.wizard',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_current_state': self.state
            }
        }
    
    # (Q) Action ajoutée pour la resoumission après retour par le demandeur
    def action_resubmit_after_return(self):
        """Resoumission de la demande après correction par le demandeur suite à un retour"""
        if self.create_uid.id != self.env.user.id:
            return self.notify(
                _("Seul le demandeur peut mettre à jour une demande retournée."),
                type="warning",
                title=_("Accès refusé")
            )
        
        if not self.returned_from_state:
            return self.notify(
                _("Impossible de déterminer l'étape d'où la demande a été retournée."),
                type="warning",
                title=_("Erreur")
            )
        
        returned_by_user = self.returned_by_user_id
        returned_from_state = self.returned_from_state
        
        self.write({
            'state': returned_from_state,
            'return_reason': False,
            'returned_by_user_id': False,
            'returned_from_state': False
        })
        
        self._log_action(f"Mise à jour de la demande - Retour à l'étape {returned_from_state}")
        
        if returned_by_user:
            self._notify_user_of_resubmission_after_return(returned_by_user)
        
        return self.notify(
            _("Demande mise à jour avec succès. Retour à l'étape de traitement."),
            type="success",
            title=_("Succès")
        )
    
    # (Q) Méthode ajoutée pour notifier l'utilisateur qui avait retourné
    def _notify_user_of_resubmission_after_return(self, user):
        """Notifier l'utilisateur qui avait retourné de la mise à jour"""
        message = _("La demande %s a été mise à jour après correction par le demandeur et est de nouveau disponible pour traitement.") % self.name
        self.message_post(
            body=message,
            partner_ids=[user.partner_id.id],
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
    
    # (Q) Action ajoutée pour la resoumission après rejet par le demandeur
    def action_resubmit_after_rejection(self):
        """Resoumission de la demande après correction par le demandeur suite à un rejet"""
        if self.create_uid.id != self.env.user.id:
            return self.notify(
                _("Seul le demandeur peut mettre à jour une demande rejetée."),
                type="warning",
                title=_("Accès refusé")
            )
        
        if not self.rejected_from_state:
            return self.notify(
                _("Impossible de déterminer l'étape d'où la demande a été rejetée."),
                type="warning",
                title=_("Erreur")
            )
        
        rejected_by_user = self.rejected_by_user_id
        rejected_from_state = self.rejected_from_state
        
        self.write({
            'state': rejected_from_state,
            'rejection_reason': False,
            'rejected_by_user_id': False,
            'rejected_from_state': False,
            'previous_state': False
        })
        
        self._log_action(f"Mise à jour de la demande - Retour à l'étape {rejected_from_state}")
        
        if rejected_by_user:
            self._notify_user_of_resubmission(rejected_by_user)
        
        return self.notify(
            _("Demande mise à jour avec succès. Retour à l'étape de traitement."),
            type="success",
            title=_("Succès")
        )
    
    # (Q) Méthode ajoutée pour notifier l'utilisateur qui avait rejeté
    def _notify_user_of_resubmission(self, user):
        """Notifier l'utilisateur qui avait rejeté de la mise à jour"""
        message = _("La demande %s a été mise à jour après correction par le demandeur et est de nouveau disponible pour traitement.") % self.name
        self.message_post(
            body=message,
            partner_ids=[user.partner_id.id],
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )




    def _send_notification(self, stage):
        """Envoyer les notifications selon l'étape"""
        template_mapping = {
            'verification': 'infrastructure_Financing_request_verification',
            'technical_support': 'infrastructure_Financing_request_support',
            'review': 'infrastructure_Financing_request_review',
            'final_decision': 'infrastructure_Financing_request_final_decision',
            'approuvee': 'infrastructure_Financing_request_approved',
        }
        # Logique de notification à implémenter si nécessaire
        pass

    def notify(self, message, type="info", title=None, sticky=False):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title or _("Notification"),
                'message': message,
                'type': type,
                'sticky': sticky,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'infrastructure.financing.request',
                    'view_mode': 'form',
                    'views': [[False, 'form']],
                    'res_id': self.id,
                    'target': 'current',
                },
            }
        }


    
    def action_view_documents(self):
        """Ouvrir la vue des documents liés à la demande"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents de la demande',
            'res_model': 'infrastructure.document',
            'view_mode': 'tree,form',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('request_id', '=', self.id)],
            'context': {'default_request_id': self.id},
            'target': 'current',
        }
    
    # (Q) Action pour ouvrir le formulaire d'appui technique
    def action_open_technical_support_form(self):
        """Ouvrir le formulaire d'appui technique"""
        if not self.technical_support_id:
            return self.notify(
                _("Aucun appui technique associé à cette demande."),
                type="warning",
                title=_("Appui technique manquant")
            )
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appui Technique',
            'res_model': 'infrastructure.technical.support',
            'view_mode': 'form',
            'res_id': self.technical_support_id.id,
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    # Actions pour ajouter les informations techniques
    def action_add_road_info(self):
        """Ouvrir le formulaire de fiche technique route"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Fiche d\'information techniques - {self.name}',
            'res_model': 'infrastructure.road',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    def action_add_artwork_info(self):
        """Ouvrir le formulaire de fiche technique ouvrage d'art"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Fiche d\'information techniques - {self.name}',
            'res_model': 'infrastructure.artwork',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }
    
    def action_add_mini_info(self):
        """Ouvrir le formulaire de fiche technique mini-infrastructure"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Fiche d\'information techniques - {self.name}',
            'res_model': 'infrastructure.mini',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }

    # (Q) Fonction de tracking ajoutée pour enregistrer qui fait quoi et quand
    def _log_action(self, action_name):
        self.ensure_one()
        # (Q) Message de tracking en texte brut pour éviter l'affichage des balises HTML
        current_time = fields.Datetime.now()
        formatted_datetime = current_time.strftime('%d/%m/%Y à %H:%M')
        
        message = "🔄 %s\n👤 Utilisateur: %s\n📅 Date: %s" % (
            action_name,
            self.env.user.name,
            formatted_datetime
        )
        self.message_post(
            body=message,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
    
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
