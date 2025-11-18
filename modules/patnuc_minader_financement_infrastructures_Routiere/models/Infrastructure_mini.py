from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class InfrastructureMini(models.Model):
    _name = 'infrastructure.mini'
    _description = "Fiche technique - Mini-infrastructure"
    
    name = fields.Char('Référence', compute='_compute_name', store=True)
    request_id = fields.Many2one('infrastructure.financing.request', string="Demande liée")
    technical_info_date = fields.Datetime('Date d\'ajout des informations techniques', default=fields.Datetime.now, readonly=True)

    mini_type = fields.Selection([
        ('poste_agricole', 'Poste Agricole'),
        ('daager', 'Délégation d\'Arrondissement'),
        ('ceac', 'CEAC'),
        ('case_communautaire', 'Case Communautaire'),
        ('hangar_marche', 'Hangar de Marché'),
        ('magasin', 'Magasin de Stockage'),
        ('aire_sechage', 'Aire de Séchage'),
        ('point_eau', 'Point d\'eau')
    ], string="Type de mini-infrastructure", required=True)
    
    localisation = fields.Char('Localisation')
    superficie = fields.Float('Superficie disponible (m²)')
    soil_type = fields.Char('Type de sol')
    hydrology = fields.Text('Hydrologie / Napper phréatique')
    design_data = fields.Text('Données de conception')
    equipment_data = fields.Text('Équipements à prévoir')
    status = fields.Text('État actuel / Fonctionnalité')
    intervention_type = fields.Selection([
        ('construction', 'Construction'),
        ('rehabilitation', 'Réhabilitation'),
        ('entretien', 'Entretien / Équipement')
    ], string="Type d'intervention")
    
    @api.depends('request_id', 'mini_type')
    def _compute_name(self):
        for record in self:
            if record.request_id and record.mini_type:
                record.name = f"Mini-infra - {record.request_id.name} - {dict(record._fields['mini_type'].selection)[record.mini_type]}"
            else:
                record.name = "Fiche Mini-infrastructure"
    
    def action_save_and_close(self):
        """Enregistrer et fermer le formulaire"""
        return {'type': 'ir.actions.act_window_close'}