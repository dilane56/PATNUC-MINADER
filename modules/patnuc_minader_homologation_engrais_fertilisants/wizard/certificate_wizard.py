# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FertilizerCertificateWizard(models.TransientModel):
    _name = 'fertilizer.certificate.wizard'
    _description = 'Assistant pour signer le certificat d\'homologation'
    
    homologation_id = fields.Many2one('fertilizer.homologation', string='Demande d\'homologation', required=True)
    certificate_signature = fields.Binary(string='Signature du certificat', required=True)
    certificate_signature_filename = fields.Char(string='Nom du fichier')
    
    def action_sign_certificate(self):
        """Signer le certificat et finaliser la génération"""
        if not self.certificate_signature:
            raise ValidationError(_("Vous devez uploader une signature pour le certificat."))
        
        # Enregistrer la signature dans la demande d'homologation
        self.homologation_id.write({
            'certificate_signature': self.certificate_signature,
            'certificate_signature_filename': self.certificate_signature_filename,
            'homologation_certificate': self._generate_certificate_pdf(),
        })
        
        self.homologation_id.message_post(body=_("Le certificat d'homologation a été signé et finalisé."))
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _generate_certificate_pdf(self):
        """Générer le PDF du certificat (à implémenter selon les besoins)"""
        # Cette méthode devrait générer un PDF du certificat avec la signature
        # Pour l'instant, on retourne la signature comme placeholder
        return self.certificate_signature