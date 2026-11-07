from sqlalchemy import text

from app import db


TIPOS_VALIDOS = ("TECNICO", "EMPRESA")


def obtener_proveedores():
    """
    Obtiene todos los proveedores de mantenimiento (técnicos y
    empresas) para la pantalla de Proveedores y técnicos.
    El filtrado por texto, tipo y especialidad se hace en la
    pantalla con JavaScript (igual que en Inquilinos).
    """

    filas_bd = db.session.execute(
        text("""
            SELECT
                id,
                nombre,
                tipo,
                telefono,
                correo,
                especialidad
            FROM proveedor_mantenimiento
            ORDER BY nombre
        """)
    ).mappings().all()

    return [
        {
            "id": fila["id"],
            "nombre": fila["nombre"],
            "tipo": fila["tipo"],
            "telefono": fila["telefono"],
            "correo": fila["correo"],
            "especialidad": fila["especialidad"],
        }
        for fila in filas_bd
    ]


def obtener_especialidades():
    """
    Lista de especialidades distintas ya registradas,
    para llenar el filtro 'Especialidad' de la pantalla.
    """

    filas = db.session.execute(
        text("""
            SELECT DISTINCT especialidad
            FROM proveedor_mantenimiento
            WHERE especialidad IS NOT NULL
              AND especialidad <> ''
            ORDER BY especialidad
        """)
    ).scalars().all()

    return list(filas)


def obtener_proveedor_por_id(proveedor_id):
    """
    Obtiene un proveedor por su id. Devuelve None si no existe.
    """

    fila = db.session.execute(
        text("""
            SELECT
                id,
                nombre,
                tipo,
                telefono,
                correo,
                especialidad
            FROM proveedor_mantenimiento
            WHERE id = :proveedor_id
        """),
        {
            "proveedor_id": proveedor_id
        }
    ).mappings().first()

    if fila is None:
        return None

    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "tipo": fila["tipo"],
        "telefono": fila["telefono"],
        "correo": fila["correo"],
        "especialidad": fila["especialidad"],
    }


def _validar_proveedor(nombre, tipo):
    """
    Validaciones comunes para crear y actualizar.
    Devuelve un mensaje de error, o None si todo está bien.
    """

    if not nombre or not tipo:
        return "Nombre y tipo son obligatorios."

    if tipo not in TIPOS_VALIDOS:
        return "El tipo de proveedor no es válido."

    return None


def crear_proveedor(nombre, tipo, telefono, correo, especialidad):
    """
    Crea un proveedor nuevo.
    Devuelve una tupla (proveedor_id, error):
    - Si error es None, el proveedor se guardó correctamente.
    - Si error trae un mensaje, no se guardó nada.
    """

    error = _validar_proveedor(nombre, tipo)

    if error:
        return None, error

    nuevo_id = db.session.execute(
        text("""
            INSERT INTO proveedor_mantenimiento
                (nombre, tipo, telefono, correo, especialidad)
            VALUES
                (:nombre, :tipo, :telefono, :correo, :especialidad)
            RETURNING id
        """),
        {
            "nombre": nombre,
            "tipo": tipo,
            "telefono": telefono or None,
            "correo": correo or None,
            "especialidad": especialidad or None,
        }
    ).scalar_one()

    db.session.commit()

    return nuevo_id, None


def actualizar_proveedor(proveedor_id, nombre, tipo, telefono, correo, especialidad):
    """
    Actualiza los datos de un proveedor existente.
    Devuelve una tupla (ok, error):
    - Si error es None, se actualizó correctamente (ok = True).
    - Si error trae un mensaje, no se guardó nada (ok = False).
    """

    error = _validar_proveedor(nombre, tipo)

    if error:
        return False, error

    resultado = db.session.execute(
        text("""
            UPDATE proveedor_mantenimiento
            SET nombre = :nombre,
                tipo = :tipo,
                telefono = :telefono,
                correo = :correo,
                especialidad = :especialidad
            WHERE id = :proveedor_id
        """),
        {
            "nombre": nombre,
            "tipo": tipo,
            "telefono": telefono or None,
            "correo": correo or None,
            "especialidad": especialidad or None,
            "proveedor_id": proveedor_id,
        }
    )

    db.session.commit()

    if resultado.rowcount == 0:
        return False, "No se encontró el proveedor a actualizar."

    return True, None