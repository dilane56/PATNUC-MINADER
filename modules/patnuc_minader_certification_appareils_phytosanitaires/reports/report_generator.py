from odoo import models, fields, api
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

class PhytosanitaryReportGenerator(models.Model):
    _name = 'phytosanitary.report.generator'
    _description = 'Générateur de Rapports Phytosanitaires'
    
    name = fields.Char('Nom du rapport', required=True)
    report_type = fields.Selection([
        ('performance', 'Rapport de Performance'),
        ('statistics', 'Statistiques'),
        ('compliance', 'Rapport de Conformité'),
        ('trends', 'Analyse des Tendances'),
    ], required=True)
    
    date_from = fields.Date('Date de début', required=True)
    date_to = fields.Date('Date de fin', required=True)
    
    partner_ids = fields.Many2many('res.partner', string='Demandeurs')
    equipment_type = fields.Selection([
        ('pulverisateur', 'Pulvérisateur'),
        ('atomiseur', 'Atomiseur'),
        ('nebuliseur', 'Nébuliseur'),
    ], string='Type d\'appareil')
    
    report_data = fields.Binary('Données du rapport')
    report_filename = fields.Char('Nom du fichier')
    
    def generate_report(self):
        """Générer le rapport selon le type sélectionné"""
        if self.report_type == 'performance':
            return self._generate_performance_report()
        elif self.report_type == 'statistics':
            return self._generate_statistics_report()
        elif self.report_type == 'compliance':
            return self._generate_compliance_report()
        elif self.report_type == 'trends':
            return self._generate_trends_report()
    
    def _generate_performance_report(self):
        """Générer rapport de performance"""
        # Récupération des données
        domain = [
            ('submission_date', '>=', self.date_from),
            ('submission_date', '<=', self.date_to),
        ]
        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        requests = self.env['phytosanitary.certification.request'].search(domain)
        
        # Analyse des performances
        data = {
            'total_requests': len(requests),
            'approved': len(requests.filtered(lambda r: r.state == 'notified')),
            'rejected': len(requests.filtered(lambda r: r.state == 'rejected')),
            'pending': len(requests.filtered(lambda r: r.state not in ['notified', 'rejected'])),
            'avg_processing_time': self._calculate_avg_processing_time(requests),
        }
        
        # Génération du graphique
        chart = self._create_performance_chart(data)
        
        # Création du rapport PDF
        report_content = self._create_pdf_report('performance', data, chart)
        
        self.write({
            'report_data': base64.b64encode(report_content),
            'report_filename': f'rapport_performance_{datetime.now().strftime("%Y%m%d")}.pdf'
        })
    
    def _create_performance_chart(self, data):
        """Créer graphique de performance"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        categories = ['Approuvées', 'Rejetées', 'En cours']
        values = [data['approved'], data['rejected'], data['pending']]
        colors = ['green', 'red', 'orange']
        
        ax.bar(categories, values, color=colors)
        ax.set_title('Répartition des Demandes de Certification')
        ax.set_ylabel('Nombre de demandes')
        
        # Convertir en base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_b64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_b64
    
    def _calculate_avg_processing_time(self, requests):
        """Calculer le temps moyen de traitement"""
        completed_requests = requests.filtered(lambda r: r.actual_completion_date and r.submission_date)
        
        if not completed_requests:
            return 0
        
        total_days = sum([
            (req.actual_completion_date - req.submission_date.date()).days 
            for req in completed_requests
        ])
        
        return total_days / len(completed_requests)