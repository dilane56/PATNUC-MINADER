from odoo import http, tools
from odoo.http import request
import json

class PhytosanitaryAPI(http.Controller):
    
    @http.route('/api/phytosanitary/requests', type='http', auth='user', methods=['GET'])
    def get_certification_requests(self, **kwargs):
        """API pour récupérer les demandes de certification"""
        
        domain = []
        if kwargs.get('state'):
            domain.append(('state', '=', kwargs['state']))
        if kwargs.get('partner_id'):
            domain.append(('partner_id', '=', int(kwargs['partner_id'])))
            
        requests = request.env['phytosanitary.certification.request'].search(domain)
        
        data = []
        for cert_request in requests:
            data.append({
                'id': cert_request.id,
                'name': cert_request.name,
                'partner_name': cert_request.partner_id.name,
                'equipment_name': cert_request.equipment_id.name,
                'state': cert_request.state,
                'submission_date': cert_request.submission_date.isoformat() if cert_request.submission_date else None,
                'certificate_number': cert_request.certificate_number,
            })
        
        return request.make_response(
            json.dumps(data, default=tools.date_utils.json_default),
            headers=[('Content-Type', 'application/json')]
        )
    
    @http.route('/api/phytosanitary/request/<int:request_id>', type='http', auth='user', methods=['GET'])
    def get_certification_request_detail(self, request_id):
        """API pour récupérer le détail d'une demande"""
        
        cert_request = request.env['phytosanitary.certification.request'].browse(request_id)
        
        if not cert_request.exists():
            return request.make_response(
                json.dumps({'error': 'Request not found'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )
        
        data = {
            'id': cert_request.id,
            'name': cert_request.name,
            'state': cert_request.state,
            'partner': {
                'id': cert_request.partner_id.id,
                'name': cert_request.partner_id.name,
                'email': cert_request.partner_id.email,
            },
            'equipment': {
                'id': cert_request.equipment_id.id,
                'name': cert_request.equipment_id.name,
                'brand': cert_request.equipment_id.brand,
                'model': cert_request.equipment_id.model,
            },
            'documents': [
                {
                    'type': doc.document_type,
                    'name': doc.name,
                    'is_valid': doc.is_valid,
                }
                for doc in cert_request.document_ids
            ]
        }
        
        return request.make_response(
            json.dumps(data, default=tools.date_utils.json_default),
            headers=[('Content-Type', 'application/json')]
        )