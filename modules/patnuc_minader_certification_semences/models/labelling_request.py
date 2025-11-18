from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LabellingRequest(models.Model):
    _name = 'labelling.request'
    _description = 'Demande d\'Étiquetage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char('Référence', required=True, copy=False, readonly=True,
                      default=lambda self: self.env['ir.sequence'].next_by_code('labelling.request'))
    
    # Lien vers la demande de certification
    certification_request_id = fields.Many2one(
        'certification.request', 
        string='Demande de Certification',
        required=True,
        domain=[('state', '=', 'labelling')],
        tracking=True
    )

    # Lot certifié sélectionné pour étiquetage
    selected_lot_id = fields.Many2one(
        'certification.parcelle.lot',
        string='Lot Certifié à Étiqueter',
        required=True,
        tracking=True,
        domain="[('request_id', '=', certification_request_id), ('state', '=', 'in_certification')]"
    )
    
    # Informations automatiques depuis la demande de certification
    operator_id = fields.Many2one(related='certification_request_id.operator_id', string='Producteur', readonly=True)
    operator_name = fields.Char(related='certification_request_id.operator_name', string='Nom du producteur', readonly=True)
    
    # Informations de localisation
    region_id = fields.Many2one(related='certification_request_id.region_id', string='Région', readonly=True)
    departement_id = fields.Many2one(related='certification_request_id.departement_id', string='Département', readonly=True)
    arrondissement_id = fields.Many2one(related='certification_request_id.arrondissement_id', string='Arrondissement', readonly=True)
    localite_id = fields.Char(related='certification_request_id.localite_id', string='Lieu de production', readonly=True)
    
    # Informations de la parcelle
    parcelle_id = fields.Many2one(related='certification_request_id.parcelle_id', string='Référence Parcelle', readonly=True)
    variete_semence = fields.Selection(related='certification_request_id.parcelle_variete', string='Variété de la semence', readonly=True)
    categorie = fields.Selection(related='certification_request_id.parcelle_categorie', string='Catégorie', readonly=True)
    campagne = fields.Char(related='certification_request_id.agricole_campain', string='Campagne', readonly=True)
    production_tonne = fields.Float(related='certification_request_id.parcelle_production', string='Production en tonne', readonly=True)
    superficie = fields.Float(related='certification_request_id.parcelle_superficie', string='Superficie', readonly=True)
    #production = fields.Float(string='Production (en tonne)')
    

    
    # Lots certifiés disponibles pour étiquetage (pour affichage)
    certified_lots_ids = fields.Many2many(
        'certification.parcelle.lot',
        string='Lots Certifiés',
        compute='_compute_certified_lots',
        store=False
    )
    
    # Affichage du lot sélectionné dans l'onglet
    selected_lot_display_ids = fields.Many2many(
        'certification.parcelle.lot',
        string='Lot Sélectionné',
        compute='_compute_selected_lot_display',
        store=False
    )
    
    # État de la demande d'étiquetage
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours de traitement'),
        ('completed', 'Étiquetage terminé'),
        ('canceled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    # Dates
    submission_date = fields.Datetime('Date de soumission', tracking=True)
    completion_date = fields.Datetime('Date de finalisation', tracking=True)
    
    # Informations d'étiquetage
    quantity_to_label = fields.Float('Quantité à étiqueter (kg)')
    production_lot_kg = fields.Float('Production du lot (kg)')
    label_type = fields.Selection([
        ('standard', 'Étiquette standard'),
        ('premium', 'Étiquette premium'),
        ('export', 'Étiquette export')
    ], string='Type d\'étiquette', default='standard')
    
    # Conditionnements dynamiques
    packaging_ids = fields.One2many('labelling.packaging', 'labelling_request_id', string='Conditionnements')
    total_packaging_weight = fields.Float('Poids total des conditionnements (kg)', compute='_compute_total_packaging_weight', store=True)
    
    traitement_chimique = fields.Selection([
        ('aucun', 'Aucun traitement'),
        ('traitement', 'Traitement')
    ], string='Traitement chimique', default='aucun')
    
    nombre_etiquettes = fields.Integer('Nombre d\'étiquettes', compute='_compute_nombre_etiquettes', store=True)
    
    # Documents et résultats
    labelling_report = fields.Binary('Rapport d\'étiquetage')
    labelling_report_filename = fields.Char('Nom du fichier')
    
    notes = fields.Text('Notes')
    rejection_reason = fields.Text('Motif de rejet')
    
    # Étiquettes générées
    label_ids = fields.One2many('labelling.label', 'labelling_request_id', string='Étiquettes générées')
    labels_count = fields.Integer('Nombre d\'étiquettes générées', compute='_compute_labels_count')
    
    @api.depends('certification_request_id', 'certification_request_id.lot_ids', 'certification_request_id.lot_ids.state')
    def _compute_certified_lots(self):
        """Affiche uniquement les lots avec l'état 'in_certification' (certifiés)"""
        for record in self:
            if record.certification_request_id:
                # Filtrer les lots qui ont l'état 'in_certification' (certifiés)
                certified_lots = record.certification_request_id.lot_ids.filtered(
                    lambda lot: lot.state == 'in_certification'
                )
                record.certified_lots_ids = [(6, 0, certified_lots.ids)]
            else:
                record.certified_lots_ids = [(6, 0, [])]
    
    @api.depends('selected_lot_id')
    def _compute_selected_lot_display(self):
        """Affiche uniquement le lot sélectionné dans l'onglet"""
        for record in self:
            if record.selected_lot_id:
                record.selected_lot_display_ids = [(6, 0, [record.selected_lot_id.id])]
            else:
                record.selected_lot_display_ids = [(6, 0, [])]
    
    @api.depends('packaging_ids', 'packaging_ids.total_weight')
    def _compute_total_packaging_weight(self):
        """Calcul du poids total des conditionnements"""
        for record in self:
            record.total_packaging_weight = sum(record.packaging_ids.mapped('total_weight'))
    
    @api.depends('packaging_ids', 'packaging_ids.quantity_packages')
    def _compute_nombre_etiquettes(self):
        """Calcul automatique du nombre d'étiquettes basé sur les conditionnements"""
        for record in self:
            record.nombre_etiquettes = sum(record.packaging_ids.mapped('quantity_packages'))
    
    @api.constrains('packaging_ids', 'production_lot_kg')
    def _check_packaging_weight_limit(self):
        """Vérifier que le poids total des conditionnements ne dépasse pas la production du lot"""
        for record in self:
            if record.production_lot_kg and record.total_packaging_weight > record.production_lot_kg:
                raise UserError(f"Le poids total des conditionnements ({record.total_packaging_weight} kg) ne peut pas dépasser la production du lot ({record.production_lot_kg} kg).")
    
    @api.onchange('certification_request_id')
    def _onchange_certification_request(self):
        """Réinitialiser le lot sélectionné quand la demande change"""
        self.selected_lot_id = False
    
    def action_submit(self):
        """Soumettre la demande d'étiquetage"""
        if not self.packaging_ids:
            raise UserError("Veuillez ajouter au moins un conditionnement avant de soumettre.")
        
        self.write({
            'state': 'in_progress',
            'submission_date': fields.Datetime.now()
        })
        self.message_post(body="Demande d'étiquetage en cours de traitement.")
    

    
    def action_next_label(self):
        """Passer à l'état étiquetage terminé"""
        if self.state != 'in_progress':
            raise UserError("Cette action n'est possible que lorsque la demande est en cours de traitement.")
        
        if not self.production_lot_kg or self.production_lot_kg <= 0:
            raise UserError("Veuillez saisir la production du lot (kg) avant de continuer.")
        
        self.write({
            'state': 'completed',
            'completion_date': fields.Datetime.now()
        })
        # self.message_post(body="Étiquetage terminé.")
        
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Étiquetage terminé',
        #         'message': 'Étiquetage terminé avec succès.',
        #         'type': 'success'
        #     }
        # }
    
    @api.depends('label_ids')
    def _compute_labels_count(self):
        for record in self:
            record.labels_count = len(record.label_ids)
    

    
    def get_labels_by_pages(self):
        """Retourne les labels découpés en pages de 14, sans remplir avec des None."""
        # Tri des labels (très important pour éviter le désordre)
        labels = list(self.label_ids.sorted(key=lambda l: l.id))

        per_page = 14
        pages = []

        for i in range(0, len(labels), per_page):
            pages.append(labels[i:i + per_page])

        return pages

    
    def action_complete(self):
        """Générer les étiquettes et terminer l'étiquetage"""
        if not self.selected_lot_id:
            raise UserError("Veuillez sélectionner un lot certifié pour l'étiquetage.")
        
        # Supprimer les anciennes étiquettes si elles existent
        self.label_ids.unlink()
        
        # Générer les étiquettes pour chaque conditionnement
        lot = self.selected_lot_id
        etiquette_counter = 1
        
        for packaging in self.packaging_ids:
            for i in range(packaging.quantity_packages):
                code_etiquette = f"{self.name}-{lot.name}-{etiquette_counter:04d}"
                
                self.env['labelling.label'].create({
                    'name': code_etiquette,
                    'labelling_request_id': self.id,
                    'lot_id': lot.id,
                    'espece': self.variete_semence or '',
                    'variete': self.variete_semence or '',
                    'lot_name': lot.name,
                    'poids_lot': self.production_lot_kg or 0.0,
                    'poids_net': packaging.packaging_weight or 0.0,
                    'lieu_production': self.localite_id or '',
                    'annee_production': self.campagne or '',
                    'traitement_chimique': dict(self._fields['traitement_chimique'].selection).get(self.traitement_chimique, '') if self.traitement_chimique else '',
                    'nom_producteur': self.operator_name or '',
                    'code_inspecteur': ''
                })
                etiquette_counter += 1
        
        self.write({
            'state': 'completed',
            'completion_date': fields.Datetime.now()
        })
        self.message_post(body=f"Étiquetage terminé avec succès. {self.labels_count} étiquettes générées.")
    
    def action_reject(self):
        """Annuler la demande d'étiquetage"""
        if not self.rejection_reason:
            raise UserError("Veuillez saisir le motif d'annulation.")
        
        self.write({'state': 'canceled'})
        self.message_post(body=f"Demande d'étiquetage annulée: {self.rejection_reason}")
    
    def action_print_labels(self):
        """Imprimer les étiquettes"""
        return self.env.ref('patnuc_minader_certification_semences.action_labels_report').report_action(self)
    
 