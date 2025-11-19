# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CertificationParcelle(models.Model):
    _name = 'certification.parcelle'
    _description = 'Parcelle de Culture Semencière'
    _order = 'espece, variete'
    
    # Relation avec l'opérateur
    operator_id = fields.Many2one('certification.operator', string='Opérateur/proprietaire',
                                 required=True, ondelete='cascade')
    
    # Relation optionnelle avec une demande (quand la parcelle est utilisée)
    request_id = fields.Many2one('certification.request', string='Demande de Certification', 
                                ondelete='set null')
    parcelle_name = fields.Char(string='Référence', copy=False, readonly=True,
                      default=lambda self: self.env['ir.sequence'].next_by_code('certification.parcelle'))
    
    # Champs de la déclaration de culture semencière
    espece = fields.Selection([
    ('mais', 'Maïs'),
    ('arachide', 'Arachide'),
    ('haricot', 'Haricot'),
    ('cacao', 'Cacao'),
    ('cafe', 'Café'),
    ('riz', 'Riz'),
    ('manioc', 'Manioc'),
    ('igname', 'Igname'),
    ('soja', 'Soja'),
    ('sorgho', 'Sorgho'),
    ('mil', 'Mil'),
    ('palmier_huile', 'Palmier à huile'),
    ('bananier_plantain', 'Bananier Plantain'),
    ('tomate', 'Tomate'),
    ('piment', 'Piment'),
    ('oignon', 'Oignon'),
    ('cotonnier', 'Coton'),
    ('ananas', 'Ananas'),
    ('pomme_de_terre', 'Pomme de terre'),
    ('patate_douce', 'Patate douce'),
    ('sesame', 'Sésame'),
    ('poivron', 'Poivron'),
    ('autres', 'Autres')
], string='Espèce', required=True,
   help="Choisir l'espèce agricole (ex: maïs, arachide, cacao...)")
    
    variete = fields.Selection([
    # --- Maïs ---
    ('cms_8501', 'CMS 8501 (Maïs)'),
    ('cam_202', 'CAM 202 (Maïs)'),
    ('cam_401', 'CAM 401 (Maïs)'),
    ('tzb_comp', 'TZB-Comp (Maïs)'),

    # --- Arachide ---
    ('h32', 'H-32 (Arachide)'),
    ('jl_24', 'JL 24 (Arachide)'),
    ('rmp_91', 'RMP 91 (Arachide)'),

    # --- Haricot ---
    ('p_80', 'P-80 (Haricot)'),
    ('nitu', 'NITU (Haricot rouge)'),
    ('glp_190', 'GLP 190 (Haricot blanc)'),

    # --- Cacao ---
    ('hybride_cacao', 'Hybride (Cacao)'),
    ('amelonado', 'Amelonado (Cacao)'),
    ('forastero', 'Forastero (Cacao)'),
    ('trinitario', 'Trinitario (Cacao)'),

    # --- Café ---
    ('arabica', 'Arabica (Café)'),
    ('robusta', 'Robusta (Café)'),
    ('excelsa', 'Excelsa (Café)'),

    # --- Riz ---
    ('nerica_1', 'NERICA 1 (Riz)'),
    ('nerica_8', 'NERICA 8 (Riz)'),
    ('togr_145', 'TOG 145 (Riz)'),

    # --- Manioc ---
    ('8034', '8034 (Manioc)'),
    ('tms_30572', 'TMS 30572 (Manioc)'),
    ('ndombe', 'Ndombe (Manioc local)'),

    # --- Igname ---
    ('kokoro', 'Kokoro (Igname)'),
    ('laboko', 'Laboko (Igname)'),
    ('florido', 'Florido (Igname)'),

    # --- Soja ---
    ('tgx_1448', 'TGX 1448 (Soja)'),
    ('tgx_1904', 'TGX 1904 (Soja)'),

    # --- Sorgho ---
    ('s_35', 'S-35 (Sorgho)'),
    ('framida', 'Framida (Sorgho)'),

    # --- Mil ---
    ('sohna', 'Sohna (Mil)'),
    ('hk_11', 'HK-11 (Mil)'),

    # --- Palmier à huile ---
    ('tenera', 'Tenera (Palmier à huile)'),
    ('dura', 'Dura (Palmier à huile)'),
    ('pisifera', 'Pisifera (Palmier à huile)'),

    # --- Bananier Plantain ---
    ('french', 'French (Bananier Plantain)'),
    ('horn', 'Horn (Bananier Plantain)'),
    ('ekona', 'Ekona (Bananier Plantain)'),

    # --- Tomate ---
    ('roma_vf', 'Roma VF (Tomate)'),
    ('marmande', 'Marmande (Tomate)'),
    ('uc_82b', 'UC-82B (Tomate)'),

    # --- Piment ---
    ('habanero', 'Habanero (Piment)'),
    ('bird_eye', 'Bird Eye (Piment)'),
    ('long_red', 'Long Red (Piment)'),

    # --- Oignon ---
    ('violet_de_galmi', 'Violet de Galmi (Oignon)'),
    ('red_creole', 'Red Creole (Oignon)'),

    # --- Coton ---
    ('irma_802', 'IRMA 802 (Coton)'),
    ('irma_803', 'IRMA 803 (Coton)'),

    # --- Ananas ---
    ('smooth_cayenne', 'Smooth Cayenne (Ananas)'),
    ('md2', 'MD2 (Ananas)'),

    # --- Pomme de terre ---
    ('spunta', 'Spunta (Pomme de terre)'),
    ('tubira', 'Tubira (Pomme de terre)'),

    # --- Patate douce ---
    ('tie_88', 'TIE 88 (Patate douce)'),
    ('vita', 'Vita (Patate douce)'),

    # --- Sésame ---
    ('s_32', 'S-32 (Sésame)'),
    ('n_9', 'N-9 (Sésame)'),

    # --- Poivron ---
    ('yolo_wonder', 'Yolo Wonder (Poivron)'),
    ('california_wonder', 'California Wonder (Poivron)'),

    # --- Divers ---
    ('generic', 'Générique / Non spécifiée'),
    ], string='Variété', required=True,
    help="Sélectionner la variété correspondant à l'espèce choisie.")
    
    
    
    categorie = fields.Selection([
        ('pre_base', 'Pré-base'),
        ('base', 'Base'),
        ('certifiee', 'Certifiée')
    ], string='Catégorie', required=True, default='certifiee')
    
    superficie = fields.Float(string='Superficie (ha)', 
                             help='Superficie en hectare pour les cultures classiques', required=True)
    
    quantite_semences_meres = fields.Float(string='Quantité de semences mères',
                                          help='Nombre d\'unités de semences mères')
    type_semence_mere = fields.Selection([
        ('cabosses', 'Cabosses'),
        ('boutures', 'Boutures'),
        ('plants', 'Plants'),
        ('tubercules', 'Tubercules'),
        ('bulbes', 'Bulbes'),
        ('greffons', 'Greffons'),
        ('autres', 'Autres')
    ], string='Type de semence mère', help='Type d\'unité pour les semences mères')
    
    production_attendue = fields.Float(string='Production attendue(ha)', required=True,
                                     help='En tonnes pour semences sèches, en nombre de plants pour arbres fruitiers')
    
    # Origine de la semence mère - informations détaillées
    region_id = fields.Many2one("minader.region", string="Région")
    departement_id = fields.Many2one("minader.departement", string="Département", required=True)
    arrondissement_id = fields.Many2one("minader.arrondissement", string="Arrondissement",required=True)
    localite_id = fields.Char(string="Localité", required=True)

    # Champs additionnels pour traçabilité
    # producteur_origine = fields.Char(string='Producteur d\'origine')
    
    # Calcul des frais de redevance semencière
    frais_redevance = fields.Float(string='Frais de redevance (FCFA)', compute='_compute_frais_redevance', store=True)


    lot_ids = fields.One2many('certification.parcelle.lot', 'parcelle_id', string='Lots')

    # Informations complémentaires

    agricole_campain = fields.Char(string="Campagne agricole", required=True)

    encadrement_structure = fields.Char(string="Structure d'encadrement et/ou d'appui", required=True)
    origine_semence_mere = fields.Text(string='Origine de la semence mère', required=True,

                                       help='Adresse du producteur, N° et date de la facture ou du bordereau de livraison, N° de l\'étiquette officielle de semences')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('lots_incomplete', 'Lots incomplets'),
        ('lots_complete', 'Lots complets'),
    ], default='draft', string="État des lots")

    @api.constrains('lot_ids')
    def _warn_incomplete_lots(self):
        for parcelle in self:
            total_area = sum(parcelle.lot_ids.mapped('area'))
            if parcelle.lot_ids and total_area < parcelle.superficie:
                parcelle.message_post(
                    body=(f"⚠️ Attention : La somme des lots ({total_area} ha) "
                          f"est inférieure à la superficie de la parcelle ({parcelle.superficie} ha).")
                )

    @api.depends('superficie', 'quantite_semences_meres')
    def _compute_frais_redevance(self):
        """Calcul des frais de redevance semencière"""
        for record in self:
            frais = 0.0
            # 10 000 FCFA par hectare
            if record.superficie:
                frais += record.superficie * 10000
            # Pour les semences mères, tarif à définir selon l'espèce
            if record.quantite_semences_meres:
                # Tarif par défaut pour les semences mères (à ajuster selon l'espèce)
                tarif_semences_meres = 100  # FCFA par unité
                frais += record.quantite_semences_meres * tarif_semences_meres
            record.frais_redevance = frais
    

    
    def name_get(self):
        """Affichage personnalisé dans les listes"""
        result = []
        for record in self:
            name = f"{record.espece} - {record.variete} ({record.categorie})"
            if record.superficie:
                name += f" - {record.superficie} ha"
            result.append((record.id, name))
        return result
    
    @api.model
    def create(self, vals):
        """Validation lors de la création"""
        if not vals.get('superficie') and not vals.get('quantite_semences_meres'):
            raise UserError(_("Veuillez renseigner soit la superficie soit la quantité de semences mères."))
        return super(CertificationParcelle, self).create(vals)
    
    def write(self, vals):
        """Validation lors de la modification"""
        result = super(CertificationParcelle, self).write(vals)
        for record in self:
            if not record.superficie and not record.quantite_semences_meres:
                raise UserError(_("Veuillez renseigner soit la superficie soit la quantité de semences mères."))
        return result

    def action_split_into_lots(self, nb_lots=3, custom_areas=None):
        """
        Split la parcelle en nb_lots lots. Si custom_areas (liste floats) fourni, on l'utilise.
        """
        for parc in self:
            if custom_areas:
                if len(custom_areas) == 0 or sum(custom_areas) <= 0:
                    raise UserError("Liste d'aires invalide.")
                for i, area in enumerate(custom_areas):
                    self.env['certification.parcelle.lot'].create({
                        'parcelle_id': parc.id,
                        'area': area,
                        'sequence': i + 1,
                    })
            else:
                if nb_lots <= 0:
                    raise UserError("Le nombre de lots doit être >= 1")
                area_each = parc.superficie / nb_lots
                for i in range(nb_lots):
                    self.env['certification.parcelle.lot'].create({
                        'parcelle_id': parc.id,
                        'area': area_each,
                        'sequence': i + 1,
                    })

    def update_lot_state(self):
        for parcelle in self:
            total_lots_area = sum(parcelle.lot_ids.mapped('area'))
            if total_lots_area == parcelle.superficie:
                parcelle.state = 'lots_complete'
            elif total_lots_area < parcelle.superficie:
                parcelle.state = 'lots_incomplete'


