from odoo import models, fields, api

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    is_phytosanitary_document = fields.Boolean('Document Phytosanitaire')
    document_id = fields.Many2one('phytosanitary.document', 'Document Phytosanitaire')