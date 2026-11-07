from flask import Blueprint, render_template, request, redirect, url_for, abort

from app.security import roles_required

from app.services.proveedor_service import (
    obtener_proveedores,
    obtener_especialidades,
    obtener_proveedor_por_id,
    crear_proveedor,
    actualizar_proveedor,
)


proveedores_bp = Blueprint("proveedores", __name__)


@proveedores_bp.route("/proveedores")
@roles_required("ADMINISTRADOR", "GESTOR")
def proveedores():

    filas = obtener_proveedores()
    especialidades = obtener_especialidades()

    return render_template(
        "proveedores/proveedores.html",
        filas=filas,
        especialidades=especialidades,
    )


@proveedores_bp.route("/proveedores/nuevo", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def nuevo_proveedor():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        especialidad = request.form.get("especialidad", "").strip()

        _, error = crear_proveedor(nombre, tipo, telefono, correo, especialidad)

        if error:
            return render_template(
                "proveedores/nuevo_proveedor.html",
                form=request.form,
                modo="nuevo",
                error=error,
            )

        return redirect(url_for("proveedores.proveedores"))

    return render_template(
        "proveedores/nuevo_proveedor.html",
        form={},
        modo="nuevo",
    )


@proveedores_bp.route("/proveedores/<int:proveedor_id>")
@roles_required("ADMINISTRADOR", "GESTOR")
def ver_proveedor(proveedor_id):

    proveedor = obtener_proveedor_por_id(proveedor_id)

    if proveedor is None:
        abort(404)

    return render_template(
        "proveedores/nuevo_proveedor.html",
        form=proveedor,
        modo="ver",
    )


@proveedores_bp.route("/proveedores/<int:proveedor_id>/editar", methods=["GET", "POST"])
@roles_required("ADMINISTRADOR", "GESTOR")
def editar_proveedor(proveedor_id):

    proveedor = obtener_proveedor_por_id(proveedor_id)

    if proveedor is None:
        abort(404)

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()
        especialidad = request.form.get("especialidad", "").strip()

        ok, error = actualizar_proveedor(
            proveedor_id, nombre, tipo, telefono, correo, especialidad
        )

        if error:
            return render_template(
                "proveedores/nuevo_proveedor.html",
                form=request.form,
                modo="editar",
                proveedor_id=proveedor_id,
                error=error,
            )

        return redirect(url_for("proveedores.proveedores"))

    return render_template(
        "proveedores/nuevo_proveedor.html",
        form=proveedor,
        modo="editar",
        proveedor_id=proveedor_id,
    )