Base de datos

-- =========================================================
-- ADMINHAUS
-- Base de datos para gestión inmobiliaria
-- PostgreSQL
-- =========================================================


-- =========================================================
-- 1. USUARIO
-- =========================================================

CREATE TABLE usuario (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    username VARCHAR(50) NOT NULL UNIQUE,

    password_hash VARCHAR(255) NOT NULL,

    rol VARCHAR(20) NOT NULL,

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_usuario_rol
        CHECK (rol IN (
            'ADMINISTRADOR',
            'GESTOR',
            'PROPIETARIO'
        ))
);


-- =========================================================
-- 2. PROPIETARIO
-- =========================================================

CREATE TABLE propietario (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,

    apellido VARCHAR(100) NOT NULL,

    dui VARCHAR(10) NOT NULL UNIQUE,

    telefono VARCHAR(20),

    correo VARCHAR(150),

    usuario_id INTEGER UNIQUE,

    CONSTRAINT fk_propietario_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario(id)
        ON DELETE SET NULL
);


-- =========================================================
-- 3. INQUILINO
-- =========================================================

CREATE TABLE inquilino (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre VARCHAR(100) NOT NULL,

    apellido VARCHAR(100) NOT NULL,

    dui VARCHAR(10) NOT NULL UNIQUE,

    telefono VARCHAR(20),

    correo VARCHAR(150)
);


-- =========================================================
-- 4. PROPIEDAD
-- =========================================================

CREATE TABLE propiedad (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    codigo VARCHAR(30) NOT NULL UNIQUE,

    tipo VARCHAR(20) NOT NULL,

    direccion TEXT NOT NULL,

    municipio VARCHAR(100) NOT NULL,

    departamento VARCHAR(100) NOT NULL,

    descripcion TEXT,

    habitaciones INTEGER NOT NULL DEFAULT 0,

    banos INTEGER NOT NULL DEFAULT 0,

    parqueos INTEGER NOT NULL DEFAULT 0,

    metros_cuadrados NUMERIC(10,2),

    precio_alquiler NUMERIC(10,2) NOT NULL,

    estado VARCHAR(20) NOT NULL DEFAULT 'DISPONIBLE',

    propietario_id INTEGER NOT NULL,

    CONSTRAINT chk_propiedad_tipo
        CHECK (tipo IN (
            'CASA',
            'APARTAMENTO'
        )),

    CONSTRAINT chk_propiedad_estado
        CHECK (estado IN (
            'DISPONIBLE',
            'ALQUILADA',
            'INACTIVA'
        )),

    CONSTRAINT chk_propiedad_habitaciones
        CHECK (habitaciones >= 0),

    CONSTRAINT chk_propiedad_banos
        CHECK (banos >= 0),

    CONSTRAINT chk_propiedad_parqueos
        CHECK (parqueos >= 0),

    CONSTRAINT chk_propiedad_metros
        CHECK (metros_cuadrados IS NULL OR metros_cuadrados > 0),

    CONSTRAINT chk_propiedad_precio
        CHECK (precio_alquiler >= 0),

    CONSTRAINT fk_propiedad_propietario
        FOREIGN KEY (propietario_id)
        REFERENCES propietario(id)
        ON DELETE RESTRICT
);


-- =========================================================
-- 5. FOTOGRAFIA
-- =========================================================

CREATE TABLE fotografia (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    propiedad_id INTEGER NOT NULL,

    ruta VARCHAR(500) NOT NULL,

    CONSTRAINT fk_fotografia_propiedad
        FOREIGN KEY (propiedad_id)
        REFERENCES propiedad(id)
        ON DELETE CASCADE
);


-- =========================================================
-- 6. CONTRATO
-- =========================================================

CREATE TABLE contrato (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    propiedad_id INTEGER NOT NULL,

    inquilino_id INTEGER NOT NULL,

    fecha_inicio DATE NOT NULL,

    fecha_fin DATE NOT NULL,

    monto_mensual NUMERIC(10,2) NOT NULL,

    deposito NUMERIC(10,2) NOT NULL DEFAULT 0,

    dia_pago INTEGER NOT NULL,

    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',

    contrato_anterior_id INTEGER,

    CONSTRAINT chk_contrato_fechas
        CHECK (fecha_fin >= fecha_inicio),

    CONSTRAINT chk_contrato_monto
        CHECK (monto_mensual >= 0),

    CONSTRAINT chk_contrato_deposito
        CHECK (deposito >= 0),

    CONSTRAINT chk_contrato_dia_pago
        CHECK (dia_pago BETWEEN 1 AND 31),

    CONSTRAINT chk_contrato_estado
        CHECK (estado IN (
            'ACTIVO',
            'FINALIZADO',
            'CANCELADO'
        )),

    CONSTRAINT fk_contrato_propiedad
        FOREIGN KEY (propiedad_id)
        REFERENCES propiedad(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_contrato_inquilino
        FOREIGN KEY (inquilino_id)
        REFERENCES inquilino(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_contrato_anterior
        FOREIGN KEY (contrato_anterior_id)
        REFERENCES contrato(id)
        ON DELETE RESTRICT
);


-- =========================================================
-- 7. REGLA:
-- Una propiedad no puede tener más de un contrato ACTIVO
-- =========================================================

CREATE UNIQUE INDEX uq_contrato_propiedad_activo
ON contrato (propiedad_id)
WHERE estado = 'ACTIVO';


-- =========================================================
-- 8. PAGO
-- =========================================================

CREATE TABLE pago (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    contrato_id INTEGER NOT NULL,

    fecha_esperada DATE NOT NULL,

    fecha_pago DATE,

    monto NUMERIC(10,2) NOT NULL,

    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',

    metodo_pago VARCHAR(30),

    CONSTRAINT chk_pago_monto
        CHECK (monto >= 0),

    CONSTRAINT chk_pago_estado
        CHECK (estado IN (
            'PENDIENTE',
            'PAGADO',
            'VENCIDO'
        )),

    CONSTRAINT chk_pago_pagado
        CHECK (
            estado <> 'PAGADO'
            OR fecha_pago IS NOT NULL
        ),

    CONSTRAINT chk_pago_metodo
        CHECK (
            estado <> 'PAGADO'
            OR metodo_pago IS NOT NULL
        ),

    CONSTRAINT fk_pago_contrato
        FOREIGN KEY (contrato_id)
        REFERENCES contrato(id)
        ON DELETE RESTRICT
);


-- =========================================================
-- 9. PROVEEDOR DE MANTENIMIENTO
-- =========================================================

CREATE TABLE proveedor_mantenimiento (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    nombre VARCHAR(150) NOT NULL,

    tipo VARCHAR(20) NOT NULL,

    telefono VARCHAR(20),

    correo VARCHAR(150),

    especialidad VARCHAR(100),

    CONSTRAINT chk_proveedor_tipo
        CHECK (tipo IN (
            'TECNICO',
            'EMPRESA'
        ))
);


-- =========================================================
-- 10. MANTENIMIENTO
-- =========================================================

CREATE TABLE mantenimiento (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    propiedad_id INTEGER NOT NULL,

    proveedor_id INTEGER,

    descripcion TEXT NOT NULL,

    categoria VARCHAR(100) NOT NULL,

    fecha_solicitud DATE NOT NULL,

    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',

    costo NUMERIC(10,2),

    observaciones TEXT,

    fecha_resolucion DATE,

    CONSTRAINT chk_mantenimiento_estado
        CHECK (estado IN (
            'PENDIENTE',
            'EN PROCESO',
            'RESUELTO',
            'CANCELADO'
        )),

    CONSTRAINT chk_mantenimiento_costo
        CHECK (costo IS NULL OR costo >= 0),

    CONSTRAINT chk_mantenimiento_fechas
        CHECK (
            fecha_resolucion IS NULL
            OR fecha_resolucion >= fecha_solicitud
        ),

    CONSTRAINT fk_mantenimiento_propiedad
        FOREIGN KEY (propiedad_id)
        REFERENCES propiedad(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_mantenimiento_proveedor
        FOREIGN KEY (proveedor_id)
        REFERENCES proveedor_mantenimiento(id)
        ON DELETE SET NULL
);


-- Propiedades
CREATE INDEX idx_propiedad_propietario
ON propiedad(propietario_id);

CREATE INDEX idx_propiedad_estado
ON propiedad(estado);


-- Contratos
CREATE INDEX idx_contrato_inquilino
ON contrato(inquilino_id);

CREATE INDEX idx_contrato_propiedad
ON contrato(propiedad_id);

CREATE INDEX idx_contrato_estado
ON contrato(estado);


-- Pagos
CREATE INDEX idx_pago_contrato
ON pago(contrato_id);

CREATE INDEX idx_pago_estado
ON pago(estado);

CREATE INDEX idx_pago_fecha_esperada
ON pago(fecha_esperada);


-- Mantenimientos
CREATE INDEX idx_mantenimiento_propiedad
ON mantenimiento(propiedad_id);

CREATE INDEX idx_mantenimiento_proveedor
ON mantenimiento(proveedor_id);

CREATE INDEX idx_mantenimiento_estado
ON mantenimiento(estado);

