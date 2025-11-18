# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FieldTest(models.Model):
    _name = 'field.test'
    _description = 'Tests en champ des engrais'
    _sql_constraints = [
        ('unique_homologation', 'unique(homologation_id)', 'Une demande d\'homologation ne peut avoir qu\'un seul test en champ.')
    ]
    
    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    #reference hom_init_eng
    homologation_id = fields.Many2one('fertilizer.homologation', string='Demande d\'homologation', required=False, ondelete='cascade')
    #reference hom_mod 
    mod_homologation_id = fields.Many2one('fertilizer.mod.homologation', 
                                          string='Demande de Modification', 
                                          required=False, 
                                          ondelete='cascade')
    product_id = fields.Many2one('fertilizer.product', string='Produit', related='homologation_id.product_id', store=True)
    start_date = fields.Date(string='Date de Test', default=fields.Date.today)
    location_ids = fields.Many2many('field.test.location', string='Sites de test')
    responsible_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    
    # Paramètres de test
    # test_crop = fields.Char(string='Culture testée')
    # test_methodology = fields.Text(string='Méthodologie de test')
    # application_rate = fields.Float(string='Dose d\'application (kg/ha)')
    # application_frequency = fields.Integer(string='Fréquence d\'application')
    
    # Résultats
    # yield_increase = fields.Float(string='Augmentation du rendement (%)')
    # quality_improvement = fields.Text(string='Amélioration de la qualité')
    # soil_impact = fields.Text(string='Impact sur le sol')
    # plant_health = fields.Text(string='Santé des plantes')
    # observations = fields.Text(string='Observations')
    
    # Documents
    # test_protocol_file = fields.Binary(string='Protocole de test')
    # test_protocol_filename = fields.Char(string='Nom du fichier')
    test_results_file = fields.Binary(string='Rapport des test en champs')
    test_results_filename = fields.Char(string='Nom du fichier')
    # test_photos = fields.Binary(string='Photos du test')
    # test_photos_filename = fields.Char(string='Nom du fichier')
    agronomic_test_report = fields.Binary(string='Rapport des tests agronomiques')
    agronomic_test_report_filename = fields.Char(string='Nom du fichier')
    
    # Conclusion
    # agronomic_efficiency = fields.Boolean(string='Efficacité agronomique démontrée')
    # test_conclusion = fields.Text(string='Conclusion')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
    ], string='État', default='draft')
    
    def action_start_test(self):
        for record in self:
            record.state = 'in_progress'
    
    def _validate_required_fields(self):
        """Validation des champs requis pour finaliser le test"""
        missing_items = []

        if not self.agronomic_test_report:
            missing_items.append("Rapport de test agronomique")

        if not self.test_results_file:
            missing_items.append("resultat de test")

        if missing_items:
            raise ValidationError(_("Éléments manquants pour finaliser le test :\n- %s") % "\n- ".join(missing_items))
        
        return True
    
    def action_complete_test(self):
        for record in self:
            record._validate_required_fields()
            record.state = 'completed'
            # Mettre à jour le rapport dans la demande d'homologation
            record.homologation_id.field_test_report = record.test_results_file
            record.homologation_id.field_agronomic_test_report =record.agronomic_test_report
    
    def export_test_report(self):
        # Fonction pour générer un rapport de test (à implémenter)
        return None
    
    @api.constrains()
    def _validate_field_test_fields(self):
        """Validation lors de l'enregistrement"""
        for record in self:
            if record.homologation_id:  # Seulement si lié à une demande
                missing_items = []
                
                # Vérifier les champs requis
                if not record.agronomic_test_report:
                    missing_items.append("Rapport de test agronomique")
                if not record.test_results_file:
                    missing_items.append("Resultat de test")
                
                if missing_items:
                    raise ValidationError(_("Éléments manquants :\n- %s") % "\n- ".join(missing_items))
    

    
    # (Q) Méthodes pour gérer les noms de fichiers
    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        binary_fields = {
            'test_protocol_file': 'test_protocol_filename',
            'test_results_file': 'test_results_filename',
            'test_photos': 'test_photos_filename',
            'agronomic_test_report': 'agronomic_test_report_filename',
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
                            'test_protocol_file': 'protocole_test.pdf',
                            'test_results_file': 'resultats_test.pdf',
                            'test_photos': 'photos_test.pdf',
                            'agronomic_test_report': 'rapport_test_agronomique.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('field.test') or _('New')
        self._capture_filenames(vals)
        result = super(FieldTest, self).create(vals)
        # Mettre à jour la relation inverse
        if result.homologation_id:
            result.homologation_id.field_test_id = result.id
        return result
    
    def write(self, vals):
        self._capture_filenames(vals)
        return super(FieldTest, self).write(vals)

class FieldTestLocation(models.Model):
    _name = 'field.test.location'
    _description = 'Sites de test en champ'
    
    name = fields.Char(string='Nom du site', required=True)
    region = fields.Selection([
        ('centre', 'Centre'),
        ('sud', 'Sud'),
        ('littoral', 'Littoral'),
        ('ouest', 'Ouest'),
        ('sud_ouest', 'Sud-Ouest'),
        ('nord_ouest', 'Nord-Ouest'),
        ('adamaoua', 'Adamaoua'),
        ('nord', 'Nord'),
        ('est', 'Est'),
        ('extreme_nord', 'Extrême-Nord'),
    ], string='Région')
    soil_type = fields.Char(string='Type de sol')
    climate_zone = fields.Char(string='Zone climatique')
    coordinates = fields.Char(string='Coordonnées GPS')
    description = fields.Text(string='Description')