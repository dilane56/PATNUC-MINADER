from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class InfrastructureArtwork(models.Model):
    _name = 'infrastructure.artwork'
    _description = "Fiche technique - Ouvrage d’art"
    
    name = fields.Char('Référence', compute='_compute_name', store=True)
    request_id = fields.Many2one('infrastructure.financing.request', string="Demande liée")
    technical_info_date = fields.Datetime('Date d\'ajout des informations techniques', default=fields.Datetime.now, readonly=True)
    
    work_type = fields.Selection([
        ('pont', 'Pont'),
        ('dalot', 'Dalot'),
        ('buse', 'Buse'),
        ('ponceau', 'Ponceau'),
        ('passerelle', 'Passerelle')
    ], string="Type d’ouvrage", required=True)

    dimensions = fields.Char('Dimensions principales')
    condition = fields.Text('État constaté')
    hydraulic_state = fields.Text('État hydraulique')
    structural_state = fields.Text('État structurel')
    recommended_work = fields.Text('Travaux recommandés')
    maintenance_urgency = fields.Selection([
        ('petit', 'Petit entretien'),
        ('gros', 'Gros entretien'),
        ('urgent', 'Intervention immédiate')
    ], string="Urgence des travaux")
    
    @api.depends('request_id', 'work_type')
    def _compute_name(self):
        for record in self:
            if record.request_id and record.work_type:
                record.name = f"Ouvrage - {record.request_id.name} - {dict(record._fields['work_type'].selection)[record.work_type]}"
            else:
                record.name = "Fiche Ouvrage d'art"
    
    def action_save_and_close(self):
        """Enregistrer et fermer le formulaire"""
        return {'type': 'ir.actions.act_window_close'}
