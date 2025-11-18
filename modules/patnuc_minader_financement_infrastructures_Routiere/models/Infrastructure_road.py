from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class InfrastructureRoad(models.Model):
    _name = 'infrastructure.road'
    _description = "Fiche technique - Route"
    
    name = fields.Char('Référence', compute='_compute_name', store=True)
    request_id = fields.Many2one('infrastructure.financing.request', string="Demande liée")
    technical_info_date = fields.Datetime('Date d\'ajout des informations techniques', default=fields.Datetime.now, readonly=True)
    
    intervention_type = fields.Selection([
        ('ouverture', 'Ouverture'),
        ('rehabilitation', 'Réhabilitation'),
        ('entretien', 'Entretien'),
    ], string="Type d’intervention", required=True)

    linear_km = fields.Float('Linéaire (Km)')
    start_point = fields.Char('Point de départ')
    end_point = fields.Char('Point d’arrivée')
    villages_served = fields.Text('Villages desservis')
    slope = fields.Char('Pente/Relief')
    soil_type = fields.Char('Type de sol')
    hydrology = fields.Text('Hydrologie (rivières, zones inondables)')
    environment = fields.Text('Environnement (zones habitées, agricoles...)')
    traffic = fields.Text('Trafic attendu')
    maintenance_needs = fields.Text('Travaux recommandés')
    
    @api.depends('request_id', 'intervention_type')
    def _compute_name(self):
        for record in self:
            if record.request_id and record.intervention_type:
                record.name = f"Route - {record.request_id.name} - {dict(record._fields['intervention_type'].selection)[record.intervention_type]}"
            else:
                record.name = "Fiche Route"
    
    def action_save_and_close(self):
        """Enregistrer et fermer le formulaire"""
        return {'type': 'ir.actions.act_window_close'}
