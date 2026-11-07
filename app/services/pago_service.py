from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_, update

from app import db
from app.models.pago import Pago
from app.models.contrato import Contrato
from app.models.propiedad import Propiedad
from app.models.inquilino import Inquilino
from app.models.propietario import Propietario
from app.services.contrato_service import generar_pagos_faltantes_contratos_activos

ESTADOS = {"PENDIENTE", "PAGADO", "VENCIDO"}
METODOS = {"EFECTIVO", "TRANSFERENCIA", "OTRO"}


def _base_query(usuario_id_propietario=None):
    q = (db.session.query(
            Pago.id.label("id"), Pago.contrato_id.label("contrato_id"),
            Pago.fecha_esperada.label("fecha_esperada"), Pago.fecha_pago.label("fecha_pago"),
            Pago.monto.label("monto"), Pago.estado.label("estado"), Pago.metodo_pago.label("metodo_pago"),
            Propiedad.codigo.label("propiedad_codigo"),
            (Inquilino.nombre + " " + Inquilino.apellido).label("inquilino_texto"),
        )
        .join(Contrato, Pago.contrato_id == Contrato.id)
        .join(Propiedad, Contrato.propiedad_id == Propiedad.id)
        .join(Inquilino, Contrato.inquilino_id == Inquilino.id))
    if usuario_id_propietario is not None:
        q = q.join(Propietario, Propiedad.propietario_id == Propietario.id).filter(Propietario.usuario_id == usuario_id_propietario)
    return q


def sincronizar_estados_vencimiento():
    """Persiste PENDIENTE/VENCIDO según la fecha actual, sin tocar PAGADO."""
    hoy = date.today()
    db.session.execute(
        update(Pago)
        .where(Pago.estado != "PAGADO")
        .where(Pago.fecha_esperada < hoy)
        .values(estado="VENCIDO", fecha_pago=None, metodo_pago=None)
    )
    db.session.execute(
        update(Pago)
        .where(Pago.estado != "PAGADO")
        .where(Pago.fecha_esperada >= hoy)
        .values(estado="PENDIENTE", fecha_pago=None, metodo_pago=None)
    )
    db.session.commit()


def obtener_pagos(buscar="", estado="todos", usuario_id_propietario=None):
    generar_pagos_faltantes_contratos_activos()
    sincronizar_estados_vencimiento()
    q = _base_query(usuario_id_propietario)
    if buscar:
        termino = f"%{buscar}%"
        q = q.filter(or_(Propiedad.codigo.ilike(termino), Inquilino.nombre.ilike(termino), Inquilino.apellido.ilike(termino)))
    filas = q.order_by(Pago.fecha_esperada.desc(), Pago.id.desc()).all()
    resultado = []
    for fila in filas:
        datos = dict(fila._mapping)
        if estado == "todos" or datos["estado"] == estado.upper():
            resultado.append(datos)
    return resultado


def obtener_pago_por_id(pago_id, usuario_id_propietario=None):
    sincronizar_estados_vencimiento()
    fila = _base_query(usuario_id_propietario).filter(Pago.id == pago_id).first()
    if not fila:
        return None
    return dict(fila._mapping)


def obtener_contratos_para_select(usuario_id_propietario=None):
    q = (db.session.query(Contrato, Propiedad.codigo, Inquilino.nombre, Inquilino.apellido)
         .join(Propiedad, Contrato.propiedad_id == Propiedad.id)
         .join(Inquilino, Contrato.inquilino_id == Inquilino.id)
         .filter(Contrato.estado == "ACTIVO"))
    if usuario_id_propietario is not None:
        q = q.join(Propietario, Propiedad.propietario_id == Propietario.id).filter(Propietario.usuario_id == usuario_id_propietario)
    return [{"id": c.id, "texto": f"{codigo} — {nombre} {apellido}", "monto": c.monto_mensual}
            for c, codigo, nombre, apellido in q.order_by(Propiedad.codigo).all()]


def _parsear_fecha(valor, campo):
    try:
        return date.fromisoformat(valor)
    except (ValueError, TypeError):
        raise ValueError(f"La {campo} es obligatoria y debe ser una fecha válida.")


def guardar_pago(datos, pago_id=None, usuario_id_propietario=None):
    try:
        contrato_id = int(datos.get("contrato_id", ""))
    except (TypeError, ValueError):
        return False, "Selecciona un contrato válido."
    contrato = db.session.get(Contrato, contrato_id)
    if not contrato:
        return False, "El contrato seleccionado no existe."
    if contrato.estado != "ACTIVO":
        return False, "Solo se pueden registrar pagos asociados a contratos activos."
    if usuario_id_propietario is not None:
        propietario = Propietario.query.filter_by(id=Propiedad.query.filter_by(id=contrato.propiedad_id).with_entities(Propiedad.propietario_id).scalar(), usuario_id=usuario_id_propietario).first()
        if not propietario:
            return False, "No tienes permiso para gestionar pagos de este contrato."
    try:
        fecha_esperada = _parsear_fecha(datos.get("fecha_esperada"), "fecha esperada")
        fecha_pago_raw = (datos.get("fecha_pago") or "").strip()
        fecha_pago = date.fromisoformat(fecha_pago_raw) if fecha_pago_raw else None
        monto = Decimal((datos.get("monto") or "").strip())
        if not monto.is_finite() or monto < 0 or monto.as_tuple().exponent < -2:
            return False, "El monto debe ser mayor o igual a cero y tener máximo dos decimales."
    except (ValueError, InvalidOperation, TypeError):
        return False, "Revisa las fechas y el monto ingresado."
    estado_solicitado = (datos.get("estado") or "PENDIENTE").strip().upper()
    metodo = (datos.get("metodo_pago") or "").strip().upper() or None
    if estado_solicitado not in ESTADOS:
        return False, "El estado seleccionado no es válido."
    if metodo and metodo not in METODOS:
        return False, "El método de pago seleccionado no es válido."

    if estado_solicitado == "PAGADO":
        if fecha_pago is None or metodo is None:
            return False, "Para marcar un pago como pagado, indica la fecha de pago y el método utilizado."
        estado = "PAGADO"
    else:
        # Pendiente y vencido no se eligen manualmente: se determinan por la fecha.
        fecha_pago = None
        metodo = None
        estado = "VENCIDO" if fecha_esperada < date.today() else "PENDIENTE"

    # Se permiten pagos anticipados; no es un error de negocio.
    pago = db.session.get(Pago, pago_id) if pago_id else Pago()
    if pago_id and not pago:
        return False, "El pago que intentas editar no existe."
    duplicado = db.session.query(Pago.id).filter(
        Pago.contrato_id == contrato_id,
        Pago.fecha_esperada == fecha_esperada,
        Pago.id != (pago_id or -1),
    ).first()
    if duplicado:
        return False, "Ya existe un pago programado para ese contrato y esa fecha."
    pago.contrato_id = contrato_id
    pago.fecha_esperada = fecha_esperada
    pago.fecha_pago = fecha_pago
    pago.monto = monto
    pago.estado = estado
    pago.metodo_pago = metodo
    try:
        db.session.add(pago)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return False, "No se pudo guardar el pago. Verifica los datos y vuelve a intentarlo."
    return True, None
