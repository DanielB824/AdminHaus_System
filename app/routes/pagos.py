from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.security import roles_required
from app.services.pago_service import (
    METODOS, obtener_pagos, obtener_pago_por_id,
    obtener_contratos_para_select, guardar_pago,
)

pagos_bp = Blueprint("pagos", __name__)


def _propietario_actual():
    return session.get("usuario_id") if session.get("rol") == "PROPIETARIO" else None


@pagos_bp.route("/pagos")
@roles_required("ADMINISTRADOR", "GESTOR", "PROPIETARIO")
def lista():
    buscar = request.args.get("buscar", "").strip()
    estado = request.args.get("estado", "todos").strip().lower()
    if estado not in {"todos", "pendiente", "pagado", "vencido"}:
        estado = "todos"
    filas = obtener_pagos(buscar, estado, _propietario_actual())
    return render_template("pagos/pagos.html", filas=filas, buscar=buscar, estado=estado)


@pagos_bp.route("/pagos/nuevo", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def nuevo():
    # Los pagos esperados se generan automáticamente al crear el contrato.
    flash("Los pagos se generan automáticamente al crear un contrato. Selecciona un pago programado para registrar su cobro.", "info")
    return redirect(url_for("pagos.lista"))

@pagos_bp.route("/pagos/<int:pago_id>")
@roles_required("ADMINISTRADOR", "GESTOR", "PROPIETARIO")
def ver(pago_id):
    pago = obtener_pago_por_id(pago_id, _propietario_actual())
    if pago is None:
        abort(404)
    return render_template("pagos/pago_form.html", form=pago, modo="ver", pago_id=pago_id, contratos=[], metodos=sorted(METODOS), error=None)


@pagos_bp.route("/pagos/<int:pago_id>/editar", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def editar(pago_id):
    pago = obtener_pago_por_id(pago_id)
    if pago is None:
        abort(404)
    contratos = obtener_contratos_para_select()
    error = None
    form = pago
    if request.method == "POST":
        form = request.form
        ok, error = guardar_pago(form, pago_id=pago_id)
        if ok:
            return redirect(url_for("pagos.lista"))
    return render_template("pagos/pago_form.html", form=form, modo="editar", pago_id=pago_id, contratos=contratos, metodos=sorted(METODOS), error=error)
