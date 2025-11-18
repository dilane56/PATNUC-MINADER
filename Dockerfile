FROM odoo:17.0

USER root

# Installer PyJWT
RUN pip3 install PyJWT

USER odoo