from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class TechnicalSupport(models.Model):
    _name = 'infrastructure.technical.support'
    _description = 'Dossier d\'appui technique'


    # Lien avec la demande de financement
    # chaque dossier d'appui technique est lié à une demande de financement spécifique

    request_id = fields.Many2one(
        'infrastructure.financing.request',
        string='Demande associée'
    )

    # Informations de base sur le dossier d'appui technique
    supporting_docs_ids = fields.One2many(
        'infrastructure.document', 'support_id',
        string='Documents d\'appui'
    )


    start_date = fields.Datetime('Date de début', default=fields.Datetime.now, readonly=True)
    
    notes = fields.Text('Observations techniques')
    
    # (Q) Champs pour l'évaluation technique
    technical_evaluation = fields.Selection([
        ('favorable', 'Favorable'),
        ('non_favorable', 'Non Favorable')
    ], string="Évaluation Technique")
    
    avis_technique = fields.Text(string="Avis Technique")
    

    
    # Documents techniques requis
    technical_plan_file = fields.Binary('Plan technique', required=True)
    technical_plan_filename = fields.Char('Nom du fichier')
    
    cost_estimate_file = fields.Binary('Devis', required=True)
    cost_estimate_filename = fields.Char('Nom du fichier')
    
    feasibility_report_file = fields.Binary('Rapport de faisabilité', required=True)
    feasibility_report_filename = fields.Char('Nom du fichier')
    
    technical_transmission_note_file = fields.Binary('Note de transmission technique', required=True)
    technical_transmission_note_filename = fields.Char('Nom du fichier')

    # (Q) Méthodes pour gérer les noms de fichiers
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        binary_fields = {
            'technical_plan_file': 'technical_plan_filename',
            'cost_estimate_file': 'cost_estimate_filename',
            'feasibility_report_file': 'feasibility_report_filename',
            'technical_transmission_note_file': 'technical_transmission_note_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field]:
                if filename_field not in vals or not vals[filename_field]:
                    filename = self.env.context.get(f'{binary_field}_filename')
                    
                    if not filename:
                        for key in [f'default_{filename_field}', filename_field, f'{binary_field}_name']:
                            filename = self.env.context.get(key)
                            if filename:
                                break
                    
                    if not filename:
                        default_names = {
                            'technical_plan_file': 'plan_technique.pdf',
                            'cost_estimate_file': 'devis.pdf',
                            'feasibility_report_file': 'rapport_faisabilite.pdf',
                            'technical_transmission_note_file': 'note_transmission_technique.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename
    
    @api.model
    def create(self, vals):
        self._capture_filenames(vals)
        return super().create(vals)
    
    def write(self, vals):
        self._capture_filenames(vals)
        result = super().write(vals)
        
        # Synchronisation avec la demande de financement
        requests_to_update = {}
        for record in self:
            if record.request_id and (record.technical_evaluation or record.avis_technique):
                requests_to_update[record.request_id.id] = {
                    'technical_evaluation': record.technical_evaluation,
                    'avis_technique': record.avis_technique
                }
        
        for request_id, update_vals in requests_to_update.items():
            self.env['infrastructure.financing.request'].browse(request_id).write(update_vals)
        
        return result
    
    @api.constrains('technical_plan_file', 'cost_estimate_file', 'feasibility_report_file', 'technical_transmission_note_file', 'technical_evaluation', 'avis_technique')
    def _validate_technical_fields(self):
        """Validation lors de l'enregistrement"""
        for record in self:
            if record.request_id:  # Seulement si lié à une demande
                missing_items = []
                
                # Vérifier les documents techniques
                if not record.technical_plan_file:
                    missing_items.append("Plan technique")
                if not record.cost_estimate_file:
                    missing_items.append("Devis")
                if not record.feasibility_report_file:
                    missing_items.append("Rapport de faisabilité")
                if not record.technical_transmission_note_file:
                    missing_items.append("Note de transmission technique")
                
                # Vérifier les champs d'évaluation
                if not record.technical_evaluation:
                    missing_items.append("Évaluation technique")
                if not record.avis_technique:
                    missing_items.append("Avis technique")
                
                if missing_items:
                    raise ValidationError(_("\u00c9léments manquants :\n- %s") % "\n- ".join(missing_items))
    
