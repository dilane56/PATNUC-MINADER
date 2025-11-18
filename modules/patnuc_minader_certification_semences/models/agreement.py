from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class SeedOperatorAgreement(models.Model):
    """
    Modèle pour gérer les agréments des opérateurs semenciers
    Un agrément est obligatoire avant de pouvoir faire une demande de certification
    """
    _name = 'certification.agreement'
    _description = 'Agrément Opérateur Semencier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc'
    
    # Référence automatique de l'agrément
    name = fields.Char(
        string='Référence Agrément', 
        required=True, 
        copy=False, 
        default=lambda self: _('Nouveau'),
        tracking=True
    )
    
    # N° CEAS (Certificat d'Exercice d'Activité Semencière)
    ceas_number = fields.Char(
        string='N° CEAS',
        required=True,
        help="Numéro du Certificat d'Exercice d'Activité Semencière",
        tracking=True
    )
    
    # Dates importantes de l'agrément
    issue_date = fields.Date(
        string='Date de délivrance',
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date de délivrance de l'agrément"
    )
    
    expiry_date = fields.Date(
        string="Date d'expiration",
        required=True,
        tracking=True,
        help="Date d'expiration de l'agrément"
    )
    
    # Lien vers l'opérateur (référence de l'opérateur/producteur)
    operator_id = fields.Many2one('res.partner', string='Opérateur',required=True, tracking=True)
    # Fichier d'agrément uploadé depuis le frontend React
    agreement_file = fields.Binary(
        string='Fichier d\'agrément',
        required=True,
        help="Document d'agrément soumis par l'opérateur"
    )
    agreement_filename = fields.Char('Nom du fichier d\'agrément')
    
    # Statut de l'agrément selon le nouveau workflow
    state = fields.Selection([
        ('inactive', 'Inactif'),  # Statut par défaut après soumission
        ('active', 'Actif'),      # Après confirmation par l'administrateur
        ('expired', 'Expiré')     # Automatiquement quand la date d'expiration est dépassée
    ], string='Statut', default='inactive', tracking=True)
    
    # Champs calculés pour le suivi
    is_valid = fields.Boolean(
        string='Agrément valide',
        compute='_compute_is_valid',
        store=True,
        help="Indique si l'agrément est encore valide"
    )
    
    days_to_expiry = fields.Integer(
        string='Jours avant expiration',
        compute='_compute_days_to_expiry',
        store=True,
        help="Nombre de jours restants avant expiration"
    )
    
    # Informations complémentaires
    notes = fields.Text(
        string='Remarques',
        help="Remarques ou conditions particulières de l'agrément"
    )
    
    # Champs de suivi automatique
    create_date = fields.Datetime(string='Date de création', readonly=True)
    create_uid = fields.Many2one('res.users', string='Créé par', readonly=True)
    
    # Index pour optimiser les performances sur une application nationale
    _sql_constraints = [
        ('unique_ceas_number', 'UNIQUE(ceas_number)', 'Le numéro CEAS doit être unique.'),
    ]
    
    def init(self):
        """Création d'index pour optimiser les requêtes cron sur de gros volumes"""
        super().init()
        # Index composé pour la requête cron (state + expiry_date)
        self.env.cr.execute(
            "CREATE INDEX IF NOT EXISTS idx_agreement_state_expiry "
            "ON certification_agreement (state, expiry_date)"
        )
        # Index sur operator_id pour les mises à jour en batch
        self.env.cr.execute(
            "CREATE INDEX IF NOT EXISTS idx_agreement_operator "
            "ON certification_agreement (operator_id)"
        )
    
    @api.model
    def create(self, vals):
        """Génération automatique de la référence lors de la création"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('certification.agreement') or _('Nouveau')
        return super().create(vals)
    
    @api.depends('expiry_date', 'state')
    def _compute_is_valid(self):
        """Calcul de la validité de l'agrément"""
        today = fields.Date.today()
        for agreement in self:
            agreement.is_valid = (
                agreement.state == 'active' and 
                agreement.expiry_date and 
                agreement.expiry_date >= today
            )
            
    
    # calcul le nombre de jour avant la date d'expiration a partir de la date d'enregistrement de l'agreement
    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        """Calcul du nombre de jours avant expiration"""
        today = fields.Date.today()
        for agreement in self:
            if agreement.expiry_date:
                delta = agreement.expiry_date - today
                agreement.days_to_expiry = delta.days
            else:
                agreement.days_to_expiry = 0
    
    
    @api.constrains('issue_date', 'expiry_date')
    def _check_dates(self):
        """Validation des dates : la date d'expiration doit être postérieure à la date de délivrance"""
        for agreement in self:
            if agreement.issue_date and agreement.expiry_date:
                if agreement.expiry_date <= agreement.issue_date:
                    raise ValidationError(
                        _("La date d'expiration doit être postérieure à la date de délivrance.")
                    )
    
    @api.constrains('ceas_number')
    def _check_unique_ceas(self):
        """Vérification de l'unicité du numéro CEAS"""
        for agreement in self:
            if agreement.ceas_number:
                existing = self.search([
                    ('ceas_number', '=', agreement.ceas_number),
                    ('id', '!=', agreement.id)
                ])
                if existing:
                    raise ValidationError(
                        _("Le numéro CEAS '%s' existe déjà pour un autre agrément.") % agreement.ceas_number
                    )
    
    def action_confirm_agreement(self):
        """Action pour confirmer l'agrément (passage de inactif à actif)"""
        self.ensure_one()
        if self.expiry_date < fields.Date.today():
            raise ValidationError(_("Impossible de confirmer un agrément expiré."))
        
        # Passage du statut à actif
        self.write({'state': 'active'})
        
        # Mise à jour du statut d'agrément de l'opérateur
        #self.operator_id.write({'is_agreed_cesp': True})
        
        # Log dans le chatter
        self.message_post(body=_("Agrément confirmé et activé"))
        
        return True
    
    def action_preview_agreement_file(self):
        """Action pour prévisualiser le fichier d'agrément"""
        self.ensure_one()
        if not self.agreement_file:
            raise ValidationError(_("Aucun fichier d'agrément à prévisualiser."))
        
        # Créer un wizard pour la prévisualisation
        wizard = self.env['document.preview.wizard'].create({
            'name': self.agreement_filename or 'agreement.pdf',
            'pdf_data': self.agreement_file,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prévisualisation du fichier d\'agrément',
            'res_model': 'document.preview.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': 'large'},
        }
    
    """
    @api.model
    def _cron_check_expiring_agreements(self):
      
        today = fields.Date.today()
        
        # 1. TRAITEMENT EN BATCH - Marquer les agréments expirés 
        expired_agreements = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<', today)
        ])
        
        if expired_agreements:
            # Mise à jour en batch des agréments : Tous les agréments de ce recordset passent à l’état "expired" en une seule commande.
            expired_agreements.write({'state': 'expired'})
            
            # Pour tous les opérateurs liés à ces agréments, on met à jour le champ is_agreed_cesp
            expired_operators = expired_agreements.mapped('operator_id')
            expired_operators.write({'is_agreed_cesp': False})
            
            # Pour chaque agrément expiré, on ajoute un message dans le chatter
            for agreement in expired_agreements:
                agreement.message_post(body=_("Agrément expiré automatiquement le %s") % today)
        
        # 2. on cherche les agréments actifs dont la date d’expiration est dans les 30 prochains jours
        warning_date = today + timedelta(days=30)
        expiring_agreements = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '<=', warning_date),
            ('expiry_date', '>=', today)
        ])
        

        for agreement in expiring_agreements:
            # Avant de créer un rappel, on vérifie qu’il n’existe pas déjà une activité similaire,
            # afin d'éviter les doublons à chaque exécution du cron
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', agreement.id),
                ('summary', 'ilike', 'Agrément expirant'),
                ('date_deadline', '>=', today)
            ], limit=1)
            
            if not existing_activity:
                # Créer l'activité de rappel uniquement si elle n'existe pas
                agreement.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_("Agrément expirant bientôt"),
                    note=_("L'agrément %s expire le %s (dans %s jours)") % (
                        agreement.name, 
                        agreement.expiry_date,
                        (agreement.expiry_date - today).days
                    ),
                    user_id=agreement.create_uid.id,
                    date_deadline=agreement.expiry_date - timedelta(days=7)  # Rappel 7 jours avant
                )
        
        # 3. LOG DE PERFORMANCE POUR MONITORING :
        #  Cette partie enregistre un log interne dans Odoo contenant : le nombre d’agréments expirés,le nbre d’agréments pour lesquels une alerte a été créée
        # LOGS CONSOLE DETAILLES
        _logger = logging.getLogger(__name__)
        
        # LOG DE DÉBUT
        _logger.info("=== DÉBUT CRON AGRÉMENTS MINADER - 9H00 ===")
        _logger.info(f"Date du jour: {today}")
        _logger.info(f"Agréments expirés traités: {len(expired_agreements)}")
        _logger.info(f"Agréments surveillés (30 jours): {len(expiring_agreements)}")
        
        # LOG DÉTAILLÉ DES EXPIRÉS
        if expired_agreements:
            _logger.info("Agréments expirés aujourd'hui:")
            for agreement in expired_agreements:
                _logger.info(f"  -> {agreement.name} - Opérateur: {agreement.operator_id.name.name}")
        else:
            _logger.info("Aucun agrément expiré aujourd'hui")
        
        # LOG DE FIN
        _logger.info("=== FIN CRON MINADER - EXÉCUTION RÉUSSIE ===")
        
        return True
    
    #  méthode qui personnalise la façon dont un enregistrement d'agrément s’affiche
    """
    def name_get(self):
        """Personnalisation de l'affichage du nom"""
        result = []
        for agreement in self:
            name = f"{agreement.name} - {agreement.operator_id.name}"
            if agreement.ceas_number:
                name += f" (CEAS: {agreement.ceas_number})"
            result.append((agreement.id, name))
        return result