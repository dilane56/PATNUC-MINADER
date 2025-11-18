from odoo import models, fields, api
import base64

class CertificationTechnicalReview(models.Model):
    _name = 'certification.technical.review'
    _description = 'Examen Technique de Certification'
    
    request_id = fields.Many2one('certification.request', string='Demande de Certification', required=True, ondelete='cascade')
    reviewer_id = fields.Many2one('res.users', string='Réviseur Technique', required=True)
    review_date = fields.Date('Date de l\'examen', default=fields.Date.context_today)
    result = fields.Selection([
        ('conforme', 'Conforme'),
        ('non_conforme', 'Non conforme'),
        ('a_completer', 'À compléter')
    ], string='Résultat', required=True)
    review_notes = fields.Text('Notes de l\'examen')
    additional_observations = fields.Text('Observations complémentaires')
    attachment_ids = fields.Many2many('ir.attachment', string='Documents joints')
    reviewer_signature = fields.Binary('Signature du réviseur', required=True)
    reviewer_signature_filename = fields.Char('Nom du fichier de signature')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('done', 'Terminé')
    ], string='État', default='draft')
    validation_date = fields.Datetime('Date de validation')

    def action_validate(self):
        for rec in self:
            rec.state = 'done'
            if rec.request_id:
                rec.request_id.write({'state': 'technical_review'})

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
        binary_fields = {
            'reviewer_signature': 'reviewer_signature_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if getattr(self, binary_field):
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model
    def create(self, vals):
        # Capturer les noms de fichiers depuis le contexte lors de la création
        self._capture_filenames(vals)
        return super(CertificationTechnicalReview, self).create(vals)
    
    def write(self, vals):
        # Capturer les noms de fichiers depuis le contexte lors de la modification
        self._capture_filenames(vals)
        result = super(CertificationTechnicalReview, self).write(vals)
        
        # Après l'écriture, essayer de récupérer les noms de fichiers depuis les attachments
        binary_fields = {
            'reviewer_signature': 'reviewer_signature_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field]:
                # Si un fichier a été uploadé, essayer de récupérer son nom
                if not vals.get(filename_field):
                    self._update_filename_from_attachment(binary_field, filename_field)
        
        return result
    
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        # Mapping des champs Binary vers leurs champs filename correspondants
        binary_fields = {
            'reviewer_signature': 'reviewer_signature_filename',
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
                            'reviewer_signature': 'signature_reviseur.png',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename 