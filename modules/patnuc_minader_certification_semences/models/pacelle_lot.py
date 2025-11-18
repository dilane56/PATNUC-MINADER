
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

class CertificationParcelleLot(models.Model):
    _name = "certification.parcelle.lot"
    _description = "Lot issu d'une parcelle"
    _order = "parcelle_id, name"

    name = fields.Char(string="Référence lot", required=True, copy=False,
                       default=lambda self: self.env['ir.sequence'].next_by_code('certification.parcelle.lot'))
    parcelle_id = fields.Many2one('certification.parcelle', string="Parcelle mère", required=True, ondelete='cascade')
    area = fields.Float(string="Superficie (ha)", required=True)
    sequence = fields.Integer(string="N°", default=0)
    state = fields.Selection(
        [('draft','En cours'),
          ('in_certification','Certifié'),
          ('cancel','Annulé')], default='draft')
    inspection_ids = fields.One2many( 'certification.inspection','lot_id',  string="Inspections" )
    request_id = fields.Many2one( 'certification.request',string="Demande de certification", ondelete='cascade')

    inspections_count = fields.Integer(string="Nombre d'inspections", compute='_compute_inspections_count', store=True)

    analysis_prelevement_ids = fields.One2many(
        'prelevement.lot.certification',
        'lot_id',
        string="Analyses de Prélèvement Associées"
    )

    @api.constrains('inspection_ids')
    def _check_minimum_inspections(self):
        for lot in self:
            # Ne déclenche pas d'erreur si aucune inspection encore planifiée
            if lot.inspection_ids and len(lot.inspection_ids) < 3:
                raise UserError(
                    f"Le lot {lot.name} doit avoir au moins 3 inspections avant validation."
                )

    @api.depends('inspection_ids')
    def _compute_inspections_count(self):
        for rec in self:
            rec.inspections_count = len(rec.inspection_ids)

    def action_mark_in_inspection(self):
        pass

    
    def action_close_and_return(self):
        return {
            'type': 'ir.actions.act_window_close'
        }

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._check_total_area()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._check_total_area()
        return res



    def unlink(self):
        for lot in self:
            if lot.inspection_ids:
                raise UserError("Impossible de supprimer ce lot car des inspections ont déjà été réalisées.")
        return super(CertificationParcelleLot, self).unlink()

    def _check_total_area(self):
        for lot in self:
            total_lots_area = sum(lot.parcelle_id.lot_ids.mapped("area"))
            parcelle_area = lot.parcelle_id.superficie

            # Cas dépassement
            if total_lots_area > parcelle_area:
                raise UserError(
                    f"La somme des superficies des lots ({total_lots_area} ha) dépasse "
                    f"la superficie de la parcelle ({parcelle_area} ha)."
                )

            # Mise à jour état de la parcelle
            lot.parcelle_id.update_lot_state()
    def action_certify_lot(self):
        """
        Passe le lot à l'état 'Certifié' si au moins une analyse de prélèvement 
        associée est déclarée 'compliant' au moment de l'appel.
        """
        self.ensure_one()
        
        if self.state == 'in_certification':
            raise UserError("Ce lot est déjà certifié.")

        # 1. Vérification de la conformité des analyses
        # Assurez-vous que le champ 'result' existe sur 'prelevement.lot.certification'
        compliant_analysis = self.analysis_prelevement_ids.filtered(
            lambda a: a.result == 'compliant' 
        )
        
        if compliant_analysis:
            # 2. Transition vers l'état 'in_certification'
            self.write({'state': 'in_certification'})
            # Optionnel: Mettre à jour la date de certification
            # self.write({'certification_date': fields.Date.today()})
        else:
            # 3. Lever une erreur si aucune analyse conforme n'est trouvée
            raise UserError(
                "Impossible de certifier ce lot. "
                "Le lot doit avoir au moins une analyse de prélèvement associée "
                "dont le résultat est 'Conforme' (compliant)."
            )
