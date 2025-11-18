# models/certification_operator.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CertificationOperator(models.Model):
    _name = 'certification.operator'
    _description = 'Opérateur habilité à effectuer la certification des semences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # --- Contraintes SQL ---
    # Unique sur user_id (la colonne en base s'appelle bien user_id)
    _sql_constraints = [
        ('unique_user', 'UNIQUE(user_id)', "Cet utilisateur est déjà rattaché à un opérateur.")
    ]

    # reference de l'operateur 
    name = fields.Char('Référence ',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('certification.operator')
    )
    # -------------------------
    # Relations principales
    # -------------------------
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur rattaché',
        required=True,
        help="Utilisateur Odoo (préférable : groupe portal) lié à cet opérateur."
    )

    # partner_id est lié au partner du user (aucune duplication de données)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire (contact)',
        related='user_id.partner_id',
        store=True,
        readonly=True
    )

    # Pour affichage lisible dans les Many2one et listes
    partner_name = fields.Char(
        string='Nom du partenaire',
        related='partner_id.name',
        store=True,
        readonly=True
    )

    partner_email = fields.Char(
        string='Email',
        related='partner_id.email',
        store=True,
        readonly=True
    )

    partner_phone = fields.Char(
        string='Téléphone',
        related='partner_id.phone',
        store=True,
        readonly=True
    )
    @api.onchange('actif')
    def _onchange_actif(self):
        if self.actif:
            if self.state not in ('approved', 'suspended', 'cancelled'):
                self.state = 'active'
        elif not self.actif:
            if self.state == 'active':
                self.state = 'draft'

    # -------------------------
    # Champs métiers propres à l'opérateur
    # -------------------------


    operator_type = fields.Selection([
        ('individual', 'Personne physique'),
        ('cooperative', 'Coopérative'),
        ('company', 'Entreprise'),
        ('approved_producer', 'Producteur agréé'),
    ], string="Type d'opérateur", required=True)

    professional_card = fields.Char(string='Carte professionnelle')
    technical_approval = fields.Char(string='Agrément technique')
    cni_number = fields.Char(string='Numéro CNI')

    actif = fields.Boolean(string='Actif', default=False)

    state = fields.Selection([
        ('draft', 'Inactif'),
        ('approved', 'Agréé'),
        ('active','actif'),
        ('suspended', 'Suspendu'),
        ('cancelled', 'Annulé')
    ], string='Statut', default='draft', tracking=True)

    # Relations métier
    certification_requests = fields.One2many('certification.request', 'operator_id', string='Demandes de certification')
    agreement_ids = fields.One2many('certification.agreement', 'operator_id', string='Agréments')

    certification_count = fields.Integer(string='Nombre de certifications', compute='_compute_certification_count', store=True)

    is_agreed_cesp = fields.Boolean(string='Opérateur agréé CESP', default=False)
    has_valid_agreement = fields.Boolean(string='Agrément valide', compute='_compute_has_valid_agreement', store=True)

   
    # -------------------------
    # Création / Séquence
    # -------------------------
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('certification.operator') or 'New'
        return super(CertificationOperator, self).create(vals)

    # -------------------------
    # Computed fields
    # -------------------------
    @api.depends('certification_requests')
    def _compute_certification_count(self):
        for rec in self:
            rec.certification_count = len(rec.certification_requests or [])

    @api.depends('agreement_ids.is_valid')
    def _compute_has_valid_agreement(self):
        for rec in self:
            rec.has_valid_agreement = any(agr.is_valid for agr in rec.agreement_ids)

    # -------------------------
    # Contraintes Python (exemples)
    # -------------------------
    @api.constrains('user_id')
    def _check_user_not_shared(self):
        for rec in self:
            if rec.user_id:
                # vérifie qu'aucun autre operator n'a ce user
                other = self.search([('user_id', '=', rec.user_id.id), ('id', '!=', rec.id)])
                if other:
                    raise ValidationError("Cet utilisateur est déjà rattaché à un autre opérateur.")
    def action_view_agreements(self):
        """Ouvre les agréments liés dans une vue tree/form"""
        self.ensure_one()
        return {
            'name': 'Agréments de l’opérateur',
            'type': 'ir.actions.act_window',
            'res_model': 'certification.agreement',
            'view_mode': 'tree,form',
            'domain': [('operator_id', '=', self.id)],
            'target': 'current',
        }