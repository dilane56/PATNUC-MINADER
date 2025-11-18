from odoo import models, fields, api
class Certificate(models.Model):
    _name = 'certification.certificate'
    _description = 'Certificat de Conformité'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # name = fields.Char('Numéro de certificat', required=True, copy=False)
    
    name = fields.Char('Numéro de certificat', required=True, copy=False, readonly=True,
                      default=lambda self: self.env['ir.sequence'].next_by_code('certification.certificate'))
    
    request_id = fields.Many2one('certification.request', string='Demande', required=True)
    operator_id = fields.Many2one('certification.operator', string='Opérateur', required=True)
    
    # Dates
    issue_date = fields.Date('Date d\'émission', required=True, default=fields.Date.today)
    validity_date = fields.Date('Date de validité')
    
    # Contenu du certificat
    seed_variety = fields.Selection('Variété certifiée', related='request_id.parcelle_variete')
    certified_quantity = fields.Float('Quantité certifiée (kg)')
    production_site = fields.Char('Site de production')
    
    # Signatures et validations
    technical_validator_id = fields.Many2one('res.users', string='Validateur technique')
    final_signatory_id = fields.Many2one('res.users', string='Signataire final')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('signed', 'Signé'),
        ('issued', 'Délivré'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # QR Code pour authentification
    qr_code = fields.Binary('QR Code', compute='_compute_qr_code', store=True)
    
    # Documents
    certificate_pdf = fields.Binary('Certificat PDF')
    
    @api.depends('name', 'issue_date', 'operator_id')
    def _compute_qr_code(self):
        import qrcode
        import io
        import base64
        
        for certificate in self:
            if certificate.name:
                # Données à encoder dans le QR Code
                qr_data = f"CERT:{certificate.name}|DATE:{certificate.issue_date}|OP:{certificate.operator_id.name}"
                
                # Génération du QR Code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                
                certificate.qr_code = base64.b64encode(buffer.getvalue())
    
    def action_validate(self):
        self.write({
            'state': 'validated',
            'technical_validator_id': self.env.user.id
        })
    
    def action_sign(self):
        self.write({
            'state': 'signed',
            'final_signatory_id': self.env.user.id
        })
    
    def action_issue(self):
        self.write({'state': 'issued'})
        self.request_id.write({'state': 'certificate_issued'})
        self._send_notification()
    
    def _send_notification(self):
        # Envoi de notification à l'opérateur
        template = self.env.ref('patnuc_minader_certification_semences.certificate_notification_template')
        if template:
            template.send_mail(self.id, force_send=True)