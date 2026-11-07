AdminHaus — cambios de la entrega

- Se agregó el módulo Pagos con listado, búsqueda por propiedad/inquilino, filtros por estado y acciones de ver/editar.
- Se agregó el registro/edición siguiendo la estructura de bases y clases CSS existentes.
- Los pagos se consultan desde PostgreSQL a través de SQLAlchemy; no se usa información ficticia en la tabla.
- Los usuarios con rol PROPIETARIO solo ven pagos de propiedades vinculadas a su cuenta y no pueden registrar ni editar pagos.
- Solo se ofrecen contratos activos para registrar/editar pagos.
- Para estado PAGADO se exige fecha de pago y método de pago. El monto debe ser no negativo y admite hasta dos decimales.
- Los pagos PENDIENTE con fecha esperada anterior a hoy se muestran como VENCIDO sin depender de una tarea programada.
- Se reemplazó el porcentaje fijo del dashboard del gestor por el dato dinámico porcentaje_alquiladas.
- Se conectó el enlace Pagos en las barras laterales.

Importante: el ZIP no incluye .env ni credenciales. Conserva tu .env local y reemplaza los archivos del proyecto con los de esta entrega. No se usa db.create_all() ni se modifica el esquema de la base de datos.

Verificación ejecutada: compilación sintáctica de archivos Python (compileall). No se pudo verificar la operación contra tu PostgreSQL porque este entorno no tiene acceso a tu base de datos.


## Corrección de generación automática y estados

- Al crear un contrato se generan automáticamente sus mensualidades esperadas, desde la primera fecha de pago que no sea anterior al inicio hasta la fecha de fin, inclusive. Si el día de pago no existe en un mes, se utiliza el último día de ese mes.
- Al consultar Pagos se completan también las mensualidades faltantes de contratos activos preexistentes. La generación evita duplicar un contrato y fecha esperada que ya tengan pago.
- No se permite crear pagos manuales desde `/pagos/nuevo`; el usuario registra el cobro editando la mensualidad generada.
- `PENDIENTE` y `VENCIDO` se determinan y guardan en PostgreSQL según la fecha esperada; al consultar el listado/detalle se sincronizan los estados. `PAGADO` requiere fecha de pago y método, y no se cambia automáticamente.
- No se alteró el esquema de la base de datos ni se usa `db.create_all()`.
- Verificación local: compilación de Python. La integración real con PostgreSQL debe probarse con la base de datos del proyecto.
