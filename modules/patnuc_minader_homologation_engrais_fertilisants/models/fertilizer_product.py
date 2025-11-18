from odoo import models, fields, api, _

class FertilizerProduct(models.Model):
    _name = 'fertilizer.product'
    _description = 'Produit engrais/fertilisant'
    
    name = fields.Char(string='Nom commercial', required=True)
    technical_name = fields.Char(string='Nom technique')
    manufacturer_id = fields.Many2one('res.partner', string='Fabricant')
    country_of_origin = fields.Many2one('res.country', string='Pays d\'origine')
    composition = fields.Text(string='Composition chimique')
    target_crops = fields.Text(string='Cultures cibles')
    usage_instructions = fields.Text(string='Instructions d\'utilisation')
    safety_measures = fields.Text(string='Mesures de sécurité')
    storage_conditions = fields.Text(string='Conditions de stockage')
    image = fields.Binary(string='Image du produit')
    image_filename = fields.Char(string='Nom du fichier image')
    
    homologation_ids = fields.One2many('fertilizer.homologation', 'product_id', string='Demandes d\'homologation')
    active = fields.Boolean(string='Actif', default=True)
    
    _sql_constraints = [
        ('name_manufacturer_uniq', 'unique(name, manufacturer_id)', 'Un produit avec ce nom existe déjà pour ce fabricant!'),
    ]
    
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
            'image': 'image_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if getattr(self, binary_field):
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        binary_fields = {
            'image': 'image_filename',
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
                            'image': 'image_produit.jpg',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.jpg')
                    
                    vals[filename_field] = filename

    @api.model
    def create(self, vals):
        self._capture_filenames(vals)
        return super(FertilizerProduct, self).create(vals)
    
    def write(self, vals):
        self._capture_filenames(vals)
        return super(FertilizerProduct, self).write(vals)