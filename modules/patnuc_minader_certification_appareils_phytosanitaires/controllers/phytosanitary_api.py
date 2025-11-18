# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools import config
from odoo.exceptions import ValidationError, AccessError
import json
import logging
import base64
import jwt
import zipfile
import io
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)
ORIGIN_LOCAL = 'http://localhost:5173'
ORIGIN_TEST = 'http://localhost:8083'
SECRET_KEY = config.get('jwt_secret')
SESSION_DURATION = 60 * 60 * 24 * 365 * 5  # 5 jours

EQUIPMENT_FIELDS = [
    'equipment_name', 'brand', 'model', 'equipment_type', 
    'capacity', 'pressure_max', 'flow_rate', 'power_source', 
    'foreign_certifications', 'country_origin', 'manufacturing_date'
]
# Mapping des noms de champs de l'API vers les noms du modèle Odoo
EQUIPMENT_FIELD_MAP = {
    'equipment_name': 'name',
    'brand': 'brand',
    'model': 'model',
    'equipment_type': 'equipment_type',
    'capacity': 'capacity',
    'pressure_max': 'pressure_max',
    'flow_rate': 'flow_rate',
    'power_source': 'power_source',
    'foreign_certifications': 'foreign_certifications',
    'country_origin': 'country_origin', # Nécessite un ID de pays
    'manufacturing_date': 'manufacturing_date',
}

class PhytosanitaryController(http.Controller):

    def _make_options_response(self):
        """Réponse pour les requêtes OPTIONS (CORS)"""
        headers = [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Access-Control-Max-Age', '3600')
        ]
        return request.make_response('', headers=headers)

    def _make_json_response(self, data, status=200):
        """Réponse JSON standardisée avec CORS"""
        headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ]
        return request.make_response(json.dumps(data), headers=headers)

    def _cors_headers(self):
        origin = request.httprequest.headers.get('Origin') or "http://localhost:8080"
        return {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true'
        }
    @http.route('/api/phytosanitary_certification/files/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def download_multiple_files(self, procedure_id, **kwargs):
        cors_headers = [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
            ('Access-Control-Allow-Headers', '*')
        ]

        # Préflight
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=cors_headers)

        try:
            # ─── 1. Vérification du token JWT ──────────────────────────────
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return request.make_json_response({"error": "Token manquant"}, status=401)

            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            env = request.env(user=request.env['res.users'].sudo().browse(user_id))

            # ─── 2. Récupérer la procédure ────────────────────────────────
            procedure = env['phytosanitary.certification.request'].search([
                ('id', '=', procedure_id),
                ('user_id', '=', user_id)
            ], limit=1)

            if not procedure:
                return request.make_json_response({"error": "Procédure introuvable"}, status=404)

            # ─── 3. Préparer le ZIP ───────────────────────────────────────
            zip_buffer = io.BytesIO()
            zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

            # Exemple : ajouter plusieurs fichiers issus du modèle
            files_to_export = [
                ('official_request_letter', 'official_request_letter_filename'),
                ('homologation_certificate', 'homologation_certificate_filename'),
                ('import_agreement_copy', 'import_agreement_copy_filename'),
                ('identity_document_copy', 'identity_document_copy_filename'),
                ('invoice_payment_cert_atp', 'invoice_payment_cert_atp_filename'),
            ]

            for field_data, field_name in files_to_export:
                data = getattr(procedure, field_data)
                filename = getattr(procedure, field_name)

                if data and filename:
                    zip_file.writestr(filename, base64.b64decode(data))

            zip_file.close()

            # ─── 4. Retourner le ZIP ──────────────────────────────────────
            response = request.make_response(
                zip_buffer.getvalue(),
                headers=[
                    ('Content-Type', 'application/zip'),
                    ('Content-Disposition', f'attachment; filename="procedure_{procedure_id}.zip"'),
                ]
            )

    
            return response

        except Exception as e:
            return request.make_json_response({"error": str(e)}, status=500)
    
    @http.route('/api/phytosanitary_certification/download/<int:procedure_id>', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
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
            procedure = request.env['phytosanitary.certification.request'].sudo().search([
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
            authorized_states = ['certificate_signed', 'approved']
            if procedure.state not in authorized_states:
                return self._make_json_response({
                    "success": False,
                    "message": f"Le certificat n'est pas encore disponible pour le téléchargement. État actuel: {procedure.state}",
                    "code": 400
                }, status=400)
            #load files 
            file_data_b64 = procedure.certificat_signed
            file_name = procedure.certificat_signed_filename

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

    
    
    @http.route('/api/phytosanitary_certification/create', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def create_v1_phytosanitary_certification_request(self, **kwargs):
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
            
            # Définir l'environnement Odoo comme l'utilisateur authentifié
            current_env = request.env(user=user)
            data = request.params


            # 3. Récupération ou Création de l'équipement
            equipment_id = data.get('equipment_id')
            equipment_name = data.get('equipment_name')

            # si l'equipment existe
            if equipment_id:
                # L'équipement existant est fourni
                equipment = current_env['phytosanitary.equipment'].sudo().browse(int(equipment_id))
                if not equipment.exists():
                    return self._make_json_response({
                        "success": False,
                        "error": f"Équipement (ID: {equipment_id}) introuvable",
                        "code": 404
                    }, status=404)
            
            elif equipment_name:
                # Tente de chercher un équipement existant par nom
                equipment = current_env['phytosanitary.equipment'].sudo().search([('name', '=', equipment_name)], limit=1)
                
                if not equipment:
                    # L'équipement n'existe pas, on procède à la création dynamique
                    
                    equipment_vals = {}
                    for api_field, odoo_field in EQUIPMENT_FIELD_MAP.items():
                        if api_field in data and data[api_field]:
                            # Gérer les types spécifiques si nécessaire (ex: convertir en float/int)
                            if odoo_field in ['capacity', 'pressure_max', 'flow_rate']:
                                try:
                                    equipment_vals[odoo_field] = float(data[api_field])
                                except ValueError:
                                    # Ignorer si la valeur n'est pas un nombre valide
                                    pass
                            # Pour le pays d'origine, on attend soit l'ID soit le nom, mais pour simplifier, on prend l'ID si le champ est 'country_origin'
                            elif odoo_field == 'country_origin':
                                try:
                                     # Supposons que l'API envoie l'ID du pays
                                    country_id = int(data[api_field])
                                    country = current_env['res.country'].sudo().browse(country_id)
                                    if country.exists():
                                        equipment_vals[odoo_field] = country_id
                                except:
                                     # Ignorer si l'ID est invalide ou non présent
                                     pass
                            else:
                                equipment_vals[odoo_field] = data[api_field]

                    # Le nom est essentiel
                    if 'name' not in equipment_vals:
                         equipment_vals['name'] = equipment_name

                    # Vérifier si on a au moins le nom et le type d'équipement pour créer un record valide (le type est required dans le modèle)
                    if 'equipment_type' not in equipment_vals or not equipment_vals['equipment_type']:
                        # Si le type manque (et qu'il est required), on peut soit utiliser un type par défaut ou retourner une erreur
                        # Ici, on lève une erreur, car c'est un champ requis dans le modèle Odoo.
                         return self._make_json_response({
                            "success": False,
                            "error": "Le champ 'equipment_type' est requis pour la création d'un nouvel équipement.",
                            "code": 400
                        }, status=400)


                    # Création effective du nouvel équipement
                    equipment = current_env['phytosanitary.equipment'].sudo().create(equipment_vals)
                   
                
                # Récupère l'ID après recherche ou création
                equipment_id = equipment.id

            else:
                # Ni equipment_id, ni equipment_name n'est fourni
                 return self._make_json_response({
                    "success": False,
                    "error": "L'équipement est manquant. Veuillez fournir 'equipment_id' ou 'equipment_name' ainsi que 'equipment_type' pour la création.",
                    "code": 400
                }, status=400)


            # 4. Préparation des valeurs pour la demande de certification
            vals = {
                'user_id': user.id,
                'equipment_id': equipment_id,
                'legal_representative': data.get('legal_representative'),
                # Ajoutez ici d'autres champs de la demande de certification que vous voulez exposer
            }
            # Gestion des fichiers uploadés
            file_fields = [
                'official_request_letter',
                'homologation_certificate',
                'import_agreement_copy',
                'identity_document_copy',
                'invoice_payment_cert_atp'
            ]
            max_file_size = 10 * 1024 * 1024  # 10 Mo

            for field in file_fields:
                file_data = request.httprequest.files.get(field)
                if file_data:
                    file_data.seek(0, 2)
                    file_size = file_data.tell()
                    file_data.seek(0)
                    if file_size > max_file_size:
                        response = request.make_json_response({
                            "success": False,
                            "error": f"Fichier {field} trop volumineux (max 10MB)",
                            "code": 400
                        })
                        response.headers.update(cors_headers)
                        return response
                    vals[field] = base64.b64encode(file_data.read()).decode('utf-8')
                    vals[f"{field}_filename"] = file_data.filename

            
            # 5. Création et soumission du record de certification
            record = current_env['phytosanitary.certification.request'].sudo().create(vals)
            record.sudo().action_submit()

            # 6. Génération du token de session et de la réponse
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=SESSION_DURATION)

            return self._make_json_response({
                "success": True,
                "data": {
                    "message": "Demande de certification créée et soumise avec succès",
                    "request_id": record.id,
                    "reference": record.name,
                    "state": record.state,
                    "user_id": user.id,
                    "equipment_id": equipment_id,
                    "equipment_name": equipment.name,
                    "expires_in": SESSION_DURATION,
                    "expires_at": expires_at.isoformat() + "Z",
                },
                "code": 200
            })

        # --- Gestion des erreurs (conservée) ---
        except ValidationError as ve:
            return self._make_json_response({
                "success": False,
                "error": str(ve),
                "code": 400
            }, status=400)

        except jwt.ExpiredSignatureError:
            return self._make_json_response({
                "success": False,
                "message": "Token expiré",
                "code": 401
            }, status=401)

        except jwt.InvalidTokenError:
            return self._make_json_response({
                "success": False,
                "message": "Token invalide",
                "code": 401
            }, status=401)

        except Exception as e:
            _logger.error("Erreur lors de la création de la demande de certification: %s", str(e), exc_info=True)
            return self._make_json_response({
                "success": False,
                "error": f"Erreur interne : {str(e)}",
                "code": 500
            }, status=500)
        
    #controler appareils list 
    @http.route('/api/equipment/list', type='http', auth='public', methods=['GET', 'OPTIONS'], csrf=False)
    def list_equipments(self, **kwargs):
     
        
        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=self._cors_headers())

        try:
            equipments = request.env['phytosanitary.equipment'].sudo().search([])
            equipment_list = []
            for equip in equipments:
                # Utilisation des champs pertinents pour l'affichage public
                equipment_list.append({
                    'id': equip.id,
                    'name': equip.name,
                    'brand': equip.brand,
                    'model': equip.model,
                    'type': equip.equipment_type,
                    'capacity': equip.capacity,
                })

            return self._make_json_response({
                "success": True,
                "data": equipment_list,
                "count": len(equipment_list)
            })
            
        except Exception as e:
            _logger.error("Erreur lors de la récupération des équipements : %s", str(e))
            return self._make_json_response({
                "success": False,
                "error": "Erreur interne du serveur lors de la récupération des équipements.",
                "details": str(e),
                "code": 500
            }, status=500)


    @http.route('/api/phytosanitary_certification/list', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def list_phytosanitary_certifications(self, **kwargs):
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
            # get demandes patner_id
            demandes = request.env['phytosanitary.certification.request'].sudo().search([
                ('user_id', '=', user.id)
            ], order='create_date desc')

            data = []
            for d in demandes:
                data.append({
                    "id": d.id,
                    "reference": d.name,
                    "etat": d.state,
                    'date_soumission': d.submission_date.strftime('%Y-%m-%d') if d.submission_date else None,
                    "appareil": d.equipment_id.name if d.equipment_id else '',
                    "representant_legal": d.legal_representative or '',
                    "verification_admin": "Oui" if d.all_documents_verified else "Non"
                })

            response = request.make_json_response({
                "success": True,
                "data": data,
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
            _logger.exception("Erreur dans /api/phytosanitary_certification/list")
            response = request.make_json_response({
                "success": False,
                "error": str(e),
                "code": 500
            })
            response.headers.update(cors_headers)
            return response

    @http.route('/api/phytosanitary_certification/list/detail/<int:record_id>', type='http', auth='none', methods=['GET', 'OPTIONS'], csrf=False)
    def phytosanitary_certification_detail(self, record_id, **kwargs):
        cors_headers = self._cors_headers()

        """Récupérer le détail complet d'une demande"""

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
            #
            demande = request.env['phytosanitary.certification.request'].sudo().search([
                ('id', '=', record_id),
                ('user_id', '=', user.id)
            ], limit=1)

            if not demande:
                response = request.make_json_response({
                    "success": False,
                    "message": "Demande introuvable ou non autorisée",
                    "code": 404
                })
                response.headers.update(cors_headers)
                return response

            detail = {
                "id": demande.id,
                "reference": demande.name,
                "etat": demande.state,
                'date_soumission': demande.submission_date.strftime('%Y-%m-%d') if demande.submission_date else None,
                "type_appareil": demande.equipment_id.equipment_type,
                "representant_legal": demande.legal_representative,
                "appareil": demande.equipment_id.name if demande.equipment_id else '',
                "attestation_homologation": bool(demande.homologation_certificate),
                "lettre_demande_officielle": bool(demande.official_request_letter),
                "copie_agrement_importation": bool(demande.import_agreement_copy),
                "piece_identite": bool(demande.identity_document_copy),
                "tous_docs_verifies": demande.all_documents_verified,
                "commentaire_verification": demande.admin_verification_comment or '',
                "note_technique": demande.technical_instruction_note or '',
                #"resultat_evaluation": demande.technical_evaluation_result or '',
                "motif_rejet": demande.rejection_reason or '',
                "certificat_numero": demande.certificate_number or '',
                "validite_debut": str(demande.certificate_validity_start) if demande.certificate_validity_start else '',
                "validite_fin": str(demande.certificate_validity_end) if demande.certificate_validity_end else '',
                "is_signed": demande.is_signed,
            }

            response = request.make_json_response({
                "success": True,
                "data": detail,
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
            _logger.exception("Erreur dans /api/phytosanitary_certification/detail")
            response = request.make_json_response({
                "success": False,
                "error": str(e),
                "code": 500
            })
            response.headers.update(cors_headers)
            return response
