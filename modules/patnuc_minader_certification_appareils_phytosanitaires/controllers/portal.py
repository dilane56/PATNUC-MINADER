# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class PhytosanitaryPortal(CustomerPortal):
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'certification_count' in counters:
            certification_count = request.env['phytosanitary.certification.request'].search_count([
                ('partner_id', '=', request.env.user.partner_id.id)
            ])
            values['certification_count'] = certification_count
        return values
    
    @http.route(['/my/certifications', '/my/certifications/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_certifications(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        CertificationRequest = request.env['phytosanitary.certification.request']

        domain = [('partner_id', '=', partner.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Date de Soumission'), 'order': 'submission_date desc'},
            'name': {'label': _('Référence'), 'order': 'name'},
            'state': {'label': _('État'), 'order': 'state'},
        }
        
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        # Comptage total
        certification_count = CertificationRequest.search_count(domain)
        
        # Pagination
        pager = portal_pager(
            url="/my/certifications",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=certification_count,
            page=page,
            step=self._items_per_page
        )
        
        # Recherche avec pagination
        certifications = CertificationRequest.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'certifications': certifications,
            'page_name': 'certification',
            'pager': pager,
            'default_url': '/my/certifications',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render("phytosanitary_certification.portal_my_certifications", values)
    
    @http.route(['/my/certification/<int:cert_id>'], type='http', auth="user", website=True)
    def portal_certification_detail(self, cert_id, **kw):
        certification = request.env['phytosanitary.certification.request'].browse(cert_id)
        
        # Vérification d'accès
        if certification.partner_id != request.env.user.partner_id:
            return request.render("website.403")
        
        values = {
            'certification': certification,
            'page_name': 'certification_detail',
        }
        
        return request.render("phytosanitary_certification.portal_certification_detail", values)