# Guía de demostración (CMD de Windows)

Servidor corriendo (`python manage.py runserver`). Reemplazar `admin` / `TuClave` por tu usuario.

## 1. Login (200) y tokens
```bat
curl -i -X POST http://127.0.0.1:8000/api/login/ -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"TuClave\"}"
```
Respuesta: `{"mensaje":"Login correcto.","access_token":"...","refresh_token":"...","usuario":"admin","sesion_id":1}`
Copiar el `access_token` donde diga `TU_ACCESS` y el `refresh_token` donde diga `TU_REFRESH`.

Errores: sin password → **400**; clave incorrecta → **401**.

## 2. Usar el Access en endpoints protegidos
```bat
curl -i http://127.0.0.1:8000/api/habitaciones/ -H "Authorization: Bearer TU_ACCESS"
curl -i -X POST http://127.0.0.1:8000/api/habitaciones/ -H "Authorization: Bearer TU_ACCESS" -H "Content-Type: application/json" -d "{\"numero\":301,\"tipo\":\"Suite\",\"precio\":90000,\"disponible\":true}"
curl -i http://127.0.0.1:8000/api/habitaciones/1/ -H "Authorization: Bearer TU_ACCESS"
curl -i -X PUT http://127.0.0.1:8000/api/habitaciones/1/ -H "Authorization: Bearer TU_ACCESS" -H "Content-Type: application/json" -d "{\"numero\":301,\"tipo\":\"Presidencial\",\"precio\":150000,\"disponible\":false}"
curl -i -X DELETE http://127.0.0.1:8000/api/habitaciones/1/ -H "Authorization: Bearer TU_ACCESS"
```
Códigos: GET 200 · POST 201 · PUT 200 · DELETE 200 · id que no existe 404 · datos inválidos 400.

Perfil protegido (clase): `curl -i http://127.0.0.1:8000/api/perfil/ -H "Authorization: Bearer TU_ACCESS"` → 200; sin token → 401.

## 3. Errores de token (todos 401)
```bat
curl -i http://127.0.0.1:8000/api/habitaciones/
curl -i http://127.0.0.1:8000/api/habitaciones/ -H "Authorization: Bearer esto.no.es.un.token"
```
- Sin token → `{"error":"Token requerido."}`
- Token inválido → `{"error":"Token inválido."}`
- Access vencido → `{"error":"El token expiró."}` (para verlo: `set JWT_ACCESS_MINUTOS=1` antes de `runserver` y esperar 1 minuto)

## 4. Renovar con el Refresh
```bat
curl -i -X POST http://127.0.0.1:8000/api/refresh/ -H "Content-Type: application/json" -d "{\"refresh_token\":\"TU_REFRESH\"}"
```
200 con un `access_token` nuevo. Sin cuerpo → 400. Refresh inválido, vencido o de una sesión cerrada → 401.

## 5. Logout (revocación)
```bat
curl -i -X POST http://127.0.0.1:8000/api/logout/ -H "Authorization: Bearer TU_ACCESS"
```
200. Después, el Access y el Refresh dan **401** aunque no hayan vencido (la fila queda `activa = 0` en la tabla `habitaciones_sesion`).

## 6. Demostración en el navegador (F12)
1. Abrir `/ingreso/` con F12 → **Network** y **Console** visibles. Entrar: `POST /api/login/ 200`, luego `GET / 200`.
2. **Application → Cookies → http://127.0.0.1:8000**: aparecen `access_token`, `refresh_token` y `aurora_sessionid`. **Local storage** y **Session storage** están vacíos.
3. En phpMyAdmin → `hotel_db` → tabla **`habitaciones_sesion`** → Examinar: las columnas `access_token` y `refresh_token` son idénticas a las cookies.
4. Crear una habitación → en la consola `[API] POST /api/habitaciones/ -> 201`; editar → `PUT ... 200`; eliminar → `DELETE ... 200`.
5. Con `set JWT_ACCESS_MINUTOS=1`: esperar 1 minuto con la página abierta y eliminar algo → se ve `DELETE 401`, `POST /api/refresh/ 200` y `DELETE 200`. La cookie y la BD cambian al Access nuevo.
6. **Salir**: `POST /api/logout/ 200`, las cookies se borran, la fila queda `activa = 0` y entrar a `/habitaciones/` redirige al login.

## 7. Script automático
```bat
python demo_errores.py --user admin --password TuClave
```
