from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class LaboratoryAnalysis(models.Model):
    _name = 'laboratory.analysis'
    _description = 'Analyse de laboratoire des engrais'
    _sql_constraints = [
        ('unique_homologation', 'unique(homologation_id)', 'Une demande d\'homologation ne peut avoir qu\'une seule analyse de laboratoire.')
    ]
    
    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    #reference hom_en_init
    homologation_id = fields.Many2one('fertilizer.homologation', string='Demande d\'homologation', required=False, ondelete='cascade')
    #reference hom_mod
    mod_homologation_id = fields.Many2one('fertilizer.mod.homologation', 
                                          string='Demande de Modification', 
                                          required=False, 
                                          ondelete='cascade')
    # === CARACTÉRISTIQUES PHYSICOCHIMIQUES ===
    aspect = fields.Selection([
        ('solide', 'Solide'),
        ('liquide', 'Liquide')
    ], string='Aspect')
    
    # Granulé par (sélection multiple)
    granule_broyage = fields.Boolean(string='Broyage')
    granule_compactage = fields.Boolean(string='Compactage')
    granule_agregation = fields.Boolean(string='Agrégation')
    granule_cristalisation = fields.Boolean(string='Cristallisation')
    granule_autres = fields.Char(string='Autres (à préciser)')
    
    couleur = fields.Char(string='Couleur')
    odeur = fields.Char(string='Odeur')
    masse_volumique = fields.Float(string='Masse Volumique (Kg/l)')
    densite_relative = fields.Float(string='Densité relative')
    temperature_cristalisation = fields.Float(string='Température de Cristallisation (°C)')
    temperature_fusion = fields.Float(string='Température de Fusion (°C)')
    temperature_ebullition = fields.Float(string='Température d\'Ébullition (°C)')
    solubilite_eau_20c = fields.Float(string='Solubilité eau à 20°C')
    ph = fields.Float(string='pH', digits=(3, 2))
    matiere_minerale_brut = fields.Float(string='Matière Minérale (%brut)')
    matiere_organique = fields.Float(string='Matière Organique (%)')
    compatible_pesticides = fields.Selection([
        ('oui', 'OUI'),
        ('non', 'NON')
    ], string='Compatible avec les pesticides')
    stabilite_entrepot = fields.Char(string='Stabilité entrepôt')
    pouvoir_corrosif = fields.Char(string='Pouvoir corrosif')
    tension_vapeur = fields.Float(string='Tension vapeur')
    taux_humidite = fields.Float(string='Taux d\'humidité (%)')
    
    # === COMPOSITION DE L'ENGRAIS ===
    teneur_co = fields.Float(string='Teneur en Monoxyde de carbone CO (%)')
    teneur_azote_n = fields.Float(string='Teneur en Azote N (%)')
    teneur_p2o5 = fields.Float(string='Teneur en pentoxyde de phosphore P2O5 (%)')
    inerte_ingredient = fields.Float(string='Inerte ingrédient (%)')
    
    # === TENEUR EN MÉTAUX LOURDS (ppm) ===
    arsenic_total = fields.Float(string='Arsenic total (ppm)')
    cadmium_total = fields.Float(string='Cadmium total (ppm)')
    chrome_total = fields.Float(string='Chrome total (ppm)')
    mercure_total = fields.Float(string='Mercure total (ppm)')
    nickel_total = fields.Float(string='Nickel total (ppm)')
    plomb = fields.Float(string='Plomb (ppm)')
    selenium_total = fields.Float(string='Sélénium total (ppm)')
    autres_metaux_lourds = fields.Text(string='Autres métaux lourds')
    
    # reference many
    product_id = fields.Many2one('fertilizer.product', string='Produit', related='homologation_id.product_id', store=True)
    analysis_date = fields.Date(string='Date d\'analyse', default=fields.Date.today)
    responsible_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    laboratory_id = fields.Many2one('res.partner', string='Laboratoire')
    
    # Documents
    chemical_analysis_report = fields.Binary(string='Rapport d\'analyse chimique')
    chemical_analysis_report_filename = fields.Char(string="Nom du fichier")
    microbiological_analysis_report = fields.Binary(string='Rapport d\'analyse microbiologique')
    microbiological_analysis_report_filename = fields.Char(string="Nom du fichier")
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
    ], string='État', default='draft')
    
    def action_start_analysis(self):
        for record in self:
            record.state = 'in_progress'
    
    def _validate_required_fields(self):
        """Validation des champs requis pour finaliser l'analyse"""
        missing_items = []
        

        
        # Vérifier les documents
        if not self.chemical_analysis_report:
            missing_items.append("Rapport d'analyse chimique")
        if not self.microbiological_analysis_report:
            missing_items.append("Rapport d'analyse microbiologique")
        

        
        if missing_items:
            raise ValidationError(_("Éléments manquants pour finaliser l'analyse :\n- %s") % "\n- ".join(missing_items))
        
        return True
    
    def action_complete_analysis(self):
        for record in self:
            record._validate_required_fields()
            record.state = 'completed'
            # Mettre à jour le rapport dans la demande d'homologation
            record.homologation_id.chemical_analysis_report = record.chemical_analysis_report
            record.homologation_id.microbiological_analysis_report = record.microbiological_analysis_report
            
    def export_chemical_report(self):
        # Fonction pour générer un rapport chimique (à implémenter)
        return None
    
    def export_microbiological_report(self):
        # Fonction pour générer un rapport microbiologique (à implémenter)
        return None
    
    @api.constrains( 'chemical_analysis_report', 'microbiological_analysis_report')
    def _validate_analysis_fields(self):
        """Validation lors de l'enregistrement"""
        for record in self:
            if record.homologation_id:  # Seulement si lié à une demande
                missing_items = []
                
                # Vérifier les documents
                if not record.chemical_analysis_report:
                    missing_items.append("Rapport d'analyse chimique")
                if not record.microbiological_analysis_report:
                    missing_items.append("Rapport d'analyse microbiologique")
                
                if missing_items:
                    raise ValidationError(_("Éléments manquants :\n- %s") % "\n- ".join(missing_items))
    
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
            'chemical_analysis_report': 'chemical_analysis_report_filename',
            'microbiological_analysis_report': 'microbiological_analysis_report_filename',
        }
        
        for binary_field, filename_field in binary_fields.items():
            if getattr(self, binary_field):
                self._update_filename_from_attachment(binary_field, filename_field)
        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _capture_filenames(self, vals):
        """Méthode pour capturer automatiquement les noms de fichiers"""
        binary_fields = {
            'chemical_analysis_report': 'chemical_analysis_report_filename',
            'microbiological_analysis_report': 'microbiological_analysis_report_filename',
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
                            'chemical_analysis_report': 'rapport_analyse_chimique.pdf',
                            'microbiological_analysis_report': 'rapport_analyse_microbiologique.pdf',
                        }
                        filename = default_names.get(binary_field, f'{binary_field}.pdf')
                    
                    vals[filename_field] = filename

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('laboratory.analysis') or _('New')
        self._capture_filenames(vals)
        result = super(LaboratoryAnalysis, self).create(vals)
        # Mettre à jour la relation inverse
        if result.homologation_id:
            result.homologation_id.laboratory_analysis_id = result.id
        return result
    
    def write(self, vals):
        self._capture_filenames(vals)
        return super(LaboratoryAnalysis, self).write(vals)