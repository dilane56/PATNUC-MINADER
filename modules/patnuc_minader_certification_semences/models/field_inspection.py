# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class CertificationInspection(models.Model):
    _name = "certification.inspection"
    _description = "Inspection d'un lot de parcelle"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "scheduled_date desc"

    name = fields.Char(string="Référence inspection", required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('certification.inspection'))
    lot_id = fields.Many2one('certification.parcelle.lot', string="Lot", required=True, ondelete='cascade')
    parcelle_id = fields.Many2one('certification.parcelle', string="Parcelle", related='lot_id.parcelle_id', store=True)
    scheduled_date = fields.Date(string="Date planifiée")
    inspection_date = fields.Datetime(string="Date inspection", default=fields.Datetime.today().now())
    assigned_by_id = fields.Many2one('res.users', string="Assigné par (superviseur)", readonly=True)
    inspector_id = fields.Many2one('res.users', string="Agent inspecteur", required=True)
    request_id = fields.Many2one('certification.request', related='lot_id.request_id', store=True)

    state = fields.Selection([
        ('draft','Planifiée'),
        ('in_progress','En cours'),
        ('done','Terminée'),
        ('cancel','Annulée')
    ], default='draft', tracking=True)
    visit_stage = fields.Selection([
        ('pre_flowering','Avant floraison'),
        ('mid_flowering','50% floraison'),
        ('pre_harvest','Pré-récolte'),
    ], string="Étape visite")
    gps_coords = fields.Char(string="Coordonnées GPS")
    observations = fields.Text(string="Observations de l'agent")
    problems = fields.Text(string="Problèmes constatés (pureté, adventices, sanitaire...)")
    recommendation = fields.Text(string="Recommandations")
    report_attachment = fields.Binary(string="Rapport (PDF/scan)")
    report_filename = fields.Char(string="Nom fichier")
    report_signed_by_farmer = fields.Boolean(string="Co-signé par le producteur")
    conclusion = fields.Selection([('ok','Conforme'), ('non_ok','Non conforme')], string="Conclusion")
    checked = fields.Boolean(string="Rapport validé par le superviseur", default=False)
    checked_by = fields.Many2one('res.users', string="Superviseur (validation)")
    checked_date = fields.Datetime(string="Date validation")

    # contraintes simples
    @api.constrains('inspector_id', 'state')
    def _check_inspector_when_assigned(self):
        for rec in self:
            if rec.state in ('in_progress','done') and not rec.inspector_id:
                raise UserError("Une inspection affectée doit avoir un agent inspecteur.")


    def action_start(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError("L'inspection doit être en état 'assignée' ou 'planifiée' pour démarrer.")
                # Verifions si l'utilisateur qui effectue l'inspection est l'utilisateur qui a ete assigné sur l'inpection
            if rec.env.user != rec.inspector_id:
                raise UserError("Vous n'avez pas l'autorisation d'effectuer cet inspection")
            rec.state = 'in_progress'
            rec.message_post(body="Inspection démarrée.")

    def action_done(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("L'inspection doit être 'en cours' pour être marquée terminée.")
            #Verifions si l'utilisateur qui effectue l'inspection est l'utilisateur qui a ete assigné sur l'inpection
            if rec.env.user != rec.inspector_id:
                raise UserError("Vous n'avez pas l'autorisation d'effectuer cet inspection")
            # on exige rapport ou conclusion
            if not rec.report_attachment and not rec.conclusion:
                raise UserError("Ajoutez une conclusion ou un rapport avant de clore l'inspection.")
            rec.state = 'done'
            rec.message_post(body="Inspection terminée.")
            # si toutes les inspections d'un lot sont done, on peut mettre lot en 'closed' ou laisser superviseur décider

    def action_cancel(self):  # <- The one your IDE is complaining about!
        # The 'Annuler' (Cancel) button logic
        self.ensure_one()
        self.state = 'cancel'
        # Add cleanup logic here, e.g., self.message_post(body="Inspection cancelled.")

    def action_back_to_previous_state(self):
        """Retourner à l'état précédent"""
        for rec in self:
            if rec.state == 'in_progress':
                rec.state = 'draft'
            elif rec.state == 'done':
                rec.state = 'in_progress'
            elif rec.state == 'cancel':
                rec.state = 'draft'
            else:
                raise UserError("Impossible de revenir en arrière à partir de cet état.")
    
    def action_close_and_return(self):
        return {
            'type': 'ir.actions.act_window_close'
        }


