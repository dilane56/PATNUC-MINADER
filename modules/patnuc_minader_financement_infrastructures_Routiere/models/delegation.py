# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Delegation(models.Model):
    _name = 'infrastructure.delegation'
    _description = 'Délégation MINADER'
    _order = 'type, name'
    # _sql_constraints = [
    #     ('code_unique', 'unique(code)', 'Le code de la délégation doit être unique.'),
    # ]

    name = fields.Char('Nom de la Délégation', required=True, index=True)
    type = fields.Selection([
        ('regional', 'Régionale'),
        ('departmental', 'Départementale')
    ], string='Type', required=True, index=True)
    
    code = fields.Char('Code Délégation', index=True)
    delegate_name = fields.Char('Nom du Délégué')
    contact_email = fields.Char('Email')
    contact_phone = fields.Char('Téléphone')
    address = fields.Text('Adresse')
    active = fields.Boolean('Actif', default=True)
    
    # Zone de compétence
    region = fields.Char('Région')
    department = fields.Char('Département')
    
    # Utilisateurs assignés
    user_ids = fields.Many2many(
        'res.users', 
        'delegation_user_rel', 
        'delegation_id', 
        'user_id',
        string='Utilisateurs Assignés'
    )
    
    # Relations inverses
    financing_request_ids = fields.One2many(
        'infrastructure.financing.request',
        'delegation_id',
        string='Demandes Assignées'
    )
    
    # Statistiques
    active_requests_count = fields.Integer(
        'Demandes Actives', 
        compute='_compute_active_requests_count',
        store=True
    )
    total_requests_count = fields.Integer(
        'Total Demandes',
        compute='_compute_total_requests_count',
        store=True
    )
    
    @api.depends('financing_request_ids', 'financing_request_ids.state')
    def _compute_active_requests_count(self):
        for record in self:
            record.active_requests_count = len(record.financing_request_ids.filtered(
                lambda r: r.state not in ['rejected', 'notified']
            ))
    
    @api.depends('financing_request_ids')
    def _compute_total_requests_count(self):
        for record in self:
            record.total_requests_count = len(record.financing_request_ids)
    
    @api.constrains('contact_email')
    def _check_email(self):
        for record in self:
            if record.contact_email and '@' not in record.contact_email:
                raise ValidationError(_("L'adresse email n'est pas valide."))
    
    @api.constrains('type', 'region', 'department')
    def _check_competence_zone(self):
        for record in self:
            if record.type == 'regional' and not record.region:
                raise ValidationError(_("Une délégation régionale doit avoir une région définie."))
            if record.type == 'departmental' and not record.department:
                raise ValidationError(_("Une délégation départementale doit avoir un département défini."))
    
    def name_get(self):
        result = []
        for record in self:
            type_label = dict(record._fields['type'].selection)[record.type]
            name = f"[{type_label}] {record.name}"
            if record.code:
                name = f"[{record.code}] {name}"
            result.append((record.id, name))
        return result
    
    def action_view_requests(self):
        """Action pour voir les demandes assignées à cette délégation"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Demandes - {self.name}',
            'res_model': 'infrastructure.financing.request',
            'view_mode': 'tree,form',
            'domain': [('delegation_id', '=', self.id)],
            'context': {'default_delegation_id': self.id},
            'target': 'current',
        }