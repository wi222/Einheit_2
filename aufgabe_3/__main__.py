import pulumi
import os
from pulumi_azure_native import resources, storage, web, insights
from pulumi import FileAsset, Output

# **1. Ressourcengruppe erstellen**
resource_group = resources.ResourceGroup("uebung3-resourcegroup", location="switzerlandnorth")

# **2. Storage-Account erstellen**
# wird benötigt zur Speicherung von Daten
storage_account = storage.StorageAccount(
    "storageaccount",
    resource_group_name=resource_group.name,  # Verknüpft mit der Ressourcengruppe
    location=resource_group.location,  # Gleicher Standort wie die Ressourcengruppe
    sku=storage.SkuArgs(name="Standard_LRS"),  # Standard Storage-Tarif
    kind="StorageV2",  # Moderner Storage-Typ für allgemeine Nutzung
    allow_blob_public_access=True  # Aktiviert öffentlichen Zugriff auf Blobs
)

# **3. Blob-Container erstellen**
blob_container = storage.BlobContainer(
    "blobcontainer",
    account_name=storage_account.name,  # Verknüpft mit dem Storage-Account
    resource_group_name=resource_group.name,  # Verknüpft mit der Ressourcengruppe
    public_access="Blob"  # Ermöglicht öffentlichen Lesezugriff auf die Blobs
)

# **4. ZIP-Datei erstellen**
# Nur den Inhalt des clco-demo-Ordners zippen
os.system('cd clco-demo && zip -r ../webapp.zip .')

# **5. ZIP-Datei in Blob-Container hochladen**
app_blob = storage.Blob(
    "webappzip",
    resource_group_name=resource_group.name,  # Verknüpft mit der Ressourcengruppe
    account_name=storage_account.name,  # Verknüpft mit dem Storage-Account
    container_name=blob_container.name,  # Verknüpft mit dem Blob-Container
    source=FileAsset("./webapp.zip")  
)

# **6. Blob-URL generieren**
blob_url = pulumi.Output.concat(
    "https://", storage_account.name, ".blob.core.windows.net/", blob_container.name, "/", app_blob.name
)

# **7. App Service Plan erstellen**
app_service_plan = web.AppServicePlan(
    "serviceplan",
    resource_group_name=resource_group.name,  # Verknüpft mit der Ressourcengruppe
    location=resource_group.location,  # Standort der Ressourcengruppe
    kind="Linux",  
    reserved=True,  
    sku=web.SkuDescriptionArgs(
        tier="Basic",
        name="B1",
    )
)

# **8. Web-App erstellen**
web_app = web.WebApp(
    "webapp",
    resource_group_name=resource_group.name,  # Verknüpft mit der Ressourcengruppe
    location=resource_group.location,  # Gleicher Standort wie die Ressourcengruppe
    server_farm_id=app_service_plan.id,  # Verknüpft mit dem App Service Plan
    site_config=web.SiteConfigArgs(  # Konfiguration der Laufzeitumgebung
        linux_fx_version='PYTHON|3.9',  # Laufzeitumgebung: Python 3.9
        app_settings=[  # Umgebungsvariablen der Web-App
            web.NameValuePairArgs(
                name="WEBSITE_RUN_FROM_PACKAGE",  # App läuft direkt von der ZIP-Datei
                value=blob_url  # URL zur ZIP-Datei
            ),
        ]
    ),
    https_only=True  # HTTPS-Zugriff erzwingen
)

# URL exportieren
pulumi.export("web_app_url", Output.concat("http://", web_app.default_host_name))
