# MAGIC %md
# MAGIC # 🧪 Validación del Endpoint MetaBuilder
# MAGIC 
# MAGIC Este notebook consulta el Endpoint de Model Serving de Databricks para probar
# MAGIC la generación del pipeline y el soporte de streaming.
# MAGIC 
# MAGIC **Nota**: Asegúrate de que el endpoint `metabuilder-endpoint` esté en estado `Ready`
# MAGIC antes de ejecutar este script.

# COMMAND ----------

# MAGIC %pip install requests databricks-sdk
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import requests
import json
import uuid
from databricks.sdk import WorkspaceClient

# Configuración
endpoint_name = "metabuilder-endpoint"
workspace_url = WorkspaceClient().config.host
token = WorkspaceClient().config.token

# La URL de Invocación
invoke_url = f"{workspace_url}/serving-endpoints/{endpoint_name}/invocations"

print(f"🔗 Endpoint URL: {invoke_url}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Prueba de Flujo Inicial (FQN)

# COMMAND ----------

# Generar un thread_id único para la sesión
test_thread_id = str(uuid.uuid4())
print(f"Thread ID: {test_thread_id}")

payload = {
    "messages": [
        {"role": "user", "content": "main.default.my_test_table"}
    ],
    "custom_inputs": {
        "thread_id": test_thread_id
    }
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    # Solicitamos Server-Sent Events (streaming)
    "Accept": "text/event-stream"
}

print("Iniciando solicitud HTTP (Streaming)...")
response = requests.post(invoke_url, json=payload, headers=headers, stream=True)

if response.status_code != 200:
    print(f"❌ Error {response.status_code}: {response.text}")
else:
    print("✅ Conectado exitosamente. Recibiendo stream:\n")
    print("-" * 60)
    for chunk in response.iter_lines(decode_unicode=True):
        if chunk:
            print(chunk)
    print("-" * 60)
    print("\n✅ Flujo Inicial Completado.")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Prueba de Reanudación (HITL Resume)
# MAGIC 
# MAGIC Una vez que el pipeline se pausa en `human_review`, podemos reanudarlo
# MAGIC enviando una decisión (ej. `approve` o `reject`) al mismo `thread_id`.

# COMMAND ----------

resume_payload = {
    "messages": [], # No necesitamos mandar mensajes nuevos
    "custom_inputs": {
        "thread_id": test_thread_id,
        "decision": "approve",
        "feedback": "Los comentarios lucen bien, procede a Unity Catalog."
    }
}

print("Enviando decisión de aprobación (Streaming)...")
resume_response = requests.post(invoke_url, json=resume_payload, headers=headers, stream=True)

if resume_response.status_code != 200:
    print(f"❌ Error {resume_response.status_code}: {resume_response.text}")
else:
    print("✅ Conectado exitosamente. Recibiendo stream de reanudación:\n")
    print("-" * 60)
    for chunk in resume_response.iter_lines(decode_unicode=True):
        if chunk:
            print(chunk)
    print("-" * 60)
    print("\n✅ Flujo de Aprobación Completado.")
