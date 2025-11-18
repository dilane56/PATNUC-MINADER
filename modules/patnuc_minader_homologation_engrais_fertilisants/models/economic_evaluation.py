from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EconomicEvaluation(models.Model):
    _name = 'economic.evaluation'
    _description = 'Évaluation économique des engrais'
    _sql_constraints = [
        ('unique_homologation', 'unique(homologation_id)', 'Une demande d\'homologation ne peut avoir qu\'une seule évaluation économique.')
    ]
    
    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    homologation_id = fields.Many2one('fertilizer.homologation', string='Demande d\'homologation', required=False)
    #reference hom_mod
    mod_homologation_id = fields.Many2one('fertilizer.mod.homologation', 
                                          string='Demande de Modification', 
                                          required=False, 
                                          ondelete='cascade')
    product_id = fields.Many2one('fertilizer.product', string='Produit', related='homologation_id.product_id', store=True)
    evaluation_date = fields.Date(string='Date d\'évaluation', default=fields.Date.today)
    responsible_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    
    # Données économiques
    # product_price = fields.Float(string='Prix du produit (FCFA/kg)')
    # application_cost = fields.Float(string='Coût d\'application (FCFA/ha)')
    # yield_increase_value = fields.Float(string='Valeur de l\'augmentation de rendement (FCFA/ha)')
    # net_benefit = fields.Float(string='Bénéfice net (FCFA/ha)', compute='_compute_net_benefit')
    # benefit_cost_ratio = fields.Float(string='Ratio bénéfice/coût', compute='_compute_benefit_cost_ratio')
    # payback_period = fields.Float(string='Période de retour sur investissement (années)')
    
    # Analyse
    economic_evalutation_report = fields.Binary(string='Rapport d\'évaluation économique', required=True)
    economic_evalutation_report_filename = fields.Char(string="Nom du fichier")
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('completed', 'Terminé'),
    ], string='État', default='draft')
    
    # @api.depends('yield_increase_value', 'product_price', 'application_cost')
    # def _compute_net_benefit(self):
    #     for record in self:
    #         record.net_benefit = record.yield_increase_value - (record.product_price + record.application_cost)
    
    # @api.depends('yield_increase_value', 'product_price', 'application_cost')
    # def _compute_benefit_cost_ratio(self):
    #     for record in self:
    #         total_cost = record.product_price + record.application_cost
    #         if total_cost > 0:
    #             record.benefit_cost_ratio = record.yield_increase_value / total_cost
    #         else:
    #             record.benefit_cost_ratio = 0
    
    def _validate_required_fields(self):
        """Validation des champs requis pour finaliser l'évaluation"""
        missing_items = []
        
        # if self.product_price is None or self.product_price <= 0:
        #     missing_items.append("Prix du produit")
        # if self.application_cost is None or self.application_cost <= 0:
        #     missing_items.append("Coût d'application")
        # if self.yield_increase_value is None or self.yield_increase_value <= 0:
        #     missing_items.append("Valeur de l'augmentation de rendement")
        # if self.payback_period is None:
        #     missing_items.append("Période de retour sur investissement")
        if not self.economic_evalutation_report:
            missing_items.append("Rapport d'évaluation économique")

        
        if missing_items:
            raise ValidationError(_("Éléments manquants pour finaliser l'évaluation :\n- %s") % "\n- ".join(missing_items))
        
        return True
    
    def action_complete_evaluation(self):
        for record in self:
            record._validate_required_fields()
            record.state = 'completed'
            # Mettre à jour le rapport dans la demande d'homologation
            record.homologation_id.economic_evaluation_report = record.economic_evalutation_report
    
    def export_evaluation_report(self):
        # Fonction pour générer un rapport d'évaluation (à implémenter)
        return None
    
    @api.constrains('economic_evalutation_report')
    def _validate_economic_evaluation_fields(self):
        """Validation lors de l'enregistrement"""
        for record in self:
            if record.homologation_id:  # Seulement si lié à une demande
                missing_items = []
                
                # Vérifier les champs requis
                # if record.product_price is None or record.product_price <= 0:
                #     missing_items.append("Prix du produit")
                # if record.application_cost is None or record.application_cost <= 0:
                #     missing_items.append("Coût d'application")
                # if record.yield_increase_value is None or record.yield_increase_value <= 0:
                #     missing_items.append("Valeur de l'augmentation de rendement")
                # if record.payback_period is None:
                #     missing_items.append("Période de retour sur investissement")
                if not record.economic_evalutation_report:
                    missing_items.append("Rapport d'évaluation économique")

                
                if missing_items:
                    raise ValidationError(_("Éléments manquants :\n- %s") % "\n- ".join(missing_items))
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('economic.evaluation') or _('New')
        result = super(EconomicEvaluation, self).create(vals)
        # Mettre à jour la relation inverse
        if result.homologation_id:
            result.homologation_id.economic_evaluation_id = result.id
        return result