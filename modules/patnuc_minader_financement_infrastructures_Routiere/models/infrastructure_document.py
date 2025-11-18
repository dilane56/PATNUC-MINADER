from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

#Modele pour les documents liés à une demande financement d'infrastructure (requis et générés)
class InfrastructureDocument(models.Model):

    #Informations de base sur le modèle
    _name = 'infrastructure.document'
    _description = 'Documents pour la demande de financement d’infrastructure'

    
    #Lien avec la demande de financement : -plusieurs documents peuvent être liés à une seule demande
    request_id = fields.Many2one(
        'infrastructure.financing.request',string='Demande de financement',

    )

    support_id = fields.Many2one(
    'infrastructure.technical.support',
    string='Appui technique lié'
    )

    #Type de document
    document_type = fields.Selection([
        
        # Documents requis
        ('official_request', "Lettre de demande officielle"),
        ('project_summary', "Note de présentation du projet"),
        ('location_plan', "Plan de situation"),
        ('communal_commitment', "Lettre d'approbation de la Mairie"),
        ('pv_validation_project', "Pv De Validation Du Commite de Maturation"),
        ('environmental_impact', "Évaluation de l’impact environnemental"),
        ('co_financing', "Preuve de cofinancement ou partenariat"),
        ('technical_doc', "Document technique"),
        ('technical_fasability_report', "rapport de faisabilité technique"),
        ('transmission_note', "Note de transmission"),

        # Documents générés 
        #('feasibility_report', "Rapport de faisabilité"),
        ('technical_plan', "Plans techniques"),
        ('cost_estimate', "Devis estimatif"),
        ('cotation', "Cotation"),
        # Document final
        ('notification_letter', "Lettre de notification"),
        ('final_decision', "Décision de financement")
    ], string='Type de document', required=True)


    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='État du document', default='draft')

  

    #infos sur le document/fichier
    name = fields.Char(string="Nom du document", required=True)
    file_data = fields.Binary('Fichier', required=True)
    file_name = fields.Char('Nom du fichier', compute='_compute_file_name', store=True)
    

    #Etat du document
    is_required = fields.Boolean('Obligatoire', default=False)
    is_provided = fields.Boolean('Fourni', default=False)
    

    #Metadonnées : trace qui a deposé le document et quand
    upload_date = fields.Datetime(string="Date d'import", default=fields.Datetime.now)
    uploaded_by = fields.Many2one('res.users', string='Téléchargé par', 
                                  default=lambda self: self.env.user)


    # (Q) Calcul automatique du nom du fichier basé sur le fichier uploadé
    @api.depends('file_data', 'name', 'document_type')
    def _compute_file_name(self):
        for record in self:
            if record.file_data:
                # Utiliser le nom du document ou un nom basé sur le type
                if record.name:
                    record.file_name = f"{record.name}.pdf"
                else:
                    doc_type_name = dict(record._fields['document_type'].selection).get(record.document_type, 'document')
                    record.file_name = f"{doc_type_name}_{record.id or 'new'}.pdf"
            else:
                record.file_name = False
    
    # cette methode est appelée lors de la création d'un document 
    # Marque comme obligatoire les documents requis et comme fourni si un document est joint
    @api.model
    def create(self, vals):
        # Si on crée un document depuis l'onglet One2many, Odoo doit injecter request_id.
        # Mais si ce n'est pas le cas → on récupère depuis le contexte.
        if not vals.get("request_id") and self.env.context.get("default_request_id"):
            vals["request_id"] = self.env.context["default_request_id"]

        # Rendre certains documents obligatoires
        if vals.get('document_type') in [
            'official_request', 'location_plan',
            'communal_commitment', 'pv_validation_project'
        ]:
            vals['is_required'] = True

        # Marquer comme fourni si un fichier est présent
        if vals.get('file_data'):
            vals['is_provided'] = True

        return super().create(vals)


    def action_submitted(self):
        """Mettre le document en brouillon"""
        self.state = 'submitted'


 