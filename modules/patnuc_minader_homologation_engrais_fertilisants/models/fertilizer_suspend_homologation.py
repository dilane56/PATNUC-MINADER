# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FertilizerSuspendHomologation(models.Model):
    _name = 'fertilizer.suspend.homologation'
    _description = 'Procédure de suspension de l\'homologation des engrais et fertilisants'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
      
    #reference demande homolog init 
    arrete_id = fields.Many2one('fertilizer.decree', 
                                 string='reference de l\'arrêté', required=True)
   #product agricole : intrants agricole
    old_product_hom = fields.Many2one(
        'fertilizer.product',
        string="Produit homologué",
        related='arrete_id.commercial_name',
        readonly=True,
        store=True
    )
   
    # Champs liés
    applicant_id = fields.Many2one(
        related='arrete_id.applicant_id',
        string="Demandeur",
        store=True,
        readonly=True,
    )
    
    #date de delivrance et de soumission
    submission_date = fields.Datetime(string='Date de soumission',default=fields.Datetime.now, readonly=True, tracking=True)
    date_suspension = fields.Date(string='Date de suspension',readonly=True, tracking=True)
    assigned_to = fields.Many2one('res.users', string='Responsable', tracking=True, default=lambda self: self.env.user)
    
    # motif de la suspension
    reason_suspension = fields.Text(string='motif de suspension de l\'homologation', tracking=True)
    
    # Séquence des états simplifiée
    state = fields.Selection([
        ('draft', 'Objet de suspension'),
        ('decision', 'Suspension confirmée'), 
    ], string='État', default='draft', tracking=True)
 
    # Documents attendu  pour la suspension
    
    pv_suspension = fields.Binary(string="PV de suspension", required=True)
    pv_suspension_filename = fields.Char(string="Nom du fichier")
   
    # Reception (Réception - State 'verification')
 
    # date de confirmation de suspension
    date_confirm_suspens = fields.Datetime(string='Date de confirmation de suspension', tracking=True)


    # Fonctions de workflow (Avancement)
   
    def action_suspend(self):
        """Passe de Brouillon à confirmation de suspension"""
        for record in self:
            if not record.pv_suspension or not record.reason_suspension :
                raise ValidationError(_("Veuillez donner une raison de suspension et le charger le PV de suspension."))
            record.submission_date = fields.Datetime.now()
            record.state = 'decision'
            record.assigned_to = self.env.user.id
            #update state arrete for suspend 
            renew_arrete =  {'state' : 'suspendu'}
            record.arrete_id.write(renew_arrete)
            record.date_suspension = fields.Datetime.now()
            record.message_post(body=_(f"L'homologation {record.name} est suspendu"))
    

    # Séquence, création et écriture (simplifié)
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('fertilizer.suspend.homologation') or _('New')
        return super(FertilizerSuspendHomologation, self).create(vals)
    
    def unlink(self):
        for record in self:
            if record.state not in ['draft']:
                raise UserError(_('Vous ne pouvez pas supprimer un dossier qui n\'est pas en brouillon '))
        return super(FertilizerSuspendHomologation, self).unlink()
