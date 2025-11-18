# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class PhytosanitaryEquipment(models.Model):
    _name = 'phytosanitary.equipment'
    _description = 'Appareil de Traitement Phytosanitaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nom de l\'appareil', required=True)
    brand = fields.Char('Marque', tracking=True)
    model = fields.Char('Modèle', tracking=True)
    equipment_type = fields.Selection([
        ('pulverisateur', 'Pulvérisateur'),
        ('atomiseur', 'Atomiseur'),
        ('nebuliseur', 'Nébuliseur'),
        ('autre', 'Autre')
    ], string='Type', required=True, tracking=True)
    
    # Spécifications techniques
    capacity = fields.Float('Capacité (L)', tracking=True)
    pressure_max = fields.Float('Pression maximale (bar)', tracking=True)
    flow_rate = fields.Float('Débit (L/min)', tracking=True)
    power_source = fields.Selection([
        ('manual', 'Manuel'),
        ('electric', 'Électrique'),
        ('gasoline', 'Essence'),
        ('battery', 'Batterie')
    ], string='Source d\'énergie', tracking=True)
    
    # Documents techniques
    technical_sheet = fields.Binary('Fiche technique', tracking=True)
    technical_sheet_filename = fields.Char('Nom du fichier', tracking=True)
    user_manual = fields.Binary('Manuel d\'utilisation', tracking=True)
    user_manual_filename = fields.Char('Nom du fichier', tracking=True)
    safety_datasheet = fields.Binary('Fiche de sécurité', tracking=True)
    safety_datasheet_filename = fields.Char('Nom du fichier', tracking=True)
    
    # Informations fabricant
    manufacturer_id = fields.Many2one('res.partner', string='Fabricant', tracking=True)
    country_origin = fields.Many2one('res.country', string='Pays d\'origine', tracking=True)
    manufacturing_date = fields.Date('Date de fabrication', tracking=True)
    
    # Certifications existantes
    foreign_certifications = fields.Text('Certifications étrangères', tracking=True)
    compliance_certificate = fields.Binary('Certificat de conformité', tracking=True)
    compliance_certificate_filename = fields.Char('Nom du fichier', tracking=True)
    
    # Historique des demandes
    certification_request_ids = fields.One2many('phytosanitary.certification.request', 
                                                'equipment_id', string='Demandes de certification', tracking=True)
    
    def _get_equipment_types(self):
        """Méthode extensible pour les types d'équipements"""
        return [
            ('pulverisateur', 'Pulvérisateur'),
            ('atomiseur', 'Atomiseur'),
            ('nebuliseur', 'Nébuliseur'),
            ('diffuseur', 'Diffuseur'),  # Nouveau type
            ('injecteur', 'Injecteur'),  # Nouveau type
            ('autre', 'Autre')
        ]

    equipment_type = fields.Selection(_get_equipment_types, string='Type', required=True, tracking=True)
    
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
            'technical_sheet': 'technical_sheet_filename',
            'user_manual': 'user_manual_filename',
            'safety_datasheet': 'safety_datasheet_filename',
            'compliance_certificate': 'compliance_certificate_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if getattr(self, binary_field):
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        binary_fields = {
            'technical_sheet': 'technical_sheet_filename',
            'user_manual': 'user_manual_filename',
            'safety_datasheet': 'safety_datasheet_filename',
            'compliance_certificate': 'compliance_certificate_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field]:
                if filename_field not in vals or not vals[filename_field]:
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
                            'technical_sheet': 'fiche_technique.pdf',
                            'user_manual': 'manuel_utilisation.pdf',
                            'safety_datasheet': 'fiche_securite.pdf',
                            'compliance_certificate': 'certificat_conformite.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename

    @api.model
    def create(self, vals):
        self._capture_filenames(vals)
        return super(PhytosanitaryEquipment, self).create(vals)
    
    def write(self, vals):
        self._capture_filenames(vals)
        result = super(PhytosanitaryEquipment, self).write(vals)
        
        # Après l'écriture, forcer la mise à jour des noms de fichiers depuis les attachments
        binary_fields = {
            'technical_sheet': 'technical_sheet_filename',
            'user_manual': 'user_manual_filename',
            'safety_datasheet': 'safety_datasheet_filename',
            'compliance_certificate': 'compliance_certificate_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if binary_field in vals and vals[binary_field]:
                # Toujours essayer de récupérer le nom depuis les attachments
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return result

    def action_view_certifications(self):
        """Afficher les certifications de l'appareil"""
        return {
            'name': 'Certifications',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'phytosanitary.certification.request',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id}
        }