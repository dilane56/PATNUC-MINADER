
"""
from odoo import models, fields
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    certification_request_ids = fields.One2many(
        'phytosanitary.certification.request', 
        'partner_id',
        string='Demandes de Certification'
    )
    
    certification_count = fields.Integer(
        'Nombre de Certifications',
        compute='_compute_certification_count'
    )
    
    def _compute_certification_count(self):
        for partner in self:
            partner.certification_count = len(partner.certification_request_ids)
    
    def action_view_certifications(self):
        #Voir les certifications du partenaire
        return {
            'name': 'Certifications',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'phytosanitary.certification.request',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }"""