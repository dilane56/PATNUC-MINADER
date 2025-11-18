from odoo import models, fields

class LabellingLabel(models.Model):
    _name = 'labelling.label'
    _description = 'Étiquette de Semence Générée'
    _order = 'name'
    
    name = fields.Char('Code Étiquette', required=True)
    labelling_request_id = fields.Many2one('labelling.request', string='Demande d\'Étiquetage', required=True, ondelete='cascade')
    lot_id = fields.Many2one('certification.parcelle.lot', string='Lot', required=True)
    
    # Données de l'étiquette (copiées au moment de génération)
    espece = fields.Char('Espèce/Species')
    variete = fields.Char('Variété/Variety')
    lot_name = fields.Char('Lot N°')
    poids_lot = fields.Float('Poids du lot/Weight of lot (kg)')
    poids_net = fields.Float('Poids net/Net weight (kg)')
    lieu_production = fields.Char('Lieu de production/Place of production')
    annee_production = fields.Char('Année de production/Year of production')
    traitement_chimique = fields.Char('Traitement chimique/Chemical treatment')
    nom_producteur = fields.Char('Nom du producteur/Name of producer')
    code_inspecteur = fields.Char('Code de l\'Inspecteur/Inspector code')