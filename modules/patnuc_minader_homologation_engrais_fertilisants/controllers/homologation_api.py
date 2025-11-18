# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.tools import config
from odoo.exceptions import UserError, AccessError , ValidationError
import base64
import logging
import jwt
from datetime import datetime, timedelta
import json

_logger = logging.getLogger(__name__)

SECRET_KEY = config.get('jwt_secret')

ORIGIN_LOCAL = 'http://localhost:5173'
ORIGIN_TEST = 'http://localhost:8080'
SESSION_DURATION = 60 * 60 * 24 * 365 * 5  # 5 jours
# Mappage des champs API vers Odoo pour le produit
PRODUCT_FIELD_MAP = {
    'technical_name': 'technical_name',
    'country_of_origin_id': 'country_of_origin', 
}


class HomologationEngraisController(http.Controller):

    def _cors_headers(self):
        origin = request.httprequest.headers.get('Origin') or "*"
        return {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true'
        }

    def _make_json_response(self, data, status=200):
        headers = self._cors_headers()
        headers['Content-Type'] = 'application/json'
        return request.make_response(json.dumps(data), headers=headers, status=status)



    # -- lecture des fichiers 
    @http.route('/api/fertilizer_homologation/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def get_files_final(self,procedure_id, **kwargs):
        cors_headers = self._cors_headers()

        # 1. Réponse à la requête préflight (OPTIONS)
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # 2. Vérification du token JWT et authentification de l'utilisateur
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé",
                    "code": 401
                }, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            # Utiliser .env(user=user) pour que toutes les opérations Odoo se fassent en tant que cet utilisateur
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable",
                    "code": 404
                }, status=404)
            
            request.env =  request.env(user=user)
            # 
            procedure = request.env['fertilizer.homologation'].sudo().search([
                ('id', '=', procedure_id),
                ('user_id', '=', user_id) # S'assurer que seul le demandeur peut télécharger
            ], limit=1)
            #check procedure 
            if not procedure:
                return self._make_json_response({
                    "success": False,
                    "message": "Demande de certification introuvable ou non autorisée.",
                    "code": 404
                }, status=404)
            authorized_states = ['signed']
            if procedure.state not in authorized_states:
                return self._make_json_response({
                    "success": False,
                    "message": f"Le certificat n'est pas encore disponible pour le téléchargement. État actuel: {procedure.state}",
                    "code": 400
                }, status=400)
            #load files 
            file_data_b64 = procedure.homologation_document
            file_name = procedure.homologation_document_filename

            if not file_data_b64 or not file_name:
                return self._make_json_response({
                    "success": False,
                    "message": "Le certificat signé n'a pas encore été attaché au dossier.",
                    "code": 404
                }, status=404)
            # download file 
            file_content = base64.b64decode(file_data_b64)
            
            response = request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="%s"' % file_name),
                ]
            )
            
            return response
            
        except jwt.ExpiredSignatureError:
            return self._make_json_response({"success": False, "message": "Token expiré.", "code": 401}, status=401)
        except jwt.InvalidTokenError:
            return self._make_json_response({"success": False, "message": "Token invalide.", "code": 401}, status=401)
        except AccessError as ae:
            _logger.warning("Erreur d'accès lors du téléchargement: %s", str(ae))
            return self._make_json_response({"success": False, "error": "Accès non autorisé.", "code": 403}, status=403)
        except Exception as e:
            _logger.error("Erreur serveur lors du téléchargement du certificat : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": f"Erreur serveur interne : {str(e)}",
                "code": 500
            }, status=500)
        
    # ---- modification ----- 
    @http.route('/api/fertilizer_mod_homologation/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def get_mod_files_final(self,procedure_id, **kwargs):
        cors_headers = self._cors_headers()

        # 1. Réponse à la requête préflight (OPTIONS)
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # 2. Vérification du token JWT et authentification de l'utilisateur
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé",
                    "code": 401
                }, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            # Utiliser .env(user=user) pour que toutes les opérations Odoo se fassent en tant que cet utilisateur
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable",
                    "code": 404
                }, status=404)
            
            request.env =  request.env(user=user)
            # 
            procedure = request.env['fertilizer.mod.homologation'].sudo().search([
                ('id', '=', procedure_id),
                ('user_id', '=', user_id) # S'assurer que seul le demandeur peut télécharger
            ], limit=1)
            #check procedure 
            if not procedure:
                return self._make_json_response({
                    "success": False,
                    "message": "Demande d'homologation introuvable ou non autorisée.",
                    "code": 404
                }, status=404)
            authorized_states = ['signed']
            if procedure.state not in authorized_states:
                return self._make_json_response({
                    "success": False,
                    "message": f"Le certificat n'est pas encore disponible pour le téléchargement. État actuel: {procedure.state}",
                    "code": 400
                }, status=400)
            #load files 
            file_data_b64 = procedure.homologation_document
            file_name = procedure.homologation_document_filename

            if not file_data_b64 or not file_name:
                return self._make_json_response({
                    "success": False,
                    "message": "Le certificat signé n'a pas encore été attaché au dossier.",
                    "code": 404
                }, status=404)
            # download file 
            file_content = base64.b64decode(file_data_b64)
            
            response = request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="%s"' % file_name),
                ]
            )
            
            return response
            
        except jwt.ExpiredSignatureError:
            return self._make_json_response({"success": False, "message": "Token expiré.", "code": 401}, status=401)
        except jwt.InvalidTokenError:
            return self._make_json_response({"success": False, "message": "Token invalide.", "code": 401}, status=401)
        except AccessError as ae:
            _logger.warning("Erreur d'accès lors du téléchargement: %s", str(ae))
            return self._make_json_response({"success": False, "error": "Accès non autorisé.", "code": 403}, status=403)
        except Exception as e:
            _logger.error("Erreur serveur lors du téléchargement du certificat : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": f"Erreur serveur interne : {str(e)}",
                "code": 500
            }, status=500)
        
    # -- renouvellement 
    @http.route('/api/fertilizer_renew_homologation/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def get_files_final(self,procedure_id, **kwargs):
        cors_headers = self._cors_headers()

        # 1. Réponse à la requête préflight (OPTIONS)
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # 2. Vérification du token JWT et authentification de l'utilisateur
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé",
                    "code": 401
                }, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            # Utiliser .env(user=user) pour que toutes les opérations Odoo se fassent en tant que cet utilisateur
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable",
                    "code": 404
                }, status=404)
            
            request.env =  request.env(user=user)
            # 
            procedure = request.env['fertilizer.renew.homologation'].sudo().search([
                ('id', '=', procedure_id),
                ('user_id', '=', user_id) # S'assurer que seul le demandeur peut télécharger
            ], limit=1)
            #check procedure 
            if not procedure:
                return self._make_json_response({
                    "success": False,
                    "message": "Demande d'homologation introuvable ou non autorisée.",
                    "code": 404
                }, status=404)
            authorized_states = ['signed']
            if procedure.state not in authorized_states:
                return self._make_json_response({
                    "success": False,
                    "message": f"Le certificat n'est pas encore disponible pour le téléchargement. État actuel: {procedure.state}",
                    "code": 400
                }, status=400)
            #load files 
            file_data_b64 = procedure.homologation_document
            file_name = procedure.homologation_document_filename

            if not file_data_b64 or not file_name:
                return self._make_json_response({
                    "success": False,
                    "message": "Le certificat signé n'a pas encore été attaché au dossier.",
                    "code": 404
                }, status=404)
            # download file 
            file_content = base64.b64decode(file_data_b64)
            
            response = request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="%s"' % file_name),
                ]
            )
            
            return response
            
        except jwt.ExpiredSignatureError:
            return self._make_json_response({"success": False, "message": "Token expiré.", "code": 401}, status=401)
        except jwt.InvalidTokenError:
            return self._make_json_response({"success": False, "message": "Token invalide.", "code": 401}, status=401)
        except AccessError as ae:
            _logger.warning("Erreur d'accès lors du téléchargement: %s", str(ae))
            return self._make_json_response({"success": False, "error": "Accès non autorisé.", "code": 403}, status=403)
        except Exception as e:
            _logger.error("Erreur serveur lors du téléchargement du certificat : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": f"Erreur serveur interne : {str(e)}",
                "code": 500
            }, status=500)
    
    # ---- suspension ---- 
    @http.route('/api/fertilizer_suspend_homologation/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def get_files_final(self,procedure_id, **kwargs):
        cors_headers = self._cors_headers()

        # 1. Réponse à la requête préflight (OPTIONS)
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # 2. Vérification du token JWT et authentification de l'utilisateur
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé",
                    "code": 401
                }, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            # Utiliser .env(user=user) pour que toutes les opérations Odoo se fassent en tant que cet utilisateur
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable",
                    "code": 404
                }, status=404)
            
            request.env =  request.env(user=user)
            # 
            procedure = request.env['fertilizer.suspend.homologation'].sudo().search([
                ('id', '=', procedure_id),
                ('user_id', '=', user_id) # S'assurer que seul le demandeur peut télécharger
            ], limit=1)
            #check procedure 
            if not procedure:
                return self._make_json_response({
                    "success": False,
                    "message": "La suspension de l'homologation introuvable ou non autorisée.",
                    "code": 404
                }, status=404)
            authorized_states = ['signed']
            if procedure.state not in authorized_states:
                return self._make_json_response({
                    "success": False,
                    "message": f"Le certificat n'est pas encore disponible pour le téléchargement. État actuel: {procedure.state}",
                    "code": 400
                }, status=400)
            #load files 
            file_data_b64 = procedure.pv_suspension
            file_name = procedure.pv_suspension_filename

            if not file_data_b64 or not file_name:
                return self._make_json_response({
                    "success": False,
                    "message": "Le certificat signé n'a pas encore été attaché au dossier.",
                    "code": 404
                }, status=404)
            # download file 
            file_content = base64.b64decode(file_data_b64)
            
            response = request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="%s"' % file_name),
                ]
            )
            
            return response
            
        except jwt.ExpiredSignatureError:
            return self._make_json_response({"success": False, "message": "Token expiré.", "code": 401}, status=401)
        except jwt.InvalidTokenError:
            return self._make_json_response({"success": False, "message": "Token invalide.", "code": 401}, status=401)
        except AccessError as ae:
            _logger.warning("Erreur d'accès lors du téléchargement: %s", str(ae))
            return self._make_json_response({"success": False, "error": "Accès non autorisé.", "code": 403}, status=403)
        except Exception as e:
            _logger.error("Erreur serveur lors du téléchargement du certificat : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": f"Erreur serveur interne : {str(e)}",
                "code": 500
            }, status=500)
    
    # ---
    @http.route('/api/fertilizer_homologation/create', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_homologation_request(self, **kwargs): 
        cors_headers = self._cors_headers()

        # Réponse CORS préflight
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # --- Vérification et récupération de l'utilisateur via JWT ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({"success": False, "message": "Token JWT manquant ou mal formé."}, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = request.env['res.users'].sudo().browse(user_id)

            if not user.exists():
                return self._make_json_response({"success": False, "message": "Utilisateur introuvable."}, status=401)
            
            current_env = request.env(user=user)
            data = request.params
            
            product = False
            manufacturer_partner_id = False
            manufacturer_name = data.get('manufacturer_name')


            # 1. CRÉATION SYSTÉMATIQUE DU FABRICANT (manufacturer_id)
            # Cette logique crée toujours un nouveau res.partner si un nom est fourni.
            if manufacturer_name:
                # La gestion du champ manufacturer_country_id a été retirée.
                partner_vals = {
                    'name': manufacturer_name,
                    'is_company': True,
                }
                
                manufacturer_partner_record = current_env['res.partner'].sudo().create(partner_vals)
                manufacturer_partner_id = manufacturer_partner_record.id


            # 2. LOGIQUE DE SÉLECTION/CRÉATION DE PRODUIT (fertilizer.product)
            product_id_input = data.get('product_id')
            product_name = data.get('product_name')

            if product_id_input:
                # CAS 1: ID de produit existant fourni
                try:
                    product = current_env['fertilizer.product'].sudo().browse(int(product_id_input))
                    if not product.exists():
                        return self._make_json_response({
                            "success": False, "error": f"Produit avec l'ID {product_id_input} introuvable."
                        }, status=404)
                except ValueError:
                    return self._make_json_response({
                        "success": False, "error": "L'identifiant de produit (product_id) doit être un entier valide."
                    }, status=400)

            elif product_name:
                # CAS 2: Nom de produit fourni (Recherche ou Création)
                
                # 2a: Recherche du produit existant par nom
                product = current_env['fertilizer.product'].sudo().search([('name', '=', product_name)], limit=1)

                # 2b: Création dynamique si non trouvé
                if not product:
                    if not manufacturer_partner_id:
                        return self._make_json_response({
                            "success": False, "error": "Le nom du fabricant (manufacturer_name) est requis pour créer un nouveau produit."
                        }, status=400)

                    product_vals = {
                        'name': product_name,
                        'manufacturer_id': manufacturer_partner_id, 
                    }
                    
                    # Ajout des champs additionnels (technical_name, country_of_origin)
                    for api_field, odoo_field in PRODUCT_FIELD_MAP.items():
                        if api_field in data and data[api_field]:
                            if odoo_field == 'country_of_origin': 
                                try:
                                    country_id = int(data[api_field])
                                    if current_env['res.country'].sudo().browse(country_id).exists():
                                        product_vals[odoo_field] = country_id
                                except (ValueError, TypeError):
                                    pass 
                            else:
                                product_vals[odoo_field] = data[api_field]

                    # Création effective du produit (avec le manufacturer_id)
                    product = current_env['fertilizer.product'].sudo().create(product_vals)
                    
            else:
                # CAS 3: Ni ID ni Nom fourni
                return self._make_json_response({
                    "success": False,
                    "error": "Veuillez fournir l'identifiant (product_id) ou le nom du produit (product_name) pour la demande."
                }, status=400)
            
            # 3. CRÉATION DE LA DEMANDE D'HOMOLOGATION
            vals = {
                'applicant_id': user.id,
                'product_id': product.id,
            }
           
            # --- Gestion des fichiers binaires ---
            file_fields = {
                'official_request_letter': 'official_request_letter_filename',
                'homologation_certificate': 'homologation_certificate_filename',
                'import_agreement_copy': 'import_agreement_copy_filename',
                'identity_document_copy': 'identity_document_copy_filename',
            }

            max_file_size = 15 * 1024 * 1024 

            for field, filename_field in file_fields.items():
                file_data = request.httprequest.files.get(field)
                if not file_data:
                    continue

                file_data.seek(0, 2)
                file_size = file_data.tell()
                file_data.seek(0)
                if file_size > max_file_size:
                    return self._make_json_response({
                        "success": False, "error": f"Fichier {field} trop volumineux (max 15MB)"
                    }, status=400)

                vals[field] = base64.b64encode(file_data.read()).decode('utf-8')
                vals[filename_field] = file_data.filename

            # --- Création de la demande ---
            record = current_env['fertilizer.homologation'].sudo().create(vals)
            record.sudo().action_submit()

            # --- Réponse de succès ---
            expires_at = datetime.utcnow() + timedelta(seconds=SESSION_DURATION)

            response = {
                "success": True,
                "data": {
                    "message": "Demande d’homologation créée avec succès.",
                    "record_id": record.id,
                    "reference": record.name,
                    "state": record.state,
                    "user_id": user.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "manufacturer_id": product.manufacturer_id.id if product.manufacturer_id else False,
                    "manufacturer_name": product.manufacturer_id.name if product.manufacturer_id else False,
                    "expires_at": expires_at.isoformat() + "Z",
                },
                "code": 200
            }
            return self._make_json_response(response, status=200)

        # ------------------------------
        # GESTION DES ERREURS
        # ------------------------------
        except (ValidationError, UserError) as e:
            _logger.error(f"Erreur de validation : {e}")
            return self._make_json_response({"success": False, "error": str(e), "code": 400}, status=400)
        except jwt.ExpiredSignatureError:
            return self._make_json_response({"success": False, "message": "Token expiré."}, status=401)
        except jwt.InvalidTokenError:
            return self._make_json_response({"success": False, "message": "Token invalide."}, status=401)
        except Exception as e:
            _logger.exception("Erreur interne lors de la création d’une homologation.")
            return self._make_json_response({"success": False, "error": "Erreur interne du serveur", "details": str(e), "code": 500}, status=500)

    
    #liste des produits 
    @http.route('/api/products', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_products(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())

        try:
            products = request.env['fertilizer.product'].sudo().search([])
            produit_list = []
            for prod in products:
                # Utilisation des champs pertinents pour l'affichage public
                produit_list.append({
                    'id': prod.id,
                    'name': prod.name,
                    'technical name': prod.technical_name,
                    'fabricant': prod.manufacturer_id.name,
                    
                })

            return self._make_json_response({
                "success": True,
                "data": produit_list,
                "count": len(produit_list)
            })
            
        except Exception as e:
            _logger.error("Erreur lors de la récupération des produits : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": "Erreur interne du serveur lors de la récupération des produits.",
                "details": str(e),
                "code": 500
            }, status=500)

    
    # liste des country
    @http.route('/api/countries', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_countries(self, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())

        try:
            # Récupère tous les pays du modèle standard res.country
            countries = request.env['res.country'].sudo().search([], order='name asc')
            country_list = []

            for country in countries:
                country_list.append({
                    'id': country.id,
                    'name': country.name,
                    'code': country.code, # Code ISO 2 lettres
                })

            return self._make_json_response({
                "success": True,
                "data": country_list,
                "count": len(country_list)
            })

        except Exception as e:
            _logger.error("Erreur lors de la récupération des pays : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": "Erreur interne du serveur lors de la récupération des pays.",
                "details": str(e),
                "code": 500
            }, status=500)

    # list homog
    @http.route('/api/fertilizer_homologation/list', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_all_fertilizer_homologations(self, **kwargs):
        cors_headers = self._cors_headers()

        # Préflight
        if request.httprequest.method == "OPTIONS":
            return request.make_response("", headers=cors_headers)

        try:
            # --- Vérification du token JWT ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = request.make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                })
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                })
                response.headers.update(cors_headers)
                return response
            #  get homologations
            homologations = request.env['fertilizer.homologation'].sudo().search([
                ('applicant_id', '=', user.id)
            ], order='create_date desc')

            homologation_list = []

            for h in homologations:
                homologation_list.append({
                    'id': h.id,
                    'reference': h.name,
                    'demandeur': h.applicant_id.name,
                    'produit': h.product_id.name,
                    'etat': h.state,
                    'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,

                })

            response = request.make_json_response({
                "success": True,
                "data": homologation_list,
                "code": 200
            })
            response.headers.update(cors_headers)
            return response

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré."
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide."
            }, status=401)

        except Exception as e:
            _logger.error(f"Erreur récupération homologations: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )

    @http.route('/api/fertilizer_homologation/list/detail/<int:request_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_fertilizer_homologation_detail(self, request_id, **kwargs):
        cors_headers = self._cors_headers()

        # Préflight
        if request.httprequest.method == "OPTIONS":
            return request.make_response("", headers=cors_headers)

        try:
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = request.make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                })
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                })
                response.headers.update(cors_headers)
                return response

            #get detail demande
            h = request.env['fertilizer.homologation'].sudo().search([
                ('id', '=', request_id),
                ('applicant_id', '=', user.id)
            ], limit=1)
            if not h.exists():
                headers = [
                    ('Content-Type', 'application/json'),
                    ('Access-Control-Allow-Origin', '*'),
                ]
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Demande non trouvée'}),
                    headers=headers
                )

            detail = {
                'id': h.id,
                'reference': h.name,
                'demandeur': h.applicant_id.name,
                'produit': h.product_id.name,
                'etat': h.state,
                'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,
                'date_expiration': h.expiry_date.strftime('%Y-%m-%d') if h.expiry_date else None,
                'notes': h.notes,
                'rejet_motif': h.rejection_reason,
                'retour_motif': h.return_reason,
                'note_conformite': h.conformity_note,
                'analyse_complete': h.analysis_complete,
                'test_champ_complet': h.field_test_complete,
                'evaluation_economique_complete': h.economic_evaluation_complete,
                'tous_documents_verifies': h.all_documents_verified,
            }

            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': True, 'data': detail}),
                headers=headers
            )

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré."
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide."
            }, status=401)

        except Exception as e:
            _logger.error(f"Erreur détail homologation: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )


    # modification homologation
    @http.route('/api/fertilizer_mod_homologation/create', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_mod_homologation(self, **kwargs):
        cors_headers = self._cors_headers()

        # --- Réponse à la requête OPTIONS ---
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # --- Vérification du token JWT ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou invalide"
                }, status=401)
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                }, status=404)
                response.headers.update(cors_headers)
                return response

            request.env = request.env(user=user)
            data = request.params

            # --- Champs obligatoires ---
            required_fields = ['num_arrete']
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                response = self._make_json_response({
                    "success": False,
                    "error": f"Champs manquants : {', '.join(missing_fields)}"
                }, status=400)
                response.headers.update(cors_headers)
                return response

            #get product
            product_name = data.get('product_name')
            product = request.env['fertilizer.product'].sudo().search([('name', '=', product_name)], limit=1)
            if not product :
                return self._make_json_response({
                    "success": False,
                    "error": f"Le produit {product_name} est introuvable "
                }, status=400)
            #get arrete
            num_arrete =  data.get('num_arrete')
            arrete = request.env['fertilizer.decree'].sudo().search([('name', '=', num_arrete)], limit=1)
            if not arrete :
                return self._make_json_response({
                    "success": False,
                    "error": f"Le numero de l'arrêté {num_arrete} est introuvable "
                }, status=400)
            #data create
            vals = {
                'arrete_id': arrete.id,
                'product_id': product.id,

            }

            # --- Gestion des fichiers uploadés ---
            file_fields = {
                'official_request_letter': 'official_request_letter_filename',
                'homologation_certificate': 'homologation_certificate_filename',
                'import_agreement_copy': 'import_agreement_copy_filename',
                'identity_document_copy': 'identity_document_copy_filename',
            }

            max_file_size = 10 * 1024 * 1024  # 10 MB

            for field, filename_field in file_fields.items():
                file_data = request.httprequest.files.get(field)
                if not file_data:
                    continue

                file_data.seek(0, 2)
                file_size = file_data.tell()
                file_data.seek(0)
                if file_size > max_file_size:
                    response = self._make_json_response({
                        "success": False,
                        "error": f"Le fichier {field} dépasse la taille maximale (10MB)"
                    }, status=400)
                    response.headers.update(cors_headers)
                    return response

                vals[field] = base64.b64encode(file_data.read()).decode('utf-8')
                vals[filename_field] = file_data.filename

            # --- Création de l'enregistrement ---
            record = request.env['fertilizer.mod.homologation'].sudo().create(vals)

            # Passage automatique à l’étape "verification"
            record.sudo().action_submit()

            response_data = {
                "success": True,
                "data" : {
                    "message": "Demande de modification d'homologation créée avec succès",
                    "id": record.id,
                    "reference": record.name,
                    "state": record.state,
                    "user_id": user.id,
                    "expires_in": SESSION_DURATION
                },
                "code": 200,
            }
            response = self._make_json_response(response_data, status=200)
            response.headers.update(cors_headers)
            return response

        except jwt.ExpiredSignatureError:
            response = self._make_json_response({
                "success": False,
                "message": "Token expiré"
            }, status=401)
            response.headers.update(cors_headers)
            return response

        except jwt.InvalidTokenError:
            response = self._make_json_response({
                "success": False,
                "message": "Token invalide"
            }, status=401)
            response.headers.update(cors_headers)
            return response

        except (ValidationError, UserError) as e:
            response = self._make_json_response({
                "success": False,
                "error": str(e)
            }, status=400)
            response.headers.update(cors_headers)
            return response

        except Exception as e:
            _logger.exception("Erreur lors de la création de la demande : %s", str(e))
            response = self._make_json_response({
                "success": False,
                "error": f"Erreur interne : {str(e)}"
            }, status=500)
            response.headers.update(cors_headers)
            return response

    @http.route('/api/fertilizer_mod_homologation/list', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_all_fertilizer_mod_homologations(self, **kwargs):
        cors_headers = self._cors_headers()

        # Préflight
        if request.httprequest.method == "OPTIONS":
            return request.make_response("", headers=cors_headers)

        try:
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = request.make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                })
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                })
                response.headers.update(cors_headers)
                return response
            #  get homologations
            homologations = request.env['fertilizer.mod.homologation'].sudo().search([
                ('applicant_id', '=', user.id)
            ], order='create_date desc')

            homologation_list = []

            for h in homologations:
                homologation_list.append({
                    'id': h.id,
                    'reference': h.name,
                    'demandeur': h.applicant_id.name,
                    'numero_arrete': h.arrete_id.name,
                    'produit': h.product_id.name,
                    'etat': h.state,
                    'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,

                })

            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': True, 'data': homologation_list}),
                headers=headers
            )

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré."
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide."
            }, status=401)

        except Exception as e:
            _logger.error(f"Erreur récupération homologations: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )

    @http.route('/api/fertilizer_mod_homologation/list/detail/<int:request_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_fertilizer_mod_homologation_detail(self, request_id, **kwargs):
        cors_headers = self._cors_headers()

        # Préflight
        if request.httprequest.method == "OPTIONS":
            return request.make_response("", headers=cors_headers)

        try:
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = request.make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                })
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                })
                response.headers.update(cors_headers)
                return response

            #get detail demande
            h = request.env['fertilizer.mod.homologation'].sudo().search([
                ('id', '=', request_id),
                ('applicant_id', '=', user.id)
            ], limit=1)
            if not h.exists():
                headers = [
                    ('Content-Type', 'application/json'),
                    ('Access-Control-Allow-Origin', '*'),
                ]
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Demande non trouvée'}),
                    headers=headers
                )

            detail = {
                'id': h.id,
                'reference': h.name,
                'demandeur': h.applicant_id.name,
                'numero_arrete':h.arrete_id.name,
                'produit': h.product_id.name,
                'etat': h.state,
                'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,
                'date_expiration': h.expiry_date.strftime('%Y-%m-%d') if h.expiry_date else None,
                'notes': h.notes,
                'rejet_motif': h.rejection_reason,
                'retour_motif': h.return_reason,
                'note_conformite': h.conformity_note,
                'analyse_complete': h.analysis_complete,
                'test_champ_complet': h.field_test_complete,
                'evaluation_economique_complete': h.economic_evaluation_complete,
                'tous_documents_verifies': h.all_documents_verified,
            }

            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]

            return request.make_response(
                json.dumps({'success': True, 'data': detail}),
                headers=headers
            )

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré."
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide."
            }, status=401)

        except Exception as e:
            _logger.error(f"Erreur détail homologation: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )


    #renouvellement homologation
    @http.route('/api/fertilizer_renew_homologation/create', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_renew_homologation(self, **kwargs):
        cors_headers = self._cors_headers()

        # --- Réponse à la requête OPTIONS ---
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # --- Vérification du token JWT ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou invalide"
                }, status=401)
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                }, status=404)
                response.headers.update(cors_headers)
                return response

            request.env = request.env(user=user)
            data = request.params

            # --- Champs obligatoires ---
            required_fields = ['num_arrete','data_toxicity','data_environnment','data_limit_max']
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                response = self._make_json_response({
                    "success": False,
                    "error": f"Champs manquants : {', '.join(missing_fields)}"
                }, status=400)
                response.headers.update(cors_headers)
                return response

            #get product

            #get arrete
            num_arrete =  data.get('num_arrete')
            arrete = request.env['fertilizer.decree'].sudo().search([('name', '=', num_arrete)], limit=1)
            if not arrete :
                return self._make_json_response({
                    "success": False,
                    "error": f"Le numero de l'arrêté {num_arrete} est introuvable "
                }, status=400)
            #data create
            vals = {
                'arrete_id': arrete.id,
                'data_toxicity': data.get('data_toxicity'),
                'data_environnment':data.get('data_environnment'),
                'data_limit_max':data.get('data_limit_max')
            }

            # --- Gestion des fichiers uploadés ---
            file_fields = {
                'official_request_letter': 'official_request_letter_filename',
                'report_suivi': 'report_suivi_filename',
            }

            max_file_size = 10 * 1024 * 1024  # 10 MB

            for field, filename_field in file_fields.items():
                file_data = request.httprequest.files.get(field)
                if not file_data:
                    continue

                file_data.seek(0, 2)
                file_size = file_data.tell()
                file_data.seek(0)
                if file_size > max_file_size:
                    response = self._make_json_response({
                        "success": False,
                        "error": f"Le fichier {field} dépasse la taille maximale (10MB)"
                    }, status=400)
                    response.headers.update(cors_headers)
                    return response

                vals[field] = base64.b64encode(file_data.read()).decode('utf-8')
                vals[filename_field] = file_data.filename

            # --- Création de l'enregistrement ---
            record = request.env['fertilizer.renew.homologation'].sudo().create(vals)

            # Passage automatique à l’étape "verification"
            record.sudo().action_submit()

            response_data = {
                "success": True,
                "data": {
                    "message": "Demande de renouvellement d'homologation créée avec succès",
                    "id": record.id,
                    "reference": record.name,
                    "state": record.state,
                    "user_id": user.id,
                    "expires_in": SESSION_DURATION
                },
                "code": 200,
            }
            response = self._make_json_response(response_data, status=200)
            response.headers.update(cors_headers)
            return response

        except jwt.ExpiredSignatureError:
            response = self._make_json_response({
                "success": False,
                "message": "Token expiré"
            }, status=401)
            response.headers.update(cors_headers)
            return response

        except jwt.InvalidTokenError:
            response = self._make_json_response({
                "success": False,
                "message": "Token invalide"
            }, status=401)
            response.headers.update(cors_headers)
            return response

        except (ValidationError, UserError) as e:
            response = self._make_json_response({
                "success": False,
                "error": str(e)
            }, status=400)
            response.headers.update(cors_headers)
            return response

        except Exception as e:
            _logger.exception("Erreur lors de la création de la demande : %s", str(e))
            response = self._make_json_response({
                "success": False,
                "error": f"Erreur interne : {str(e)}"
            }, status=500)
            response.headers.update(cors_headers)
            return response

    @http.route('/api/fertilizer_renew_homologation/list', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_all_fertilizer_renew_homologations(self, **kwargs):
        cors_headers = self._cors_headers()

        # Préflight
        if request.httprequest.method == "OPTIONS":
            return request.make_response("", headers=cors_headers)

        try:
            # --- Vérification du token JWT ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = request.make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                })
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                })
                response.headers.update(cors_headers)
                return response
            #  get homologations
            homologations = request.env['fertilizer.renew.homologation'].sudo().search([
                ('applicant_id', '=', user.id)
            ], order='create_date desc')

            homologation_list = []

            for h in homologations:
                homologation_list.append({
                    'id': h.id,
                    'reference': h.name,
                    'demandeur': h.applicant_id.name,
                    'numero_arrete': h.arrete_id.name,
                    'produit': h.old_product_hom.name,
                    'etat': h.state,
                    'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,

                })

            response = request.make_json_response({
                "success": True,
                "data": homologation_list,
                "code": 200
            })
            response.headers.update(cors_headers)
            return response

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré."
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide."
            }, status=401)

        except Exception as e:
            _logger.error(f"Erreur récupération homologations: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )

    @http.route('/api/fertilizer_renew_homologation/list/detail/<int:request_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_fertilizer_renew_homologation_detail(self, request_id, **kwargs):
        cors_headers = self._cors_headers()

        # Préflight
        if request.httprequest.method == "OPTIONS":
            return request.make_response("", headers=cors_headers)

        try:
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                response = request.make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                })
                response.headers.update(cors_headers)
                return response

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable"
                })
                response.headers.update(cors_headers)
                return response

            #get detail demande
            h = request.env['fertilizer.renew.homologation'].sudo().search([
                ('id', '=', request_id),
                ('applicant_id', '=', user.id)
            ], limit=1)
            if not h.exists():
                headers = [
                    ('Content-Type', 'application/json'),
                    ('Access-Control-Allow-Origin', '*'),
                ]
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Demande non trouvée'}),
                    headers=headers
                )

            detail = {
                'id': h.id,
                'reference': h.name,
                'demandeur': h.applicant_id.name,
                'numero_arrete':h.arrete_id.name,
                'produit': h.old_product_hom.name,
                'etat': h.state,
                'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,
                'date_expiration': h.expiry_date.strftime('%Y-%m-%d') if h.expiry_date else None,
                'tous_documents_verifies': h.all_documents_verified,
            }

            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]

            return request.make_response(
                json.dumps({'success': True, 'data': detail}),
                headers=headers
            )

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré."
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide."
            }, status=401)

        except Exception as e:
            _logger.error(f"Erreur détail homologation: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )
