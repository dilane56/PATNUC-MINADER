# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, tools
from dateutil.relativedelta import relativedelta

class FertilizerDecree(models.Model):
    _name = 'fertilizer.decree'
    _description = 'Arrêté d\'Homologation Ministériel'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # 1. Référence de l'Arrêté (MAINTENANT GENEREE PAR SEQUENCE)
    name = fields.Char(
        string='Référence de l\'Arrêté', 
        required=True,
        copy=False, 
        readonly=True, 
        tracking=True,
        default=lambda self: _('Nouveau'),
    )

    # NOUVEAU CHAMP : Statut de l'Arrêté
    state = fields.Selection([
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('expiré', 'Expiré'),
        ('inactif', 'Inactif'),
         
    ], required=True , string='Statut de l\'arrêté', default='inactif', tracking=True)
    
    # 2. Lien vers la Demande d'Homologation
    homologation_id =  fields.Many2one(
        'fertilizer.homologation', 
        string='Reference de la demande d\'homologation initiale',
        required=True,
        ondelete='restrict', 
        tracking=True,
    )

    delivery_date = fields.Date(
        string="Date de Délivrance",
    )
    
    expiration_date = fields.Date(string="Date d'Expiration", compute='_compute_expiration_date', store=True)

    # Related fields 
    applicant_id = fields.Many2one(
        related='homologation_id.applicant_id',
        string="Demandeur",
        store=True,
        readonly=True,
    )
    # Numéro de Téléphone (Hypothèse: champ 'phone' sur res.partner)
    phone_number = fields.Char(
        string="Téléphone", 
        related='applicant_id.phone', 
        readonly=True, 
        store=False
    )
    
    # Nom Commercial du Produit (Valeur par défaut du produit initial, mais modifiable)
    commercial_name = fields.Many2one('fertilizer.product', 
                                      string='Produit commercial homologué', 
                                      required=True, tracking=True)
    # Nom Technique du Produit (Valeur par défaut du produit initial, mais modifiable)
    technical_name = fields.Char(
        string="Nom technique du produit homologué",
        store=True,
    )
    # Fabricant (Valeur par défaut du produit initial, mais modifiable)
    manufacturer_id = fields.Many2one(
        'res.partner', 
        string="Fabricant",
        store=True,
    )
    
    # ----------------------------------------------------------------------
    
    # 6. Arrêté Chargé (Related au fichier final dans la demande d'homologation)
    decree_file = fields.Binary(
        string="Fichier de l'Arrêté",
        related='homologation_id.homologation_document', 
        readonly=True,
        store=False
    )
    decree_filename = fields.Char(
        string="Nom du Fichier Arrêté",
        related='homologation_id.homologation_document_filename', 
        readonly=True,
        store=False
    )

    # Logique de calcul de la date d'expiration
    @api.depends('delivery_date')
    def _compute_expiration_date(self):
        """Calcul la date d'expiration comme la date de délivrance + 2 ans."""
        for record in self:
            if record.delivery_date:
                # Ajoute 2 ans à la date de délivrance
                record.expiration_date = record.delivery_date + relativedelta(years=2)
            else:
                record.expiration_date = False

    # Logique de Séquençage (Indispensable pour générer la référence)
    @api.model_create_multi
    def create(self, vals_list):
        """Génère la référence de l'Arrêté à partir de la séquence 'fertilizer.decree'."""
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fertilizer.decree') or _('Nouveau')
        return super(FertilizerDecree, self).create(vals_list)
