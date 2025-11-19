# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CertificationInspection(models.Model):
    _name = "certification.inspection"
    _description = "Inspection d'un lot de parcelle"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "inspection_date desc"

    name = fields.Char(string="Référence inspection", required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('certification.inspection'))
    lot_id = fields.Many2one('certification.parcelle.lot', string="Lot", required=True, ondelete='cascade')
    parcelle_id = fields.Many2one('certification.parcelle', string="Parcelle", related='lot_id.parcelle_id', store=True)
    inspection_date = fields.Datetime(string="Date inspection", default=fields.Datetime.today().now())
    assigned_by_id = fields.Many2one('res.users', string="Assigné par (superviseur)", readonly=True)
    inspector_id = fields.Many2one('res.users', string="Agent inspecteur", required=True)
    inspector_code = fields.Integer(string="Code inspecteur", required=True)
    request_id = fields.Many2one('certification.request', related='lot_id.request_id', store=True)

    # Informations générales
    multiplacator_name = fields.Char(string="Raison sociale ou Nom du multiplicateur")
    addresse = fields.Char(string="Adresse/Tel")
    region = fields.Char(string="Région", compute='_compute_parcelle_location', store=True)
    departement = fields.Char(string="Département", compute='_compute_parcelle_location', store=True)
    arrondissement = fields.Char(string="Arrondissement", compute='_compute_parcelle_location', store=True)
    espece = fields.Char(string="Espèce", compute='_compute_parcelle_info', store=True)
    variety = fields.Char(string="Variété", compute='_compute_parcelle_info', store=True)
    category = fields.Char(string="Catégorie a produire", compute='_compute_parcelle_info', store=True)
    estimated_harvest_date = fields.Date(string="Date estimée de récolte")
    superficie_or_number = fields.Char(string="Superficie/nombre de plants inspectée(s)")
    gps_coordinates = fields.Char(string="Coordonnées GPS")
    is_pancarte_implanted = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string="Pancarte implantée",
                                             default='oui')
    # Calendrier et quantités
    inspected_area = fields.Float(string="Superficie/nombre de plants inspectée(s)",
                                  help="Surface en ha ou nombre de plants")
    seeding_date = fields.Date(string="Date semis")
    estimated_yield = fields.Char(string="Récolte estimée (unité)")
    seed_buyer = fields.Char(string="Acheteur de la semence brute")
    # Semence mère
    mother_seed_source = fields.Text(string="Source de la semence mère")
    is_mother_seed_certified = fields.Selection([('oui', 'Oui'), ('non', 'Non')],
                                                string="Semence mère inspectée et certifiée", default='oui')
    # Attribution et Encadrement
    lot_number_attribution = fields.Char(string="Attribution N° du lot", compute='_compute_lot_number', store=True)
    support_structure = fields.Char(string="Structure d'encadrement ou d'appui", compute='_compute_parcelle_location',
                                    store=True)

    # Informations sur l'inspection

    isolation_status = fields.Selection([('bon', 'Bon'), ('mauvais', 'Mauvais')], string="Isolement",
                                        help="Bon/mauvais")
    seed_transmissible_diseases_names = fields.Char(string="Nom de maladies transmissibles par les semences")
    dangerous_weeds_names = fields.Char(string="Nom des adventices dangereux")
    non_transmissible_diseases_names = fields.Char(string="Nom des maladies non transmissibles par les semences")
    culture_maintenance_status = fields.Text(string="État d'entretien de la culture")

    is_compliant_to_standards = fields.Selection([('oui', 'Oui'), ('non', 'Non')],
                                                 string="La parcelle répond-elle aux normes de certification?",
                                                 store=True)

    is_last_inspection = fields.Selection([('oui', 'Oui'), ('non', 'Non')], string="Est-ce la dernière inspection?",
                                          default='non')
    next_inspection_date = fields.Date(string="Date de la prochaine inspection")

    multiplicator_present = fields.Selection([('oui', 'Oui'), ('non', 'Non')],
                                             string="Multiplicateur ou son représentant présent lors de l'inspection?",
                                             default='oui')

    remarks_recommendations = fields.Text(string="Remarques/Recommandations")

    state = fields.Selection([
        ('draft', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('done', 'Terminée'),
        ('cancel', 'Annulée')
    ], default='draft', tracking=True)
    visit_stage = fields.Selection([
        ('pre_flowering', 'Avant floraison'),
        ('mid_flowering', '50% floraison'),
        ('pre_harvest', 'Pré-récolte'),
    ], string="Étape visite")

    recommendation = fields.Text(string="Recommandations")
    report_attachment = fields.Binary(string="Rapport (PDF/scan)")
    report_filename = fields.Char(string="Nom fichier")
    report_signed_by_farmer = fields.Boolean(string="Co-signé par le producteur")
    conclusion = fields.Selection([('ok', 'Conforme'), ('non_ok', 'Non conforme')], string="Conclusion")
    checked = fields.Boolean(string="Rapport validé par le superviseur", default=False)
    checked_by = fields.Many2one('res.users', string="Superviseur (validation)")
    checked_date = fields.Datetime(string="Date validation")

    @api.depends('lot_id')
    def _compute_lot_number(self):
        for rec in self:
            if rec.lot_id and rec.lot_id.name:
                # Extraire le numéro du lot (ex: LOT-0001 -> 0001)
                lot_ref = rec.lot_id.name
                if '-' in lot_ref:
                    rec.lot_number_attribution = lot_ref.split('-')[-1]
                else:
                    rec.lot_number_attribution = str(rec.lot_id.id).zfill(4)
            else:
                rec.lot_number_attribution = ''

    @api.depends('parcelle_id')
    def _compute_parcelle_info(self):
        for rec in self:
            if rec.parcelle_id:
                rec.espece = rec.parcelle_id.espece or ''
                rec.variety = rec.parcelle_id.variete or ''
                rec.category = rec.parcelle_id.categorie or ''
            else:
                rec.espece = ''
                rec.variety = ''
                rec.category = ''

    @api.depends('parcelle_id')
    def _compute_parcelle_location(self):
        for rec in self:
            if rec.parcelle_id:
                rec.region = rec.parcelle_id.region_id.name if rec.parcelle_id.region_id else ''
                rec.departement = rec.parcelle_id.departement_id.name if rec.parcelle_id.departement_id else ''
                rec.arrondissement = rec.parcelle_id.arrondissement_id.name if rec.parcelle_id.arrondissement_id else ''
                rec.support_structure = rec.parcelle_id.encadrement_structure or ''
            else:
                rec.region = ''
                rec.departement = ''
                rec.arrondissement = ''
                rec.support_structure = ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code('certification.inspection') or _('Nouveau')
        records = super().create(vals_list)
        return records

    # contraintes simples
    @api.constrains('inspector_id', 'state')
    def _check_inspector_when_assigned(self):
        for rec in self:
            if rec.state in ('in_progress', 'done') and not rec.inspector_id:
                raise UserError("Une inspection affectée doit avoir un agent inspecteur.")

    def action_start(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError("L'inspection doit être en état 'assignée' ou 'planifiée' pour démarrer.")
                # Verifions si l'utilisateur qui effectue l'inspection est l'utilisateur qui a ete assigné sur l'inpection
            if rec.env.user != rec.inspector_id:
                raise UserError("Vous n'avez pas l'autorisation d'effectuer cet inspection")
            rec.state = 'in_progress'
            rec.message_post(body="Inspection démarrée.")

    def action_done(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("L'inspection doit être 'en cours' pour être marquée terminée.")
            # Verifions si l'utilisateur qui effectue l'inspection est l'utilisateur qui a ete assigné sur l'inpection
            if rec.env.user != rec.inspector_id:
                raise UserError("Vous n'avez pas l'autorisation d'effectuer cet inspection")
            # on exige rapport ou conclusion
            if not rec.report_attachment and not rec.conclusion and not rec.estimated_yield:
                raise UserError(
                    " Veillez Ajoutez une conclusion , un rapport et la recolte estimée avant de clore l'inspection.")
            rec.state = 'done'
            rec.message_post(body="Inspection terminée.")
            # si toutes les inspections d'un lot sont done, on peut mettre lot en 'closed' ou laisser superviseur décider

    def action_cancel(self):  # <- The one your IDE is complaining about!
        # The 'Annuler' (Cancel) button logic
        self.ensure_one()
        self.state = 'cancel'
        # Add cleanup logic here, e.g., self.message_post(body="Inspection cancelled.")

    def action_back_to_previous_state(self):
        """Retourner à l'état précédent"""
        for rec in self:
            if rec.state == 'in_progress':
                rec.state = 'draft'
            elif rec.state == 'done':
                rec.state = 'in_progress'
            elif rec.state == 'cancel':
                rec.state = 'draft'
            else:
                raise UserError("Impossible de revenir en arrière à partir de cet état.")

    def action_close_and_return(self):
        return {
            'type': 'ir.actions.act_window_close'
        }

