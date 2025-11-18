from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LabellingPackaging(models.Model):
    _name = 'labelling.packaging'
    _description = 'Conditionnement pour Étiquetage'
    _order = 'packaging_weight desc'
    
    labelling_request_id = fields.Many2one('labelling.request', string='Demande d\'Étiquetage', required=True, ondelete='cascade')
    packaging_weight = fields.Float('Poids du conditionnement (kg)', required=True)
    quantity_packages = fields.Integer('Nombre de conditionnements', required=True, default=1)
    total_weight = fields.Float('Poids total (kg)', compute='_compute_total_weight', store=True)
    
    @api.depends('packaging_weight', 'quantity_packages')
    def _compute_total_weight(self):
        for record in self:
            record.total_weight = record.packaging_weight * record.quantity_packages
    
    @api.constrains('packaging_weight', 'quantity_packages')
    def _check_positive_values(self):
        for record in self:
            if record.packaging_weight <= 0:
                raise UserError("Le poids du conditionnement doit être supérieur à zéro.")
            if record.quantity_packages <= 0:
                raise UserError("Le nombre de conditionnements doit être supérieur à zéro.")