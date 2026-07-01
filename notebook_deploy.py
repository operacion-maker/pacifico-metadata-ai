# MAGIC %md
# MAGIC # 🚀 Despliegue del Agente MetaBuilder (MLflow 3.0)
# MAGIC 
# MAGIC Este notebook empaca el `MetadataGovernanceAgent` como un modelo PyFunc y lo despliega
# MAGIC como un Endpoint de Model Serving en Databricks.
# MAGIC 
# MAGIC **Requisitos:**
# MAGIC - MLflow 2.13+ (MLflow 3.0 standard para Agentes)
# MAGIC - Databricks SDK

# COMMAND ----------

# MAGIC %pip install mlflow>=2.13.0 databricks-sdk langgraph langchain-core langchain-databricks
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import os
import time
import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

# Importar el agente desde nuestro archivo agent.py
from agent import MetadataGovernanceAgent

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Configuración de Unity Catalog y MLflow

# COMMAND ----------

# Configurar Unity Catalog como el registro de MLflow
mlflow.set_registry_uri("databricks-uc")

# Define tu catálogo y esquema
catalog_name = "main"    # <-- Cambia esto si usas otro catálogo
schema_name = "default"  # <-- Cambia esto si usas otro esquema
model_name = f"{catalog_name}.{schema_name}.metabuilder_agent"
endpoint_name = "metabuilder-endpoint"

print(f"Model Name: {model_name}")
print(f"Endpoint Name: {endpoint_name}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Registro del Modelo (Model Tracking)

# COMMAND ----------

with mlflow.start_run() as run:
    # Empacar el modelo con las dependencias exactas
    model_info = mlflow.pyfunc.log_model(
        artifact_path="agent_model",
        python_model=MetadataGovernanceAgent(),
        pip_requirements=[
            "mlflow>=2.13.0",
            "langgraph>=0.2.0",
            "langchain-core>=0.3.0",
            "langchain-databricks>=0.1.0"
        ],
        input_example={
            "messages": [{"role": "user", "content": "main.default.my_table"}],
            "custom_inputs": {"thread_id": "12345"}
        }
    )

print(f"Modelo registrado localmente en: {model_info.model_uri}")

# Registrar el modelo en Unity Catalog
registered_model = mlflow.register_model(
    model_uri=model_info.model_uri,
    name=model_name
)

print(f"✅ Modelo {model_name} versión {registered_model.version} registrado en Unity Catalog.")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Despliegue a Model Serving Endpoint

# COMMAND ----------

w = WorkspaceClient()

# Comprobar si el endpoint ya existe
try:
    w.serving_endpoints.get(endpoint_name)
    endpoint_exists = True
except Exception:
    endpoint_exists = False

served_entity = ServedEntityInput(
    entity_name=model_name,
    entity_version=registered_model.version,
    workload_size="Small",
    scale_to_zero_enabled=True
)

if endpoint_exists:
    print(f"Actualizando el endpoint existente '{endpoint_name}' con la versión {registered_model.version}...")
    w.serving_endpoints.update_config_and_wait(
        name=endpoint_name,
        served_entities=[served_entity]
    )
else:
    print(f"Creando nuevo endpoint '{endpoint_name}'...")
    w.serving_endpoints.create_and_wait(
        name=endpoint_name,
        config=EndpointCoreConfigInput(
            served_entities=[served_entity]
        )
    )

print(f"🚀 ¡El endpoint '{endpoint_name}' está listo y operando con la última versión!")
