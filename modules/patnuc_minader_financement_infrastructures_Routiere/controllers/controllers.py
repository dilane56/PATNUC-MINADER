# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.tools import config
from odoo.exceptions import UserError, ValidationError
import base64
import logging
import jwt
from datetime import datetime, timedelta
import json
_logger = logging.getLogger(__name__)

SECRET_KEY = config.get('jwt_secret')

ORIGIN_LOCAL = 'http://localhost:5173'
ORIGIN_TEST = 'http://localhost:8083'
SESSION_DURATION = 60 * 60 * 24 * 365 * 5  # 5 jours



class MinaderFinancementDemandeController(http.Controller) :
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
    @http.route('/api/financing_request/create', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_request_financing(self, **kwargs):
        cors_headers = self._cors_headers()

        # Réponse CORS préflight
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # --- Vérification du token JWT ---
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return self._make_json_response({
                    "success": False,
                    "message": "Token JWT manquant ou mal formé."
                }, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = request.env['res.users'].sudo().browse(user_id)

            if not user.exists():
                return self._make_json_response({
                    "success": False,
                    "message": "Utilisateur introuvable."
                }, status=401)

            request.env = request.env(user=user)
            data = request.params

            #get commune by user.id
            commune_id =  request.env['infrastructure.commune'].sudo().search([('resp_commune', '=', user.id)], limit=1)
            if not commune_id :
                return self._make_json_response({
                    "success": False,
                    "message": "Aucune commune associé a votre compte."
                }, status=400)

            # --- Vérification des champs requis ---
            required_fields = ['project_description','project_title', 'localite_id','infrastructure_type','estimated_budget']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return self._make_json_response({
                    "success": False,
                    "error": f"Champs obligatoires manquants : {', '.join(missing_fields)}"
                }, status=400)

            # --- Préparation des valeurs à créer ---

            vals = {
                'project_title':data.get('project_title'),
                'localite_id' : data.get('localite_id'),
                'infrastructure_type': data.get('infrastructure_type'),
                'estimated_budget' : int(data.get('estimated_budget')),
                'project_description' : data.get('project_description'),
                'commune_id':commune_id.id,
                'state':'verification',
            }

            # --- Gestion des fichiers binaires ---
            file_fields = {
                'official_request_file': 'official_request_filename',
                'location_plan_file': 'location_plan_filename',
                'communal_commitment_file': 'communal_commitment_filename',
                'environmental_impact_file': 'environmental_impact_filename',
            }

            max_file_size = 15 * 1024 * 1024  # 15 MB

            for field, filename_field in file_fields.items():
                file_data = request.httprequest.files.get(field)
                if not file_data:
                    continue

                file_data.seek(0, 2)
                file_size = file_data.tell()
                file_data.seek(0)
                if file_size > max_file_size:
                    return self._make_json_response({
                        "success": False,
                        "error": f"Fichier {field} trop volumineux (max 15MB)"
                    }, status=400)

                vals[field] = base64.b64encode(file_data.read()).decode('utf-8')
                vals[filename_field] = file_data.filename

            # --- Création de la demande ---
            record = request.env['infrastructure.financing.request'].sudo().create(vals)
            record.sudo().action_submit()  # Passage automatique à l’état “verification”

            # --- Réponse de succès ---
            expires_at = datetime.utcnow() + timedelta(seconds=SESSION_DURATION)

            response = {
                "success": True,
                "data": {
                    "message": f"Demande de financement pour la commune {commune_id.name} soumise avec succès.",
                    "record_id": record.id,
                    "reference": record.name,
                    "state": record.state,
                    "responsable_commune": user.id,
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
            return self._make_json_response({
                "success": False,
                "error": str(e),
                "code": 400
            }, status=400)

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
            _logger.exception("Erreur interne lors de la création d’une demande de financement.")
            return self._make_json_response({
                "success": False,
                "error": "Erreur interne du serveur",
                "details": str(e),
                "code": 500
            }, status=500)

    @http.route('/api/financing_request/list', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def list_request_financing(self, **kwargs) :
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
            #  get financing request
            financing_requests = request.env['infrastructure.financing.request'].sudo().search([
                ('commune_id.resp_commune', '=', user.id)
            ], order='create_date desc')

            financing_list = []

            for h in financing_requests:
                financing_list.append({
                    'id': h.id,
                    'reference': h.name,
                    'localite':h.localite_id,
                    'responsable_commune': h.commune_id.resp_commune.name,
                    'titre_projet': h.project_title,
                    'description_projet' : h.project_description,
                    'type_projet': h.infrastructure_type,
                    'budget_projet' : h.estimated_budget,
                    'etat': h.state,
                    'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,

                })

            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': True, 'data': financing_list}),
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
            _logger.error(f"Erreur récupération demandes financement: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )


    @http.route('/api/financing_request/list/detail/<int:request_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def list_detail_request_financing(self, request_id , **kwargs) :
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
            h = request.env['infrastructure.financing.request'].sudo().search([
                ('id', '=', request_id),
                ('commune_id.resp_commune', '=', user.id)
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
                'responsable_commune': h.commune_id.resp_commune.name,
                'localite': h.localite_id,
                'titre_projet': h.project_title,
                'description_projet' : h.project_description,
                'type_projet': h.infrastructure_type,
                'budget_projet' : h.estimated_budget,
                'date_soumission': h.submission_date.strftime('%Y-%m-%d') if h.submission_date else None,

                'note_revue': h.review_notes,
                'date_revue': h.review_date,
                'revue_complete':h.is_review_complete,
                'retour_motif': h.return_reason,
                'documents_requis_complet' : h.required_documents_complete ,
                'note_conformite': h.conformity_notes,
                'avis_technique': h.avis_technique,
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
            _logger.error(f"Erreur détail financement: {str(e)}")
            headers = [
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Origin', '*'),
            ]
            return request.make_response(
                json.dumps({'success': False, 'error': str(e)}),
                headers=headers
            )
