from odoo import models, fields, api

class Laboratory(models.Model):
    _name = 'certification.laboratory'
    _description = 'Laboratoire'
    
    name = fields.Char('Nom', required=True)
    code = fields.Char('Code', required=True)
    address = fields.Text('Adresse')
    phone = fields.Char('Téléphone')
    email = fields.Char('Email')
    responsible_id = fields.Many2one('res.users', string='Responsable')
    
    # Capacités
    accreditation = fields.Char('Accréditation')
    test_capabilities = fields.Text('Capacités de test')
    
    active = fields.Boolean('Actif', default=True)