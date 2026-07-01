# Reglas de Diseño: Entidades vs Atributos (UDV/DDV)
## Granularidad, Reutilización y Cardinalidades

---

## 1. Propósito del documento
Este estándar define *reglas de decisión* para responder consistentemente:
❓ *¿Cuándo modelar como entidad vs atributo?*  
❓ *¿Cómo validar la granularidad correcta (grano)?*  
❓ *¿Cuándo reutilizar vs especializar* (federación)?  
❓ *¿Qué cardinalidades son permitidas* y cómo representarlas?

### 1.1 Por qué es necesario
Decisiones incorrectas en este nivel generan:
❌ Duplicación semántica entre squads  
❌ Integraciones frágiles  
❌ Métricas inconsistentes en DDV  
❌ Retrabajo en revisiones de modelamiento  
❌ Imposibilidad de reutilización  
❌ Linaje de datos roto  

### 1.2 Contexto de modelo federado
Este documento está pensado para *modelamiento federado*:
- Los squads pueden *proponer* diseños
- Pero el criterio debe ser *común y defendible*
- Arquitectura de Datos valida consistencia
- Data Governance aprueba excepciones
---

## 2. Alcance del documento

### 2.1 ✅ Aplica a
Este estándar aplica a decisiones de *diseño lógico* de:

| Capa | Tipos de entidades |
|------|-------------------|
| *UDV (Silver)* | Históricas, Maestras, Últimas |
| *DDV (Gold)* | Datasets, Facts, Dimensions, Feature Tables |

### 2.2 ✅ Cubre
1. *Decisión entidad vs atributo*
2. *Definición de granularidad* (grano)
3. *Reglas de reutilización/especialización* en modelo federado
4. *Cardinalidades permitidas* (1-1, 1-N, N-N) y su representación

### 2.3 ❌ No cubre
- *Nomenclatura* de entidades/atributos (ver documentos 01 y 02)
- *Diseño físico* (particionado, performance, clustering)
- *Implementación ETL/ELT* (pipelines, transformaciones)
- *Tipos de dato* específicos (ver documento 02)

---

## 3. Principio fundamental: Significado vs Consumo

### 3.1 Regla de oro

mermaid
graph LR
    A[UDV - Silver] --> |"Custodia el"| B[SIGNIFICADO]
    C[DDV - Gold] --> |"Custodia el"| D[CONSUMO]
    
    style A fill:#E3F2FD
    style B fill:#BBDEFB
    style C fill:#F3E5F5
    style D fill:#E1BEE7


*Implicación*:

| Decisión | Dónde se toma | Razón |
|----------|---------------|-------|
| Crear nueva entidad con significado propio | *UDV* | Define semántica del negocio |
| Crear nueva entidad para análisis | *DDV* | Optimiza consumo, no redefine significado |
| Cambiar grano de una entidad | *UDV* | Afecta significado canónico |
| Agregar atributos derivados | *DDV* | Facilita análisis, no cambia semántica |

*Ejemplo*:

sql
-- ✅ CORRECTO: UDV define semántica
-- udv_prod.sch_gen.md_dac_persona
CREATE TABLE md_dac_persona (
  idpersona      BIGINT,
  numdoc         STRING,
  tipodoc        STRING,
  nompersona     STRING,
  ...
);

-- ✅ CORRECTO: DDV consume y agrega valor analítico
-- ddv_prod.sch_analytics.dim_cliente
CREATE TABLE dim_cliente (
  idcliente      BIGINT,      -- SK (referencia a idpersona de UDV)
  codcliente     STRING,      -- NK
  nomcliente     STRING,      -- De UDV
  segmento       STRING,      -- Derivado en DDV
  ...
);


---

## 4. Decisión 1: ¿Entidad o Atributo?

### 4.1 Árbol de decisión

mermaid
graph TD
    Start["¿Necesitas modelar el concepto?"]
    
    Start --> VidaPropia["¿Tiene vida propia?<br/>(puede existir sin el padre)"]
    
    VidaPropia -->|Sí| MultiAtrib["¿Tiene múltiples<br/>atributos (>3)?"]
    MultiAtrib -->|Sí| E1["✅ ENTIDAD"]
    MultiAtrib -->|No| Evaluar["Evaluar más criterios"]
    
    VidaPropia -->|No| Repite["¿Se repite (1-N)?"]
    Repite -->|Sí| E2["✅ ENTIDAD"]
    Repite -->|No| A1["✅ ATRIBUTO"]
    
    Start --> Reutiliza["¿Se reutiliza en<br/>múltiples entidades?"]
    Reutiliza -->|Sí| E3["✅ ENTIDAD"]
    Reutiliza -->|No| Historia["¿Necesita<br/>historia propia?"]
    Historia -->|Sí| E4["✅ ENTIDAD"]
    Historia -->|No| A2["✅ ATRIBUTO"]
    
    style E1 fill:#C8E6C9
    style E2 fill:#C8E6C9
    style E3 fill:#C8E6C9
    style E4 fill:#C8E6C9
    style A1 fill:#FFCCBC
    style A2 fill:#FFCCBC


### 4.2 Reglas claras: DEBE ser entidad cuando

| # | Regla | Ejemplo |
|---|-------|---------|
| 1 | *Tiene vida propia* (puede existir independientemente) | direccion puede existir sin persona |
| 2 | *Tiene múltiples atributos* (>3-5 atributos relevantes) | direccion tiene: calle, numero, distrito, ciudad, codpostal, ubigeo |
| 3 | *Se reutiliza* por múltiples entidades | producto usado por poliza, cotizacion, siniestro |
| 4 | *Requiere historia/vigencia propia* | agente cambia de región → SCD Type 2 |
| 5 | *Participa en relaciones* con otras entidades | cobertura se relaciona con poliza (N-N) |
| 6 | *Se repite* (cardinalidad 1-N o N-N) | Persona tiene múltiples telefono (1-N) |

### 4.3 Reglas claras: DEBE ser atributo cuando

| # | Regla | Ejemplo |
|---|-------|---------|
| 1 | *Propiedad atómica y estable* | estadocivil de persona |
| 2 | *No requiere relaciones propias* | sexo de persona (simple: M/F) |
| 3 | *No requiere historia independiente* | tipodoc de persona (hereda historia del registro) |
| 4 | *Descriptor o métrica directa* del grano | primaneta de póliza |
| 5 | *No se repite* (único por registro) | fecnacimiento de persona |

### 4.4 ❌ NO hacer (antipatrones)

sql
-- ❌ NO: Crear entidad solo por "comodidad del pipeline"
CREATE TABLE tmp_calculos_intermedios (
  idcalculo    BIGINT,
  valor1       DECIMAL,
  valor2       DECIMAL
  -- Sin significado de negocio
);

-- ❌ NO: Atributo que es realmente una lista (N-N escondido)
CREATE TABLE poliza (
  idpoliza     BIGINT,
  coberturas   STRING  -- ❌ "001,002,003" lista concatenada
);

-- ✅ SÍ: Entidad asociativa N-N
CREATE TABLE poliza_cobertura (
  idpoliza     BIGINT,
  idcobertura  BIGINT,
  ...
);


### 4.5 Ejemplos detallados

#### Ejemplo 1: Estado Civil (Atributo)

*Análisis*:
- ¿Vida propia? NO (depende de persona)
- ¿Múltiples atributos? NO (solo código y descripción)
- ¿Se reutiliza? NO (solo para persona)
- ¿Historia propia? NO (si cambia, se registra en persona)
- ¿Se repite? NO (una persona tiene UN estado civil a la vez)

*Decisión: ✅ **ATRIBUTO*

sql
CREATE TABLE md_dac_persona (
  idpersona        BIGINT,
  codestadocivil   STRING,      -- ✅ Atributo simple
  desestadocivil   STRING,      -- ✅ Descripción
  ...
);


#### Ejemplo 2: Dirección (Entidad)

*Análisis*:
- ¿Vida propia? SÍ (existe la dirección, esté o no asociada)
- ¿Múltiples atributos? SÍ (calle, numero, distrito, ciudad, codpostal, ubigeo, referencia)
- ¿Se reutiliza? SÍ (persona, empresa, agente pueden compartir direcciones)
- ¿Historia propia? SÍ (cambios de nomenclatura de calles)
- ¿Se repite? SÍ (1 persona puede tener N direcciones: casa, trabajo, fiscal)

*Decisión: ✅ **ENTIDAD*

sql
-- Entidad dirección
CREATE TABLE md_direccion (
  iddireccion      BIGINT,
  nomcalle         STRING,
  numcalle         STRING,
  distrito         STRING,
  ciudad           STRING,
  codpostal        STRING,
  ubigeo           STRING(6),
  referencia       STRING,
  ...
);

-- Relación persona-dirección (1-N)
CREATE TABLE persona_direccion (
  idpersona        BIGINT,      -- FK
  iddireccion      BIGINT,      -- FK
  tipdireccion     STRING,      -- 'casa', 'trabajo', 'fiscal'
  flgprincipal     INT,         -- 1 = principal
  fecinicio        DATE,
  fecfin           DATE,
  ...
);


#### Ejemplo 3: Teléfono (Entidad)

*Análisis*:
- ¿Vida propia? PARCIAL (identificado por número)
- ¿Múltiples atributos? SÍ (numero, tipo, extension, operador, flgwhatsapp)
- ¿Se reutiliza? POTENCIAL (mismo número compartido)
- ¿Historia propia? SÍ (cambios de operador, portabilidad)
- ¿Se repite? SÍ (1 persona tiene N teléfonos)

*Decisión: ✅ **ENTIDAD* (1-N)

sql
-- Entidad teléfono
CREATE TABLE md_telefono (
  idtelefono       BIGINT,
  numtelefono      STRING,
  tiptelefono      STRING,      -- 'celular', 'fijo', 'trabajo'
  extension        STRING,
  codoperador      STRING,
  flgwhatsapp      INT,
  ...
);

-- Relación persona-teléfono (1-N)
CREATE TABLE persona_telefono (
  idpersona        BIGINT,      -- FK
  idtelefono       BIGINT,      -- FK
  flgprincipal     INT,
  fecinicio        DATE,
  fecfin           DATE,
  ...
);


*❌ Antipatrón evitado*:

sql
-- ❌ NO hacer esto:
CREATE TABLE md_dac_persona (
  idpersona        BIGINT,
  telefono1        STRING,      -- ❌ Repetición numerada
  telefono2        STRING,      -- ❌ Límite arbitrario
  telefono3        STRING,      -- ❌ Muchos NULLs
  ...
);


---

## 5. Decisión 2: Granularidad (Grano)

### 5.1 Definición de grano

> *Grano: El nivel de detalle que representa **una fila* de la entidad.

*Formato de definición*:

"1 fila = [qué objeto/evento del mundo real representa]"


### 5.2 Ejemplos de grano bien definido

| Entidad | Grano | Ejemplo de fila |
|---------|-------|-----------------|
| hd_poliza_movimiento | 1 fila = 1 movimiento de 1 póliza en 1 fecha | Póliza 12345, Emisión, 2026-01-15 |
| md_dac_persona | 1 fila = 1 persona en su estado actual | Persona DNI 12345678 |
| ft_emision_poliza | 1 fila = 1 póliza emitida en 1 día | Póliza 12345, 2026-01-15 |
| dim_producto | 1 fila = 1 producto | Producto VIDA-001 |
| fs_cartera_snapshot | 1 fila = estado de 1 producto en 1 día | Producto VIDA-001, 2026-01-31 |

### 5.3 Reglas de validación de grano

#### Regla 1: DEBE definirse explícitamente antes de agregar atributos

sql
-- ✅ CORRECTO: Grano definido primero
-- Grano: 1 fila = 1 póliza en su movimiento diario

CREATE TABLE hd_poliza_movimiento (
  -- PK define el grano
  PRIMARY KEY (idpoliza, fecmovimiento, codtipomovimiento),
  
  idpoliza             BIGINT,
  fecmovimiento        DATE,
  codtipomovimiento    STRING,
  
  -- Atributos al mismo grano
  primaneta            DECIMAL(20,6),    -- ✅ Prima de ESTA póliza en ESTE movimiento
  codestado            STRING,           -- ✅ Estado en ESTE movimiento
  ...
);


#### Regla 2: NO agregar atributos de grano diferente

sql
-- ❌ INCORRECTO: Mezcla de granos
CREATE TABLE hd_poliza_movimiento (
  PRIMARY KEY (idpoliza, fecmovimiento),
  
  idpoliza             BIGINT,
  fecmovimiento        DATE,
  
  primaneta            DECIMAL(20,6),    -- ✅ Grano: movimiento
  
  primatotalanio       DECIMAL(20,6),    -- ❌ Grano: año (más grueso)
  primaultimacuota     DECIMAL(20,6),    -- ❌ Grano: cuota (más fino)
  
  -- Problemas:
  -- - primatotalanio se repite en todas las filas del año
  -- - primaultimacuota solo tiene sentido en UNA fila
);

-- ✅ CORRECTO: Separar granos
-- Grano movimiento (como está)
CREATE TABLE hd_poliza_movimiento (...);

-- Grano año (nueva entidad)
CREATE TABLE ha_poliza_resumen_anual (
  PRIMARY KEY (idpoliza, anio),
  primatotalanio       DECIMAL(20,6)    -- ✅ Grano correcto
);

-- Grano cuota (nueva entidad)
CREATE TABLE hd_cuota (
  PRIMARY KEY (idpoliza, numcuota),
  primacuota           DECIMAL(20,6)    -- ✅ Grano correcto
);


#### Regla 3: NO corregir error de grano con "parches"

sql
-- ❌ INCORRECTO: Parche con concatenación
CREATE TABLE hd_poliza_movimiento (
  idpoliza             BIGINT,
  fecmovimiento        DATE,
  
  -- ❌ Intentando meter N teléfonos en 1 campo
  telefonos            STRING,          -- "987654321|912345678|..."
  
  -- ❌ Intentando meter N coberturas en 1 campo
  coberturas           STRING           -- "001|002|003"
);

-- ✅ CORRECTO: Entidades del grano correcto
CREATE TABLE hd_poliza_movimiento (...);

CREATE TABLE poliza_telefono (
  idpoliza             BIGINT,
  idtelefono           BIGINT,
  ...
);

CREATE TABLE poliza_cobertura (
  idpoliza             BIGINT,
  idcobertura          BIGINT,
  ...
);


### 5.4 Grano en UDV vs DDV

| Aspecto | UDV (Silver) | DDV (Gold) |
|---------|-------------|-----------|
| *Propósito del grano* | Define *significado y trazabilidad* | Define *interpretabilidad analítica* |
| *Estabilidad* | Alta (cambia rara vez) | Media (puede cambiar por nuevos análisis) |
| *Nivel de detalle* | Atómico (máximo detalle) | Variable (según necesidad analítica) |
| *Ejemplos* | hd_poliza_movimiento: 1 movimiento de póliza | ft_emision_poliza: 1 póliza emitida<br>fs_cartera_snapshot: estado mensual |

### 5.5 Checklist de validación de grano

Antes de agregar un atributo, validar:

- [ ] ¿Cada fila representa exactamente *un objeto/evento*?
- [ ] ¿El atributo se define a ese *mismo nivel*?
- [ ] ¿El atributo NO fuerza *duplicación de filas*?
- [ ] ¿NO estoy mezclando "detalle" con "agregado"?
- [ ] ¿El atributo NO genera *NULLs masivos* porque no aplica a todas las filas?

*Si alguna validación falla*, se requiere:
1. Nueva entidad del grano correcto, O
2. Entidad asociativa (bridge), O
3. Mover el atributo a otra entidad existente del grano correcto

---

## 6. Decisión 3: Reutilización vs Especialización

### 6.1 Principio de reutilización (modelo federado)


┌──────────────────────────────────────────────┐
│ PRIMERO buscar entidad existente            │
│ DESPUÉS justificar por qué no aplica        │
│ SOLO ENTONCES crear nueva entidad           │
└──────────────────────────────────────────────┘


### 6.2 Reglas de reutilización

#### DEBE reutilizarse una entidad existente cuando:

| # | Condición | Ejemplo |
|---|-----------|---------|
| 1 | Representa el *mismo concepto* | cliente es cliente, no crear cliente_marketing |
| 2 | A la *misma granularidad* | Grano = 1 cliente |
| 3 | Con el *mismo significado* | Semántica canónica de "cliente activo" |

#### DEBE especializarse (subtipo o entidad derivada) SOLO cuando:

| # | Condición | Ejemplo | Acción |
|---|-----------|---------|--------|
| 1 | El *concepto cambia su significado* | "Cliente habilitado para embedded" tiene reglas distintas | Crear md_cliente_embedded con referencia a md_cliente |
| 2 | El *grano cambia* | Cliente agregado por región | Crear entidad agregada en DDV |
| 3 | El *conjunto de reglas es distinto* y justificable | Segmentación específica de marketing | Documentar reglas y crear vista derivada |

### 6.3 ❌ NO hacer (antipatrones)

sql
-- ❌ NO: Duplicar semántica sin justificación
CREATE TABLE md_cliente_marketing (
  idcliente        BIGINT,
  nomcliente       STRING,
  ...
  -- Mismo concepto, mismo grano, mismo significado que md_cliente
);

-- ❌ NO: Crear "otra tabla parecida" para un caso de uso puntual
CREATE TABLE md_cliente_v2 (
  ...
  -- Solo para un reporte específico
);

-- ❌ NO: Especializar sin documentar
CREATE TABLE md_cliente_especial (
  ...
  -- Sin documentación de por qué es "especial"
);


### 6.4 ✅ Proceso de validación de reutilización

*Workflow obligatorio*:

mermaid
graph TD
    Start["Squad quiere crear<br/>nueva entidad 'X'"]
    Start --> Buscar["1. Buscar entidad<br/>equivalente en UDV"]
    
    Buscar --> Existe{"¿Existe?"}
    
    Existe -->|No| Crear["Proceder con creación<br/>(revisar con Arquitectura)"]
    
    Existe -->|Sí| Concepto{"¿Mismo concepto?"}
    
    Concepto -->|No| Justif1["Justificar diferencia<br/>semántica documentada"]
    
    Concepto -->|Sí| Grano{"¿Mismo grano?"}
    
    Grano -->|No| Justif2["Justificar cambio<br/>de grano"]
    
    Grano -->|Sí| Reutil["✅ REUTILIZAR<br/>NO crear nueva"]
    
    style Crear fill:#FFF9C4
    style Justif1 fill:#FFCCBC
    style Justif2 fill:#FFCCBC
    style Reutil fill:#C8E6C9


### 6.5 Documentación obligatoria para especialización

Si se aprueba especialización, *DEBE documentarse*:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| *Entidad base* | De qué entidad se especializa | md_dac_cliente |
| *Regla que cambia* | Qué regla de negocio difiere | "Incluye solo clientes con productos activos" |
| *Grano que cambia* | Si el grano es diferente | "Agregado por región" vs "Detalle por cliente" |
| *Consumidores* | Quién requiere esta especialización | "Equipo de Marketing Digital", "Dashboards embebidos" |
| *Justificación* | Por qué no sirve la entidad base | "Requiere atributos específicos de scoring digital no aplicables a clientes tradicionales" |

*Metadata obligatoria*:

json
{
  "entity_name": "md_cliente_embedded",
  "specialization_of": "md_cliente",
  "specialization_reason": "Clientes con productos embedded tienen reglas de scoring digital específicas",
  "grain": "1 fila = 1 cliente con al menos 1 producto embedded activo",
  "business_rules": [
    "Solo clientes con flgembebido = 1",
    "Incluye scoring digital calculado por API externa",
    "Se actualiza diariamente (vs mensual en md_dac_cliente)"
  ],
  "consumers": ["Equipo Marketing Digital", "Dashboard Embedded"],
  "approval_date": "2026-02-15",
  "approved_by": "Arquitectura de Datos + Data Governance"
}


### 6.6 Casos válidos de especialización

#### Ejemplo 1: Cliente Embedded (Válido)

*Entidad base*: md_dac_cliente

*Especialización*: md_cliente_embedded

*Justificación*:
- ✅ Cambio de significado: "Cliente habilitado para embedded" ≠ "Cliente general"
- ✅ Reglas distintas: Scoring digital, validaciones API externa
- ✅ Atributos específicos: scoredigital, flgaprobadoapi, fecultimosync
- ✅ Consumidores específicos: Equipo de productos digitales

sql
-- Entidad base
CREATE TABLE md_dac_cliente (
  idcliente        BIGINT,
  codcliente       STRING,
  nomcliente       STRING,
  segmento         STRING,
  ...
);

-- Especialización válida
CREATE TABLE md_dac_cliente_embedded (
  idclienteembedded  BIGINT,        -- SK propio
  idcliente          BIGINT,        -- FK a md_cliente (herencia)
  
  -- Atributos específicos de embedded
  scoredigital       DECIMAL(5,2),
  flgaprobadoapi     INT,
  fecultimosync      TIMESTAMP,
  codpartner         STRING,
  
  -- Metadata
  feccargainfo       DATE
);


#### Ejemplo 2: Producto por Canal (NO válido - usar DDV)

*Intento*: Crear md_producto_canal con agregaciones por canal

*Evaluación*:
- ❌ Cambio de grano: Producto → Producto × Canal
- ❌ NO cambia significado de "producto"
- ❌ Es una agregación para análisis

*Solución correcta: Crear en **DDV*, no duplicar en UDV

sql
-- ❌ NO crear en UDV
CREATE TABLE md_producto_canal (
  idproducto       BIGINT,
  codcanal         STRING,
  ctdpolizas       INT,      -- Agregación
  primatotal       DECIMAL   -- Agregación
);

-- ✅ SÍ crear en DDV
CREATE TABLE ddv_prod.sch_analytics.producto_canal_metricas (
  idproducto       BIGINT,
  codcanal         STRING,
  periodomes       STRING,
  ctdpolizas       INT,
  primatotal       DECIMAL(20,6),
  ...
);


---

## 7. Decisión 4: Cardinalidades

### 7.1 Cardinalidades permitidas

| Cardinalidad | Descripción | Cuándo usar | Representación |
|--------------|-------------|-------------|----------------|
| *1-1* | Uno a uno | Raro; validar si es realmente 1 atributo o split técnico | FK en cualquier lado |
| *1-N* | Uno a muchos | Lo más común | FK en el lado "N" |
| *N-N* | Muchos a muchos | Común en seguros (póliza-cobertura) | Tabla puente/bridge |

### 7.2 Cardinalidad 1-1 (rara)

#### Cuándo usar 1-1

Solo en casos excepcionales:

1. *Split técnico por performance*: Atributos BLOB separados
2. *Split de seguridad*: Datos PII/DAC en tabla separada con control de acceso diferenciado
3. *Extensión de entidad*: Subtipo específico que solo aplica a ALGUNOS registros

#### Ejemplo válido de 1-1

sql
-- Entidad principal
CREATE TABLE md_dac_persona (
  idpersona        BIGINT PRIMARY KEY,
  numdoc           STRING,
  nompersona       STRING,
  ...
);

-- Extensión 1-1 para datos médicos (solo aplicable a asegurados)
CREATE TABLE md_persona_datos_medicos (
  idpersona        BIGINT PRIMARY KEY,  -- 1-1 con md_dac_persona
  
  gruposanguineo   STRING,
  alergias         STRING,
  enfermedades     STRING,
  ...
  
  FOREIGN KEY (idpersona) REFERENCES md_dac_persona(idpersona)
);


*Validación*: ¿Podría ser simplemente atributos en la entidad principal?

- ✅ SÍ usar 1-1: Si solo un % pequeño tiene estos datos (evita NULLs masivos)
- ✅ SÍ usar 1-1: Si requiere control de acceso diferenciado
- ❌ NO usar 1-1: Si todos los registros tienen estos datos (mejor como atributos)

### 7.3 Cardinalidad 1-N (la más común)

#### Representación estándar

sql
-- Lado "1" (padre)
CREATE TABLE md_dac_persona (
  idpersona        BIGINT PRIMARY KEY,
  nompersona       STRING,
  ...
);

-- Lado "N" (hijo) - FK apunta al padre
CREATE TABLE persona_direccion (
  idpersona        BIGINT,              -- FK (lado "N")
  iddireccion      BIGINT,
  tipdireccion     STRING,
  flgprincipal     INT,
  
  FOREIGN KEY (idpersona) REFERENCES md_dac_persona(idpersona)
);


#### Ejemplos comunes de 1-N

| Relación | Lado 1 | Lado N |
|----------|--------|--------|
| Persona → Teléfonos | md_dac_persona | persona_telefono |
| Persona → Direcciones | md_dac_persona | persona_direccion |
| Póliza → Cuotas | hd_poliza | hd_cuota |
| Cliente → Pólizas | md_cliente | hd_poliza |
| Producto → Pólizas | md_producto | hd_poliza |

### 7.4 Cardinalidad N-N (tabla puente/bridge)

#### Cuándo usar N-N

*Indicadores de N-N*:

1. Ambas entidades pueden tener múltiples relaciones con la otra
2. La relación tiene atributos propios
3. La relación tiene vigencia temporal

#### Ejemplo 1: Póliza - Cobertura (N-N)

*Análisis*:
- 1 póliza puede tener N coberturas
- 1 cobertura puede estar en N pólizas (reutilizable)
- La relación tiene atributos propios: suma asegurada específica, vigencia

*Representación*:

sql
-- Lado 1: Póliza
CREATE TABLE md_poliza (
  idpoliza         BIGINT PRIMARY KEY,
  numpoliza        BIGINT,
  ...
);

-- Lado 2: Cobertura
CREATE TABLE md_cobertura (
  idcobertura      BIGINT PRIMARY KEY,
  codcobertura     STRING,
  descobertura     STRING,
  ...
);

-- Tabla puente (Bridge) N-N
CREATE TABLE poliza_cobertura (
  idpoliza         BIGINT,              -- FK a poliza
  idcobertura      BIGINT,              -- FK a cobertura
  
  -- Atributos de la RELACIÓN
  sumaaseg         DECIMAL(20,2),       -- Suma asegurada específica
  primacobertura   DECIMAL(20,6),       -- Prima de esta cobertura
  fecinicio        DATE,                -- Vigencia inicio
  fecfin           DATE,                -- Vigencia fin
  flgprincipal     INT,                 -- 1 = cobertura principal
  
  PRIMARY KEY (idpoliza, idcobertura),
  FOREIGN KEY (idpoliza) REFERENCES md_poliza(idpoliza),
  FOREIGN KEY (idcobertura) REFERENCES md_cobertura(idcobertura)
);


#### Ejemplo 2: Siniestro - Afectado (N-N)

*Análisis*:
- 1 siniestro puede tener N afectados (siniestro vehicular con múltiples heridos)
- 1 persona puede estar en N siniestros (como afectado)

*Representación*:

sql
-- Lado 1: Siniestro
CREATE TABLE hd_siniestro (
  idsiniestro      BIGINT PRIMARY KEY,
  numsiniestro     BIGINT,
  ...
);

-- Lado 2: Persona
CREATE TABLE md_dac_persona (
  idpersona        BIGINT PRIMARY KEY,
  ...
);

-- Tabla puente (Bridge) N-N
CREATE TABLE siniestro_afectado (
  idsiniestro      BIGINT,
  idpersona        BIGINT,
  
  -- Atributos de la RELACIÓN
  rolafectado      STRING,              -- 'conductor', 'pasajero', 'peaton', 'tercero'
  gradolesion      STRING,              -- 'leve', 'grave', 'muerte'
  mtoindemnizacion DECIMAL(18,2),
  
  PRIMARY KEY (idsiniestro, idpersona),
  FOREIGN KEY (idsiniestro) REFERENCES hd_siniestro(idsiniestro),
  FOREIGN KEY (idpersona) REFERENCES md_dac_persona(idpersona)
);


### 7.5 ❌ Representaciones NO permitidas de N-N

#### ❌ Campos multivalor

sql
-- ❌ NO hacer esto
CREATE TABLE md_poliza (
  idpoliza         BIGINT,
  coberturas       STRING,              -- ❌ "001,002,003" concatenado
  ...
);


*Problemas*:
- ❌ No se pueden hacer joins
- ❌ No se pueden agregar atributos por cobertura
- ❌ No se puede validar integridad referencial
- ❌ No se puede consultar "pólizas con cobertura X"

#### ❌ Columnas repetidas

sql
-- ❌ NO hacer esto
CREATE TABLE md_poliza (
  idpoliza         BIGINT,
  idcobertura1     BIGINT,              -- ❌ Límite arbitrario
  idcobertura2     BIGINT,
  idcobertura3     BIGINT,
  sumaaseg1        DECIMAL,             -- ❌ Muchos NULLs
  sumaaseg2        DECIMAL,
  sumaaseg3        DECIMAL,
  ...
);


*Problemas*:
- ❌ Límite arbitrario (¿y si hay 4 coberturas?)
- ❌ Muchos NULLs si no llega a ese número
- ❌ Consultas complejas para agregar
- ❌ No normalizado

#### ✅ Solución correcta: Tabla puente

sql
-- ✅ Usar tabla puente
CREATE TABLE poliza_cobertura (
  idpoliza         BIGINT,
  idcobertura      BIGINT,
  sumaaseg         DECIMAL(20,2),
  ...
);


---

## 8. Casos especiales y excepciones

### 8.1 Tablas de lookup/catálogo pequeñas

*Pregunta*: ¿Tabla separada o atributo embebido?

*Regla*:

| Característica | Tabla separada | Atributo embebido |
|----------------|----------------|-------------------|
| *Tamaño* | >10 valores, cambios frecuentes | <=10 valores, estable |
| *Reutilización* | Múltiples entidades | Solo 1 entidad |
| *Complejidad* | Múltiples atributos | Solo código + descripción |

*Ejemplo: Tipo de Documento*

sql
-- Opción 1: Tabla separada (recomendado si se reutiliza)
CREATE TABLE md_tipo_documento (
  codtipodoc       STRING PRIMARY KEY,
  destipodoc       STRING,
  longitudvalida   INT,
  regex            STRING,
  ...
);

-- Opción 2: Atributo embebido (si es muy simple y no se reutiliza)
CREATE TABLE md_dac_persona (
  idpersona        BIGINT,
  tipodoc          STRING,              -- 'D', 'C', 'P', 'R'
  destipodoc       STRING,              -- 'DNI', 'CE', 'Pasaporte', 'RUC'
  numdoc           STRING,
  ...
);


*Decisión*:
- ✅ Tabla separada: Si hay validaciones complejas (regex, longitud) o se reutiliza
- ✅ Atributo embebido: Si es catálogo estable de <10 valores y solo para esta entidad

### 8.2 Atributos calculados/derivados

*Regla*:

| Capa | Estrategia |
|------|-----------|
| *UDV* | Evitar derivados; preservar datos atómicos |
| *DDV* | Permitir derivados para facilitar consumo |

*Ejemplo*:

sql
-- UDV: Solo atómicos
CREATE TABLE hd_poliza_movimiento (
  idpoliza         BIGINT,
  primaneta        DECIMAL(20,6),       -- ✅ Atómico
  mtoigv           DECIMAL(18,2),       -- ✅ Atómico
  mtorecargo       DECIMAL(18,2),       -- ✅ Atómico
  -- NO incluir primabruta (derivado de primaneta + mtoigv + mtorecargo)
);

-- DDV: Con derivados
CREATE TABLE ft_emision_poliza (
  idpoliza         BIGINT,
  primaneta        DECIMAL(20,6),       -- De UDV
  mtoigv           DECIMAL(18,2),       -- De UDV
  mtorecargo       DECIMAL(18,2),       -- De UDV
  primabruta       DECIMAL(20,6),       -- ✅ Derivado: primaneta + mtoigv + mtorecargo
  porccomision     DECIMAL(7,4),        -- ✅ Derivado para análisis
);


### 8.3 Atributos JSON/STRUCT anidados

*Regla: Usar con **extrema cautela* y solo cuando:

1. Esquema es variable y no se puede normalizar
2. No se requieren queries frecuentes sobre estos campos
3. Se consume principalmente de forma completa (no por partes)

*Ejemplo válido*:

sql
CREATE TABLE hd_api_request_log (
  idrequest        BIGINT,
  fecrequest       TIMESTAMP,
  endpoint         STRING,
  
  -- ✅ JSON para request/response (log técnico, no se consulta por partes)
  request_body     STRING,              -- JSON
  response_body    STRING,              -- JSON
  ...
);


*Ejemplo NO válido*:

sql
-- ❌ NO hacer esto
CREATE TABLE md_poliza (
  idpoliza         BIGINT,
  
  -- ❌ Coberturas como JSON (deberían ser tabla puente)
  coberturas       STRING               -- JSON: [{"cod":"001","suma":10000}, ...]
);


---

## 9. Errores comunes y antipatrones

### 9.1 Tabla de antipatrones

| # | Antipatrón | Problema | Solución |
|---|------------|----------|----------|
| 1 | *N-N como atributo multivalor* | coberturas STRING con "001,002,003" | Tabla puente poliza_cobertura |
| 2 | *1-N con columnas numeradas* | telefono1, telefono2, telefono3 | Tabla persona_telefono (1-N) |
| 3 | *Mezcla de granularidades* | Atributo de cuota en entidad póliza | Separar en entidad hd_cuota |
| 4 | *Duplicación semántica* | md_cliente + md_cliente_marketing sin justificación | Reutilizar md_cliente |
| 5 | *Entidad sin vida propia* | tmp_calculos solo para pipeline | Eliminar o mover a staging |
| 6 | *Atributo que es realmente entidad* | direccion STRING completa | Entidad md_direccion |
| 7 | *Grano inconsistente* | Prima anual en tabla de movimientos diarios | Separar en entidad agregada |
| 8 | *Especialización sin documentar* | md_cliente_v2 sin metadata | Documentar o reutilizar existente |
| 9 | *DDV redefine semántica UDV* | Cambio de significado en Gold | Cambio debe hacerse en Silver |
| 10 | *Tabla de lookup embebida* | Catálogo complejo como atributo | Tabla separada de lookup |

### 9.2 Ejemplos detallados de antipatrones

#### Antipatrón 1: N-N escondido en concatenación

sql
-- ❌ INCORRECTO
CREATE TABLE md_poliza (
  idpoliza         BIGINT,
  coberturas       STRING,              -- "VIDA,INVALIDEZ,MUERTE_ACC"
  sumas            STRING               -- "10000,5000,8000"
);

-- Problemas:
SELECT * FROM md_poliza WHERE coberturas LIKE '%VIDA%';  -- ❌ Ineficiente
-- ❌ No se pueden hacer joins
-- ❌ No se puede validar que las coberturas existan
-- ❌ No se puede agregar suma asegurada por cobertura específica

-- ✅ CORRECTO
CREATE TABLE md_poliza (
  idpoliza         BIGINT PRIMARY KEY,
  ...
);

CREATE TABLE md_cobertura (
  idcobertura      BIGINT PRIMARY KEY,
  codcobertura     STRING,
  descobertura     STRING
);

CREATE TABLE poliza_cobertura (
  idpoliza         BIGINT,
  idcobertura      BIGINT,
  sumaaseg         DECIMAL(20,2),
  PRIMARY KEY (idpoliza, idcobertura)
);

-- Ahora sí se puede consultar eficientemente:
SELECT p.*, c.*
FROM md_poliza p
JOIN poliza_cobertura pc ON p.idpoliza = pc.idpoliza
JOIN md_cobertura c ON pc.idcobertura = c.idcobertura
WHERE c.codcobertura = 'VIDA';


#### Antipatrón 2: Columnas numeradas (1-N escondido)

sql
-- ❌ INCORRECTO
CREATE TABLE md_dac_persona (
  idpersona        BIGINT,
  telefono1        STRING,
  tiptelefono1     STRING,
  telefono2        STRING,
  tiptelefono2     STRING,
  telefono3        STRING,
  tiptelefono3     STRING,
  ...
);

-- Problemas:
-- ❌ Límite arbitrario (¿y si tiene 4 teléfonos?)
-- ❌ Muchos NULLs si solo tiene 1 teléfono
-- ❌ Consultas complejas: "personas con teléfono celular"
SELECT * FROM md_dac_persona
WHERE tiptelefono1 = 'celular' 
   OR tiptelefono2 = 'celular'
   OR tiptelefono3 = 'celular';  -- ❌ Horrible

-- ✅ CORRECTO
CREATE TABLE md_dac_persona (
  idpersona        BIGINT PRIMARY KEY,
  nompersona       STRING,
  ...
);

CREATE TABLE persona_telefono (
  idpersona        BIGINT,
  idtelefono       BIGINT,
  numtelefono      STRING,
  tiptelefono      STRING,
  flgprincipal     INT,
  PRIMARY KEY (idpersona, idtelefono),
  FOREIGN KEY (idpersona) REFERENCES md_dac_persona(idpersona)
);

-- Ahora es simple:
SELECT DISTINCT p.*
FROM md_dac_persona p
JOIN persona_telefono pt ON p.idpersona = pt.idpersona
WHERE pt.tiptelefono = 'celular';  -- ✅ Limpio


#### Antipatrón 3: Mezcla de granos

sql
-- ❌ INCORRECTO
CREATE TABLE hd_poliza_movimiento (
  idpoliza         BIGINT,
  fecmovimiento    DATE,
  codtipomov       STRING,
  
  -- Grano correcto (movimiento)
  primaneta        DECIMAL(20,6),       -- ✅ Del movimiento
  
  -- Grano incorrecto (más grueso)
  primatotalanio   DECIMAL(20,6),       -- ❌ Del año (se repite)
  
  -- Grano incorrecto (más fino)
  primaultimacuota DECIMAL(20,6)        -- ❌ De la cuota (solo 1 fila relevante)
);

-- ✅ CORRECTO: Separar granos
-- Grano movimiento
CREATE TABLE hd_poliza_movimiento (
  idpoliza         BIGINT,
  fecmovimiento    DATE,
  primaneta        DECIMAL(20,6)
);

-- Grano año
CREATE TABLE ha_poliza_resumen_anual (
  idpoliza         BIGINT,
  anio             INT,
  primatotalanio   DECIMAL(20,6),
  PRIMARY KEY (idpoliza, anio)
);

-- Grano cuota
CREATE TABLE hd_cuota (
  idpoliza         BIGINT,
  numcuota         INT,
  primacuota       DECIMAL(20,6),
  PRIMARY KEY (idpoliza, numcuota)
);


---

## 10. Proceso de validación (checklist operativo)

### 10.1 Checklist para crear nueva entidad

Antes de crear una entidad, validar:

*Paso 1: Búsqueda de entidad existente*
- [ ] Busqué en el catálogo de UDV si ya existe una entidad similar
- [ ] Busqué en el catálogo de DDV si ya existe un producto similar
- [ ] Si existe, evalué si puedo reutilizar

*Paso 2: Validación de necesidad*
- [ ] La entidad tiene vida propia (puede existir independientemente)
- [ ] La entidad tiene >3 atributos relevantes
- [ ] La entidad se reutiliza en múltiples contextos O se requiere historia propia

*Paso 3: Definición de grano*
- [ ] Definí explícitamente el grano: "1 fila = [qué representa]"
- [ ] El grano está documentado en metadata
- [ ] Todos los atributos son consistentes con ese grano

*Paso 4: Validación de cardinalidades*
- [ ] Identifiqué las relaciones con otras entidades (1-1, 1-N, N-N)
- [ ] Si es N-N, creé tabla puente
- [ ] Si es 1-N, el FK está en el lado "N"

*Paso 5: Documentación*
- [ ] Documenté el propósito de la entidad
- [ ] Documenté el grano
- [ ] Documenté las relaciones (PKs, FKs)
- [ ] Si es especialización, documenté la justificación

### 10.2 Checklist para agregar atributo

Antes de agregar un atributo a una entidad existente:

- [ ] El atributo es del *mismo grano* que la entidad
- [ ] El atributo NO es realmente una *lista* (1-N o N-N escondido)
- [ ] El atributo NO fuerza *duplicación* de filas
- [ ] El atributo NO genera *NULLs masivos* (aplicable a la mayoría)
- [ ] El atributo NO es un *derivado* que debería calcularse en DDV
- [ ] El atributo tiene un *prefijo correcto* según el estándar

### 10.3 Checklist para relaciones N-N

Cuando identifico una relación N-N:

- [ ] Creé tabla puente con FKs a ambas entidades
- [ ] La tabla puente tiene PK compuesta (ambas FKs)
- [ ] Identifiqué atributos propios de la *relación* (no de las entidades)
- [ ] Consideré si la relación tiene vigencia temporal (fecinicio, fecfin)
- [ ] Validé que NO estoy usando campos multivalor ni concatenaciones

---

## 11. Impacto esperado

Aplicar estas reglas consistentemente:

### 11.1 Beneficios para el equipo

| Beneficio | Impacto |
|-----------|---------|
| ✅ *Reduce retrabajo* | Menos revisiones de modelamiento, menos refactorings |
| ✅ *Evita duplicación semántica* | Menos entidades "parecidas" entre squads |
| ✅ *Mejora consistencia* | Modelo más predecible y navegable |
| ✅ *Acelera incorporación* | Decisiones repetibles, menos debate |
| ✅ *Mejora Knowledge Assistant* | Respuestas más precisas sobre diseño |
| ✅ *Habilita gobernanza* | Linaje claro, calidad medible, auditoría sólida |

### 11.2 Métricas de éxito

| Métrica | Objetivo |
|---------|----------|
| % de entidades con grano documentado | >95% |
| % de relaciones N-N con tabla puente | 100% |
| Tiempo promedio de revisión de diseño | <50% vs baseline |
| # de entidades duplicadas (misma semántica) | <5 por año |
| % de squads que reutilizan entidades existentes | >70% |

---

## 12. Gobernanza y proceso de revisión

### 12.1 Roles y responsabilidades

| Rol | Responsabilidad |
|-----|-----------------|
| *Squad / Data Engineer* | Proponer diseño siguiendo este estándar |
| *Arquitectura de Datos* | Validar consistencia con modelo existente |
| *Data Governance* | Aprobar excepciones y especializaciones |
| *Data Steward* | Validar semántica de negocio |

### 12.2 Proceso de revisión de diseño

mermaid
graph TD
    Start["1. Squad propone diseño"]
    Start --> Check["2. Completa checklist<br/>de validación"]
    
    Check --> Arq["3. Arquitectura revisa:<br/>• Búsqueda de reutilización<br/>• Validación de grano<br/>• Validación de cardinalidades"]
    
    Arq --> Aprobado{"¿Aprobado?"}
    
    Aprobado -->|Sí| Impl["✅ Implementar"]
    
    Aprobado -->|No| Ajustes{"¿Requiere<br/>ajustes menores?"}
    
    Ajustes -->|Sí| Reenvio["Squad ajusta<br/>y re-envía"]
    Reenvio --> Arq
    
    Ajustes -->|No| Sesion["Sesión de diseño<br/>con Arquitectura"]
    
    style Impl fill:#C8E6C9
    style Sesion fill:#FFCCBC


### 12.3 Excepciones

*Proceso de aprobación de excepciones*:

1. Squad documenta justificación técnica y de negocio
2. Arquitectura evalúa impacto en modelo
3. Data Governance aprueba o rechaza
4. Si se aprueba, se documenta en metadata como excepción

*Ejemplos de excepciones válidas*:
- Especialización de entidad con reglas de negocio distintas (documentadas)
- Atributo JSON para logs técnicos (no se consulta por partes)
- Entidad temporal para migración (con fecha de sunset definida)

---

## Apéndice A: Árbol de decisión completo

mermaid
graph TD
    Start["¿Necesito modelar<br/>este concepto?"]
    
    Start --> Atomico{"¿Es ATÓMICO<br/>y ESTABLE?"}
    Start --> Vida{"¿Tiene VIDA<br/>PROPIA?"}
    
    Atomico -->|Sí| A1["✅ ATRIBUTO"]
    
    Vida -->|Sí| Multi{"¿Tiene >3<br/>ATRIBUTOS?"}
    
    Multi -->|Sí| E1["✅ ENTIDAD"]
    
    Multi -->|No| Repite1{"¿Se REPITE<br/>(1-N)?"}
    
    Repite1 -->|Sí| E2["✅ ENTIDAD<br/>(1-N)"]
    
    Repite1 -->|No| Historia{"¿Necesita<br/>HISTORIA propia?"}
    
    Historia -->|Sí| E3["✅ ENTIDAD<br/>(SCD)"]
    
    Historia -->|No| A2["✅ ATRIBUTO"]
    
    style E1 fill:#C8E6C9
    style E2 fill:#C8E6C9
    style E3 fill:#C8E6C9
    style A1 fill:#FFCCBC
    style A2 fill:#FFCCBC


---

## Apéndice B: Matriz de decisión rápida

| Pregunta | Entidad | Atributo |
|----------|---------|----------|
| ¿Vida propia? | ✅ Sí | ❌ No |
| ¿>3 atributos relevantes? | ✅ Sí | ❌ No |
| ¿Se reutiliza? | ✅ Sí | ❌ No |
| ¿Historia/vigencia propia? | ✅ Sí | ❌ No |
| ¿Participa en relaciones? | ✅ Sí | ❌ No |
| ¿Se repite (1-N o N-N)? | ✅ Sí | ❌ No |
| ¿Atómico y estable? | ❌ No | ✅ Sí |
| ¿Solo descriptor del padre? | ❌ No | ✅ Sí |

*Regla*: Si la mayoría de respuestas son ✅ en columna "Entidad" → Es ENTIDAD

---

## Apéndice C: Glosario

| Término | Definición |
|---------|------------|
| *Grano (Grain)* | Nivel de detalle que representa una fila de la entidad |
| *Cardinalidad* | Número de instancias en una relación (1-1, 1-N, N-N) |
| *Entidad asociativa* | Tabla que representa una relación N-N (bridge table) |
| *Especialización* | Subtipo de entidad con reglas específicas |
| *Reutilización* | Usar entidad existente en lugar de crear nueva |
| *Degenerate dimension* | Atributo dimensional que queda en el fact |
| *Surrogate key (SK)* | Llave técnica sin significado de negocio |
| *Natural key (NK)* | Llave de negocio (business key) |

---

*Versión*: 2.0  
*Fecha*: Marzo 2026  
*Autor*: Equipo de Arquitectura de Datos  
*Relacionado con*: 
- DM-BL-01: Principios de Diseño de Data Modelling
- 01_convenciones_nomenclatura_entidades_ddv.md
- 02_nomenclatura_atributos_ddv.md