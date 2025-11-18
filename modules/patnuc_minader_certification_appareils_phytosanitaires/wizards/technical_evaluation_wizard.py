from odoo import models, fields, api

class TechnicalEvaluationWizard(models.TransientModel):
    _name = 'phytosanitary.technical.evaluation.wizard'
    _description = 'Assistant Évaluation Technique'

    request_id = fields.Many2one('phytosanitary.certification.request', string='Demande', required=True)
    evaluation_notes = fields.Text('Notes d\'évaluation', required=True)
    evaluation_result = fields.Selection([
        ('favorable', 'Favorable'),
        ('conditional', 'Favorable sous conditions'),
        ('unfavorable', 'Défavorable')
    ], string='Résultat de l\'évaluation', required=True)
    
    def action_confirm_evaluation(self):
        # Créer l'évaluation technique
        evaluation = self.env['phytosanitary.technical.evaluation'].create({
            'request_id': self.request_id.id,
            'equipment_id': self.request_id.equipment_id.id,
            'technical_report': self.evaluation_notes,
            'recommendation': self.evaluation_result,
            'evaluator_id': self.env.user.id,
            'evaluation_date': fields.Date.today()
        })
        
        # Mettre à jour la demande
        self.request_id.write({
            'technical_evaluation_id': evaluation.id,
            'technical_evaluation_notes': self.evaluation_notes,
            'technical_evaluation_result': self.evaluation_result
        })
        
        return {'type': 'ir.actions.act_window_close'}