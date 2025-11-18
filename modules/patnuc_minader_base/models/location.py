from odoo import models, fields

class MinaderRegion(models.Model):
    _name = "minader.region"
    _description = "Région administrative du Cameroun"
    _order = "name"

    name = fields.Char(string="Nom de la région", required=True)
    code = fields.Char(string="Code", required=True)
    departement_ids = fields.One2many('minader.departement', 'region_id', string="Départements")


class MinaderDepartement(models.Model):
    _name = "minader.departement"
    _description = "Département administratif du Cameroun"
    _order = "name"

    name = fields.Char(string="Nom du département", required=True)
    code = fields.Char(string="Code")
    region_id = fields.Many2one('minader.region', string="Région", required=True, ondelete='cascade')
    arrondissement_ids = fields.One2many('minader.arrondissement', 'departement_id', string="Arrondissements")


class MinaderArrondissement(models.Model):
    _name = "minader.arrondissement"
    _description = "Arrondissement administratif du Cameroun"
    _order = "name"

    name = fields.Char(string="Nom de l’arrondissement", required=True)
    code = fields.Char(string="Code")
    departement_id = fields.Many2one('minader.departement', string="Département", required=True, ondelete='cascade')
    region_id = fields.Many2one('minader.region', string="Région", related="departement_id.region_id", store=True)
