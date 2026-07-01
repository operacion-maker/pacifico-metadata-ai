# Lineamientos de Nomenclatura de Campos en Entidades UDV (Silver Layer)

## 1. Propósito
Definir el estándar corporativo de nomenclatura de campos para las entidades de la capa UDV (Silver Layer), con el objetivo de:

- Garantizar consistencia semántica y técnica
- Facilitar la integración de datos entre dominios
- Asegurar claridad para analítica, reporting y gobierno de datos
- Evitar ambigüedad, duplicidad y dependencia de sistemas origen
- Habilitar razonamiento efectivo del Knowledge Assistant

## 2. Fundamentos y Referencias
Este estándar se fundamenta en mejores prácticas del sector asegurador:

### Estándares de Seguros
- *ACORD Data Model*: Information Model y Data Model con conceptos canónicos (Policy, Party, Claim, Product)
- *ACORD NDR (Naming and Design Rules)*: Especificación de arquitectura XML, nombres y tipos de datos comunes
- *ACORD Business Glossary*: Definiciones no técnicas estandarizadas para conceptos de seguros

*Referencias:*
- [ACORD Standards Architecture](https://www.acord.org/standards-architecture)

## 3. Principios generales
Todo campo en una entidad UDV debe cumplir:

### 3.1 Nombre físico compacto y estandarizado
Se utiliza *lowercase* (minúsculas), sin tildes ni caracteres especiales.
*Fundamento:* Esta convención facilita portabilidad entre sistemas de bases de datos y evita problemas de compatibilidad.

### 3.2 Prefijo semántico obligatorio
Todo campo inicia con un *prefijo* que indica su naturaleza (id, cod, des, fec, mto, flg, etc.).

### 3.3 Un solo significado por nombre
Un nombre de campo representa un *único concepto*, reutilizable transversalmente.
*Fundamento:* Alineado con principios de Master Data Management y ACORD Business Glossary.

### 3.4 Independiente de la fuente
No se replica nomenclatura técnica de sistemas origen.
*Fundamento:* La capa UDV es semántica e independiente de la implementación técnica de los sistemas fuente.

### 3.5 Orientado al negocio
El nombre describe el *concepto del negocio*, no el proceso técnico.
*Fundamento:* Alineado con ACORD Reference Architecture que prioriza conceptos de negocio sobre implementación técnica.

## 4. Estándar de nomenclatura de campos
### 4.1 Tipos de campos y prefijos
*⚠️ IMPORTANTE: Precisión de Datos en Silver*
La capa Silver (UDV) debe preservar la *precisión necesaria para todos los casos de uso de negocio. DECIMAL(18,2) es **insuficiente* para primas, tasas, reservas y cálculos actuariales. Ver sección 4.2 para justificación.

| Tipo de campo | Prefijo | Descripción | Tipo Databricks |
|---------------|---------|-------------|-----------------|
| *Identificadores* | | | |
| Identificador único | id | Llave primaria (surrogate key) | BIGINT |
| Código | cod | Código numérico o alfanumérico que identifica un valor en un catálogo de referencia | STRING |
| Identificador encriptado | codclave | Identificador sensible encriptado (ej: documento identidad) | STRING |
| *Descriptivos* | | | |
| Descripción | des | Campo de texto descriptivo | STRING |
| Nombre | nom | Nombre propio de persona, entidad o producto | STRING |
| Título | titulo | Título o encabezado | STRING |
| *Temporales* | | | |
| Fecha | fec | Fecha en formato yyyy-MM-dd | DATE |
| Periodo | periodo | Periodo lógico (yyyyMMdd, yyyyMM, yyyy) | STRING |
| Timestamp | ts | Marca de tiempo con fecha y hora | TIMESTAMP |
| Año | anio | Año calendario o fiscal | INT |
| Mes | mes | Mes numérico (01-12) | TINYINT |
| Trimestre | trim | Trimestre (Q1, Q2, Q3, Q4) | STRING |
| Hora | hora | Hora del día | STRING |
| *Indicadores y Flags* | | | |
| Flag | flg | Indicador booleano (0 / 1) | INT |
| Indicador | ind | Indicador lógico (S / N, SI / NO) | STRING (longitud 2) |
| Tipo | tip | Clasificación o tipo categórico | STRING |
| *Numéricos Monetarios* | | | |
| Prima | prima | Prima de seguro (sin prefijo mto) | *DECIMAL(20,6)* |
| Suma Asegurada | sumaaseg | Suma asegurada (sin prefijo mto) | *DECIMAL(20,2)* |
| Monto | mto | Valores monetarios generales | DECIMAL(18,2) |
| Comisión | mtocomision | Monto de comisión | *DECIMAL(18,4)* |
| Reserva | mtoreserva | Reserva técnica | *DECIMAL(22,8)* |
| *Numéricos No Monetarios* | | | |
| Tasa | tasa | Tasa de interés o actuarial | *DECIMAL(12,8)* |
| Porcentaje | porc | Valor porcentual | *DECIMAL(7,4)* |
| Factor | factor | Factor actuarial o de cálculo | *DECIMAL(18,12)* |
| Peso | peso | Peso o ponderación | *DECIMAL(12,8)* |
| Cantidad | ctd | Cantidad numérica de items | INT |
| Número | num | Número secuencial o contador | BIGINT |
| *Textuales y Contacto* | | | |
| Dirección | dir | Dirección postal | STRING |
| Email | email | Correo electrónico | STRING |
| Teléfono | telef | Número telefónico | STRING |
| URL | url | Dirección web | STRING |
| Nota | nota | Nota, comentario o anotación | STRING |
| Observación | obs | Observación técnica o de negocio | STRING |
| *Geográficos* | | | |
| País | pais | Código o nombre de país | STRING |
| Ciudad | ciudad | Ciudad o localidad | STRING |
| Región | region | Región, departamento o estado | STRING |
| Distrito | distrito | Distrito o municipalidad | STRING |
| Código Postal | codpostal | Código postal o ZIP | STRING |
| Ubigeo | ubigeo | Código INEI geográfico (Perú) | STRING(6) |
| Latitud | latitud | Coordenada de latitud | DECIMAL(10,8) |
| Longitud | longitud | Coordenada de longitud | DECIMAL(11,8) |
| *Seguros - Conceptos ACORD* | | | |
| Póliza | poliza | Relacionado con póliza | STRING |
| Certificado | cert | Certificado de seguro | STRING |
| Siniestro | siniestro | Relacionado con siniestro/claim | STRING |
| Cobertura | cobert | Cobertura de seguro | STRING |
| Deducible | ded | Deducible o franquicia | DECIMAL(18,2) |
| Beneficiario | benef | Beneficiario | STRING |
| Endoso | endoso | Endoso/modificación de póliza | STRING |
| Renovación | renov | Renovación de póliza | STRING |
| Cotización | cotiz | Cotización/quote | STRING |
| Exclusión | excl | Exclusión de cobertura | STRING |
| Límite | lim | Límite de cobertura | DECIMAL(20,2) |
| Suscripción | susc | Suscripción/underwriting | STRING |
| Reaseguro | reaseg | Reaseguro | STRING |
| Retención | retencion | Retención (reaseguro) | DECIMAL(18,4) |

✅ *El prefijo es obligatorio y define el significado técnico del campo*

*Nota importante sobre tipos de datos:*
- flg: Siempre INT (0/1) para optimización de almacenamiento en Delta Tables
- ind: Siempre STRING con longitud específica (1 o 2 caracteres) para valores alfanuméricos
- des, nom, titulo, nota, obs: STRING sin longitud fija (Delta Tables optimiza automáticamente)
- *Primas*: DECIMAL(20,6) - 6 decimales suficiente para mayoría de casos
- *Tasas*: DECIMAL(12,8) - 8 decimales para tasas diarias y cálculos compuestos
- *Reservas*: DECIMAL(22,8) - 8 decimales para productos largo plazo y regulatorio
- *Factores*: DECIMAL(18,12) - 12 decimales para tablas actuariales (mortalidad, invalidez)

### 4.2 Justificación de Precisión de Datos en Silver

*Principio: La capa Silver (UDV) es la **Vista Única de Verdad* y debe preservar la precisión necesaria para *TODOS* los casos de uso de negocio.

#### *¿Por qué NO usar DECIMAL(18,2) para todo?*

*Problema: DECIMAL(18,2) solo permite 2 decimales, lo que es **insuficiente* para:
- Cálculos actuariales (reservas matemáticas)
- Prorrateos y distribuciones de primas
- Tasas de interés y factores
- Conversión de moneda
- Modelos estadísticos y actuariales

*Ejemplo de pérdida de precisión:*

sql
-- Prima anual calculada por tarificador:
primaanual = 1,234.5678  (4 decimales)

-- Prorrateo a prima mensual:
primamensual = 1,234.5678 / 12 = 102.880650

-- Con DECIMAL(18,2): 102.88  ❌ Pierde 0.000650
-- Con DECIMAL(20,6): 102.880650 ✅ Mantiene precisión


*Impacto en cartera de 100,000 pólizas:*
- Error por póliza: 0.01 soles
- Error total: 100,000 × 0.01 = *1,000 soles*
- En reservas (30 años): 1,000 × 30 = *30,000 soles* de diferencia

#### *Tipos de dato por contexto:*

| Campo | Tipo Recomendado | Decimales | Justificación |
|-------|------------------|-----------|---------------|
| *Primas* | DECIMAL(20,6) | 6 | Cálculos actuariales, prorrateos, conversión moneda |
| *Tasas* | DECIMAL(12,8) | 8 | Interés compuesto amplifica errores, tasas muy pequeñas (ver nota) |
| *Porcentajes* | DECIMAL(7,4) | 4 | Comisiones escalonadas, distribuciones precisas |
| *Reservas* | DECIMAL(22,8) | 8 | Regulatorio, cálculos actuariales complejos (ver nota) |
| *Factores* | DECIMAL(18,12) | 12 | Modelos actuariales, factores de mortalidad (ver nota) |
| *Comisiones* | DECIMAL(18,4) | 4 | Cálculos porcentuales sobre primas |
| *Sumas aseguradas* | DECIMAL(20,2) | 2 | Valores muy grandes (edificios, flotas), 2 decimales OK |
| *Montos generales* | DECIMAL(18,2) | 2 | Pagos, deducibles, estándar monetario |

*⚠️ Nota sobre precisión extendida:*

Algunos casos requieren *más de 6 decimales*:

1. *Tasas de interés diarias o por periodos muy cortos:*
   sql
   -- Tasa anual 12.5% convertida a diaria:
   -- 12.5% / 365 = 0.03424657534% = 0.0003424657534
   -- Necesita 8+ decimales: DECIMAL(12,8)
   
   tasa DECIMAL(12,8)  -- 8 decimales para tasas de interés
   

2. *Reservas matemáticas con cálculos compuestos:*
   sql
   -- Reserva = Prima × Factor × (1 + tasa)^plazo
   -- En plazos largos (30+ años), errores se amplifican
   -- Necesita 8 decimales: DECIMAL(22,8)
   
   mtoreserva DECIMAL(22,8)  -- 8 decimales para reservas
   

3. *Factores actuariales de mortalidad:*
   sql
   -- Tablas de mortalidad tienen factores muy pequeños
   -- Ejemplo: qx = 0.000123456789 (12 decimales)
   -- DECIMAL(18,12) permite 12 decimales
   
   factor DECIMAL(18,12)  -- 12 decimales para factores
   

*Recomendación actualizada:*

| Tipo de dato | Precisión mínima | Precisión recomendada | Cuándo usar mayor precisión |
|--------------|------------------|----------------------|----------------------------|
| Prima | DECIMAL(20,6) | DECIMAL(20,6) | 6 decimales suficiente para mayoría de casos |
| Tasa | DECIMAL(10,6) | *DECIMAL(12,8)* | Tasas diarias, cálculos compuestos largos |
| Reserva | DECIMAL(20,6) | *DECIMAL(22,8)* | Plazos >20 años, cálculos regulatorios SBS |
| Factor | DECIMAL(15,10) | *DECIMAL(18,12)* | Tablas actuariales, mortalidad, invalidez |
| Porcentaje | DECIMAL(7,4) | DECIMAL(7,4) | 4 decimales suficiente |

*Decisión por caso de uso:*

- *Productos de corto plazo* (salud, auto): DECIMAL(20,6) para primas, DECIMAL(10,6) para tasas
- *Productos de largo plazo* (vida, rentas): DECIMAL(20,6) para primas, *DECIMAL(12,8)* para tasas, *DECIMAL(22,8)* para reservas
- *Productos con tabla actuarial* (vida, invalidez): Factores con *DECIMAL(18,12)*

#### *Ejemplos de casos de uso que requieren alta precisión:*

*1. Reserva Matemática:*
sql
reserva = prima × factor_mortalidad × factor_interes
reserva = 10,000.00 × 0.003456 × 1.000789
reserva = 34.587270  (necesita 6 decimales)


*2. Tasa de Interés Diaria:*
sql
tasa_diaria = tasa_anual / 365
tasa_diaria = 12.5% / 365 = 0.034247% = 0.00034247
-- Necesita 6+ decimales


*3. Conversión de Moneda:*
sql
primadolares = primasoles / tipocambio
primadolares = 10,000.00 / 3.789456 = 2,639.267891
-- Necesita 6 decimales en tipo de cambio


*4. Comisión Escalonada:*
sql
comision = prima × porcentaje
comision = 10,000.00 × 0.123456 = 1,234.56
-- Porcentaje necesita 4-6 decimales: 12.3456%


#### *Recomendación por capa:*

| Capa | Estrategia de Precisión |
|------|------------------------|
| *RDV* | Preservar precisión ORIGINAL del sistema fuente (usar STRING si hay duda) |
| *UDV* | Usar precisión SUFICIENTE para todos los casos de uso de negocio |
| *DDV* | Redondear según necesidad del consumidor (dashboards, reportes) |

#### *Decisión final: NO usar DECIMAL(18,2) como tipo por defecto*

Cada tipo de dato debe elegirse según:
1. Rango de valores esperado
2. Precisión requerida por cálculos de negocio
3. Regulaciones (SBS puede exigir precisión específica)
4. Casos de uso downstream (actuarial, financiero, reporting)

### 4.3 Sufijos comunes (opcionales según contexto)

| Sufijo | Uso | Ejemplo | Contexto |
|--------|-----|---------|----------|
| *Financieros* | | | |
| bruto | Valor antes de descuentos | primabruta | Financiero |
| neto | Valor después de descuentos | primaneta | Financiero |
| *Data Warehousing* | | | |
| original | Valor original sin ajustes | mtooriginal | Data warehousing |
| ajustado | Valor después de ajustes | mtoajustado | Data warehousing |
| estimado | Valor estimado o proyectado | primaestimado | Data warehousing |
| real | Valor real o efectivo | primareal | Data warehousing |
| *Temporales* | | | |
| ini | Valor al inicio de periodo | primaini | Temporal |
| fin | Valor al final de periodo | primafin | Temporal |
| *Estados (Seguros - ACORD)* | | | |
| vigente | Actualmente vigente | primavigente | Seguros |
| emitido | Póliza/prima emitida | primaemitida | Seguros |
| cobrado | Prima cobrada | primacobrada | Seguros |
| anulado | Póliza/prima anulada | primaanulado | Seguros |
| activo | Estado activo | polizaactivo | Seguros |
| inactivo | Estado inactivo | polizainactivo | Seguros |
| *Multi-moneda* | | | |
| local | Moneda local del país | primalocal | Multi-currency |
| corp | Moneda corporativa | primacorp | Multi-currency |
| soles | En soles peruanos (PEN) | primasoles | Multi-currency |
| dolares | En dólares estadounidenses (USD) | primadolares | Multi-currency |
| mn | Moneda nacional | mtopagomn | Multi-currency |
| me | Moneda extranjera | mtopagome | Multi-currency |

*Nota: Los sufijos se escriben **sin separador* (sin guión bajo), excepto cuando se requiere disambiguación de contexto múltiple (ver sección 8.8).

## 5. Convención de nombre físico

### Estructura general


<prefijo><concepto>[<contexto>][<sufijo_opcional>]


### Componentes

- *prefijo*: Tipo de dato (obligatorio) - ver tabla 4.1
- *concepto*: Descripción del negocio (obligatorio) - en singular
- *contexto*: Contexto adicional cuando sea necesario para disambiguación (opcional)
- *sufijo*: Calificador temporal o de estado (opcional) - ver tabla 4.2

### Ejemplos bien formados

| Nombre físico | Significado | Análisis |
|---------------|-------------|----------|
| idpoliza | Identificador único de la póliza | prefijo: id + concepto: poliza |
| codproducto | Código del producto | prefijo: cod + concepto: producto |
| fecemisionpoliza | Fecha de emisión de la póliza | prefijo: fec + concepto: emisionpoliza |
| primaneta | Prima neta | prefijo: prima + sufijo: neta |
| primabruta | Prima bruta | prefijo: prima + sufijo: bruta |
| flgobservado | Indicador de registro observado | prefijo: flg + concepto: observado |
| ctdsiniestros | Cantidad de siniestros | prefijo: ctd + concepto: siniestros |
| desestadopoliza | Descripción del estado de póliza | prefijo: des + concepto: estadopoliza |
| telefmovil | Teléfono móvil | prefijo: tel + concepto: movil |
| porccomision | Porcentaje de comisión | prefijo: porc + concepto: comision |

## 6. Campos técnicos transversales (UDV)

Estos campos son *obligatorios y estandarizados* en *TODAS* las entidades UDV. Son campos técnicos de control de calidad y auditoría.

### 6.1 Tabla de campos técnicos

| Nombre físico | Prefijo | Tipo de dato | Descripción | Obligatorio |
|---------------|---------|--------------|-------------|-------------|
| codapp | cod | STRING | Código de la aplicación origen | ✅ Siempre |
| feccargainfo | fec | DATE | Fecha de carga de la información | ✅ Siempre |
| periododia | periodo | STRING | Periodo diario de ejecución (yyyyMMdd) | ✅ Siempre |
| flgvalido | flg | INT | Indica si el registro es técnicamente válido (1=válido, 0=inválido) | ✅ *Siempre* |
| flgobservado | flg | INT | Indica incumplimiento de reglas de negocio (1=observado, 0=sin observación) | ✅ *Siempre* |
| desmensajeobs | des | STRING | Detalle del motivo de observación | Cuando flgobservado=1 |
| flgactivo | flg | INT | Indica si el registro está activo (1=activo, 0=inactivo) | Cuando aplica soft delete |

*⚠️ Importante:*
- flgvalido y flgobservado son *campos técnicos obligatorios* en *TODAS* las entidades UDV
- Sirven para control de calidad de datos y trazabilidad de validaciones
- flgvalido=0 indica problema técnico (estructura, tipos de datos, integridad referencial)
- flgobservado=1 indica incumplimiento de reglas de negocio (valores fuera de rango, inconsistencias lógicas)

### 6.2 Uso de campos técnicos

*Campos de auditoría (siempre presentes):*

codapp, feccargainfo, periododia


*Campos de calidad de datos (obligatorios en todas las entidades):*

flgvalido, flgobservado, desmensajeobs


*Campos de control (cuando aplica soft delete):*

flgactivo


### 6.3 Ejemplo de uso

sql
-- Registro válido y sin observaciones
flgvalido = 1
flgobservado = 0
desmensajeobs = NULL

-- Registro válido pero observado (advertencia de negocio)
flgvalido = 1
flgobservado = 1
desmensajeobs = 'Prima menor al mínimo establecido para el producto'

-- Registro técnicamente inválido
flgvalido = 0
flgobservado = 0
desmensajeobs = 'Integridad referencial: codproducto no existe en catálogo'


## 7. Definición formal de campos (documentación)

Cada campo debe documentarse con:

1. *Nombre lógico*: Descripción en lenguaje de negocio
2. *Nombre físico*: Nombre técnico en la base de datos
3. *Tipo de prefijo*: Categoría del campo
4. *Tipo de dato*: Tipo SQL (VARCHAR, INTEGER, DATE, DECIMAL, etc.)
5. *Descripción*: Explicación completa del significado semántico
6. *Valores permitidos*: Dominio de valores cuando aplica
7. *Relación con ACORD*: Mapeo a conceptos ACORD cuando existe

### 7.1 Ejemplo – Campo identificador

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Identificador único de la póliza |
| *Nombre físico* | idpoliza |
| *Tipo* | id |
| *Tipo de dato* | BIGINT |
| *Descripción* | Llave subrogada única que identifica a la póliza en las capas UDV y DDV. Generada automáticamente durante el proceso de integración. No tiene significado de negocio. |
| *Relación ACORD* | Policy.id (surrogate key) |

### 7.2 Ejemplo – Campo de fecha

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Fecha de pago |
| *Nombre físico* | fecpago |
| *Tipo* | fec |
| *Tipo de dato* | DATE |
| *Descripción* | Fecha exacta de procesamiento del pago en formato yyyy-MM-dd según ISO 8601. Representa la fecha en que el pago fue efectivamente procesado por el sistema, no la fecha de compromiso o vencimiento. |
| *Relación ACORD* | Payment.PaymentDate |

### 7.3 Ejemplo – Campo de prima

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Prima neta |
| *Nombre físico* | primaneta |
| *Tipo* | prima |
| *Tipo de dato* | DECIMAL(18,2) |
| *Descripción* | Prima neta de la póliza, calculada como prima bruta menos descuentos y recargos. Expresado en la moneda de la póliza. |
| *Relación ACORD* | Policy.CurrentTermAmount.Amt (NetPremium) |

### 7.4 Ejemplo – Campo flag técnico

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Indicador de registro observado |
| *Nombre físico* | flgobservado |
| *Tipo* | flg |
| *Tipo de dato* | TINYINT |
| *Descripción* | Indica si el registro presenta algún incumplimiento a las reglas de negocio propias de la entidad durante la carga de datos. |
| *Valores permitidos* | 1 = observado, 0 = sin observación |
| *Uso técnico* | Campo de calidad de datos para filtrado y reporting de excepciones |

### 7.5 Ejemplo – Campo descriptivo de observación

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Mensaje de observación |
| *Nombre físico* | desmensajeobs |
| *Tipo* | des |
| *Tipo de dato* | VARCHAR(500) |
| *Descripción* | Describe el motivo por el cual el registro fue marcado como observado según las reglas de negocio aplicadas. Contiene mensaje técnico para troubleshooting y análisis de calidad. |
| *Uso técnico* | Diagnóstico de calidad de datos y trazabilidad de validaciones |

### 7.6 Ejemplo – Campo de código con catálogo

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Código de tipo de documento |
| *Nombre físico* | codtipodocumento |
| *Tipo* | cod |
| *Tipo de dato* | VARCHAR(10) |
| *Descripción* | Código que identifica el tipo de documento de identidad según catálogo estandarizado. |
| *Valores permitidos* | DNI, CE, PASAPORTE, RUC, etc. (referencia a lkp_tipo_documento) |
| *Relación ACORD* | Party.GovernmentIssuedID.CommercialName |

## 8. Reglas específicas y prohibiciones

### 8.1 Fechas: siempre con evento explícito

El nombre del campo debe indicar *qué representa la fecha*, no solo que es una fecha.

❌ *Incorrecto:*

fecinicio
fecfin
fecha
fec


✅ *Correcto:*

feciniciovigencia      // Fecha de inicio de vigencia
fecfinvigencia         // Fecha de fin de vigencia
fecemisionpoliza       // Fecha de emisión de póliza
fecvencimientopago     // Fecha de vencimiento de pago
fecregistrosiniestro   // Fecha de registro del siniestro


*Fundamento:* Evita ambigüedad. Una póliza tiene múltiples fechas (emisión, vigencia, vencimiento, cancelación). El nombre debe ser autoexplicativo.

### 8.2 Montos: siempre con concepto específico

*Regla general para montos:* Nunca usar términos genéricos. Siempre especificar *qué se está midiendo*.

*Importante:* Las *primas NO llevan prefijo mto*, se expresan directamente como prima[sufijo].

❌ *Prohibido:*

mtomonto
mtovalor
mtoprecio
mto
mtoprimaneta      // Incorrecto: primas no llevan prefijo mto


✅ *Correcto para primas:*

primaneta          // Prima neta
primabruta         // Prima bruta
primacotizada      // Prima en cotización
primaemitida       // Prima emitida
primacobrada       // Prima cobrada
primasoles         // Prima en soles
primadolares       // Prima en dólares


✅ *Correcto para otros montos (SÍ llevan prefijo mto):*

mtodeducible           // Monto del deducible
mtosumaasegurada       // Monto de suma asegurada
mtoreservasiniestro    // Monto de reserva de siniestro
mtopagoreclamacion     // Monto de pago de reclamación
mtocomisionagente      // Monto de comisión del agente
mtoreembolso           // Monto de reembolso
mtogastosiniestro      // Monto de gastos de siniestro


*Fundamento:* En seguros, las primas son un concepto fundamental que merece su propio prefijo semántico. Otros montos (deducibles, sumas aseguradas, comisiones, siniestros) sí llevan el prefijo mto para diferenciarse.

### 8.3 Uso correcto de flags vs indicadores

*Regla de oro:*

- flg → Valores numéricos binarios: *0 / 1*
- ind → Valores alfanuméricos: *S / N, SI / NO, Y / N*

*No deben mezclarse.*

*Ejemplos:*

sql
-- FLAGS (0/1)
flgobservado       TINYINT     -- 0 o 1
flgvalido          TINYINT     -- 0 o 1
flgactivo          TINYINT     -- 0 o 1

-- INDICADORES (S/N)
indrenovacion      CHAR(1)     -- 'S' o 'N'
indcoberturatotal  CHAR(1)     -- 'S' o 'N'
indpolizaactiva    VARCHAR(2)  -- 'SI' o 'NO'


*Fundamento:* Oracle Business Analytics Warehouse y estándares de data warehousing diferencian flags booleanos de indicadores alfanuméricos para optimización de almacenamiento y queries.

### 8.4 Cantidades: siempre con unidad implícita

Cuando el campo representa una cantidad, debe quedar claro *qué se está contando*.

❌ *Incorrecto:*

cantidad
ctd
num


✅ *Correcto:*

ctdsiniestros          // Cantidad de siniestros
ctdpolizasemitidas     // Cantidad de pólizas emitidas
ctdasegurados          // Cantidad de asegurados
ctdreclamaciones       // Cantidad de reclamaciones
numcuotas              // Número de cuotas
numbeneficiarios       // Número de beneficiarios


### 8.5 Nombres descriptivos: evitar abreviaturas crípticas

Usar nombres completos y claros. Las abreviaturas solo se permiten cuando son estándar y ampliamente conocidas.

❌ *Evitar:*

desobspol          // ¿Qué significa "obs"?
mtopnb             // ¿Prima neta bruta?
flgpv              // ¿Póliza vigente? ¿Pago vencido?
codtdoc            // ¿Tipo documento?


✅ *Usar:*

desobservacionpoliza
mtoprimanetabruta      // O mejor: mtoprimabruta
flgpolizavigente
codtipodocumento


*Fundamento:* Kimball Group y estándares modernos de DW priorizan claridad sobre brevedad. Los nombres deben ser autoexplicativos para analistas de negocio.

### 8.6 Coherencia con nomenclatura de entidades

Si la entidad se llama hd_poliza_movimiento_gen_core, los campos relacionados deben usar poliza como concepto, no variaciones.

✅ *Consistente:*

idpoliza
codpoliza
fecemisionpoliza
primapoliza           // Prima relacionada con póliza


❌ *Inconsistente:*

idpolicy           // Mezcla inglés-español
codpol             // Abreviatura no estandarizada
fecemision         // Falta contexto de qué se emite
mtoprime           // Nombre incorrecto


### 8.7 Evitar redundancia con nombre de tabla

Si el campo está en la tabla hd_poliza_movimiento_gen_core, *no es necesario* repetir "poliza" en todos los campos, *excepto cuando sea necesario para claridad*.

*Balance recomendado:*

sql
-- Tabla: hd_poliza_movimiento_gen_core

-- IDs y códigos: SÍ incluir contexto
idpoliza              -- ✅ Claridad en joins
codproducto           -- ✅ Qué producto

-- Descripciones y atributos: contexto opcional
destipomovimiento     -- ✅ Es un atributo del movimiento
fecemision            -- ⚠️ ¿Emisión de qué? Mejor: fecemisionpoliza
primaneta             -- ✅ Ya se entiende que es de la póliza
flgobservado          -- ✅ Es el registro observado

-- Campos técnicos: NO incluir contexto
codapp                -- ✅ Estándar transversal
feccargainfo          -- ✅ Estándar transversal


*Fundamento:* Baeldung y estándares modernos recomiendan evitar redundancia excesiva, pero priorizar claridad en campos que se usan en joins o que podrían ser ambiguos.

### 8.8 Uso de guión bajo (_) para múltiples contextos

*Regla:* Usar guión bajo (_) *SOLO* cuando en la misma entidad existen campos con el mismo concepto pero diferentes contextos.

*Cuándo usar guión bajo:*

sql
-- Tabla que tiene AMBOS conceptos (póliza Y certificado):
feciniciovigencia_poliza      -- ✅ Con guión bajo (contexto póliza)
fecfinvigencia_poliza         -- ✅ Con guión bajo (contexto póliza)
feciniciovigencia_cert        -- ✅ Con guión bajo (contexto certificado)
fecfinvigencia_cert           -- ✅ Con guión bajo (contexto certificado)
primaanual_poliza             -- ✅ Con guión bajo (contexto póliza)
primaanual_cert               -- ✅ Con guión bajo (contexto certificado)


*Cuándo NO usar guión bajo:*

sql
-- Tabla que SOLO tiene concepto de póliza:
feciniciovigencia             -- ✅ Sin guión bajo (contexto único implícito)
fecfinvigencia                -- ✅ Sin guión bajo (contexto único implícito)
primaanual                    -- ✅ Sin guión bajo (contexto único implícito)

-- Tabla que SOLO tiene concepto de certificado:
feciniciovigencia             -- ✅ Sin guión bajo (contexto único implícito)
fecfinvigencia                -- ✅ Sin guión bajo (contexto único implícito)


*Fundamento:* El guión bajo actúa como *disambiguador* cuando existe potencial de confusión entre múltiples contextos en la misma entidad. Si solo hay un contexto, el guión bajo es redundante.

## 9. Nombres de campos en contextos multi-moneda

En entornos donde se manejan múltiples monedas, usar sufijos estándar de moneda *SIN separador* (sin guión bajo).

### 9.1 Estándar de sufijos de moneda

*Decisión de estándar:*
- Para campos *específicos de Perú*: usar soles y dolares (nombres completos)
- Para campos *genéricos internacionales*: usar mn (moneda nacional) y me (moneda extranjera)
- Para campos *multi-país*: usar local (moneda del país) y corp (moneda corporativa)

### 9.2 Patrones recomendados

#### *Patrón 1: Nombres completos (preferido para primas y sumas aseguradas)*


<concepto><moneda_completa>


*Ejemplos:*
sql
primasoles              -- Prima en soles peruanos (PEN)
primadolares            -- Prima en dólares estadounidenses (USD)
primaneta soles          -- Prima neta en soles
primanetadolares        -- Prima neta en dólares
primabrutasoles          -- Prima bruta en soles
primabrutadolares       -- Prima bruta en dólares
sumaasegsoles           -- Suma asegurada en soles
sumaasegdolares         -- Suma asegurada en dólares


#### *Patrón 2: Abreviaturas (para otros montos)*


mto<concepto>mn         -- Moneda nacional
mto<concepto>me         -- Moneda extranjera


*Ejemplos:*
sql
mtopagomn               -- Monto de pago en moneda nacional (PEN)
mtopagome               -- Monto de pago en moneda extranjera (USD)
mtodeduciblemn          -- Deducible en moneda nacional
mtodeducibleme          -- Deducible en moneda extranjera
mtocomisionmn           -- Comisión en moneda nacional
mtocomisionme           -- Comisión en moneda extranjera


#### *Patrón 3: Moneda local vs corporativa*


<concepto>local         -- Moneda local del país de operación
<concepto>corp          -- Moneda corporativa para consolidación


*Ejemplos:*
sql
primalocal              -- Prima en moneda local (varía según país)
primacorp               -- Prima en moneda corporativa (ej: USD para consolidación)
sumaaseglocal           -- Suma asegurada en moneda local
sumaasegcorp            -- Suma asegurada en moneda corporativa


### 9.3 Regla de decisión

| Tipo de campo | Patrón recomendado | Ejemplo |
|---------------|-------------------|---------|
| Prima | Nombres completos | primasoles, primadolares |
| Suma asegurada | Nombres completos | sumaasegsoles, sumaasegdolares |
| Otros montos | Abreviaturas | mtopagomn, mtopagome |
| Multi-país | local/corp | primalocal, primacorp |

### 9.4 Diferencia local vs. corporativa

- *local*: Moneda del país donde se emite la póliza (ej: soles en Perú, pesos en Chile, soles en Bolivia)
- *corp*: Moneda única para consolidación corporativa global (ej: USD para todo el grupo)

*Cuándo usar cada una:*
- Usar soles o dolares cuando el valor está *explícitamente* en esa moneda específica (Perú)
- Usar mn/me para montos genéricos en contexto binario moneda nacional vs extranjera
- Usar local cuando el valor está en la moneda del país, sin importar cuál sea (multi-país)
- Usar corp para valores convertidos a moneda corporativa para reporting consolidado

## 10. Campos derivados y calculados

Campos que son resultado de cálculos o transformaciones deben documentarse claramente.

### 10.1 Ejemplo de campo calculado

| Atributo | Valor |
|----------|-------|
| *Nombre lógico* | Prima total anual |
| *Nombre físico* | primatotalanual |
| *Tipo* | prima |
| *Tipo de dato* | DECIMAL(18,2) |
| *Descripción* | Prima total anual calculada como suma de todas las primas del año. Fórmula: SUM(primaneta) por poliza por año |
| *Derivación* | Calculado en capa UDV mediante agregación temporal |
| *Metadata adicional* | derivation_type = aggregated |

### 10.2 Sufijos para campos derivados

| Sufijo | Significado | Ejemplo | Uso |
|--------|-------------|---------|-----|
| agg | Agregado | primaagg | Valor agregado de múltiples registros |
| prom | Promedio | primaprom | Promedio aritmético |
| acum | Acumulado | primaacum | Acumulación progresiva en el tiempo |
| ult3m | Últimos 3 meses | primapromult3m | Promedio de últimos 3 meses |
| ult6m | Últimos 6 meses | primault6m | Total últimos 6 meses |
| ult12m | Últimos 12 meses | primapromult12m | Promedio últimos 12 meses |
| ytd | Year to date | primaytd | Acumulado año actual |
| mtd | Month to date | primamtd | Acumulado mes actual |

### 10.3 Ejemplos de campos derivados con sufijos temporales

sql
-- Agregaciones
primaagg                -- Prima agregada (suma total)
primapromagg            -- Prima promedio agregada

-- Promedios temporales
primapromult3m          -- Promedio de prima últimos 3 meses
mtodeduciblepromult6m   -- Promedio de deducible últimos 6 meses

-- Acumulados
primaacumytd            -- Prima acumulada año a la fecha
primane

taacummtd        -- Prima neta acumulada mes a la fecha

-- Totales con ventana temporal
primatotalult12m        -- Total de prima últimos 12 meses
ctdsiniestrosult3m      -- Cantidad de siniestros últimos 3 meses


### 10.4 Consideraciones sobre semántica

*Evitar nombres ambiguos como:*
- ❌ primanetacalc - No queda claro qué cálculo se realiza
- ❌ primacalculada - Demasiado genérico

*Preferir nombres descriptivos:*
- ✅ primatotalanual - Claro: total anual
- ✅ primaprom_ult3m - Claro: promedio últimos 3 meses
- ✅ prima_acum_ytd - Claro: acumulado año a la fecha

## 11. Relación con modelamiento federado

Todo nuevo campo propuesto en una entidad UDV debe:

1. *Respetar esta nomenclatura* de forma obligatoria
2. *Reutilizar nombres existentes* cuando el concepto ya existe en el modelo corporativo
3. *Sustentarse semánticamente* en la Ficha UDV correspondiente
4. *Ser aprobado por Arquitectura de Datos* si introduce una nueva semántica
5. *Documentarse formalmente* con definición completa (sección 7)
6. *Mapearse a ACORD* cuando el concepto existe en el Information Model

### Proceso de aprobación de nuevos campos

mermaid
graph TD
    A[Squad propone nuevo campo] --> B{¿Campo existe?}
    B -->|Sí| C[Reutilizar nombre existente]
    B -->|No| D[Documentar en Ficha UDV]
    D --> E[Validar con Arquitectura de Datos]
    E --> F{¿Aprobado?}
    F -->|Sí| G[Incorporar a catálogo corporativo]
    F -->|No| H[Revisar y ajustar]
    H --> D
    C --> I[Implementar en entidad]
    G --> I


## 12. Catálogo de campos corporativos reutilizables

### 12.1 Campos de identificación (comunes en todas las entidades)

| Nombre físico | Descripción | Entidades típicas |
|---------------|-------------|-------------------|
| idpoliza | ID único de póliza | Todas relacionadas con Policy |
| idcliente | ID único de cliente | Todas relacionadas con Party |
| idproducto | ID único de producto | Policy, Product |
| idsiniestro | ID único de siniestro | Claim |
| idbeneficiario | ID único de beneficiario | Policy, Claim |
| idagente | ID único de agente/intermediario | Policy, Commission |

### 12.2 Campos temporales (alta reutilización)

| Nombre físico | Descripción | Uso típico |
|---------------|-------------|------------|
| fecemision | Fecha de emisión | Documentos, pólizas |
| fecvigenciainicio | Fecha inicio vigencia | Pólizas, coberturas, contratos |
| fecvigenciafin | Fecha fin vigencia | Pólizas, coberturas, contratos |
| fecvencimiento | Fecha de vencimiento | Pagos, cuotas |
| fecregistro | Fecha de registro en sistema | Siniestros, reclamaciones |
| feccancelacion | Fecha de cancelación | Pólizas, contratos |

### 12.3 Campos de prima y montos (sector seguros)

| Nombre físico | Descripción | Contexto ACORD |
|---------------|-------------|----------------|
| primabruta | Prima bruta | Policy.GrossPremium |
| primaneta | Prima neta | Policy.NetPremium |
| primacotizada | Prima cotizada | Quote.QuotedPremium |
| primaemitida | Prima emitida | Policy.IssuedPremium |
| primacobrada | Prima cobrada | Policy.CollectedPremium |
| mtosumaasegurada | Suma asegurada | Coverage.Limit |
| mtodeducible | Deducible | Coverage.Deductible |
| mtoreserva | Reserva técnica | Claim.Reserve |
| mtopagoreclamacion | Pago de reclamación | Claim.PaymentAmount |
| mtocomision | Comisión | Commission.Amount |

## 13. Validación y cumplimiento

### 13.1 Checklist de validación de nombres de campos

Antes de aprobar un campo, verificar:

- [ ] ✅ Tiene prefijo semántico obligatorio
- [ ] ✅ Usa lowercase sin separadores
- [ ] ✅ No contiene tildes ni caracteres especiales
- [ ] ✅ No usa abreviaturas crípticas
- [ ] ✅ El nombre es autoexplicativo
- [ ] ✅ Reutiliza nombres existentes si el concepto ya existe
- [ ] ✅ Sigue las reglas de fechas (evento explícito)
- [ ] ✅ Sigue las reglas de montos (concepto específico)
- [ ] ✅ Usa correctamente flg (0/1) vs ind (S/N)
- [ ] ✅ Está documentado formalmente (sección 7)
- [ ] ✅ Tiene metadata obligatoria cuando aplica

### 13.2 Herramientas de validación

El Knowledge Assistant puede:

1. *Validar sintaxis* de nombres de campos contra este estándar
2. *Sugerir correcciones* para nombres que no cumplen
3. *Detectar duplicados* semánticos (mismo concepto, diferentes nombres)
4. *Recomendar reutilización* de campos existentes
5. *Generar documentación* automática en formato estándar

## 14. Consideraciones finales

### 14.1 Importancia del estándar

La nomenclatura de campos en UDV:

- ✅ *Es obligatoria* para todas las entidades de la capa Silver
- ✅ *Forma parte del modelo semántico corporativo*
- ✅ *No es una decisión local del squad*
- ✅ *Requiere validación de Arquitectura de Datos*
- ✅ *Se alinea con estándares internacionales* (ACORD, ISO, Kimball)

### 14.2 Beneficios de aplicación rigurosa

Su correcta aplicación:

- ✅ *Reduce deuda semántica* del Lakehouse
- ✅ *Mejora calidad de datos* y confiabilidad
- ✅ *Habilita reutilización transversal* entre dominios
- ✅ *Facilita integración* con sistemas externos
- ✅ *Acelera desarrollo* de nuevas capacidades analíticas
- ✅ *Mejora razonamiento* del Knowledge Assistant

### 14.3 Evolución del estándar

Este estándar es un *documento vivo* que evoluciona con:

- Nuevos casos de uso de negocio
- Incorporación de dominios adicionales
- Actualización de estándares ACORD
- Mejores prácticas emergentes de la industria

*Proceso de evolución:*

1. Propuesta documentada de cambio
2. Análisis de impacto en modelo existente
3. Validación con stakeholders (Arquitectura, Squads, Gobierno)
4. Aprobación formal
5. Actualización de documentación
6. Comunicación a equipos

---

## Resumen de Prefijos por Categoría

### Identificación

id, cod, codclave


### Temporales

fec, periodo, ts, anio, mes, trim, hora


### Indicadores

flg, ind, tip


### Numéricos

mto, ctd, num, porc, tasa, peso


### Textuales

des, nom, titulo, dir, email, tel, url, nota, obs


### Geográficos

pais, ciudad, region, distrito, codpostal, latitud, longitud


### Seguros (primas sin prefijo mto)

prima, poliza, cert, siniestro, cobert, ded, sumaaseg, benef


### Abreviaturas temporales comunes

_ini (inicio), _fin (final)
_ult3m (últimos 3 meses), _ult6m, _ult12m
_ytd (year to date), _mtd (month to date)
_agg (agregado), _prom (promedio), _acum (acumulado)


---

*Documento alineado con:*
- ACORD Data Standards (NDR, Information Model)
- Azure Databricks SQL tipos de datos
- Mejores prácticas de modelamiento dimensional