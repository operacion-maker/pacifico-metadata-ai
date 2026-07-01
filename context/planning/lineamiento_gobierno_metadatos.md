# Guía Operativa de Definición de Metadatos

**Versión:** V1.1 | **Fecha:** Mayo 2026

---

## Objetivo

El objetivo de describir correctamente los metadatos es asegurar que los datos sean comprendidos de manera uniforme en toda la organización, proporcionando claridad sobre su significado, propósito, nivel de detalle y contexto, lo que permite mejorar su uso, facilitar su integración y apoyar la toma de decisiones basada en información confiable.

### Beneficios del uso correcto de metadatos

- Mejora la comprensión del dato
- Evita interpretaciones erróneas o inconsistentes
- Facilita la integración entre sistemas y fuentes
- Apoya la gobernanza y estandarización de datos
- Mejora la confianza en la información
- Potencia la toma de decisiones basada en datos

---

## Tipos de Metadatos

> **Recuerda:** No todos los metadatos son iguales; su correcta clasificación y definición es clave para su uso adecuado.

### Metadatos Técnicos

- Nombre físico del objeto (tabla, campo, vista)
- Tipo de dato, longitud y formato
- Origen y destino del dato
- Catálogos, esquema y entorno
- Reglas técnicas de transformación y cálculo
- Frecuencia de actualización o carga
- Relaciones técnicas (llaves primarias y foráneas)

### Metadatos Funcionales

- Nombre con el que es conocido el activo en el negocio
- Definición funcional clara y comprensible
- Descripción del uso del dato (procesos, reportes, análisis)
- Reglas de negocio asociadas
- Dominio de valores permitido
- Valores especiales o excepciones
- Dominio o área responsable
- Relación con términos del Glosario de Negocio

---

## Pilares de Metadatos Funcionales

Los metadatos funcionales se construyen sobre cuatro pilares fundamentales que deben respetarse en toda definición.

### 1. Claridad y Comprensión

Las definiciones deben ser claras, precisas y comprensibles, evitando ambigüedades. Todo término técnico debe ser explicado para asegurar una correcta interpretación del dato por parte de los usuarios.

### 2. Propósito del Dato

Los metadatos deben proporcionar el contexto de negocio del dato, describiendo para qué se utiliza dentro de la organización y cuál es su valor, permitiendo comprender claramente su uso esperado.

### 3. Nivel de Detalle

El nivel de detalle describe el contenido, alcance y condiciones del dato, incluyendo escenarios de uso, excepciones y particularidades relevantes.

### 4. Contexto y Relacionamiento

Los metadatos deben describir el contexto del dato, sus relaciones y su rol dentro del ecosistema de información de la organización.

### Consideraciones opcionales para definir

- Reglas o lógicas de negocios relevantes
- Reglas o lógicas particulares de negocios
- Dominio de valores
- Información adicional relevante
- Observaciones de Calidad de Datos
- Ejemplos

---

## Preguntas Clave para Metadatos Funcionales por Tipo de Activo

### Tablas

#### 1. Claridad y comprensión
- ¿Qué representa esta tabla en términos de negocio?
- ¿Qué tipo de tabla es? (hechos, dimensión, maestro, data entry, etc.)
- ¿Existen términos técnicos que deban aclararse?
- ¿Con qué frecuencia se actualiza la información?

#### 2. Propósito del Dato
- ¿Para qué se usa esta tabla en el negocio?
- ¿Qué proceso(s) de negocio habilita o impacta?
- ¿Quién(es) la utilizan?

#### 3. Nivel de Detalle
- ¿Qué productos de datos, modelos analíticos o soluciones la utilizan?
- ¿Incluye información histórica o solo estado actual?
- ¿Existen reglas relevantes que definan su alcance o interpretación?

#### 4. Contexto y Relacionamiento
- ¿De qué fuentes o sistemas proviene la información?
- ¿Con qué otras tablas o activos de datos se relaciona?
- ¿Cómo se integra dentro del ecosistema de datos?

**Consideraciones opcionales:** Ejemplos | Observaciones de Calidad de Datos | Información adicional relevante

**Ejemplo de definición funcional aplicada — Tabla `ScoreBuro`:**

> Representa un score de riesgo que permite evaluar a los clientes o relacionados con Pacífico según su nivel de riesgo. Es una tabla con variables analíticas que se almacenan en UM/HM con frecuencia mensual. Se utiliza para evaluar el nivel de riesgo de personas y facilitar su segmentación, apoyando gestión de riesgo, segmentación de clientes, evaluación de comportamiento y procesos analíticos asociados a riesgo. La utilizan principalmente Data Scientists en modelos de Machine Learning orientados a riesgo. Incluye un enfoque histórico y transversal, ya que considera el comportamiento en un periodo determinado y no solo el estado actual. El campo ScoreBuro permite el cálculo de campos como flag y de evaluación que contribuyen al modelo de ML. Proviene de fuentes corporativas internas y fuentes core Pacífico, y se relaciona con `md_dac_persona`. Se integra como un componente analítico dentro del ecosistema de Data & Analytics, funcionando como input para modelos.

---

### Campos

#### 1. Claridad y comprensión
- ¿Qué permite identificar, clasificar o medir?
- ¿Qué reglas de negocio aplica?

#### 2. Propósito del Dato
- ¿Para qué sirve este dato dentro del negocio?
- ¿Qué decisiones se apoyan en este dato?

#### 3. Nivel de Detalle
- ¿Cuál es el dominio de valores esperado y qué significa cada uno?
- ¿Es un valor único por entidad o puede haber múltiples?
- ¿El dato es obligatorio o puede estar vacío?
- ¿El dato es calculado o derivado?
- ¿Qué campos o fuentes participan en su cálculo?

#### 4. Contexto y Relacionamiento
- ¿Está basado en algún estándar o clasificación externa?
- ¿Se utiliza para segmentación, scoring o reporting?
- ¿Está alineado con definiciones corporativas?

**Consideraciones opcionales:** Ejemplos | Observaciones de Calidad de Datos | Información adicional relevante

**Ejemplo de definición funcional aplicada — Campo `ScoreBuro`:**

> Permite medir el nivel de riesgo crediticio de una persona, facilitando su clasificación según su comportamiento financiero. El score se calcula mediante un modelo de regresión logística basado en Weight of Evidence (WoE). Los valores extremadamente bajos son imputados con códigos específicos (-999.9 y -999.8). Sirve para evaluar y segmentar el riesgo de clientes, apoyando análisis financieros, evaluación de riesgo crediticio, segmentación de clientes según perfil de riesgo e input en modelos analíticos o predictivos. Dominio de valores: -999.9 / -999.8 representan valores imputados para casos extremos; nulos indican ausencia de información; valores numéricos representan el nivel de riesgo. Es un valor único por persona y periodo de evaluación. Puede estar vacío (nulo) cuando no existe información suficiente o la persona no está registrada. No es un campo calculado internamente; proviene directo de la fuente. Se basa en información proveniente del sistema financiero (SF) y en técnicas estándar de modelamiento como regresión logística y WoE. Se utiliza para scoring (cálculo del riesgo). Forma parte de los criterios corporativos de evaluación de riesgo, siendo utilizado como insumo estandarizado en procesos analíticos y modelos dentro de la organización.

---

### Producto de Datos

#### 1. Claridad y comprensión
- ¿Qué representa exactamente este producto de datos?
- ¿Existen términos técnicos que requieran definición?
- ¿Hay conceptos que puedan generar múltiples interpretaciones?

#### 2. Propósito del Dato
- ¿Qué problema de negocio resuelve este producto?
- ¿Qué decisiones de negocio o analíticas habilita?
- ¿Cuáles son los principales casos de uso asociados?
- ¿Qué roles lo utilizan?

#### 3. Nivel de Detalle
- ¿Qué tipo de datos integra?
- ¿Se utiliza alguna estandarización de variables?
- ¿Cuál es la frecuencia de actualización del producto?
- ¿Existen excepciones o consideraciones en los datos?
- ¿Qué información está disponible dentro del producto?

#### 4. Contexto y Relacionamiento
- ¿Qué dominio de datos representa?
- ¿Qué dependencias críticas presenta?

**Consideraciones opcionales:** Ejemplos | Observaciones de Calidad de Datos | Información adicional relevante

**Ejemplo de definición funcional aplicada — Producto `Feature Store`:**

> El Feature Store es una capa especializada dentro de la arquitectura de datos, materializada en un conjunto de tablas (feature tables), que centraliza las distintas fuentes de datos de entrada provenientes de los intercambios corporativos gestionados a través del Marketplace, así como datos de los sistemas core de Pacífico. Su propósito es centralizar, estandarizar, gestionar y disponibilizar las variables (features) utilizadas en los distintos modelos de Machine Learning (ML).
>
> Esta capa integra y consolida la información asegurando su homogeneización, trazabilidad y consistencia semántica. A través de procesos de transformación y enriquecimiento, los datos se convierten en features gobernadas, listas para su consumo analítico. Estas variables, previamente definidas y gestionadas, permiten a las distintas áreas del negocio reutilizarlas de manera consistente, optimizando los tiempos de desarrollo y mejorando la capacidad de respuesta ante las diversas necesidades analíticas.
>
> La frecuencia de actualización es mensual a nivel de las feature tables. Los usuarios de negocio no cuentan con acceso directo a las variables analíticas de este producto de datos, ya que estas son consumidas directamente por modelos de machine learning, los cuales utilizan la información como insumo para la generación de predicciones, segmentaciones o mejoras en la calidad de contacto.

---

### Dashboard

#### 1. Claridad y comprensión
- ¿Qué términos de negocio deben ser explicados o contextualizados?
- ¿Existen términos técnicos que requieran definición?

#### 2. Propósito del Dato
- ¿Qué valor de negocio aporta este dashboard?
- ¿Qué problema o necesidad del negocio busca resolver?
- ¿Qué decisiones se soportan a partir de este dashboard?
- ¿Cuáles son los principales casos de uso?
- ¿Quiénes son los usuarios objetivo?
- ¿Cuál es su uso principal en la práctica?

#### 3. Nivel de Detalle
- ¿Qué indicadores o métricas contiene el dashboard?
- ¿Cuál es la frecuencia de actualización?
- ¿Qué periodo de análisis cubre?
- ¿Qué excepciones, reglas o exclusiones aplican en los datos mostrados?
- ¿El dashboard utiliza Datos de Alta Criticidad (DAC)?
- ¿El dashboard es utilizado para reportes regulatorios?

#### 4. Contexto y Relacionamiento
- ¿Qué dependencias críticas presenta?
- ¿Qué fuentes de datos alimentan el dashboard?
- ¿Proviene de un Data Lakehouse o no?
- ¿Qué catálogos consume?

**Consideraciones opcionales:** Ejemplos | Observaciones de Calidad de Datos | Información adicional relevante

**Ejemplo de definición funcional aplicada — Dashboard `Indicadores de Gobierno de Datos`:**

> El Dashboard de Indicadores de Gobierno de Datos es una herramienta de monitoreo corporativo que permite dar seguimiento al nivel de adopción, cumplimiento y uso de las prácticas de gobierno de datos en la organización. Este dashboard integra información proveniente del Data Lakehouse (Databricks) y listas de SharePoint, consolidando indicadores clave relacionados con metadatos, calidad de datos y gestión de activos de información, con una actualización mensual.
>
> Desde una perspectiva de negocio, el dashboard proporciona una visión centralizada del desempeño de los dominios de datos, permitiendo evaluar el cumplimiento en la definición de metadatos y la aplicación de reglas de calidad, considerando específicamente las capas UDV y DDV, y excluyendo RDV y EDV de este alcance de medición. Asimismo, incorpora mecanismos de control sobre la zona EDV, identificando la creación y permanencia de tablas bajo la regla de no superar los seis meses, con el objetivo de evitar crecimiento desordenado en entornos de exploración.
>
> Adicionalmente, el dashboard incluye el monitoreo de accesos a Datos de Alta Criticidad (DAC), permitiendo analizar qué usuarios cuentan con acceso, la frecuencia de descarga de información y su distribución por dominio, fortaleciendo la trazabilidad y control del uso de datos sensibles. Complementariamente, presenta indicadores de usabilidad de dashboards gobernados, identificando niveles de adopción a través de usuarios top, así como alertas sobre dashboards que no cumplen con niveles mínimos de uso o actualización esperada.
>
> Este dashboard es utilizado principalmente por equipos de Gobierno de Datos, Data Stewards, Product Owners y Data Owners, y tiene como objetivo facilitar la toma de decisiones orientadas a la mejora continua del gobierno de datos, priorización de dominios, control de activos y fortalecimiento del uso eficiente de la información en la organización.

---

### Términos de Negocio

#### 1. Claridad y comprensión
- ¿Qué se entiende por este término?
- ¿Existen interpretaciones alternativas que deban descartarse?
- ¿Qué términos similares podrían generar confusión?
- ¿Qué ejemplos ayudan en el entendimiento?

#### 2. Propósito del Dato
- ¿Qué función tiene el término dentro del negocio?
- ¿En qué procesos de negocio es utilizado?
- ¿Qué indicadores, reportes o análisis lo requieren?

#### 3. Nivel de Detalle
- ¿Existen subclasificaciones o variantes del término?
- ¿Qué excepciones se deben considerar?

#### 4. Contexto y Relacionamiento
- ¿En qué dominios de negocio se utiliza este término?
- ¿Con qué otro término se relaciona directamente?

**Consideraciones opcionales:** Ejemplos | Observaciones de Calidad de Datos | Información adicional relevante

**Ejemplo de definición funcional aplicada — Término `Canal de Atención`:**

> Es el medio formal e institucionalmente habilitado mediante el cual la organización establece interacción con sus clientes, prospectos, usuarios o terceros, con el fin de brindar información, gestionar solicitudes, resolver requerimientos, atender consultas o ejecutar transacciones relacionadas a sus productos, servicios o procesos. Este concepto se define a nivel corporativo, garantizando un entendimiento único, consistente y estandarizado en toda la organización, independientemente del área, dominio o proceso en el que se utilice.
>
> Desde una perspectiva de negocio, el Canal de Atención constituye el vehículo de relación formal entre la organización y sus usuarios, permitiendo estructurar y ordenar la forma en que se gestionan las interacciones. En este sentido, no se limita únicamente a un medio físico o digital, sino que abarca cualquier mecanismo reconocido dentro del modelo operativo oficial, incluyendo canales presenciales, remotos, digitales o asistidos, siempre que estos se encuentren institucionalmente validados.
>
> A nivel organizacional, este término permite identificar, clasificar y analizar de manera uniforme las interacciones con los usuarios, constituyéndose en un elemento clave para la construcción de indicadores, reportes y análisis relacionados con la atención, la eficiencia operativa, la adopción de canales, la experiencia del cliente y la efectividad comercial. Su uso transversal facilita la comparación, integración y estandarización de información entre distintos dominios como clientes, ventas, servicio, operaciones o experiencia, evitando interpretaciones divergentes entre áreas.

> **Recuerda:** Toda definición de un término de negocio debe ser construida en conjunto con las áreas de negocio, ya que son quienes poseen el conocimiento más profundo y completo sobre su significado, uso y contexto dentro de la organización.

---

## Procedimientos de Gobierno de Metadatos

### Procedimiento 1: Definir Metadatos en Diccionario de Datos

Este procedimiento aplica cuando se incorpora un activo de datos nuevo que requiere documentación inicial de sus metadatos.

**Roles involucrados:** Data Governance Expert | Data Steward | Business Specialist | Domain Owner

#### Fase 1 — Diseño del Activo

1. Confirmación del activo a documentar.
2. Solicitud de metadatos técnicos del activo.
3. Activación de mesa de trabajo para recoger metadatos funcionales.

#### Fase 2 — Definición

4. Llenado del Diccionario de Datos.
5. Envío de correo solicitando conformidad.

#### Fase 3 — Aprobación

6. Evaluación: ¿Aprueba la documentación?
   - **Sí** → continúa al paso 7.
   - **No** → retorna al paso 4 para correcciones.

#### Fase 4 — Comunicación

7. Carga al SharePoint del Chapter de Gobierno.
8. Envío de correo con el Visto Bueno (VB) de metadatos en diccionario al LT.

#### Fase 5 — Publicación

9. Carga de metadatos en MS Purview.
10. Informe al dominio del avance.

**Herramientas utilizadas:** Diccionario de Datos

**Entregables:**
- Visto Bueno de Metadatos
- Activos publicados en Purview
- Documento Aprobado

---

### Procedimiento 2: Actualizar Metadatos en Diccionario de Datos

Este procedimiento aplica cuando un activo de datos existente requiere actualización de sus metadatos por cambios en su definición, uso o estructura.

**Roles involucrados:** Data Governance Expert | Data Steward | Business Specialist | Domain Owner

#### Fase 1 — Diseño del Activo

1. Confirmación de la actualización del activo.
2. Solicitud de metadatos técnicos del activo.
3. Descarga del diccionario desde el SharePoint del Chapter de Gobierno.

#### Fase 2 — Definición

4. Activación de mesa de trabajo para recoger metadatos funcionales actualizados.
5. Actualización del Diccionario de Datos.
6. Envío de correo solicitando conformidad.

#### Fase 3 — Aprobación

7. Evaluación: ¿Aprueba la documentación?
   - **Sí** → continúa al paso 8.
   - **No** → retorna al paso 5 para correcciones.

#### Fase 4 — Comunicación

8. Reemplazo del documento en el SharePoint del Chapter de Gobierno.
9. Envío de correo con el Visto Bueno (VB) de metadatos en diccionario al LT.

#### Fase 5 — Publicación

10. Carga de metadatos actualizados en MS Purview.

**Herramientas utilizadas:** Diccionario de Datos

**Entregables:**
- Visto Bueno de Metadatos
- Activos publicados en Purview
- Documento Aprobado

---

## Ejemplo Integrado de Metadatos Funcionales

### Tabla: `hm_dac_persona_score_riesgo_corp`

La tabla tiene como finalidad generar y exponer un score de riesgo de personas que han mantenido o mantienen relación con Pacífico, independientemente de su estado actual, permitiendo una visión histórica y transversal del nivel de riesgo. Este score facilita la segmentación de clientes según su nivel de riesgo, a partir del análisis de su comportamiento en un periodo determinado y su probabilidad asociada, siendo utilizado como insumo para procesos analíticos.

El universo de análisis se construye con información proveniente de fuentes corporativas, la cual es enriquecida mediante su cruce con la entidad `md_dac_persona` para consolidar y validar la base de evaluación. Asimismo, el atributo clave `ScoreBuro` se origina en estas fuentes y es sometido a cálculos adicionales internos para su adecuación a las necesidades analíticas.

Cabe destacar que esta información no está orientada al consumo directo por el negocio, sino que constituye un input para modelos analíticos, apoyando iniciativas de segmentación y gestión de riesgo.

### Campo: `ScoreBuro`

Score de riesgo del cliente proveniente del sistema financiero (SF), calculado mediante un modelo de regresión logística basado en Weight of Evidence (WoE), por lo que puede tomar valores negativos. Los valores extremadamente bajos son imputados utilizando códigos específicos (-999.9 y -999.8), mientras que los valores nulos indican que la persona no contaba con información suficiente (mínimo 3 meses de historial) o no se encontraba registrada en el sistema financiero (SF) durante el periodo de observación.

---

## Principios de Gobierno de Metadatos

Los siguientes principios son de cumplimiento obligatorio para todos los roles que participan en la definición, actualización, aprobación y publicación de metadatos en la organización.

1. **Unicidad:** Cada activo de datos debe tener una única definición canónica, validada y publicada en MS Purview. No se permiten definiciones paralelas o informales.

2. **Colaboración obligatoria con el negocio:** Toda definición de metadatos funcionales, especialmente los términos de negocio, debe construirse en conjunto con las áreas de negocio responsables del activo. El equipo de datos no puede definir unilateralmente el significado de un concepto de negocio.

3. **Trazabilidad del proceso:** Toda definición o actualización de metadatos debe seguir el flujo establecido en los procedimientos 1 y 2, con sus entregables correspondientes: Diccionario de Datos, Visto Bueno y publicación en Purview.

4. **Aprobación formal:** Ningún metadato puede considerarse oficial sin el Visto Bueno (VB) del Domain Owner correspondiente. La aprobación debe quedar documentada y registrada.

5. **Actualización continua:** Los metadatos deben actualizarse cada vez que el activo de datos sufra cambios estructurales, funcionales o de uso. La desactualización de metadatos es una deuda de gobernanza que debe gestionarse activamente.

6. **Clasificación correcta:** Metadatos técnicos y funcionales no son intercambiables. Deben documentarse de forma separada y complementaria, siguiendo los pilares de Claridad, Propósito, Nivel de Detalle y Contexto.

7. **Publicación centralizada:** El repositorio oficial de metadatos es MS Purview. El SharePoint del Chapter de Gobierno es el repositorio de tránsito durante el proceso de aprobación. Una vez aprobado, el documento definitivo reside en Purview.
