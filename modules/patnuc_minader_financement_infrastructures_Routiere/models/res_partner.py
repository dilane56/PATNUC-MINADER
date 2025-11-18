from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # (Q) Relation supprimée car c'est la commune qui effectue directement la demande
    # infrastructure_request_ids = fields.One2many(
    #     'infrastructure.financing.request',
    #     'requester_id',
    #     string="Demandes de financement"
    # )

    # (Q) Champs et méthodes supprimés car la relation avec requester_id n'existe plus
    # infrastructure_request_count = fields.Integer(
    #     'Nombre de demandes',
    #     compute='_compute_infrastructure_request_count'
    # )

    # def _compute_infrastructure_request_count(self):
    #     for partner in self:
    #         partner.infrastructure_request_count = len(partner.infrastructure_request_ids)

    # def action_view_infrastructure_requests(self):
    #     return {
    #         'name': 'Demandes de financement',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'tree,form',
    #         'res_model': 'infrastructure.financing.request',
    #         'domain': [('requester_id', '=', self.id)],
    #         'context': {'default_requester_id': self.id}
    #     }
