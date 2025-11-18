# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class PhytosanitaryTechnicalEvaluation(models.Model):
    _name = 'phytosanitary.technical.evaluation'
    _description = 'Évaluation Technique des Appareils Phytosanitaires'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Référence', required=True, default=lambda self: _('Evaluation technique'), tracking=True)
    request_id = fields.Many2one('phytosanitary.certification.request', 
                                 string='Demande', required=True, tracking=True)
    equipment_id = fields.Many2one('phytosanitary.equipment', string='Appareil', required=True, tracking=True)
    evaluator_id = fields.Many2one('res.users', string='Évaluateur', required=True, tracking=True)
    evaluation_date = fields.Date('Date d\'évaluation',tracking=True)
    
    # Critères d'évaluation
    functionality_score = fields.Float('Score de fonctionnalité', tracking=True)
    safety_score = fields.Float('Score de sécurité', tracking=True)
    compliance_score = fields.Float('Score de conformité', tracking=True)
    environmental_impact_score = fields.Float('Score d\'impact environnemental', tracking=True)
    durability_score = fields.Float('Score de durabilité', tracking=True)
    maintenance_score = fields.Float('Score de facilité de maintenance', tracking=True)

    overall_score = fields.Float('Score global', compute='_compute_overall_score', store=True, tracking=True)

    @api.depends(
        'functionality_score', 'safety_score', 'compliance_score',
        'environmental_impact_score', 'durability_score', 'maintenance_score'
    )
    def _compute_overall_score(self):
        for record in self:
            scores = [
                record.functionality_score,
                record.safety_score,
                record.compliance_score,
                record.environmental_impact_score,
                record.durability_score,
                record.maintenance_score
            ]
            valid_scores = [s for s in scores if s > 0]
            record.overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
   
    # Évaluation détaillée
    functionality_comments = fields.Text('Commentaires sur la fonctionnalité', tracking=True)
    safety_comments = fields.Text('Commentaires sur la sécurité', tracking=True)
    compliance_comments = fields.Text('Commentaires sur la conformité', tracking=True)
    environmental_comments = fields.Text('Commentaires sur l\'impact environnemental', tracking=True)
    durability_comments = fields.Text('Commentaires sur la durabilité', tracking=True)
    maintenance_comments = fields.Text('Commentaires sur la maintenance', tracking=True)

     
    # Tests effectués
    field_test_performed = fields.Boolean('Test terrain effectué', tracking=True)
    field_test_date = fields.Date('Date du test terrain', tracking=True)
    field_test_results = fields.Text('Résultats du test terrain', tracking=True)
    laboratory_test_performed = fields.Boolean('Test en laboratoire effectué', tracking=True)
    laboratory_test_results = fields.Text('Résultats du test laboratoire', tracking=True)

   
    # Recommandations
    recommendation = fields.Selection([
        ('favorable', 'Favorable'),
        ('conditional', 'Favorable sous conditions'),
        ('unfavorable', 'Défavorable')
    ], string='Recommandation', tracking=True)

    conditions = fields.Text('Conditions spécifiques (si applicable)', tracking=True)

    
    # Rapport technique
    
    technical_report = fields.Text('Note d\'evaluation technique', tracking=True)
    technical_report_file = fields.Binary('Fichier rapport technique')
    technical_report_filename = fields.Char('Nom du fichier rapport')
    
    # État de l’évaluation

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('done', 'Validé'),
    ], string='Statut', default='draft', tracking=True)
    
    

    def action_set_in_progress(self):
        for record in self:
            record.state = 'in_progress'

    def action_set_done(self):
        for record in self:
            record.state = 'done'
    
    @api.model
    def create(self, vals):
        evaluation = super().create(vals)
        # Lier l'évaluation à la demande
        if evaluation.request_id:
            evaluation.request_id.write({'technical_evaluation_id': evaluation.id})
        return evaluation

class PhytosanitaryAdminEvaluation(models.Model):
    _name = 'phytosanitary.admin.evaluation'
    _description = 'Évaluation Administrative'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    request_id = fields.Many2one('phytosanitary.certification.request', 
                                 string='Demande', required=True, tracking=True)
    evaluator_id = fields.Many2one('res.users', string='Évaluateur', required=True, tracking=True)
    evaluation_date = fields.Date('Date d\'évaluation', required=True, tracking=True)
    
    # Vérifications documentaires
    documents_complete = fields.Boolean('Documents complets', tracking=True)
    documents_valid = fields.Boolean('Documents valides', tracking=True)
    fees_verified = fields.Boolean('Frais vérifiés', tracking=True)
    
    # Résultat
    is_compliant = fields.Boolean('Conforme', tracking=True)
    non_compliance_reasons = fields.Text('Motifs de non-conformité', tracking=True)
    
    # Actions requises
    additional_documents_needed = fields.Text('Documents supplémentaires requis', tracking=True)
    corrections_needed = fields.Text('Corrections nécessaires', tracking=True)
    
    # État de l’évaluation
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('done', 'Validé'),
    ], string='Statut', default='draft', tracking=True)
    
    
    def action_set_in_progress(self):
        self.state = 'in_progress'

    def action_set_done(self):
        self.state = 'done'