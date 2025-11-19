# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Commune(models.Model):
    _name = 'infrastructure.commune'
    _description = 'Commune'
    _order = 'name'
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Le code de la commune doit être unique.'),
        ('name_unique', 'unique(name)', 'Le nom de la commune doit être unique.')
    ]

    #reference user commune
    resp_commune =  fields.Many2one('res.users', string='Responsable de la commune', required=True, tracking=True)

#data
    name = fields.Char('Nom de la Commune', required=True, index=True)
    code = fields.Char('Code Commune', required=True, index=True)
    mayor_name = fields.Char('Nom du Maire')
    contact_email = fields.Char('Email de Contact')
    contact_phone = fields.Char('Téléphone de Contact')
    address = fields.Text('Adresse')
    active = fields.Boolean('Actif', default=True)
    
    # Relations
    region_id = fields.Many2one("minader.region", string="Région")
    departement_id = fields.Many2one("minader.departement", string="Département", required=True)
    arrondissement_id = fields.Many2one("minader.arrondissement", string="Arrondissement", required=True)

    # Relations inverses
    financing_request_ids = fields.One2many(
        'infrastructure.financing.request', 
        'commune_id', 
        string='Demandes de Financement'
    )
    
    # Statistiques
    funding_request_count = fields.Integer(
        'Nombre de Demandes', 
        compute='_compute_funding_request_count',
        store=True
    )
    
    @api.depends('financing_request_ids')
    def _compute_funding_request_count(self):
        for record in self:
            record.funding_request_count = len(record.financing_request_ids)
    
    @api.constrains('contact_email')
    def _check_email(self):
        for record in self:
            if record.contact_email and '@' not in record.contact_email:
                raise ValidationError(_("L'adresse email n'est pas valide."))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
    
    # (Q) Champ calculé pour déterminer si la commune doit être en lecture seule
    is_readonly = fields.Boolean(
        string="Lecture seule",
        compute='_compute_is_readonly',
        help="True si la commune a des demandes en cours à partir de l'étape verification"
    )
    
    @api.depends('financing_request_ids', 'financing_request_ids.state')
    def _compute_is_readonly(self):
        """(Q) Calculer si la commune doit être en lecture seule"""
        for record in self:
            # (Q) Vérifier s'il y a des demandes en cours à partir de l'étape verification
            active_requests = record.financing_request_ids.filtered(
                lambda r: r.state not in ['draft', 'rejected', 'notified']
            )
            record.is_readonly = bool(active_requests)
    
    def action_view_requests(self):
        """Action pour voir les demandes de financement de cette commune"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Demandes de {self.name}',
            'res_model': 'infrastructure.financing.request',
            'view_mode': 'tree,form',
            'domain': [('commune_id', '=', self.id)],
            'context': {'default_commune_id': self.id},
            'target': 'current',
        }