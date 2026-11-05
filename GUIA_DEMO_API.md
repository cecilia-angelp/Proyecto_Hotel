# Guía de demostración de la API (CMD de Windows)

Con el servidor corriendo (`python manage.py runserver`) y un superusuario creado. Reemplazar `admin` / `TuClave` por el usuario creado.

**1. Pedir el token (login API)**
```bat
curl -X POST http://127.0.0.1:8000/api/token/ -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"TuClave\"}"
```
Respuesta esperada (200): `{"token":"abc123...","user":"admin","detail":"Autenticación correcta."}`
Usar el valor del token en lugar de `TU_TOKEN`.

**2. GET – listar**
```bat
curl http://127.0.0.1:8000/api/habitaciones/ -H "Authorization: Token TU_TOKEN"
```

**3. POST – crear** (201)
```bat
curl -X POST http://127.0.0.1:8000/api/habitaciones/ -H "Authorization: Token TU_TOKEN" -H "Content-Type: application/json" -d "{\"numero\":301,\"tipo\":\"Suite\",\"precio\":90000,\"disponible\":true}"
```

**4. GET – consultar por ID** (reemplaza `1` por el id que devolvió el POST)
```bat
curl http://127.0.0.1:8000/api/habitaciones/1/ -H "Authorization: Token TU_TOKEN"
```

**5. PUT – actualizar** (200)
```bat
curl -X PUT http://127.0.0.1:8000/api/habitaciones/1/ -H "Authorization: Token TU_TOKEN" -H "Content-Type: application/json" -d "{\"numero\":301,\"tipo\":\"Presidencial\",\"precio\":150000,\"disponible\":false}"
```

**6. DELETE – eliminar** (204, sin cuerpo)
```bat
curl -i -X DELETE http://127.0.0.1:8000/api/habitaciones/1/ -H "Authorization: Token TU_TOKEN"
```

## Casos de error para mostrar al profesor
| Caso | Comando | Resultado |
|---|---|---|
| Sin token | `curl -i http://127.0.0.1:8000/api/habitaciones/` | 401 |
| Token inválido | `curl -i http://127.0.0.1:8000/api/habitaciones/ -H "Authorization: Token falso"` | 401 |
| Clave incorrecta | login con una clave mala | 401 |
| Datos inválidos | POST con `"numero":-1,"tipo":"A","precio":0` | 400 con el detalle de cada campo |
| Número repetido | POST con un número que ya existe | 400 |
| ID inexistente | `curl -i http://127.0.0.1:8000/api/habitaciones/99999/ -H "Authorization: Token TU_TOKEN"` | 404 |

Tras cada POST / PUT / DELETE, recarga `http://127.0.0.1:8000/habitaciones/` y revisa la tabla `habitaciones_habitacion` en phpMyAdmin: los cambios deben verse en ambos.

---

## Huéspedes y Reservas

Todas llevan el header `Authorization: Token <key>` (sin token → 401).

| Recurso | Lista / crear | Ver / editar / borrar |
|---|---|---|
| Huéspedes | `GET/POST /api/huespedes/` | `GET/PUT/DELETE /api/huespedes/<id>/` |
| Reservas | `GET/POST /api/reservas/` | `GET/PUT/DELETE /api/reservas/<id>/` |

Ejemplo huésped (POST): `{"nombre":"Camila","apellido":"Rojas","rut":"12.159.159-8","email":"camila@correo.cl","telefono":"912345678"}`
(El RUT solo se valida por formato: 7-8 dígitos, guion y dígito 0-9 o K. Se guarda sin puntos.)

Ejemplo reserva (POST): `{"habitacion":1,"huesped":1,"fecha_entrada":"2026-12-10","fecha_salida":"2026-12-13","personas":2,"observaciones":""}`
→ 201, con `noches` y `total` calculados. Estado inicial siempre `pendiente`.

Reglas de negocio (400 si no se cumplen): salida posterior a entrada; máximo 30 noches; entrada no en el pasado
ni a más de 2 años; 1 a 6 personas; la habitación debe estar disponible y sin otra reserva activa en esas fechas;
estados permitidos: pendiente→confirmada/cancelada, confirmada→en_curso/cancelada, en_curso→finalizada.
Borrar una habitación/huésped con reservas → 409; borrar una reserva en curso → 409.
