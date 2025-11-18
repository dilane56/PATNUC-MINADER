
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class AnalysisPrelevementLot(models.Model):

    _name = 'prelevement.lot.certification'
    _description = 'Analyse des échantillons des lots'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Référence', compute='_compute_name', store=True)
    request_id = fields.Many2one('certification.request', string='Demande', required=False)
    #reference de l'analyse laboratoire
    analyse_id = fields.Many2one('certification.laboratory.analysis', string='Analyse Laboratoire', 
                                   required=True)
    
    #reference du lot concerné 
    lot_id = fields.Many2one("certification.parcelle.lot", string="Lot", required=True)

    # Tests réalisés
    germination_test = fields.Boolean('Test de germination')
    germination_rate = fields.Float('Taux de germination (%)')
    
    humidity_test = fields.Boolean('Test d\'humidité')
    humidity_rate = fields.Float('Taux d\'humidité (%)')
    
    purity_test = fields.Boolean('Test de pureté')
    purity_rate = fields.Float('Taux de pureté (%)')
    
    varietal_purity = fields.Boolean('Pureté variétale')
    varietal_purity_rate = fields.Float('Taux pureté variétale (%)')
    
    # date analyse du lot 
    analysis_date = fields.Datetime('Date d\'analyse du lot', tracking=True, default=fields.Datetime.today().now())
    #rapports d'analyse du lot 
    lot_analysis_report= fields.Binary(string='rapport d\'analyse du lot', readonly=True)
    lot_analysis_report_filename = fields.Char(string='Nom du rapport', readonly=True)

    # agent d'analyse du lot responsable 
    analyste_lot_id = fields.Many2one('res.users', string='Analyste de l\'echantillon du lot',required=True, tracking=True)

    #sequence 
    sequence = fields.Integer(string="N°", default=0)
    
    # state 
    state = fields.Selection([
        ('draft','Planifiée'),
        ('in_progress','En cours'),
        ('done','Terminée'),
        ('cancel','Annulée')
    ], default='draft', tracking=True)

    #results 
    result = fields.Selection([
        ('compliant', 'Conforme'),
        ('non_compliant', 'Non conforme'),
    ], string='Résultat')

    #methode compute
    @api.depends('request_id', 'analysis_date')
    def _compute_name(self):
        for record in self:
            record.name = f"Analyse {record.request_id.name} - {record.analysis_date}"
    
    def action_start(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Le prélèvement doit être à l'état 'Brouillon' pour démarrer l'analyse.")
        self.write({'state': 'in_progress', 'analyste_lot_id': self.env.user.id, 'analysis_date': fields.Datetime.now()})

    def action_complete(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError("Le prélèvement doit être à l'état 'En cours' pour être marqué terminé.")
        if not self.result or not self.lot_analysis_report:
             raise UserError("Veuillez saisir le Résultat final et joindre le Rapport d'analyse du lot.")
             
        self.state = 'done'
        self.message_post(body=("Analyse du lot terminée. Résultat : %s") % dict(self._fields['result'].selection).get(self.result))

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})


    @api.model
    def create(self, vals):
        record = super().create(vals)
        return record

    def write(self, vals):
        res = super().write(vals)
        return res
    def unlink(self):
        for record in self:
            if record.analyse_id:
                raise UserError("Impossible de supprimer cette analyse du lot car l'analyse est deja en cours ")
        return super(AnalysisPrelevementLot, self).unlink()
