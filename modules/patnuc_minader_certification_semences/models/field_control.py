from odoo import models, fields, api
import base64
from odoo.exceptions import ValidationError

class FieldControl(models.Model):
    _name = 'certification.field.control'
    _description = 'Contrôle Terrain'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Référence', compute='_compute_name', store=True)
    request_id = fields.Many2one('certification.request', string='Demande', required=True)
    
    # Lieux
    lieu_saisi = fields.Char(string="Lieu saisi")
    lieu_prelevement = fields.Char(string="Lieu de prélèvement")
    
    # Planification
    scheduled_date = fields.Date('Date prévue', required=True)
    actual_date = fields.Date('Date réelle')
    inspector_id = fields.Many2one('res.users', string='Inspecteur', required=True)
    
    # Résultats du contrôle et état
    state = fields.Selection([
        ('scheduled', 'Planifié'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='scheduled', tracking=True)
    
    # Observations et recommandations
    variety_compliance = fields.Boolean('Conformité variétale')
    surface_compliance = fields.Boolean('Conformité superficie')
    cultivation_practices = fields.Boolean('Pratiques culturales conformes')
    
    observations = fields.Text('Observations générales')
    recommendations = fields.Text('Recommandations')
    
    # Échantillons et localisation
    samples_taken = fields.Boolean('Échantillons prélevés')
    sample_quantity = fields.Float('Quantité échantillon (kg)')
    sample_location = fields.Text('Localisation des prélèvements')
    
    # Documents et photos
    control_report = fields.Binary('Rapport de contrôle', required=True)
    control_report_filename = fields.Char('Nom du rapport de contrôle')
    photos = fields.Binary('Photos du site', required=True)
    photos_filename = fields.Char('Nom des photos')
    
    # Résultat du contrôle
    result = fields.Selection([
        ('compliant', 'Conforme'),
        ('non_compliant', 'Non conforme'),
        ('conditional', 'Conforme sous conditions')
    ], string='Résultat')
    
    @api.depends('request_id', 'scheduled_date')
    def _compute_name(self):
        """Méthode pour calculer le nom du contrôle"""
        for record in self:
            record.name = f"Contrôle {record.request_id.name} - {record.scheduled_date}"
    
    @api.constrains('lieu_saisi', 'lieu_prelevement')
    def _check_lieu_prelevement(self):
        """Méthode pour vérifier que le lieu saisi correspond au lieu de prélèvement"""
        for record in self:
            if record.lieu_saisi and record.lieu_prelevement and record.lieu_saisi != record.lieu_prelevement:
                raise ValidationError("Le lieu saisi doit correspondre au lieu de prélèvement.")
    
    # def action_complete(self):
    #     self.write({
    #         'state': 'completed',
    #         'actual_date': fields.Date.today()
    #     })
    #     if self.samples_taken:
    #         self.request_id.action_start_laboratory_analysis()
    #     else:
    #         self.request_id.write({'state': 'technical_review'})
    
    def action_validate(self):
        """Méthode pour valider le contrôle"""
        for rec in self:
            rec.state = 'done'
            if rec.request_id:
                rec.request_id.write({'state': 'laboratory_analysis'})

    def _update_filename_from_attachment(self, binary_field, filename_field):
        """Méthode utilitaire pour récupérer le nom de fichier depuis les attachments"""
        if self.id:
            # Rechercher l'attachment le plus récent pour ce champ
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('res_field', '=', binary_field)
            ], order='id desc', limit=1)
            
            if attachment and attachment.name:
                # Mettre à jour le nom de fichier directement sans déclencher write à nouveau
                self.env.cr.execute(
                    f"UPDATE {self._table} SET {filename_field} = %s WHERE id = %s",
                    (attachment.name, self.id)
                )
                # Invalider le cache pour ce champ
                self.invalidate_cache([filename_field])
                return attachment.name
        return None
    
    def action_update_filenames(self):
        """Action pour forcer la mise à jour des noms de fichiers"""
        # Mapping des champs Binary vers leurs champs filename correspondants
        binary_fields = {
            'control_report': 'control_report_filename',
            'photos': 'photos_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            # Si un fichier est uploadé
            if getattr(self, binary_field):
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def create(self, vals):
        """Méthode pour créer un contrôle"""
        # Capturer les noms de fichiers depuis le contexte lors de la création
        self._capture_filenames(vals)
        return super(FieldControl, self).create(vals)
    
    def write(self, vals):
        """Méthode pour écrire un contrôle"""
        # Capturer les noms de fichiers depuis le contexte lors de la modification
        self._capture_filenames(vals)
        result = super(FieldControl, self).write(vals)
        
        # Après l'écriture, essayer de récupérer les noms de fichiers depuis les attachments
        # Mapping des champs Binary vers leurs champs filename correspondants
        binary_fields = {
            'control_report': 'control_report_filename',
            'photos': 'photos_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            # Si un fichier est uploadé
            if binary_field in vals and vals[binary_field]:
                # Si un fichier a été uploadé, essayer de récupérer son nom
                if not vals.get(filename_field):
                    self._update_filename_from_attachment(binary_field, filename_field)
        
        return result
    
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        # Mapping des champs Binary vers leurs champs filename correspondants
        binary_fields = {
            'control_report': 'control_report_filename',
            'photos': 'photos_filename',
        }
        
        # Vérifier chaque champ Binary pour capturer le nom de fichier
        for binary_field, filename_field in binary_fields.items():
            # Si un fichier est uploadé
            if binary_field in vals and vals[binary_field]:
                # Vérifier si le nom de fichier n'est pas déjà fourni
                if filename_field not in vals or not vals[filename_field]:
                    # Essayer plusieurs méthodes pour récupérer le nom
                    filename = None
                    
                    # 1. Depuis le contexte direct
                    filename = self.env.context.get(f'{binary_field}_filename')
                    
                    # 2. Depuis le contexte avec différentes clés possibles
                    if not filename:
                        for key in [f'default_{filename_field}', filename_field, f'{binary_field}_name']:
                            filename = self.env.context.get(key)
                            if filename:
                                break
                    
                    # 3. Depuis les paramètres de la requête HTTP si disponible
                    if not filename and hasattr(self.env, 'request') and self.env.request:
                        request_files = getattr(self.env.request, 'httprequest', None)
                        if request_files and hasattr(request_files, 'files'):
                            for file_key, file_obj in request_files.files.items():
                                if binary_field in file_key and hasattr(file_obj, 'filename'):
                                    filename = file_obj.filename
                                    break
                    
                    # 4. Si toujours pas de nom, utiliser un nom par défaut descriptif
                    if not filename:
                        default_names = {
                            'control_report': 'rapport_controle.pdf',
                            'photos': 'photos_site.jpg',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename