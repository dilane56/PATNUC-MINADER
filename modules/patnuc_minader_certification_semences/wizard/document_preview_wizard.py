from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DocumentPreviewWizard(models.TransientModel):
    _name = 'document.preview.wizard'
    _description = 'Aperçu du document PDF'

    name = fields.Char("Nom du fichier")
    pdf_data = fields.Binary("Fichier PDF")

    def action_open_pdf(self):
        """Ouvre le PDF directement dans la fenêtre du navigateur."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=pdf_data&filename_field=name&download=false',
            'target': 'new',
        }
