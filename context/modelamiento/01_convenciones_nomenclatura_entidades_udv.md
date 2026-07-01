# Convenciones de Nomenclatura para Entidades UDV (Silver Layer)

## 1. Propósito del documento

Este documento define el estándar corporativo de nomenclatura y metadata obligatoria para entidades UDV (Silver).

Su propósito es:

- proteger la semántica del modelo integrado,
- asegurar consistencia y reutilización,
- habilitar modelamiento federado con gobierno explícito,
- y servir como fuente primaria de razonamiento para el Knowledge Assistant.

Este estándar se enfoca en *qué es el dato, a **qué ámbito pertenece* y *cómo debe gobernarse*, no en su procesamiento ni consumo analítico final.

## 2. Contexto arquitectónico

UDV es la capa de integración semántica del Lakehouse.

En UDV:

- se unifican conceptos provenientes de múltiples fuentes,
- se define el significado del dato,
- se establece granularidad, historia y estado,
- se alinean conceptos a modelos canónicos (por ejemplo, ACORD).

*Regla clave de arquitectura:*

- Si una decisión cambia el *significado del dato* → UDV
- Si una decisión cambia *cómo se analiza o presenta* → DDV

Este documento existe para custodiar ese significado.

## 3. Principio rector

*El nombre identifica el concepto.*  
*La metadata gobierna el contexto de uso.*

*El nombre de la entidad responde a:*  
¿Qué es este dato en términos de negocio?

*La metadata responde a:*  
¿A qué ámbito pertenece? ¿De dónde proviene? ¿Cómo se deriva?

Por diseño:

- el nombre debe ser estable en el tiempo,
- la metadata puede evolucionar sin renombrar entidades.

## 4. Alcance del estándar

### Aplica a

- Entidades UDV.
- Entidades de integración y conformación semántica.

### No aplica a

- RDV (ingesta cruda).
- DDV (datasets, datamarts, métricas).
- Nomenclatura de campos (atributos), definida en un estándar separado.

## 5. Familias de patrones de nomenclatura UDV

UDV utiliza *familias de patrones controlados*, no un único patrón rígido, para cubrir casuísticas reales sin perder gobernabilidad.

## 6. Patrón base de nomenclatura

### 6.1 Entidades UDV por ramo SBS

Cuando la semántica de la entidad depende de un ramo SBS, el scope puede formar parte del nombre.

*Patrón:*


prefijo_[dac]_dominio_concepto_scope_origen


*Donde:*

- prefijo: tipo de entidad y granularidad
- dac: opcional, solo si contiene datos sensibles
- dominio: concepto canónico
- concepto: descripción funcional (multi-token permitido)
- scope: ramo SBS o excepción (embebido)
- origen: sistema o fuente gobernada

*Ejemplos por ramo SBS:*

- hd_poliza_movimiento_gen_core
- hd_poliza_movimiento_vida_core
- hd_renta_flujo_pago_renta_core

*Ejemplos con scope embebido:*

- hd_poliza_movimiento_embebido_core
- hd_siniestro_reclamacion_embebido_core

### 6.2 Entidades transversales

Cuando la entidad es transversal a más de un ramo SBS (scope = cross), el scope *NO se incluye en el nombre* y se gestiona exclusivamente como metadata.

*Patrón:*


prefijo_[dac]_dominio_concepto_origen


*Ejemplos:*

- hd_cobro_poliza_core (metadata: scope = cross)
- hd_riesgo_cliente_core (metadata: scope = cross)
- ud_consentimiento_cliente_core (metadata: scope = cross)

*Nota:* Para entidades con scope = embebido, el scope *SÍ se incluye* en el nombre según el patrón 6.1.

## 7. Prefijos: tipo de entidad y granularidad

Los prefijos indican *tipo de entidad* y *granularidad temporal*. Ambos son conceptos semánticos fundamentales que definen el significado del dato.

### Tipo de entidad

Define la *naturaleza temporal* de los datos:

- *Histórica (h_)*: Registra el historial completo de cambios y movimientos. Preserva toda la evolución temporal del dato.
  - *Características*: Cada registro representa un evento, movimiento o cambio individual que ocurrió en el tiempo.
  - *Uso típico*: Auditoría, trazabilidad completa, análisis de comportamiento temporal, reconstrucción histórica.
  - *Granularidad*: Puede ser diaria (cada evento individual), mensual (consolidado mensual que preserva historia), o anual (ejercicios históricos).
  - *Ejemplo*: hd_poliza_movimiento_gen_core registra cada emisión, endoso, renovación, cancelación de pólizas como un registro individual. Permite reconstruir toda la historia de la póliza.

- *Maestra (m_): Entidad que materializa un **dato maestro*, entendido como la fuente única y confiable que describe la identidad y características esenciales de un objeto de negocio, y que es reutilizada de forma consistente por múltiples procesos y dominios.

  - *Características*: 
    - *Fuente única de verdad (Single Source of Truth)*: Representa la versión autoritativa y consensuada del dato.
    - *Identidad y atributos esenciales*: Define qué es la entidad y sus propiedades fundamentales.
    - *Reutilización transversal*: Consumida por múltiples procesos, sistemas y dominios de forma consistente.
    - *Granularidad temporal*: Puede tener granularidad (diaria, mensual, anual) representando el estado maestro en ese período.
  - *Uso típico*: 
    - Catálogo maestro de clientes, productos, o pólizas vigentes
    - Cierres periódicos que consolidan el estado maestro (cierre mensual de cartera, inventario de activos)
    - Vista consolidada y normalizada de una entidad proveniente de múltiples fuentes
  - *Diferencia con histórica*: La maestra no registra movimientos individuales, sino el estado maestro resultante después de aplicar todos los movimientos. Es la "versión dorada" del dato.
  - *Diferencia con última*: La maestra puede tener granularidad temporal (una maestra por mes/año), mientras que última solo contiene el estado más reciente sin periodicidad.
  - *Ejemplos*: 
    - md_cliente_gen_core: Maestro diario de clientes (estado maestro actualizado diariamente)
    - mm_poliza_vigencia_gen_core: Maestro mensual de pólizas vigentes (estado maestro al cierre de cada mes)
    - ma_producto_catalogo_gen_core: Maestro anual del catálogo de productos (versión autoritativa por ejercicio)

- *Última (u_)*: Contiene únicamente el último estado conocido, sin historial previo. Optimizada para consultas de estado actual.
  - *Características*: Solo mantiene la versión más reciente de cada entidad. No hay múltiples versiones temporales.
  - *Uso típico*: Consultas operativas de estado actual, dashboards en tiempo real, validaciones de vigencia actual.
  - *Diferencia con maestra*: La última no tiene granularidad temporal (no hay una por día/mes/año), solo existe "la última" disponible.
  - *Ejemplo*: ud_poliza_vigente_gen_core contiene solo las pólizas actualmente vigentes (una fila por póliza), sin historial de estados anteriores.

*Tabla comparativa de tipos de entidad:*

| Aspecto | Histórica (h_) | Maestra (m_) | Última (u_) |
|---------|----------------|--------------|-------------|
| *Contenido* | Todos los eventos/movimientos | *Dato maestro*: fuente única y confiable de identidad y atributos esenciales | Solo estado actual |
| *Temporal* | ✅ Múltiples registros en el tiempo | ✅ Estado maestro por período (día/mes/año) | ❌ Un solo registro (última versión) |
| *Propósito* | Auditoría, análisis temporal | *Single Source of Truth*, reutilización transversal | Consultas operativas de estado actual |
| *Reutilización* | Específica del análisis temporal | ✅ *Alta*: consumida por múltiples dominios y procesos | Media: consultas de estado vigente |
| *Ejemplo* | Cada movimiento de póliza | Catálogo maestro de productos, estado maestro mensual de cartera | Pólizas vigentes en este momento |
| *Tamaño típico* | Mayor (historia completa) | Medio (snapshots maestros periódicos) | Menor (solo actual) |
| *Consolidación* | No consolidada (eventos individuales) | ✅ *Consolidada y normalizada* desde múltiples fuentes | Consolidada de última versión |

*📌 Nota sobre Master Data Management (MDM):*

Las entidades *maestras (m_)* en UDV implementan los principios de *Master Data Management*:

1. *Golden Record*: La entidad maestra representa el "registro dorado" - la versión autoritativa y consensuada del dato.
2. *Data Governance*: Las maestras son el punto de control y gobierno del dato, asegurando calidad, consistencia y trazabilidad.
3. *Reusabilidad*: Una vez definida una maestra, debe ser consumida por todos los procesos que requieran ese dato, evitando duplicaciones y divergencias.
4. *Lifecycle Management*: Las maestras con granularidad temporal (md, mm, ma) permiten rastrear la evolución del dato maestro a lo largo del tiempo.

*Cuándo crear una entidad maestra:*
- ✅ Cuando múltiples procesos o dominios necesitan consumir la misma versión del dato
- ✅ Cuando se requiere consolidar datos de múltiples fuentes en una vista única
- ✅ Cuando se necesita establecer la "fuente de verdad" para un concepto de negocio
- ✅ Cuando el dato requiere gobierno centralizado y control de calidad

*Cuándo NO crear una entidad maestra:*
- ❌ Para datos altamente volátiles que cambian constantemente (usar histórica)
- ❌ Para datos que solo se usan en un proceso específico sin reutilización transversal
- ❌ Para métricas o agregaciones analíticas (van a DDV, no a UDV)

### Granularidad temporal

Define la *unidad de tiempo mínima* que representa cada registro:

- *Diaria (d)*: Cada registro representa un día de operación o un evento específico en el tiempo.
- *Mensual (m)*: Cada registro representa un mes completo. Típicamente usado para cierres contables, agregaciones estructurales o snapshots mensuales.
- *Anual (a)*: Cada registro representa un año completo. Usado para cierres anuales, ejercicios fiscales o análisis de largo plazo.

### Tabla de prefijos

| Prefijo | Significado | Ejemplo de uso |
|---------|-------------|----------------|
| hd | histórica diaria | Movimientos de póliza día a día |
| hm | histórica mensual | Histórico de estados mensuales |
| ha | histórica anual | Histórico de ejercicios anuales |
| md | maestra diaria | *Dato maestro* actualizado diariamente: catálogo de clientes vigentes |
| mm | maestra mensual | *Dato maestro* mensual: snapshot autoritativo de cartera al cierre de mes |
| ma | maestra anual | *Dato maestro* anual: catálogo de productos por ejercicio fiscal |
| ud | última diaria | Último estado conocido por día |
| um | última mensual | Último mes disponible |
| ua | última anual | Último ejercicio cerrado |

*⚠️ Importante:* La granularidad es *semántica, no técnica*. Cambiarla cambia el significado del dato y constituye un cambio MAJOR de versión.

*Ejemplo:*
- hd_poliza_movimiento_gen_core registra cada movimiento individual de pólizas (emisión, endoso, renovación)
- mm_poliza_vigencia_gen_core es el *dato maestro mensual* que consolida el estado autoritativo de pólizas vigentes al cierre de cada mes
- Aunque parecen similares, son *conceptos semánticamente distintos*: una registra eventos, la otra materializa el estado maestro consolidado

## 8. Scope (ámbito principal de la entidad)

El atributo scope representa el *ámbito principal de clasificación* de la entidad en el modelo de datos.

### Fundamento: Ramos SBS

La clasificación de scope se fundamenta en los *ramos definidos por la SBS* (Superintendencia de Banca, Seguros y AFP del Perú), que es el organismo regulador del sector asegurador peruano.

La SBS establece una clasificación oficial de ramos de seguros para efectos de:
- Regulación y supervisión
- Reportería regulatoria obligatoria
- Cálculo de reservas técnicas
- Solvencia y capital regulatorio
- Estadísticas del sector

*¿Por qué los ramos SBS son el fundamento del scope?*

1. *Obligatoriedad regulatoria*: Toda aseguradora debe reportar información segregada por ramo SBS.
2. *Consistencia sectorial*: Permite comparabilidad entre aseguradoras del mercado peruano.
3. *Gobernanza contable y financiera*: Los estados financieros, provisiones y capital se calculan por ramo.
4. *Trazabilidad*: Facilita la auditoría y el cumplimiento regulatorio.

Por estas razones, los ramos SBS constituyen el *eje primario de clasificación semántica* en UDV, garantizando que el modelo de datos esté alineado con la estructura regulatoria del negocio.

### Valores permitidos

| Valor | Descripción | Fundamento |
|-------|-------------|------------|
| gen | Generales | Ramo SBS: Seguros Generales (patrimoniales, responsabilidad civil, automóviles, etc.) |
| vida | Vida | Ramo SBS: Seguros de Vida (individual, colectivo, rentas vitalicias) |
| renta | Rentas | Ramo SBS: Rentas (productos de jubilación y rentas vitalicias) |
| cross | Transversal | No pertenece a un ramo específico; aplica a múltiples ramos SBS simultáneamente |
| embebido | Embebidos | Excepción consciente: línea de negocio no regulada como ramo SBS pero con independencia analítica |

### Regla sobre embebidos

*"Embebido" no constituye un ramo SBS.*

Sin embargo, se modela al mismo nivel que los ramos SBS como una *excepción consciente del estándar*, debido a que:

- posee cuantificación y KPIs propios,
- presenta una naturaleza de negocio diferenciada (seguros distribuidos a través de terceros: e-commerce, bancos, retailers),
- requiere análisis, reporting y gobierno independientes,
- y debe poder identificarse explícitamente en el modelo UDV para trazabilidad de negocio.

*Cuando scope = embebido:*

- no se utiliza gen, vida ni renta,
- el valor *se incluye en el nombre* (ej: hd_poliza_movimiento_embebido_core)

### Regla sobre cross (transversal)

Las entidades cross representan conceptos que no están vinculados a un ramo SBS específico:

*Ejemplos de entidades cross:*
- hd_cobro_poliza_core: Los cobros pueden aplicar a cualquier ramo
- hd_riesgo_cliente_core: La evaluación de riesgo del cliente es transversal
- ud_consentimiento_cliente_core: Los consentimientos aplican independientemente del ramo

*Cuando scope = cross:*

- el valor *NO se incluye en el nombre*
- se expresa exclusivamente como *metadata*

### Importancia del scope

El scope es *metadata obligatoria* porque:

1. *Gobierno regulatorio*: Facilita el cumplimiento de reportería SBS
2. *Análisis de negocio*: Permite segmentación por línea de negocio
3. *Trazabilidad*: Identifica claramente el ámbito de cada entidad
4. *Reutilización controlada*: Previene uso incorrecto de entidades entre ramos con semánticas diferentes

## 9. Metadata obligatoria por entidad UDV

Las siguientes propiedades deben gestionarse como *metadata de la entidad*. Esta metadata es obligatoria porque:

- Gobierna el contexto de uso sin afectar el nombre
- Permite evolución sin renombrar entidades
- Facilita búsqueda, clasificación y gobierno
- Habilita razonamiento automático del Knowledge Assistant

### scope

*Propósito:* Identifica el ámbito regulatorio y de negocio de la entidad.

*Valores:* gen | vida | renta | cross | embebido

*Uso en el nombre:*
- gen, vida, renta, embebido: *SÍ* se incluyen en el nombre
- cross: *NO* se incluye en el nombre (solo metadata)

*Ejemplo:*

Entidad: hd_poliza_movimiento_gen_core
Metadata: scope = gen


### domain_type

*Propósito:* Clasifica la entidad según su naturaleza semántica en el modelo de negocio.

*Valores:*

| Valor | Descripción | Cuándo usar |
|-------|-------------|-------------|
| dominio_informacion | Objeto canónico del negocio | Cliente, Póliza, Siniestro, Producto, Persona |
| capacidad_negocio | Función o gestión transversal | Cobro, Pago, Consentimiento, Riesgo |

*Importancia:* Esta distinción permite al Knowledge Assistant razonar sobre la naturaleza del dato y sugerir relaciones apropiadas entre entidades.

*Ejemplo:*

Entidad: hd_poliza_movimiento_gen_core
Metadata: domain_type = dominio_informacion

Entidad: hd_cobro_poliza_core
Metadata: domain_type = capacidad_negocio


### source_type

*Propósito:* Identifica el origen y naturaleza de los datos de la entidad.

*Valores:*

| Valor | Descripción | Ejemplos |
|-------|-------------|----------|
| core | Sistema core de la aseguradora | AS400, sistema de pólizas central |
| external | Fuente externa a la organización | SUNAT, SBS, proveedores de datos |
| derived | Resultado de transformaciones o reglas | Jerarquías calculadas, clasificaciones |
| config | Configuración o parámetros | Parámetros de negocio, reglas |
| lookup | Catálogos y tablas de referencia | Tipos de documento, estados |
| legacy | Sistema heredado o en desuso | Sistemas antiguos en proceso de migración |

*Importancia:* Permite trazabilidad del origen del dato y decisiones de governance (ej: datos externos requieren validación adicional).

*Ejemplo:*

Entidad: hd_poliza_movimiento_gen_core
Metadata: source_type = core

Entidad: hd_ext_persona_vehiculo_core
Metadata: source_type = external


### derivation_type

*Propósito:* Indica si la entidad contiene datos derivados y de qué tipo.

*Valores:*

| Valor | Descripción | Cuándo usar |
|-------|-------------|-------------|
| none | Sin derivación, datos directos de la fuente | Mayoría de entidades de integración |
| calculated | Contiene campos calculados mediante fórmulas | Campos con reglas de negocio aplicadas |
| aggregated | Agregación estructural (temporal) | Cierres mensuales/anuales, snapshots |
| rule_based | Resultado de aplicar reglas de negocio complejas | Clasificaciones, segmentaciones |

*⚠️ Importante sobre aggregated en UDV:*

aggregated es *válido en UDV* cuando la agregación es *estructural* (consolidación temporal o snapshot), no cuando representa métricas finales de negocio:

- ✅ *Válido en UDV*: hm_poliza_vigencia_gen_core (snapshot mensual de vigencia)
- ❌ *NO válido en UDV*: Métricas calculadas tipo KPI → van a DDV

*Ejemplo:*

Entidad: hd_poliza_movimiento_gen_core
Metadata: derivation_type = none

Entidad: hd_drv_jerarquia_arbol_canal_core
Metadata: derivation_type = rule_based

Entidad: hm_poliza_vigencia_gen_core
Metadata: derivation_type = aggregated


### Tabla resumen de metadata obligatoria

| Metadata | Propósito | Impacto en nombre |
|----------|-----------|-------------------|
| scope | Ámbito regulatorio/negocio | Solo cross no va en nombre |
| domain_type | Naturaleza semántica | No aplica |
| source_type | Origen del dato | Prefijos ext_, lkp_, config_ |
| derivation_type | Tipo de derivación | Prefijo drv_ si aplica |

## 10. Dominio de información vs capacidad de negocio

### Dominio de información

Representa un objeto canónico del negocio.

*Ejemplos:*
- cliente
- persona
- poliza
- siniestro
- producto

### Capacidad de negocio

Representa una gestión o función transversal.

*Ejemplos:*
- cobro
- pago
- consentimiento
- riesgo_cliente

*Esta distinción no se expresa en el nombre y se gobierna por metadata.*

## 11. Entidades derivadas (drv_)

Se utiliza drv_ cuando la entidad:

- existe principalmente como resultado de reglas o combinaciones,
- no es 1:1 con una fuente,
- y su propósito es semánticamente derivado.

*Ejemplo:*


hd_drv_jerarquia_arbol_canal_core


*No se utiliza drv_ cuando solo existen algunos campos calculados dentro de una entidad base.*

## 12. Integraciones externas (ext_)

Las entidades provenientes de fuentes externas deben usar ext_.

*Ejemplos:*

- hd_ext_persona_vehiculo_core
- hm_ext_estado_financiero_aseg_core

Estas entidades deben tener source_type = external.

## 13. Lookups y catálogos (lkp_)

Las entidades referenciales usan lkp_.

*Ejemplos:*

- lkp_tipo_documento
- lkp_estado_poliza

## 14. Entidades de configuración (config_)

Entidades usadas como:

- parámetros,
- reglas,
- formatos de entrada.

*Ejemplo:*


hm_config_digitalidad_poliza_gen_core


## 15. Regla de legacy (_vida)

Las entidades que contienen _vida sin cumplir el patrón completo se consideran *legacy*.

Su reutilización o evolución requiere *revalidación con Modelamiento* para integrarse al modelo canónico UDV.

## 16. Abreviaturas normalizadas

### No abreviar

- persona
- cliente

### Abreviaturas permitidas

| Abreviatura | Significado |
|-------------|-------------|
| interm | intermediario |
| cobro | cobranza |
| cobert | cobertura |
| cert | certificado |
| pol | poliza |
| llcc | lineas_comerciales |
| llpp | lineas_personales |
| vg_emp | vida_grupo_empresa |
| vg_prs | vida_grupo_persona |
| vi | vida_individual |

*Nuevas abreviaturas requieren validación.*

## 17. Errores comunes y antipatrones

❌ *NO hacer:*

- Usar drv_ solo por tener campos calculados.
- Crear abreviaturas no gobernadas.
- Mezclar ramos SBS con criterios comerciales en el nombre.

## 18. Relación con nomenclatura de campos

Este documento define nomenclatura y metadata de *ENTIDADES UDV*.

La nomenclatura de *CAMPOS (atributos)* se define en un estándar separado para evitar mezclar reglas de entidad con reglas de atributo y facilitar el razonamiento del Knowledge Assistant.

---

## Resumen de Patrones

### Entidades por ramo SBS o embebido


prefijo_[dac]_dominio_concepto_scope_origen

Ejemplo ramo SBS: hd_poliza_movimiento_gen_core
Ejemplo embebido: hd_poliza_movimiento_embebido_core


### Entidades transversales (cross)


prefijo_[dac]_dominio_concepto_origen

Ejemplo: hd_cobro_poliza_core
Metadata: scope = cross


### Entidades embebidos


prefijo_[dac]_dominio_concepto_embebido_origen

Ejemplo: hd_poliza_movimiento_embebido_core
Metadata: scope = embebido


### Entidades derivadas


prefijo_drv_dominio_concepto_origen

Ejemplo: hd_drv_jerarquia_arbol_canal_core


### Entidades externas


prefijo_ext_dominio_concepto_origen

Ejemplo: hd_ext_persona_vehiculo_core


### Lookups


lkp_concepto

Ejemplo: lkp_tipo_documento


### Configuración


prefijo_config_concepto_[scope]_origen

Ejemplo: hm_config_digitalidad_poliza_gen_core