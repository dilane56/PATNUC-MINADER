from odoo import models, fields, api
class FieldControlWizard(models.TransientModel):
    _name = 'certification.field.control.wizard'
    _description = 'Assistant de contrôle terrain'
    
    request_id = fields.Many2one('certification.request', string='Demande')
    inspector_id = fields.Many2one('res.users', string='Inspecteur', required=True)
    scheduled_date = fields.Date('Date prévue', required=True, default=fields.Date.today)
    
    def action_schedule_control(self):
        """Planifier le contrôle terrain"""
        self.env['certification.field.control'].create({
            'request_id': self.request_id.id,
            'inspector_id': self.inspector_id.id,
            'scheduled_date': self.scheduled_date,
            'state': 'scheduled'
        })
        
        self.request_id.write({'state': 'field_control'})
        
        return {'type': 'ir.actions.act_window_close'}