import qrcode
import io
import base64
from odoo import models, api

class QRCodeGenerator(models.AbstractModel):
    _name = 'certification.qr.generator'
    _description = 'Générateur de QR Code'
    
    @api.model
    def generate_qr_code(self, data, size=10, border=4):
        """Génère un QR code à partir des données fournies"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.read())