from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class LaboratoryAnalysis(models.Model):
    _name = 'certification.laboratory.analysis'
    _description = 'Analyse Laboratoire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'analysis_date desc, name'
    
    name = fields.Char('Référence', compute='_compute_name', store=True)
    request_id = fields.Many2one('certification.request', string='Demande', required=True, tracking=True)
    
    # Relation avec les prélèvements des lots
    prelevement_lots = fields.One2many('prelevement.lot.certification', 'analyse_id', 
                                        string='Échantillonnage des lots', copy=True)
    
    # Laboratoire
    laboratory_id = fields.Many2one('certification.laboratory', string='Laboratoire', tracking=True)
    
    # Date d'analyse
    analysis_date = fields.Date('Date d\'analyse', default=fields.Date.today(), tracking=True)
    
    # Responsable laboratoire 
    analyst_id = fields.Many2one('res.users', string='Responsable laboratoire', tracking=True)
    
    # Workflow et Résultats
    state = fields.Selection([
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='pending', tracking=True)
    
    result = fields.Selection([
        ('compliant', 'Conforme'),
        ('non_compliant', 'Non conforme'),
        ('requires_additional_tests', 'Tests supplémentaires requis')
    ], string='Résultat global',tracking=True)
    
    # Documents
    analysis_report = fields.Binary('Rapport final d\'analyse')
    analysis_report_filename = fields.Char('Nom du rapport d\'analyse')
    technical_opinion = fields.Text('Avis technique', tracking=True)
    
    @api.depends('request_id', 'analysis_date')
    def _compute_name(self):
        for record in self:
            # Assurez-vous que request_id.name est disponible ou utilisez une référence par défaut
            request_name = record.request_id.name or 'N/A'
            date_str = record.analysis_date.strftime('%Y-%m-%d') if record.analysis_date else 'Inconnue'
            record.name = f"ANALYSE/{request_name}/{date_str}"

    @api.depends('prelevement_lots.result')
    def _compute_global_result(self):
        """ Détermine le résultat global en fonction des résultats des lots. """
        for analysis in self:
            if not analysis.prelevement_lots:
                analysis.result = False
                continue
            
            # Si au moins un lot est Non Conforme, l'analyse globale l'est.
            if any(lot.result == 'non_compliant' for lot in analysis.prelevement_lots):
                analysis.result = 'non_compliant'
            # Si tous les lots sont Conformes
            elif all(lot.result == 'compliant' for lot in analysis.prelevement_lots):
                analysis.result = 'compliant'
            # Sinon (s'il y a des tests supplémentaires requis, ou des états intermédiaires), on peut laisser vide ou ajouter une logique spécifique.
            else:
                analysis.result = 'requires_additional_tests'

    # --- Méthodes de Workflow ---

    def action_start_analysis(self):
        """ Passe l'analyse de 'pending' à 'in_progress'. """
        for rec in self:
            if rec.state != 'pending':
                raise UserError("L'analyse doit être en attente pour être démarrée.")
            rec.write({'state': 'in_progress'})

    def action_complete_analysis(self):
        """ Passe l'analyse de 'in_progress' à 'completed' après vérifications. """
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("L'analyse doit être en cours pour être terminée.")
            
            # 1. Vérification des lots (Doit être complet ou conforme/non-conforme)
            if not rec.prelevement_lots or any(not lot.result for lot in rec.prelevement_lots):
                 raise UserError("Veuillez vous assurer que tous les prélèvements de lots ont un résultat enregistré.")

            # 2. Vérification du rapport et de l'avis technique
            if not rec.analysis_report :
                raise UserError("Le Rapport final d'analyse est obligatoire pour terminer l'analyse.")
                
            rec.write({'state': 'completed'})
    
    def action_cancel(self) :
        for rec in self: 
            rec.write({'state': 'cancelled'})
    
    def action_validate(self):
        """ Passe l'analyse de 'completed' à 'validated'. """
        for rec in self:
            if rec.state != 'completed':
                raise UserError("L'analyse doit être au statut 'Terminé' pour être validée.")
        
            rec.write({'state': 'validated'})
            
            # Mise à jour de l'état de la demande de certification
            if rec.request_id:
                rec.request_id.write({'state': 'technical_review'})


    # --- Logique de gestion des noms de fichiers (Conservée) ---
    
    def _update_filename_from_attachment(self, binary_field, filename_field):
        """Méthode utilitaire pour récupérer le nom de fichier depuis les attachments"""
        if self.id:
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('res_field', '=', binary_field)
            ], order='id desc', limit=1)
            
            if attachment and attachment.name:
                self.env.cr.execute(
                    f"UPDATE {self._table} SET {filename_field} = %s WHERE id = %s",
                    (attachment.name, self.id)
                )
                self.invalidate_cache([filename_field])
                return attachment.name
        return None
    
    def action_update_filenames(self):
        """Action pour forcer la mise à jour des noms de fichiers"""
        binary_fields = {
            'analysis_report': 'analysis_report_filename',
        }
        
        for record in self:
            for binary_field, filename_field in binary_fields.items():
                if getattr(record, binary_field):
                    record._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def create(self, vals):
        self._capture_filenames(vals)
        return super(LaboratoryAnalysis, self).create(vals)
    
    def write(self, vals):
        self._capture_filenames(vals)
        result = super(LaboratoryAnalysis, self).write(vals)
        
        # Logique pour capturer le nom de fichier après le write si le binaire a été mis à jour
        binary_fields = {
            'analysis_report': 'analysis_report_filename',
        }
        
        for rec in self:
            for binary_field, filename_field in binary_fields.items():
                if binary_field in vals and vals[binary_field] and not vals.get(filename_field):
                    rec._update_filename_from_attachment(binary_field, filename_field)
        
        return result
    
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers lors des opérations ORM"""
        binary_fields = {
            'analysis_report': 'analysis_report_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field] and (filename_field not in vals or not vals[filename_field]):
                # Logique pour tenter de récupérer le nom depuis le contexte (comme dans votre code original)
                filename = self.env.context.get(f'{binary_field}_filename')
                if not filename:
                    filename = self.env.context.get(f'{binary_field}_name') # Clé alternative
                
                if not filename:
                    default_names = {'analysis_report': 'rapport_analyse_laboratoire.pdf'}
                    filename = default_names.get(binary_field, f'{binary_field}.pdf')
                
                vals[filename_field] = filename