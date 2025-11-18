# -*- coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    #is_laboratory = fields.Boolean(string='Est un laboratoire', default=False)
    #laboratory_accreditation = fields.Char(string='Numéro d\'accréditation')
    #laboratory_specialties = fields.Text(string='Spécialités du laboratoire')