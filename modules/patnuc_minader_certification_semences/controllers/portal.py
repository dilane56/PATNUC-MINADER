from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class CertificationPortal(CustomerPortal):
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'certification_count' in counters:
            # Compter les demandes de certification pour l'utilisateur connecté
            operator = request.env['certification.operator'].sudo().search([
                ('create_uid', '=', request.env.user.id)
            ], limit=1)
            if operator:
                values['certification_count'] = len(operator.certification_requests)
        return values
    
    @http.route(['/my/certifications'], type='http', auth="user", website=True)
    def my_certifications(self, **kwargs):
        """Page des certifications de l'utilisateur connecté"""
        operator = request.env['certification.operator'].sudo().search([
            ('create_uid', '=', request.env.user.id)
        ], limit=1)
        
        certifications = request.env['certification.request'].sudo().search([
            ('operator_id', '=', operator.id)
        ]) if operator else []
        
        values = {
            'certifications': certifications,
            'operator': operator,
            'page_name': 'certifications',
        }
        return request.render("patnuc_minader_certification_semences.portal_my_certifications", values)
    
    @http.route(['/my/certification/<int:cert_id>'], type='http', auth="user", website=True)
    def my_certification_detail(self, cert_id, **kwargs):
        """Détail d'une certification"""
        certification = request.env['certification.request'].sudo().browse(cert_id)
        
        # Vérifier que l'utilisateur a accès à cette certification
        if certification.operator_id.create_uid.id != request.env.user.id:
            return request.render("website.403")
        
        values = {
            'certification': certification,
            'page_name': 'certification_detail',
        }
        return request.render("patnuc_minader_certification_semences.portal_certification_detail", values)
    
    @http.route(['/certification/verify/<string:cert_number>'], type='http', auth="public", website=True)
    def verify_certificate(self, cert_number, **kwargs):
        """Vérification publique d'un certificat"""
        certificate = request.env['certification.certificate'].sudo().search([
            ('name', '=', cert_number),
            ('state', '=', 'issued')
        ], limit=1)
        
        values = {
            'certificate': certificate,
            'page_name': 'certificate_verification',
        }
        return request.render("patnuc_minader_certification_semences.certificate_verification", values)