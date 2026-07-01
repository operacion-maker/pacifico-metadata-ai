# Estándares de Modelamiento en Silver (UDV)
## Definición de la Capa Semántica del Negocio

*Versión*: 2.0  
*Fecha*: Marzo 2026  
*Autor*: Equipo de Arquitectura de Datos

---

## 1. Propósito del documento
Este documento define *qué condiciones debe cumplir un modelo para ser considerado Silver (UDV)* dentro del Lakehouse.

### 1.1 Definición de Silver (UDV)
> *Silver (UDV) es la capa semántica del negocio.*
*Aquí se define*:
- ✅ *Qué ES* el negocio (conceptos, entidades, relaciones)
- ✅ *Qué SIGNIFICA* cada dato (semántica gobernada)
- ✅ *Cómo se RELACIONAN* los conceptos

*Aquí NO se define*:
- ❌ Cómo se *mide* (métricas → Gold/DDV)
- ❌ Cómo se *reporta* (dashboards → Gold/DDV)
- ❌ Cómo se *visualiza* (gráficos → Consumo)

### 1.2 Características de un modelo UDV correcto
Un modelo UDV correcto:

| Característica | Descripción |
|----------------|-------------|
| ✅ *Representa conceptos claros* | Cliente, Póliza, Siniestro (del negocio real) |
| ✅ *Tiene semántica estable* | El significado no cambia por campañas temporales |
| ✅ *Es reutilizable* | Sirve para múltiples casos de uso |
| ✅ *Es base para DDV* | DDV construye sobre UDV, no lo redefine |

### 1.3 Regla de oro
> *UDV NO existe para un reporte ni para una métrica puntual.*
Si el modelo solo sirve para un dashboard específico → *NO es UDV*.

---

## 2. Alcance del documento
### 2.1 ✅ Aplica a
Este estándar aplica a:
- *Entidades Silver (UDV)*: md_dac_cliente, hd_poliza_mov_gen_core, md_producto
- *Modelos conformados*: Cliente canónico, Póliza core
- *Relaciones semánticas*: FKs entre entidades UDV

### 2.2 ❌ NO aplica a
| Capa | Razón |
|------|-------|
| *RDV (Bronze)* | Captura datos crudos sin semántica |
| *DDV (Gold)* | Agrega, calcula métricas, responde preguntas analíticas |
*Propósito*: Evitar discusiones de "¿esto va aquí o allá?"

---

## 3. Arquitectura de capas
### 3.1 Medallion Architecture

mermaid
graph LR
    subgraph RDV["RDV (Bronze)"]
        B1[Datos Crudos]
        B2[Sin Semántica]
    end
    
    subgraph UDV["UDV (Silver)"]
        S1[Conceptos de Negocio]
        S2[Semántica Gobernada]
        S3[Reutilizable]
    end
    
    subgraph DDV["DDV (Gold)"]
        G1[Métricas]
        G2[KPIs]
        G3[Agregaciones]
    end
    
    RDV -->|Alimenta| UDV
    UDV -->|Base para| DDV
    DDV -->|No redefine| UDV
    
    style RDV fill:#CD7F32,color:#fff
    style UDV fill:#C0C0C0
    style DDV fill:#FFD700


### 3.2 Responsabilidades por capa
| Capa | Responsabilidad |
|------|----------------|
| *RDV (Bronze)* | Ingerir datos crudos |
| *UDV (Silver)* | Definir semántica de negocio |
| *DDV (Gold)* | Responder preguntas analíticas |

### 3.3 Flujo de datos

mermaid
graph TD
    A[Fuente Operacional<br/>API, DB, Files]
    A -->|Ingesta| B[RDV Bronze<br/>Datos Crudos]
    
    B -->|Conformación| C[UDV Silver<br/>Semántica]
    
    C -->|Agregación| D1[DDV Gold<br/>Datamarts]
    C -->|Derivación| D2[DDV Gold<br/>Feature Tables]
    C -->|Métricas| D3[DDV Gold<br/>Datasets]
    
    D1 --> E[Consumo<br/>BI, ML, APIs]
    D2 --> E
    D3 --> E
    
    style B fill:#CD7F32,color:#fff
    style C fill:#C0C0C0
    style D1 fill:#FFD700
    style D2 fill:#FFD700
    style D3 fill:#FFD700


---

## 4. Principios clave de UDV (no negociables)
### 4.1 Principio 1: Reusabilidad transversal

mermaid
graph TD
    UDV["Entidad UDV<br/>md_dac_cliente"]
    
    UDV --> BI["Dashboard BI"]
    UDV --> ML["Feature Table ML"]
    UDV --> API["API Consulta"]
    UDV --> Reg["Reporte Regulatorio"]
    
    style UDV fill:#C0C0C0
    style BI fill:#E3F2FD
    style ML fill:#E3F2FD
    style API fill:#E3F2FD
    style Reg fill:#E3F2FD


*Regla*:
Un modelo UDV:
- ❌ NO pertenece a un reporte
- ❌ NO pertenece a un dashboard
- ❌ NO pertenece a un solo consumo
- ✅ DEBE poder ser reutilizado por múltiples productos de datos

*Test de validación*:
Si solo sirve para un caso puntual → *NO es UDV*.

### 4.2 Principio 2: Semántica clara y estable
*Cada entidad UDV representa*:
| Característica | Descripción | Ejemplo |
|----------------|-------------|---------|
| Concepto claro | Concepto de negocio inequívoco | md_dac_cliente = Cliente |
| Significado único | Una sola interpretación | primaneta siempre es prima sin impuestos |
| Estable en el tiempo | No cambia por campañas temporales | Definición de "cliente" no cambia por promoción |

*❌ Antipatrón*:

sql
-- ❌ INCORRECTO: Semántica temporal
CREATE TABLE md_cliente_campania_verano (
  idcliente   BIGINT,
  ...
  -- Semántica temporal, NO es Silver estable
);

-- ✅ CORRECTO: Semántica estable
CREATE TABLE md_dac_cliente (
  idcliente   BIGINT,
  ...
);

-- La campaña se filtra en Gold/DDV, NO en Silver


### 4.3 Principio 3: Desacople del uso específico

*UDV NO conoce*:
| Concepto | Dónde vive | Ejemplo |
|----------|-----------|---------|
| Métricas | *DDV (Gold)* | porcsiniestralidad, primatotal |
| KPIs | *DDV (Gold)* | kpiretencion, kpicrecimiento |
| Indicadores | *DDV (Gold)* | indsatisfaccion |
| Lógica de reporte | *DDV (Gold)* | Filtros, agrupaciones |
| Reglas temporales | *DDV (Gold)* | Campañas, promociones |

*Regla*:
> *UDV define el negocio, no cómo se mide.*

*Ejemplo*:
sql
-- ❌ INCORRECTO: Métrica en Silver
CREATE TABLE md_dac_cliente (
  idcliente          BIGINT,
  nomcliente         STRING,
  
  -- ❌ Métrica calculada (no es atómico)
  scoreretencion     DECIMAL(5,2),
  
  -- ❌ KPI temporal
  flgcampanaverano   INT
);

-- ✅ CORRECTO: Solo conceptos atómicos
CREATE TABLE md_dac_cliente (
  idcliente          BIGINT,
  nomcliente         STRING,
  fecingreso         DATE,
  codestado          STRING,
  codsegmento        STRING
);

-- Las métricas se calculan en Gold/DDV
CREATE TABLE ddv_prod.sch_analytics.cliente_metricas (
  idcliente          BIGINT,
  scoreretencion     DECIMAL(5,2),  -- ✅ Calculado en DDV
  flgcampanaverano   INT            -- ✅ Regla temporal en DDV
);


### 4.4 Principio 4: Independencia de herramientas

*UDV NO se diseña para*:
- ❌ Power BI
- ❌ Tableau
- ❌ Un dashboard específico
- ❌ Una herramienta de consumo

*La optimización ocurre en Gold/DDV.*

mermaid
graph LR
    S["Silver UDV<br/>Semántica pura"]
    S -->|Optimiza para BI| G1["Gold DDV<br/>Star Schema"]
    S -->|Optimiza para ML| G2["Gold DDV<br/>Feature Store"]
    S -->|Optimiza para API| G3["Gold DDV<br/>Denormalizado"]
    
    G1 --> PBI["Power BI"]
    G2 --> ML["MLflow"]
    G3 --> API["REST API"]
    
    style S fill:#C0C0C0
    style G1 fill:#FFD700
    style G2 fill:#FFD700
    style G3 fill:#FFD700


### 4.5 Principio 5: Consistencia entre dominios

*Conceptos comunes se definen UNA sola vez*:

| Concepto | Entidad UDV | Dominio Responsable |
|----------|---------------|---------------------|
| Cliente | md_dac_cliente | Cliente (core) |
| Póliza | md_poliza | Póliza (core) |
| Producto | md_producto | Producto (core) |
| Siniestro | md_siniestro | Siniestro (core) |

*❌ NO crear versiones paralelas*:

sql
-- ❌ INCORRECTO: Duplicación semántica
md_dac_cliente              -- Cliente core
md_cliente_marketing    -- ❌ Sin justificación semántica
md_cliente_ventas       -- ❌ Mismo concepto, distinto nombre
md_cliente_cobranza     -- ❌ Duplicación

-- ✅ CORRECTO: Una sola definición
md_dac_cliente              -- Cliente canónico (core)



### 4.6 Principio 6: Gobierno y ownership explícito

*Regla*:

> *UDV es reutilizable, pero NO es sin dueño.*

Toda entidad UDV *DEBE tener*:

- ✅ *Ownership claro* (dominio, equipo)
- ✅ *Data Steward* responsable
- ✅ *Reglas de calidad* definidas

*Tipos de ownership*:

mermaid
graph TD
    UDV["Entidad Silver"]
    
    UDV --> Trans{"¿Semántica<br/>transversal?"}
    
    Trans -->|Sí| Core["Ownership:<br/>Dominio CORE<br/>(Cliente, Póliza, Producto)"]
    
    Trans -->|No| Espec["Ownership:<br/>Modelo o Subdominio<br/>ESPECÍFICO<br/>(Incidentes comerciales,<br/>Siniestros empresas)"]
    
    style Core fill:#C8E6C9
    style Espec fill:#FFF9C4


---

## 5. Qué se considera un modelo UDV
### 5.1 Entidades maestras (md_)
*Conceptos fundamentales del negocio*:

sql
-- Ejemplos de entidades maestras UDV
md_dac_persona          -- Persona física/jurídica
md_cliente              -- Cliente canónico
md_poliza               -- Póliza core
md_producto             -- Producto de seguros
md_siniestro            -- Siniestro core
md_cobertura            -- Cobertura
md_agente               -- Agente de ventas
md_canal                -- Canal de distribución


*Características*:
| Característica | Descripción |
|----------------|-------------|
| ✅ Identidad clara | PK definida (surrogate key) |
| ✅ Pueden tener historia | SCD Type 2 si aplica |
| ✅ Reutilizables | Múltiples consumos |
| ✅ Dominio responsable | Ownership definido |

*Ejemplo completo*:

sql
-- md_producto: Entidad maestra de productos
CREATE TABLE udv_prod.sch_udv_tb.md_producto (
  -- Identificadores
  idproducto         BIGINT,           -- SK (surrogate key)
  codproducto        STRING,           -- NK (natural key)
  
  -- Descriptivos
  desproducto        STRING,
  nomproducto        STRING,
  nomproductocorto   STRING,
  
  -- Jerarquía
  codramo            STRING,
  desramo            STRING,
  codlinea           STRING,
  deslinea           STRING,
  
  -- Clasificación
  tipproducto        STRING,
  segmentoproducto   STRING,
  
  -- Estado
  flgactivo          INT,
  flgvigente         INT,
  
  -- Fechas
  feclanzamiento     DATE,
  fecretiro          DATE,
  
  -- Técnicos
  codapp             STRING,
  feccargainfo       DATE,
  periododia         STRING,
  flgvalido          INT,
  
  PRIMARY KEY (idproducto)
);

-- Metadata obligatoria
COMMENT ON TABLE md_producto IS 'Entidad maestra de productos de seguros';
COMMENT ON COLUMN md_producto.idproducto IS 'Surrogate key de producto';
COMMENT ON COLUMN md_producto.codproducto IS 'Natural key: código de producto';


### 5.2 Entidades históricas (hd_)
*Registros de eventos y movimientos*:

sql
-- Ejemplos de entidades históricas Silver
hd_poliza_movimiento      -- Movimientos de póliza (emisión, endoso, anulación)
hd_siniestro_movimiento   -- Movimientos de siniestro
hd_cuota                  -- Cuotas de pago
hd_pago                   -- Pagos realizados
hd_contacto               -- Contactos con cliente


*Características*:
| Característica | Descripción |
|----------------|-------------|
| ✅ Grano temporal | Un evento en un momento específico |
| ✅ Inmutables | No se actualizan, se insertan nuevos registros |
| ✅ Append-only | Solo crecen (no DELETE, no UPDATE) |
| ✅ Trazabilidad completa | Historia de cambios |

*Ejemplo completo*:

sql
-- hd_poliza_movimiento: Histórico de movimientos de póliza
CREATE TABLE udv_prod.sch_udv_tb.hd_poliza_movimiento (
  -- Grano: 1 movimiento de 1 póliza en 1 fecha
  idpoliza             BIGINT,
  fecmovimiento        DATE,
  codtipomovimiento    STRING,     -- 'EMISION', 'ENDOSO', 'ANULACION', 'RENOVACION'
  nummovimiento        BIGINT,
  
  -- Estado resultante del movimiento
  codestado            STRING,
  desestado            STRING,
  
  -- Datos del movimiento
  primaneta            DECIMAL(20,6),
  primabruta           DECIMAL(20,6),
  sumaaseg             DECIMAL(20,2),
  
  -- Vigencia resultante
  fecinivigencia       DATE,
  fecfinvigencia       DATE,
  
  -- Técnicos
  codapp               STRING,
  feccargainfo         DATE,
  periododia           STRING,
  flgvalido            INT,
  
  PRIMARY KEY (idpoliza, fecmovimiento, codtipomovimiento, nummovimiento)
);


### 5.3 Entidades últimas (ud_)
*Estado actual sin historia*:
sql
-- Ejemplos de entidades últimas UDV
ud_poliza_vigente     -- Estado actual de pólizas vigentes
ud_cliente_activo     -- Estado actual de clientes activos
ud_producto           -- Catálogo actual de productos


*Características*:
| Característica | Descripción |
|----------------|-------------|
| ✅ Sin historia | Solo estado actual (Type 1) |
| ✅ Se actualiza | UPDATE o MERGE |
| ✅ Snapshot | Foto del momento actual |
| ✅ Performance | Más rápido que consultar histórico |

*Ejemplo completo*:

sql
-- ud_poliza_vigente: Estado actual de pólizas vigentes
CREATE TABLE udv_prod.sch_udv_tb.ud_poliza_vigente (
  -- Identificador
  idpoliza             BIGINT PRIMARY KEY,
  numpoliza            BIGINT,
  
  -- Referencias
  idcliente            BIGINT,
  idproducto           BIGINT,
  idcanal              BIGINT,
  
  -- Estado actual
  codestado            STRING,
  desestado            STRING,
  
  -- Datos actuales
  primaneta            DECIMAL(20,6),
  sumaaseg             DECIMAL(20,2),
  
  -- Vigencia actual
  fecinivigencia       DATE,
  fecfinvigencia       DATE,
  
  -- Técnicos
  codapp               STRING,
  feccargainfo         DATE,
  fecactualizacion     DATE,
  flgvalido            INT
);


### 5.4 Entidades conformadas de negocio
*Integración de múltiples fuentes con semántica única*:

sql
-- Ejemplo: Cliente conformado de múltiples fuentes
CREATE TABLE udv_prod.sch_udv_tb.md_dac_cliente (
  idcliente            BIGINT PRIMARY KEY,
  
  -- De CRM
  codcliente_crm       STRING,
  nomcliente           STRING,
  emailprincipal       STRING,
  
  -- De Core de Seguros
  codcliente_core      STRING,
  codsegmento          STRING,
  
  -- De SAP
  codcliente_sap       STRING,
  codcuentacontable    STRING,
  
  -- Conformado (Golden Record)
  codcliente           STRING,      -- NK conformado
  tipcliente           STRING,
  fecingreso           DATE,
  
  -- Técnicos
  codapp               STRING,
  feccargainfo         DATE
);


*Reglas de conformación*:
1. ✅ Integra múltiples fuentes
2. ✅ Mantiene un solo significado
3. ✅ Tiene un solo grano
4. ✅ Reglas semánticas claras y documentadas

### 5.6 Relaciones semánticas explícitas

*En UDV las relaciones son claras*:

sql
-- Relación 1-N: Cliente → Pólizas
ALTER TABLE md_poliza 
ADD CONSTRAINT fk_poliza_cliente 
FOREIGN KEY (idcliente) REFERENCES md_cliente(idcliente);

-- Relación N-N: Póliza ↔️ Cobertura (con bridge)
CREATE TABLE poliza_cobertura (
  idpoliza       BIGINT,
  idcobertura    BIGINT,
  sumaaseg       DECIMAL(20,2),
  fecinicio      DATE,
  fecfin         DATE,
  
  PRIMARY KEY (idpoliza, idcobertura),
  FOREIGN KEY (idpoliza) REFERENCES md_poliza(idpoliza),
  FOREIGN KEY (idcobertura) REFERENCES md_cobertura(idcobertura)
);


*Características*:
- ✅ Relaciones explícitas (FKs declaradas)
- ✅ Cardinalidad clara (1-1, 1-N, N-N)
- ✅ Reflejan el negocio real
- ❌ NO se ocultan relaciones para facilitar queries

---

## 6. Ownership en entidades UDV
### 6.1 Tipos de ownership

mermaid
graph TD
    Start["Entidad UDV"]
    
    Start --> Tipo{"¿Tipo de ownership?"}
    
    Tipo -->|Transversal| Core["CORE<br/>Ownership de Dominio Core"]
    Tipo -->|Específico| Modelo["MODELO<br/>Ownership de Subdominio"]
    
    Core --> CoreDef["• Define semántica<br/>• Define calidad<br/>• Aprueba cambios<br/>• Otros CONSUMEN"]
    
    Modelo --> ModDef["• Define semántica local<br/>• Controla calidad local<br/>• No se asume transversal"]
    
    style Core fill:#C8E6C9
    style Modelo fill:#FFF9C4


### 6.2 Entidades con ownership de dominio CORE
*Son entidades transversales y canónicas*:
| Entidad | Dominio Responsable | Alcance |
|---------|-------------------|---------|
| md_dac_persona | DAC (Datos de Alta Criticidad) | Todas las personas físicas/jurídicas |
| md_cliente | Cliente | Clientes canónicos |
| md_poliza | Póliza | Pólizas core |
| md_producto | Producto | Productos de seguros |
| md_siniestro | Siniestro | Siniestros core |
| md_agente | Comercial | Agentes de ventas |

*Reglas*:
1. ✅ *Dominio core define* la semántica
2. ✅ *Dominio core define* reglas de calidad
3. ✅ *Dominio core aprueba* cambios estructurales
4. ✅ *Otros dominios CONSUMEN*, no redefinen

*Ejemplo de metadata*:
json
{
  "entity_name": "md_dac_cliente",
  "ownership_type": "core",
  "domain": "Cliente",
  "data_steward": "Juan Pérez (Cliente)",
}


### 6.3 Entidades con ownership de modelo o subdominio ESPECÍFICO
*Son entidades UDV cuya semántica solo existe en un contexto específico*:
| Entidad | Modelo/Subdominio | Justificación |
|---------|------------------|---------------|
| md_incidente_comercial | Gestión Comercial | Concepto específico del proceso comercial |
| md_poliza_vehicular | Automotriz | Atributos exclusivos de vehículos |
| md_siniestro_empresas | Empresas | Siniestros con lógica específica de empresas |
| hd_contacto_cobranza | Cobranza | Contactos específicos del proceso de cobranza |

*Reglas*:
1. ✅ *Ownership pertenece al modelo/subdominio* que la define
2. ✅ *Reglas de calidad se controlan ahí*
3. ✅ *Semántica NO se asume transversal*
4. ✅ *Siguen siendo UDV* (semántica clara, conformadas, sin métricas)

*Ejemplo*:

sql
-- md_incidente_comercial
-- Ownership: Gestión Comercial (específico)
CREATE TABLE udv_prod.sch_comercial.md_incidente_comercial (
  idincidente          BIGINT PRIMARY KEY,
  codincidente         STRING,
  
  -- Contexto específico del proceso comercial
  idagente             BIGINT,
  tipincidente         STRING,      -- 'QUEJA', 'RECLAMO', 'CONSULTA'
  desincidente         STRING,
  
  -- Estado del incidente
  codestado            STRING,
  fecapertura          DATE,
  feccierre            DATE,
  
  -- Resolución
  tipresolucion        STRING,
  desresolucion        STRING,
  
  -- Técnicos
  codapp               STRING,
  feccargainfo         DATE
);


*Metadata*:

json
{
  "entity_name": "md_incidente_comercial",
  "ownership_type": "specific",
  "model": "Gestión Comercial",
  "data_steward": "María García (Comercial)",
  "is_transversal": false
}


*¿Por qué sigue siendo UDV?*
- ✅ Tiene semántica clara (concepto de negocio definido)
- ✅ Está conformada (integra fuentes si aplica)
- ✅ NO contiene métricas (solo datos atómicos)
- ✅ NO existe solo para un reporte (base reutilizable dentro de su contexto)

---

## 7. Qué NO debe existir en UDV
### 7.1 Tabla de restricciones
| Tipo | Descripción | Dónde debe ir |
|------|-------------|---------------|
| ❌ *Agregaciones* | SUM, COUNT, AVG | *Gold (DDV)* |
| ❌ *Métricas calculadas* | Ratios, tasas, scores | *Gold (DDV)* |
| ❌ *KPIs* | Indicadores de performance | *Gold (DDV)* |
| ❌ *Lógica de reporte* | Filtros para dashboards | *Gold (DDV)* |
| ❌ *Columnas para dashboards* | Flags de visualización | *Gold (DDV)* |
| ❌ *Flags de un solo consumo* | Creados para un reporte | *Gold (DDV)* |
| ❌ *Reglas temporales* | Campañas, promociones | *Gold (DDV)* |
| ❌ *Optimización de herramientas* | Diseñado para Power BI | *Gold (DDV)* |
| ❌ *Entidades sin ownership* | Sin responsable definido | *Rechazar* |

### 7.2 Test rápido
*Si la entidad o atributo responde a*:
- ❓ "Cómo se *mide" → **NO es UDV*
- ❓ "Cómo se *muestra" → **NO es UDV*
- ❓ "Para este *reporte" → **NO es UDV*
- ❓ "En este *dashboard" → **NO es UDV*
- ❓ "Para esta *campaña" → **NO es UDV*

*Si responde a*:
- ✅ "Qué *ES" → **SÍ es UDV*
- ✅ "Qué *SIGNIFICA" → **SÍ es UDV*
- ✅ "Cómo se *RELACIONA" → **SÍ es UDV*

### 7.3 Ejemplos de antipatrones

#### Antipatrón 1: Agregaciones en UDV

sql
-- ❌ INCORRECTO: Agregaciones en UDV
CREATE TABLE md_dac_cliente (
  idcliente            BIGINT,
  nomcliente           STRING,
  
  -- ❌ Agregación (NO es atómico)
  ctdpolizas           INT,            -- COUNT de pólizas
  primatotal           DECIMAL(20,6),  -- SUM de primas
  primapromedioult3m   DECIMAL(20,6)   -- AVG con ventana temporal
);

-- ✅ CORRECTO: Datos atómicos en UDV
CREATE TABLE md_cliente (
  idcliente            BIGINT,
  nomcliente           STRING,
  fecingreso           DATE,
  codestado            STRING
);

-- Agregaciones en DDV
CREATE TABLE ddv_prod.sch_ddv_cliente_tb.cliente_metricas (
  idcliente            BIGINT,
  ctdpolizas           INT,           -- ✅ Calculado en DDV
  primatotal           DECIMAL(20,6), -- ✅ Calculado en DDV
  primapromedioult3m   DECIMAL(20,6)  -- ✅ Calculado en DDV
);


#### Antipatrón 2: KPIs en UDV

sql
-- ❌ INCORRECTO: KPIs en UDV
CREATE TABLE md_agente (
  idagente             BIGINT,
  nomagente            STRING,
  
  -- ❌ KPIs (lógica de medición)
  kpicumplimiento      DECIMAL(5,2),
  kpiretencion         DECIMAL(5,2),
  scoreventa           INT
);

-- ✅ CORRECTO: Datos atómicos en UDV
CREATE TABLE md_agente (
  idagente             BIGINT,
  nomagente            STRING,
  codregion            STRING,
  fecingreso           DATE,
  codestado            STRING
);

-- KPIs en DDV
CREATE TABLE ddv_prod.sch_ddv_dm_seguimiento_agente_tb.agente_kpis (
  idagente             BIGINT,
  periodomes           STRING,
  kpicumplimiento      DECIMAL(5,2),  -- ✅ En DDV
  kpiretencion         DECIMAL(5,2),  -- ✅ En DDV
  scoreventa           INT            -- ✅ En DDV
);


#### Antipatrón 3: Flags para un solo consumo

sql
-- ❌ INCORRECTO: Flag temporal para un dashboard
CREATE TABLE md_cliente (
  idcliente            BIGINT,
  nomcliente           STRING,
  
  -- ❌ Flag solo para un dashboard específico
  flgmostrar_dashboard_ventas  INT
);

-- ✅ CORRECTO: Sin flags de consumo
CREATE TABLE md_cliente (
  idcliente            BIGINT,
  nomcliente           STRING,
  codestado            STRING,
  codsegmento          STRING
);

-- El filtro se hace en DDV o en la consulta


#### Antipatrón 4: Reglas temporales de campaña

sql
-- ❌ INCORRECTO: Lógica de campaña temporal
CREATE TABLE md_producto (
  idproducto           BIGINT,
  desproducto          STRING,
  
  -- ❌ Reglas temporales
  flgcampaniaverano2026    INT,
  porcdesccampania         DECIMAL(5,2)
);

-- ✅ CORRECTO: Datos estables
CREATE TABLE md_producto (
  idproducto           BIGINT,
  desproducto          STRING,
  codramo              STRING,
  flgactivo            INT
);

-- Campañas en DDV
CREATE TABLE ddv_prod.sch_ddv_marketing_tb.campania_producto (
  idproducto           BIGINT,
  codcampania          STRING,
  fecinicamp           DATE,
  fecfincamp           DATE,
  porcdesc             DECIMAL(5,2)  -- ✅ En DDV, temporal
);


---

## 8. Reglas de diseño semántico en UDV
### 8.1 Un solo grano por entidad
*Regla*:
> Cada entidad UDV representa *un solo nivel de detalle*, explícito, respetado por todos sus atributos.

*Formato de grano*:


"1 fila = [qué representa exactamente]"


*Ejemplos*:
| Entidad | Grano |
|---------|-------|
| md_cliente | 1 fila = 1 cliente |
| hd_poliza_movimiento | 1 fila = 1 movimiento de 1 póliza en 1 fecha |
| hd_cuota | 1 fila = 1 cuota de 1 póliza |
| poliza_cobertura | 1 fila = 1 relación póliza-cobertura |

*❌ Antipatrón: Mezcla de granos*

sql
-- ❌ INCORRECTO: Grano inconsistente
CREATE TABLE hd_poliza_movimiento (
  idpoliza             BIGINT,
  fecmovimiento        DATE,
  
  primaneta            DECIMAL(20,6),  -- ✅ Grano: movimiento
  
  primatotalanio       DECIMAL(20,6),  -- ❌ Grano: año (diferente)
  primaultimacuota     DECIMAL(20,6)   -- ❌ Grano: cuota (diferente)
);

-- ✅ CORRECTO: Granos separados
CREATE TABLE hd_poliza_movimiento (
  idpoliza             BIGINT,
  fecmovimiento        DATE,
  primaneta            DECIMAL(20,6)   -- ✅ Grano: movimiento
);

CREATE TABLE ha_poliza_resumen_anual (
  idpoliza             BIGINT,
  anio                 INT,
  primatotalanio       DECIMAL(20,6)   -- ✅ Grano: año
);

CREATE TABLE hd_cuota (
  idpoliza             BIGINT,
  numcuota             INT,
  primacuota           DECIMAL(20,6)   -- ✅ Grano: cuota
);


### 8.2 Atributos en UDV
*Regla*: Los atributos UDV deben ser:

| Característica | Descripción | Ejemplo |
|----------------|-------------|---------|
| ✅ *Estables* | No cambian por campañas temporales | primaneta siempre es prima sin impuestos |
| ✅ *Semánticamente claros* | Significado inequívoco | codestado tiene catálogo definido |
| ✅ *Mismo grano* | Al nivel de la entidad | No mezclar detalle con agregado |
| ✅ *Independientes del uso* | No pensados para un dashboard | No flgmostrar_dashboard |

*✅ Atributos válidos en UDV*:

sql
CREATE TABLE md_poliza (
  -- Identificadores
  idpoliza             BIGINT,
  numpoliza            BIGINT,
  
  -- Referencias
  idcliente            BIGINT,
  idproducto           BIGINT,
  
  -- Descriptivos
  codestado            STRING,
  desestado            STRING,
  
  -- Monetarios atómicos
  primaneta            DECIMAL(20,6),
  sumaaseg             DECIMAL(20,2),
  
  -- Fechas atómicas
  fecemision           DATE,
  fecinivigencia       DATE,
  fecfinvigencia       DATE
);


### 8.3 Relaciones explícitas y justificadas
*Regla*: Toda relación UDV tiene:
1. ✅ Justificación de negocio (refleja realidad)
2. ✅ Cardinalidad correcta (1-1, 1-N, N-N)
3. ✅ FK declarada (cuando posible)
4. ❌ NO se introduce solo para facilitar queries

*Ejemplo de relaciones correctas*:

sql
-- 1-N: Cliente → Pólizas
CREATE TABLE md_poliza (
  idpoliza       BIGINT PRIMARY KEY,
  idcliente      BIGINT NOT NULL,
  
  FOREIGN KEY (idcliente) REFERENCES md_cliente(idcliente)
);

-- N-N: Póliza ↔️ Cobertura
CREATE TABLE poliza_cobertura (
  idpoliza       BIGINT,
  idcobertura    BIGINT,
  
  PRIMARY KEY (idpoliza, idcobertura),
  FOREIGN KEY (idpoliza) REFERENCES md_poliza(idpoliza),
  FOREIGN KEY (idcobertura) REFERENCES md_cobertura(idcobertura)
);


### 8.4 Ownership según alcance semántico

mermaid
graph TD
    Entidad["Nueva Entidad UDV"]
    
    Entidad --> Alcance{"¿Alcance semántico?"}
    
    Alcance -->|Transversal<br/>Múltiples dominios| Core["Ownership: CORE<br/>• Define el dominio principal<br/>• Otros consumen<br/>• Cambios aprobados por Governance"]
    
    Alcance -->|Específico<br/>Un modelo/subdominio| Modelo["Ownership: MODELO<br/>• Define el subdominio<br/>• Controla calidad local<br/>• No se asume transversal"]
    
    style Core fill:#C8E6C9
    style Modelo fill:#FFF9C4


*Reglas*:
- ✅ Si semántica es *transversal* → Ownership de *dominio core*
- ✅ Si semántica es *específica* → Ownership de *modelo/subdominio*
- ❌ NO se permite redefinir semántica desde consumo
- ❌ NO se permite reutilizar fuera de contexto sin evaluación
- ❌ NO se permite duplicar entidades para evitar gobierno

---

## 9. Relación de UDV con otras capas

### 9.1 UDV y RDV

mermaid
graph LR
    B[RDV Bronze]
    S[UDV Silver]
    
    B -->|Alimenta| S
    B -.->|No define semántica| S
    S -.->|Integra y conforma| B
    
    style B fill:#CD7F32,color:#fff
    style S fill:#C0C0C0


| Aspecto | Bronze (RDV) | Silver (UDV) |
|---------|-------------|-------------|
| *Propósito* | Captura cruda | Semántica de negocio |
| *Transformación* | Mínima (cast, rename) | Conformación, integración |
| *Calidad* | Como viene de origen | Validada y gobernada |
| *Ownership* | Ingeniería de Datos | Dominio de Negocio |

### 9.2 UDV y GDDVld

mermaid
graph LR
    S[UDV Silver]
    G[DDV Gold]
    
    G -->|Deriva desde| S
    G -.->|Agrega y calcula| S
    S -.->|No depende de| G
    
    style S fill:#C0C0C0
    style G fill:#FFD700


| Aspecto | Silver (UDV) | Gold (DDV) |
|---------|-------------|-----------|
| *Propósito* | Semántica de negocio | Valor analítico |
| *Contenido* | Datos atómicos | Agregados, métricas |
| *Dependencia* | No depende de DDV | Depende de UDV |
| *Cambios* | Poco frecuentes | Más frecuentes (nuevos análisis) |

*Regla clave*:
> *UDV es base, NO subproducto.*

---

## 10. Criterios de calidad mínima para UDV
### 10.1 Checklist de validación
Un modelo UDV *DEBE cumplir*:

- [ ] *Concepto de negocio claro*: Representa un concepto real del negocio
- [ ] *Identidad bien definida*: PK clara (surrogate key o natural key)
- [ ] *Grano explícito*: Documentado "1 fila = [qué representa]"
- [ ] *Relaciones coherentes*: FKs declaradas cuando aplica
- [ ] *Naming consistente*: Sigue estándar de nomenclatura UDV
- [ ] *Ownership definido*: Data Steward asignado
- [ ] *Documentación mínima*: Ver sección 10.2

### 10.2 Metadata obligatoria

*Tabla completa de metadata*:

| Campo Metadata | Descripción | Ejemplo |
|----------------|-------------|---------|
| entity_name | Nombre físico | md_cliente |
| entity_type | Tipo de entidad | master, historical, latest |
| business_concept | Concepto de negocio | "Cliente canónico de seguros" |
| grain | Grano explícito | "1 fila = 1 cliente" |
| ownership_type | Tipo de ownership | core o specific |
| domain | Dominio responsable | "Cliente" |
| data_steward | Responsable de datos | "Juan Pérez (Cliente)" |
| primary_key | Llave primaria | idcliente |
| natural_key | Llave de negocio | codcliente |
| is_transversal | ¿Es transversal? | true / false |

*Ejemplo completo*:

json
{
  "entity_name": "md_cliente",
  "entity_type": "master",
  "business_concept": "Cliente canónico de seguros",
  "grain": "1 fila = 1 cliente en su estado actual",
  "ownership_type": "core",
  "domain": "Cliente",
  "data_steward": "Juan Pérez",
  "primary_key": "idcliente",
  "natural_key": "codcliente"
}


---

## 11. Ejemplos completos
### 11.1 ✅ Ejemplo UDV CORRECTO
*Entidad*: md_cliente
*Descripción*: Cliente canónico que integra múltiples fuentes.

sql
CREATE TABLE udv_prod.sch_udv_tb.md_cliente (
  -- Surrogate key
  idcliente            BIGINT PRIMARY KEY,
  
  -- Natural key (conformado)
  codcliente           STRING NOT NULL,
  
  -- Identificación
  numdoc               STRING,
  tipodoc              STRING,
  
  -- Descriptivos
  nomcliente           STRING,
  apecliente           STRING,
  razonsocial          STRING,
  
  -- Clasificación
  tipcliente           STRING,      -- 'PERSONA', 'EMPRESA'
  codsegmento          STRING,
  
  -- Estado
  codestado            STRING,
  desestado            STRING,
  flgactivo            INT,
  
  -- Fechas
  fecingreso           DATE,
  fecnacimiento        DATE,
  
  -- Contacto
  emailprincipal       STRING,
  telcelular           STRING,
  
  -- Técnicos obligatorios UDV
  codapp               STRING,
  feccargainfo         DATE,
  periododia           STRING,
  flgvalido            INT,
  flgobservado         INT,
  desmensajeobs        STRING
);

COMMENT ON TABLE md_cliente IS 'Cliente canónico de seguros (Silver/UDV)';


*Por qué es UDV correcto*:

- ✅ Concepto claro: "Cliente"
- ✅ Semántica estable: Definición de cliente no cambia
- ✅ Reutilizable: Múltiples consumos (Emisión, Cobranza, BI, ML)
- ✅ Sin métricas: Solo datos atómicos
- ✅ Sin lógica temporal: No tiene flags de campaña
- ✅ Ownership core: Dominio Cliente responsable

### 11.2 ❌ Ejemplo NO UDV

*Entidad*: md_cliente_kpi_ventas

sql
-- ❌ INCORRECTO: Esto NO es UDV
CREATE TABLE md_cliente_kpi_ventas (
  idcliente            BIGINT,
  nomcliente           STRING,
  
  -- ❌ Métricas calculadas
  ctdpolizasult12m     INT,
  primatotalult12m     DECIMAL(20,6),
  
  -- ❌ KPIs
  kpiretencion         DECIMAL(5,2),
  kpicrecimiento       DECIMAL(5,2),
  
  -- ❌ Flag para dashboard específico
  flgmostrar_dashboard_ventas  INT,
  
  -- ❌ Regla temporal de campaña
  flgcampaniaverano    INT
);


*Por qué NO es UDV*:
- ❌ Contiene *métricas* (ctdpolizasult12m, primatotalult12m)
- ❌ Contiene *KPIs* (kpiretencion, kpicrecimiento)
- ❌ Existe solo para *un reporte* (ventas)
- ❌ Tiene *flags de consumo* (flgmostrar_dashboard_ventas)
- ❌ Tiene *reglas temporales* (flgcampaniaverano)
- ❌ Evita reglas de calidad del dominio core

*Solución correcta*:

sql
-- ✅ CORRECTO: Datos atómicos en UDV
CREATE TABLE udv_prod.sch_udv_tb.md_cliente (
  idcliente            BIGINT,
  nomcliente           STRING,
  fecingreso           DATE,
  codestado            STRING
);

-- ✅ CORRECTO: Métricas y KPIs en DDV
CREATE TABLE ddv_prod.sch_seguimiento_cliente_tb.cliente_kpi_ventas (
  idcliente            BIGINT,
  periodomes           STRING,
  ctdpolizasult12m     INT,
  primatotalult12m     DECIMAL(20,6),
  kpiretencion         DECIMAL(5,2),
  kpicrecimiento       DECIMAL(5,2)
);


### 11.3 ✅ Ejemplo UDV ESPECÍFICO (no transversal)

*Entidad*: md_incidente_comercial

*Ownership*: Gestión Comercial (específico)

sql
CREATE TABLE udv_prod.sch_comercial.md_incidente_comercial (
  -- Identificadores
  idincidente          BIGINT PRIMARY KEY,
  codincidente         STRING NOT NULL,
  
  -- Contexto específico comercial
  idagente             BIGINT,
  idcliente            BIGINT,
  
  -- Clasificación del incidente
  tipincidente         STRING,      -- 'QUEJA', 'RECLAMO', 'CONSULTA'
  codcategoria         STRING,
  desincidente         STRING,
  
  -- Estado
  codestado            STRING,
  fecapertura          DATE,
  feccierre            DATE,
  
  -- Resolución
  tipresolucion        STRING,
  desresolucion        STRING,
  idusuarioresuelve    BIGINT,
  
  -- Técnicos
  codapp               STRING,
  feccargainfo         DATE,
  periododia           STRING,
  flgvalido            INT
);


*Por qué SÍ es UDV (aunque específico)*:

- ✅ Concepto claro: "Incidente comercial"
- ✅ Semántica estable dentro de su contexto
- ✅ Datos atómicos (no métricas)
- ✅ No existe solo para un reporte
- ✅ Ownership claro (Gestión Comercial)
- ✅ Reutilizable dentro de su dominio

*Metadata*:

json
{
  "entity_name": "md_incidente_comercial",
  "ownership_type": "specific",
  "model": "Gestión Comercial",
  "is_transversal": false,
  "data_steward": "María García (Comercial)",
  "consumers": ["Dashboard Servicio", "Métricas NPS", "Alertas Comerciales"]
}


---

## 12. Errores comunes en UDV

### 12.1 Tabla de errores

| # | Error | Impacto | Solución |
|---|-------|---------|----------|
| 1 | *Asumir toda entidad UDV es transversal* | Bloqueo de modelamiento | Permitir ownership específico documentado |
| 2 | *No declarar ownership* | Nadie cuida la calidad | Asignar Data Steward obligatorio |
| 3 | *Mezclar métricas con entidades* | Confusión semántica | Mover métricas a DDV |
| 4 | *Ajustar UDV para un reporte* | Pierde reusabilidad | Crear vista/tabla en DDV |
| 5 | *Duplicar entidades para evitar gobierno* | Inconsistencia | Consolidar bajo ownership único |
| 6 | *Introducir lógica temporal* | Semántica inestable | Mover campañas a DDV |
| 7 | *Diseñar para dashboards* | Acoplamiento a herramienta | Optimizar en DDV |
| 8 | *Grano inconsistente* | Datos duplicados o NULLs | Separar en entidades del grano correcto |
| 9 | *Relaciones implícitas* | Dificulta integraciones | Declarar FKs explícitas |
| 10 | *Sin documentación* | Nadie entiende la semántica | Metadata obligatoria |

### 12.2 Antipatrones detallados

#### Error 1: Asumir todo UDV es transversal


❌ PENSAMIENTO INCORRECTO:
"Si es UDV, debe ser core y transversal"

✅ PENSAMIENTO CORRECTO:
"Si es UDV, debe tener semántica clara y ownership definido.
Puede ser transversal (core) o específico (modelo/subdominio)"


#### Error 2: No declarar ownership


❌ Entidad sin dueño:
md_cliente_temp  -- ¿Quién define calidad? ¿Quién aprueba cambios?

✅ Entidad con ownership:
md_cliente
  ownership: Dominio Cliente
  data_steward: Juan Pérez
  change_approval: Data Governance


#### Error 3: Mezclar métricas con entidades

sql
-- ❌ Mezcla métricas
md_poliza
  primaneta        -- ✅ Dato atómico
  primatotalanio   -- ❌ Métrica agregada

-- ✅ Separar
md_poliza (UDV)
  primaneta        -- Solo atómico

poliza_metricas (DDV)
  primatotalanio   -- Agregado


---

## 13. Impacto esperado
### 13.1 Beneficios de aplicar estos estándares

mermaid
graph TD
    Std["Estándares Silver UDV"]
    
    Std --> B1["Reduce retrabajo"]
    Std --> B2["Mejora reutilización"]
    Std --> B3["Refuerza gobierno"]
    Std --> B4["Acelera revisiones"]
    Std --> B5["Habilita federación"]
    Std --> B6["Mejora calidad DDV"]
    
    B1 --> R1["Menos refactoring"]
    B2 --> R2["Menos duplicación"]
    B3 --> R3["Ownership claro"]
    B4 --> R4["Criterios objetivos"]
    B5 --> R5["Squads autónomos"]
    B6 --> R6["DDV consistente"]
    
    style Std fill:#C0C0C0
    style B1 fill:#C8E6C9
    style B2 fill:#C8E6C9
    style B3 fill:#C8E6C9
    style B4 fill:#C8E6C9
    style B5 fill:#C8E6C9
    style B6 fill:#C8E6C9


### 13.2 Métricas de éxito

| Métrica | Objetivo |
|---------|----------|
| % entidades UDV con ownership definido | 100% |
| % entidades UDV con grano documentado | 100% |
| % entidades UDV reutilizadas (>1 consumo) | >80% |
| Tiempo promedio de revisión de diseño UDV | <50% vs baseline |
| # de entidades duplicadas (misma semántica) | <3 por año |
| % de entidades UDV sin métricas | 100% |

---

## 14. Proceso de validación
### 14.1 Checklist operativo: ¿Es UDV correcto?
Antes de aprobar una entidad como UDV:

*Validación semántica*:
- [ ] ¿Representa un concepto claro de negocio?
- [ ] ¿La semántica es estable (no temporal)?
- [ ] ¿Es reutilizable (>1 consumo potencial)?

*Validación de contenido*:
- [ ] ¿Tiene solo datos atómicos (sin agregaciones)?
- [ ] ¿NO tiene métricas calculadas?
- [ ] ¿NO tiene KPIs?
- [ ] ¿NO tiene flags de un solo consumo?
- [ ] ¿NO tiene lógica temporal de campaña?

*Validación de diseño*:
- [ ] ¿Tiene grano explícito y documentado?
- [ ] ¿Todos los atributos respetan ese grano?
- [ ] ¿Las relaciones son explícitas (FKs)?
- [ ] ¿Sigue estándar de nomenclatura UDV?

*Validación de gobierno*:
- [ ] ¿Tiene ownership definido (core o específico)?
- [ ] ¿Tiene Data Steward asignado?
- [ ] ¿Tiene metadata completa?
- [ ] ¿Tiene reglas de calidad definidas?

*Si todas las respuestas son SÍ* → ✅ Es UDV correcto

### 14.2 Workflow de aprobación

mermaid
graph TD
    Start["Squad propone<br/>entidad UDV"]
    
    Start --> Check["Completa checklist<br/>de validación"]
    
    Check --> Sem{"¿Semántica<br/>clara y estable?"}
    
    Sem -->|No| Reject1["Rechazar:<br/>No es UDV"]
    
    Sem -->|Sí| Cont{"¿Contenido<br/>atómico sin métricas?"}
    
    Cont -->|No| Reject2["Rechazar:<br/>Mover a DDV"]
    
    Cont -->|Sí| Own{"¿Ownership<br/>definido?"}
    
    Own -->|No| Reject3["Rechazar:<br/>Asignar ownership"]
    
    Own -->|Sí| TipoOwn{"¿Tipo de<br/>ownership?"}
    
    TipoOwn -->|Core| ApCore["Aprobar con<br/>Data Governance"]
    TipoOwn -->|Específico| ApEspec["Aprobar con<br/>Modelo/Subdominio"]
    
    ApCore --> Impl["✅ Implementar"]
    ApEspec --> Impl
    
    style Reject1 fill:#FFCCBC
    style Reject2 fill:#FFCCBC
    style Reject3 fill:#FFCCBC
    style Impl fill:#C8E6C9


---

## 15. Referencias

### 15.1 Estándares relacionados

| Estándar | Descripción |
|----------|-------------|
| 01_convenciones_nomenclatura_entidades_udv.md | Nomenclatura de entidades UDV |
| 02_lineamientos_nomenclatura_campos_udv.md | Nomenclatura de atributos UDV |
| 05_reglas_diseno_entidades_atributos.md | Diseño de entidades y atributos |

### 15.2 Frameworks de referencia

| Framework | Aplicación |
|-----------|-----------|
| *DAMA-DMBOK* | Data Modeling & Design, Data Quality |
| *TOGAF* | Architecture Principles, Information Architecture |
| *ACORD* | Semántica canónica del dominio Seguros |
| *Kimball* | Dimensional Modeling (para DDV, NO UDV) |

---

## Apéndice A: Matriz de decisión UDV vs DDV

| Pregunta | Silver (UDV) | Gold (DDV) |
|----------|-------------|-----------|
| ¿Qué ES? | ✅ SÍ | ❌ NO |
| ¿Qué SIGNIFICA? | ✅ SÍ | ❌ NO |
| ¿Cómo se MIDE? | ❌ NO | ✅ SÍ |
| ¿Cómo se REPORTA? | ❌ NO | ✅ SÍ |
| ¿Cómo se VISUALIZA? | ❌ NO | ✅ SÍ |
| Datos atómicos | ✅ SÍ | Opcional |
| Agregaciones | ❌ NO | ✅ SÍ |
| Métricas | ❌ NO | ✅ SÍ |
| KPIs | ❌ NO | ✅ SÍ |
| Lógica temporal | ❌ NO | ✅ SÍ |
| Optimización herramienta | ❌ NO | ✅ SÍ |

---

## Apéndice B: Glosario

| Término | Definición |
|---------|------------|
| *Silver (UDV)* | Capa semántica del Lakehouse con conceptos de negocio conformados |
| *Bronze (RDV)* | Capa de ingesta cruda sin transformación semántica |
| *Gold (DDV)* | Capa de consumo analítico con métricas y agregaciones |
| *Ownership core* | Responsabilidad de dominio principal sobre entidad transversal |
| *Ownership específico* | Responsabilidad de modelo/subdominio sobre entidad específica |
| *Grano* | Nivel de detalle que representa una fila de la entidad |
| *Semántica* | Significado de negocio de los datos |
| *Conformación* | Integración de múltiples fuentes con significado único |
| *Reutilizable* | Que sirve para múltiples consumos (>1) |
| *Atómico* | Dato en su mínima expresión, sin agregación |

---

*Versión*: 2.0  
*Fecha*: Marzo 2026  
*Autor*: Equipo de Arquitectura de Datos  
*Relacionado con*: Estándares UDV, Reglas de Diseño, Nomenclatura