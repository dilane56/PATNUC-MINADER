from odoo import models, fields, api
from odoo import tools

class CertificationStatisticalReport(models.Model):
    _name = 'certification.statistical.report'
    _description = 'Rapport Statistique Certification'
    _auto = False
    
    operator_id = fields.Many2one('res.partner', string='Opérateur')
    parcelle_variete = fields.Char('Variété')
    request_count = fields.Integer('Nombre de demandes')
    approved_count = fields.Integer('Nombre approuvées')
    rejected_count = fields.Integer('Nombre rejetées')
    average_processing_time = fields.Float('Temps moyen de traitement (jours)')
    total_certified_quantity = fields.Float('Quantité totale certifiée (kg)')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    1 as id,
                    1 as operator_id,
                    'test' as parcelle_variete,
                    0 as request_count,
                    0 as approved_count,
                    0 as rejected_count,
                    0 as average_processing_time,
                    0 as total_certified_quantity
                WHERE FALSE
            )
        """ % self._table)