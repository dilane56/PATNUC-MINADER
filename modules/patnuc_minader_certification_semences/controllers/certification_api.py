# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from odoo.tools import config
from odoo.exceptions import ValidationError, AccessError , UserError
import json
import logging
import base64
import jwt
from datetime import datetime, timedelta


_logger = logging.getLogger(__name__)
SECRET_KEY = config.get('jwt_secret')

ORIGIN_LOCAL = 'http://localhost:5173'
ORIGIN_TEST = 'http://localhost:8080'
SESSION_DURATION = 60 * 60 * 24 * 365 * 5  # 5 jours

class CertificationSemencesController(http.Controller):

    def _make_options_response(self):
        """Réponse CORS pour les requêtes OPTIONS"""
        headers = [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Access-Control-Max-Age', '3600'),
        ]
        return request.make_response('', headers=headers)

    def _make_json_response(self, data, status=200):
        """Réponse JSON avec en-têtes CORS"""
        headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
        ]
        return request.make_response(json.dumps(data), headers=headers, status=status)

    def _cors_headers(self):
        origin = request.httprequest.headers.get('Origin') or "http://localhost:8080"
        return {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true'
        }
    
    @http.route('/api/certification_request/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
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
            procedure = request.env['certification.request'].sudo().search([
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
            authorized_states = ['labelling', 'approved']
            if procedure.state not in authorized_states:
                return self._make_json_response({
                    "success": False,
                    "message": f"Le certificat n'est pas encore disponible pour le téléchargement. État actuel: {procedure.state}",
                    "code": 400
                }, status=400)
            #load files 
            file_data_b64 = procedure.certificat_document
            file_name = procedure.certificat_document_filename

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


    @http.route('/api/certification_request/create', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def submit_declaration(self, **kwargs):
        cors_headers = self._cors_headers()

        # Réponse à la requête préflight (OPTIONS)
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # --- 1. Vérification du Token JWT et de l'utilisateur ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({
                    "success": False,
                    "message": "Token manquant ou mal formé"
                }, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists() or not user.partner_id:
                return self._make_json_response({
                    "success": False,
                    "message": "Utilisateur ou partenaire introuvable"
                }, status=401)
            
            # Utilisation de l'environnement avec l'utilisateur authentifié
            request.env = request.env(user=user)
            #recuperation de l'operateur rattaché a l'utilisateur effectuant la demande 
            operator_partner_id = request.env['certification.operator'].sudo().search([
                ('user_id', '=', user.id),
                ('actif', '=', True) 
            ], limit=1)

           
            if not operator_partner_id : 
                return self._make_json_response({
                    "success": False,
                    "message": "Cet utilisateur n'est pas rattaché a un opérateur agrée"
                }, status=401)
            
            # verifie si operateur agrée

            today = fields.Date.today()
            agreement = request.env['certification.agreement'].sudo().search([
                ('operator_id', '=', operator_partner_id.id),
                ('state', '=', 'active'),
                ('expiry_date', '>=', today)
            ], limit=1)

            if not agreement:
                return self._make_json_response({
                    "success": False,
                    "message": "Aucun agrément actif trouvé pour cet opérateur. Impossible de continuer."
                }, status=401)


            # verifier si l'utilisateur est un operateur habilité 
            data = request.params

            # --- 2. Préparation des données de la Parcelle ---
            parcelle_required_fields = ['espece', 'variete', 'categorie', 'production_attendue']
            parcelle_data = {
                'operator_id': operator_partner_id.id,
                'espece': data.get('espece'),
                'variete': data.get('variete'),
                'categorie': data.get('categorie'),
                'superficie': float(data.get('superficie', 0.0)),
                'quantite_semences_meres': float(data.get('quantite_semences_meres', 0.0)),
                'type_semence_mere': data.get('type_semence_mere'),
                'production_attendue': float(data.get('production_attendue', 0.0)),
                'region_id': int(data.get('region_id')),
                'departement_id': int(data.get('departement_id')),
                'arrondissement_id': int(data.get('arrondissement_id')),
                'localite_id': data.get('localite_id'),
               
            }

            missing_parcelle_fields = [f for f in parcelle_required_fields if not parcelle_data.get(f)]
            if missing_parcelle_fields:
                raise UserError(f"Champs de parcelle manquants ou invalides : {', '.join(missing_parcelle_fields)}")
            
            if parcelle_data['superficie'] <= 0.0 and parcelle_data['quantite_semences_meres'] <= 0.0:
                 raise UserError("Veuillez renseigner soit la superficie soit la quantité de semences mères.")


            # --- 3. Création de la Parcelle ---
            parcelle_record = request.env['certification.parcelle'].sudo().create(parcelle_data)

            # --- 4. Préparation des données de la Demande de Certification ---
            request_required_fields = ['agricole_campain', 'encadrement_structure']
            file_fields = {
                'declaration_activite_semenciere_timbre': 'declaration_activite_semenciere_timbre_filename',
                'redevance_semenciere_payement_receipt': 'redevance_semenciere_payement_receipt_filename',
            }
            
            # Vérification des fichiers binaires requis
            missing_files = [f for f in file_fields if f not in request.httprequest.files]
            if missing_files:
                raise UserError(f"Fichiers manquants : {', '.join(missing_files)}")

            request_vals = {
                'operator_id': operator_partner_id.id,
                'parcelle_id': parcelle_record.id,
                
                'agricole_campain': data.get('agricole_campain'),
                'encadrement_structure': data.get('encadrement_structure'),
            }

            missing_request_fields = [f for f in request_required_fields if not request_vals.get(f)]
            if missing_request_fields:
                raise UserError(f"Champs de demande manquants ou invalides : {', '.join(missing_request_fields)}")
            
            max_file_size = 10 * 1024 * 1024  # 10 MB

            # Gestion des fichiers
            for field, filename_field in file_fields.items():
                file_data = request.httprequest.files.get(field)
                
                file_data.seek(0, 2)
                file_size = file_data.tell()
                file_data.seek(0)

                if file_size > max_file_size:
                    raise UserError(f"Fichier {field} trop volumineux (max 10MB)")

                request_vals[field] = base64.b64encode(file_data.read()).decode('utf-8')
                request_vals[filename_field] = file_data.filename

            # --- 5. Création de la Demande ---
            request_record = request.env['certification.request'].sudo().create(request_vals)
            
            # Mettre à jour l'état initial
            request_record.sudo().action_submit() # Si cette méthode existe et fait passer à 'doc_verification'

            # --- 6. Réponse de succès ---
            return self._make_json_response({
                "success": True,
                "message": "Déclaration de parcelle et demande de certification créées avec succès.",
                "parcelle_id": parcelle_record.id,
                "parcelle_reference": parcelle_record.parcelle_name,
                "request_id": request_record.id,
                "request_reference": request_record.name,
                "state": request_record.state,
                "code": 200
            })

        # --- Gestion des erreurs ---
        except jwt.ExpiredSignatureError:
            return self._make_json_response({"success": False, "message": "Token expiré."}, status=401)
        except jwt.InvalidTokenError:
            return self._make_json_response({"success": False, "message": "Token invalide."}, status=401)
        except (ValidationError, UserError) as ve:
            _logger.warning("Erreur de validation ou utilisateur lors de la soumission: %s", str(ve))
            return self._make_json_response({"success": False, "error": str(ve), "code": 400}, status=400)
        except Exception as e:
            _logger.error("Erreur serveur lors de la soumission de la déclaration : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": f"Erreur serveur interne : {str(e)}",
                "code": 500
            }, status=500)

    @http.route('/api/certification_request/list', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def get_certification_requests(self, **kwargs):
        """Récupérer la liste des demandes de certification"""
        cors_headers = self._cors_headers()
        if request.httprequest.method == 'OPTIONS':
            return self._make_options_response()

        try:
            # --- 1. Vérification du token JWT ---
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
            if not user.exists() or not user.partner_id:
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur ou partenaire introuvable"
                })
                response.headers.update(cors_headers)
                return response

            # ID du partenaire de l'utilisateur (le champ Many2one operator_id pointe vers res.partner)
            operator_partner_id = request.env['certification.operator'].sudo().search([
                ('user_id', '=', user.id),
                ('actif', '=', True) 
            ], limit=1)
            
            requests_list = []
            
            # --- 2. FILTRE CORRIGÉ : Utilisation de operator_id ---
            requests_records = request.env['certification.request'].sudo().search([
                ('operator_id', '=', operator_partner_id.id)
            ], order='create_date desc')

            for rec in requests_records:
                requests_list.append({
                    'id': rec.id,
                    'reference': rec.name,
                    'operator': rec.operator_id.name if rec.operator_id else '',
                    'site_production': rec.parcelle_id.parcelle_name if rec.parcelle_id else '',
                    'variete_semence': rec.parcelle_variete,
                    'superficie': rec.parcelle_superficie,
                    'etat': rec.state,
                    'date_soumission': rec.submission_date.strftime("%Y-%m-%d %H:%M:%S") if rec.submission_date else '',
                })

            return self._make_json_response({
                'success': True,
                'count': len(requests_list),
                'requests': requests_list
            })

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
            _logger.error(f"Erreur récupération demandes de certification : {str(e)}")
            return self._make_json_response({'success': False, 'error': str(e)}, status=500)

    @http.route('/api/certification_request/list/detail/<int:request_id>', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def get_certification_request_detail(self, request_id, **kwargs):
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
            if not user.exists() or not user.partner_id:
                response = request.make_json_response({
                    "success": False,
                    "message": "Utilisateur ou partenaire introuvable"
                })
                response.headers.update(cors_headers)
                return response

            # ID du partenaire de l'utilisateur
            operator_partner_id = request.env['certification.operator'].sudo().search([
                ('user_id', '=', user.id),
                ('actif', '=', True) 
            ], limit=1)

            # On filtre par l'ID de l'utilisateur qui fait la requête (sécurité)
            rec = request.env['certification.request'].sudo().search([
                ('id', '=', request_id),
                # --- FILTRE CORRIGÉ : Utilisation de operator_id ---
                ('operator_id', '=', operator_partner_id.id) 
            ], limit=1)
            
            if not rec.exists():
                response = request.make_json_response({
                    'success': False,
                    'error': f"Demande {request_id} introuvable ou non autorisée.",
                    'code': 404
                }, status=200)
                response.headers.update(cors_headers)
                return response

            data = {
                'id': rec.id,
                'reference': rec.name,
                'operator': rec.operator_id.name if rec.operator_id else '',
                'parcelle_reference': rec.parcelle_id.parcelle_name if rec.parcelle_id else '',
                'variete_semence': rec.parcelle_variete,
                'plan_culture': rec.agricole_campain,
                'superficie': rec.parcelle_superficie,
                'etat': rec.state,
                'date_soumission': rec.submission_date.strftime("%Y-%m-%d %H:%M:%S") if rec.submission_date else '',
                'localisation': {
                    'region_id': rec.region_id.id if rec.region_id else '',
                    'departement_id': rec.departement_id.id if rec.departement_id else '',
                    'arrondissement_id': rec.arrondissement_id.id if rec.arrondissement_id else '',
                    'localite': rec.localite_id,
                    'campagne_agricole': rec.agricole_campain,
                    'structure_encadrement': rec.encadrement_structure,
                },
                'documents': {
                    'declaration_activite_semenciere_timbre': rec.declaration_activite_semenciere_timbre_filename,
                    'redevance_semenciere_payement_receipt': rec.redevance_semenciere_payement_receipt_filename,
                },
                'verifications': {
                    'declaration_activite_semenciere_verified': rec.declaration_activite_semenciere_verified,
                    'payement_receipt_verified': rec.payement_receipt_verified,
                    'comment': rec.documents_verfication_comment,
                    'tous_verifies': rec.all_documents_verified
                }
            }

            return self._make_json_response({'success': True, 'request': data})

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
            _logger.error(f"Erreur détail demande certification : {str(e)}")
            return self._make_json_response({'success': False, 'error': str(e)}, status=500)