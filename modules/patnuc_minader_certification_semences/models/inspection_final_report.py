from odoo import models, fields, api
from odoo.exceptions import UserError


class CertificationInspectionFinalReport(models.Model):
    _name = "certification.inspection.final"
    _description = "Rapport final d'inspection (agrégé par superviseur)"
    _rec_name = "name"

    name = fields.Char(string="Référence rapport final", required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('certification.inspection.final'))
    request_id = fields.Many2one('certification.request', string="Demande", required=True, ondelete='cascade')
    parcelle_id = fields.Many2one('certification.parcelle', string="Parcelle", related='request_id.parcelle_id', store=True)
    created_by = fields.Many2one('res.users', string="Superviseur", default=lambda self: self.env.user)
    created_date = fields.Datetime(string="Date de création", default=fields.Datetime.now)
    inspection_ids = fields.Many2many('certification.inspection', string="Inspections agrégées")
    summary = fields.Text(string="Synthèse / conclusion")
    decision = fields.Selection([('ok','Valide'), ('non_ok','Rejette')], string="Décision finale", required=True)
    final_report = fields.Binary(string="Rapport final (pdf)", required=True)
    final_report_filename = fields.Char(string="Nom du fichier PDF")


    # Champs pour affichage rapide sur la demande
    report_summary = fields.Text(string="Résumé du rapport", compute='_compute_report_summary', store=True)
    total_inspections = fields.Integer(string="Nombre d'inspections", compute='_compute_inspection_stats', store=True)
    lots_inspected = fields.Integer(string="Lots inspectés", compute='_compute_inspection_stats', store=True)


    
    @api.depends('summary', 'decision')
    def _compute_report_summary(self):
        for rec in self:
            if rec.decision:
                decision_text = dict(rec._fields['decision'].selection).get(rec.decision, '')
                summary_text = rec.summary[:200] + '...' if rec.summary and len(rec.summary) > 200 else rec.summary or ''
                rec.report_summary = f"Décision: {decision_text}\n{summary_text}"
            else:
                rec.report_summary = "Rapport en cours de rédaction"
    
    @api.depends('inspection_ids')
    def _compute_inspection_stats(self):
        for rec in self:
            rec.total_inspections = len(rec.inspection_ids)
            rec.lots_inspected = len(rec.inspection_ids.mapped('lot_id'))
    
    def action_save_and_close(self):
        """Sauvegarder et fermer le rapport"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
    
    @api.model
    def create(self, vals):
        """Lier automatiquement le rapport à la demande lors de la création"""
        report = super().create(vals)
        if report.request_id and not report.request_id.final_inspection_report_id:
            report.request_id.final_inspection_report_id = report.id
        return report
