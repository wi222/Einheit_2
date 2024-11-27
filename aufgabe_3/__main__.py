import pulumi
from pulumi_azure_native import resources, storage, web, insights

# **1. Ressourcengruppe erstellen**
resource_group = resources.ResourceGroup("uebung3-resourcegroup", location="westeurope")

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



# **4. App Service Plan erstellen**
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

# **5. Application Insights hinzufügen**
app_insights = insights.Component(
    "appinsights",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    application_type="web",
    kind="web",
    ingestion_mode="ApplicationInsights"
)

# **6. Web-App erstellen**
web_app_name = "myUniqueWebAppName"
github_repo_url = "https://github.com/dmelichar/clco-demo"
branch_name = "main"

web_app = web.WebApp(
    web_app_name,
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        linux_fx_version='PYTHON|3.9',  
        app_settings=[
            web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key
            ),
            web.NameValuePairArgs(
                name="FLASK_ENV",
                value="development"
            ),
            web.NameValuePairArgs(
                name="FLASK_DEBUG",
                value="1"
            )
        ]
    ),
    https_only=True, 
    opts=pulumi.ResourceOptions(depends_on=[app_service_plan])
)

# **7. Quellcodeverwaltung konfigurieren**
source_control = web.WebAppSourceControl(
    "sourceControl",
    resource_group_name=resource_group.name,
    name=web_app.name,
    repo_url=github_repo_url,
    branch=branch_name,
    is_manual_integration=False,
    opts=pulumi.ResourceOptions(depends_on=[web_app])
)

# URL exportieren
pulumi.export("web_app_url", pulumi.Output.concat("https://", web_app.default_host_name))
