#!/usr/bin/env python3
import argparse, json, re, sys, time, uuid, random
import urllib.request, urllib.error, urllib.parse, http.cookiejar
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

OK, MAL = "\033[92m✓\033[0m", "\033[91m✗\033[0m"
if sys.platform == "win32":
    try:
        import os; os.system("")
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

resultados = []


def registrar(nombre, esperado, obtenido, detalle=""):
    bien = obtenido in (esperado if isinstance(esperado, (list, tuple, set)) else [esperado])
    resultados.append(bien)
    esp = "/".join(map(str, esperado)) if isinstance(esperado, (list, tuple, set)) else esperado
    print(f"  {OK if bien else MAL} {nombre:<62} esperado {esp!s:<4} obtenido {obtenido!s:<4} {detalle}")
    return bien


def titulo(t):
    print(f"\n\033[93m━━ {t} ━━\033[0m")


class SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def peticion(opener, metodo, url, cuerpo=None, cabeceras=None, form=False):
    datos = None
    cab = dict(cabeceras or {})
    if cuerpo is not None:
        if form:
            datos = urllib.parse.urlencode(cuerpo).encode()
            cab["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            datos = json.dumps(cuerpo).encode()
            cab["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=datos, method=metodo, headers=cab)
    try:
        r = opener.open(req, timeout=15)
        return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)


# Pruebas API
def probar_api(base, user, clave):
    op = urllib.request.build_opener()
    token = {"v": None}

    def api(metodo, ruta, cuerpo=None, con_token=True, cab=None):
        c = dict(cab or {})
        if con_token and token["v"]:
            c["Authorization"] = f"Token {token['v']}"
        st, txt, _ = peticion(op, metodo, base + ruta, cuerpo, c)
        try:
            return st, json.loads(txt) if txt else None
        except ValueError:
            return st, txt

    sufijo = str(random.randint(1000, 9999))
    num = 9000 + random.randint(0, 800)
    hoy = date.today()
    entrada, salida = hoy + timedelta(days=40), hoy + timedelta(days=43)
    creados = {"hab": [], "hue": [], "res": []}

    titulo("API · TOKEN Y AUTENTICACIÓN")
    registrar("Pedir token sin enviar datos", 400, api("POST", "/api/token/", {}, False)[0])
    registrar("Pedir token con contraseña incorrecta", 401, api("POST", "/api/token/", {"username": user, "password": "mala-" + sufijo}, False)[0])
    registrar("Pedir token con usuario que no existe", 401, api("POST", "/api/token/", {"username": "fantasma" + sufijo, "password": "x"}, False)[0])
    st, d = api("POST", "/api/token/", {"username": user, "password": clave}, False)
    registrar("Pedir token con datos correctos", 200, st)
    if st != 200:
        print("\n  No se pudo obtener el token: revisa --user y --password. Se detiene la prueba API.")
        return
    token["v"] = d["token"]
    registrar("GET habitaciones SIN token", 401, api("GET", "/api/habitaciones/", con_token=False)[0])
    registrar("GET habitaciones con token FALSO", 401, api("GET", "/api/habitaciones/", con_token=False, cab={"Authorization": "Token falso123"})[0])
    registrar("GET huéspedes SIN token", 401, api("GET", "/api/huespedes/", con_token=False)[0])
    registrar("GET reservas SIN token", 401, api("GET", "/api/reservas/", con_token=False)[0])

    titulo("API · HABITACIONES")
    buena = {"numero": num, "tipo": "Suite " + sufijo[:2], "precio": 85000, "disponible": True}
    st, h = api("POST", "/api/habitaciones/", buena)
    registrar("Crear habitación válida (POST)", 201, st)
    hab_id = h["id"] if st == 201 else None
    if hab_id: creados["hab"].append(hab_id)
    registrar("Listar habitaciones (GET)", 200, api("GET", "/api/habitaciones/")[0])
    registrar("Consultar una por id (GET)", 200, api("GET", f"/api/habitaciones/{hab_id}/")[0])
    registrar("Consultar id que no existe", 404, api("GET", "/api/habitaciones/99999999/")[0])
    registrar("PUT sobre la lista (método no permitido)", 405, api("PUT", "/api/habitaciones/", buena)[0])
    malos = [
        ("Número 10000 (máximo es 9999)", dict(buena, numero=10000)),
        ("Número 0", dict(buena, numero=0)),
        ("Número negativo", dict(buena, numero=-5)),
        ("Número con letras", dict(buena, numero="abc")),
        ("Número decimal (1.5)", dict(buena, numero=1.5)),
        ("Sin ningún campo ({})", {}),
        ("Tipo vacío", dict(buena, tipo="", numero=num + 1)),
        ("Tipo de solo 2 caracteres", dict(buena, tipo="Su", numero=num + 1)),
        ("Tipo de 31 caracteres", dict(buena, tipo="S" * 31, numero=num + 1)),
        ("Tipo con símbolos raros <script>", dict(buena, tipo="<script>alert(1)", numero=num + 1)),
        ("Precio 0", dict(buena, precio=0, numero=num + 1)),
        ("Precio 10.000.000 (máximo 9.999.999)", dict(buena, precio=10000000, numero=num + 1)),
        ("Precio con letras", dict(buena, precio="caro", numero=num + 1)),
        ("Número repetido (ya existe)", buena),
    ]
    for nombre, cuerpo in malos:
        registrar("Crear con " + nombre, 400, api("POST", "/api/habitaciones/", cuerpo)[0])
    registrar("Modificar válido (PUT)", 200, api("PUT", f"/api/habitaciones/{hab_id}/", dict(buena, precio=90000))[0])
    registrar("Modificar con datos inválidos (PUT)", 400, api("PUT", f"/api/habitaciones/{hab_id}/", dict(buena, precio=-1))[0])
    registrar("Modificar id que no existe (PUT)", 404, api("PUT", "/api/habitaciones/99999999/", buena)[0])
    registrar("Eliminar id que no existe (DELETE)", 404, api("DELETE", "/api/habitaciones/99999999/")[0])

    titulo("API · HUÉSPEDES")
    rut_ok = f"{random.randint(10000000, 24999999)}-{random.choice('0123456789K')}"
    hue = {"nombre": "Camila", "apellido": "Pruebas", "rut": rut_ok, "email": f"c{sufijo}@correo.cl", "telefono": "912345678"}
    st, hu = api("POST", "/api/huespedes/", hue)
    registrar("Crear huésped válido (RUT inventado, solo formato)", 201, st)
    hue_id = hu["id"] if st == 201 else None
    if hue_id: creados["hue"].append(hue_id)
    registrar("Listar huéspedes", 200, api("GET", "/api/huespedes/")[0])
    registrar("Consultar huésped por id", 200, api("GET", f"/api/huespedes/{hue_id}/")[0])
    registrar("Consultar huésped que no existe", 404, api("GET", "/api/huespedes/99999999/")[0])
    for nombre, cambio in [("RUT con formato malo (123)", {"rut": "123"}),
                           ("RUT con letras", {"rut": "abcdefgh-1"}),
                           ("RUT repetido", {}),
                           ("Nombre con números", {"nombre": "Cami1a", "rut": "11.111.111-1"}),
                           ("Apellido de 1 letra", {"apellido": "R", "rut": "11.111.111-1"}),
                           ("Nombre de 41 caracteres", {"nombre": "A" * 41, "rut": "11.111.111-1"}),
                           ("Correo sin @", {"email": "correo-malo", "rut": "11.111.111-1"}),
                           ("Teléfono con letras", {"telefono": "12ab", "rut": "11.111.111-1"}),
                           ("Teléfono demasiado corto", {"telefono": "1234", "rut": "11.111.111-1"})]:
        registrar("Crear huésped con " + nombre, 400, api("POST", "/api/huespedes/", dict(hue, **cambio))[0])

    titulo("API · RESERVAS")
    res = {"habitacion": hab_id, "huesped": hue_id, "fecha_entrada": entrada.isoformat(),
           "fecha_salida": salida.isoformat(), "personas": 2, "observaciones": ""}
    st, r = api("POST", "/api/reservas/", res)
    registrar("Crear reserva válida", 201, st, f"(total ${r.get('total')}, {r.get('noches')} noches)" if st == 201 else "")
    res_id = r["id"] if st == 201 else None
    if res_id: creados["res"].append(res_id)
    registrar("Listar reservas", 200, api("GET", "/api/reservas/")[0])
    registrar("Consultar reserva por id", 200, api("GET", f"/api/reservas/{res_id}/")[0])
    registrar("Consultar reserva que no existe", 404, api("GET", "/api/reservas/99999999/")[0])
    casos = [
        ("las MISMAS fechas (choque con la anterior)", res),
        ("fechas que se solapan (un día antes)", dict(res, fecha_entrada=(entrada - timedelta(days=1)).isoformat(), fecha_salida=(entrada + timedelta(days=1)).isoformat())),
        ("salida IGUAL a la entrada", dict(res, fecha_salida=res["fecha_entrada"])),
        ("salida ANTES de la entrada", dict(res, fecha_salida=(entrada - timedelta(days=2)).isoformat())),
        ("entrada en el PASADO", dict(res, fecha_entrada=(hoy - timedelta(days=3)).isoformat(), fecha_salida=(hoy + timedelta(days=1)).isoformat())),
        ("más de 30 noches", dict(res, fecha_entrada=(hoy + timedelta(days=100)).isoformat(), fecha_salida=(hoy + timedelta(days=140)).isoformat())),
        ("entrada a más de 2 años", dict(res, fecha_entrada=(hoy + timedelta(days=900)).isoformat(), fecha_salida=(hoy + timedelta(days=902)).isoformat())),
        ("fecha con formato inválido", dict(res, fecha_entrada="31-12-2026")),
        ("fecha que no existe (30 de febrero)", dict(res, fecha_entrada="2027-02-30")),
        ("0 personas", dict(res, personas=0)),
        ("7 personas (máximo 6)", dict(res, personas=7)),
        ("personas con letras", dict(res, personas="dos")),
        ("habitación que no existe", dict(res, habitacion=99999999)),
        ("huésped que no existe", dict(res, huesped=99999999)),
        ("observaciones de 201 caracteres", dict(res, observaciones="x" * 201, fecha_entrada=(hoy + timedelta(days=200)).isoformat(), fecha_salida=(hoy + timedelta(days=202)).isoformat())),
        ("estado inicial 'confirmada' (debe nacer pendiente)", dict(res, estado="confirmada", fecha_entrada=(hoy + timedelta(days=200)).isoformat(), fecha_salida=(hoy + timedelta(days=202)).isoformat())),
        ("sin ningún campo ({})", {}),
    ]
    for nombre, cuerpo in casos:
        registrar("Crear reserva con " + nombre, 400, api("POST", "/api/reservas/", cuerpo)[0])
    st, hoff = api("POST", "/api/habitaciones/", {"numero": num + 50, "tipo": "Cerrada", "precio": 1000, "disponible": False})
    if st == 201:
        creados["hab"].append(hoff["id"])
        registrar("Crear reserva en habitación NO disponible", 400, api("POST", "/api/reservas/", dict(res, habitacion=hoff["id"]))[0])
    registrar("Estado: pendiente → finalizada (salto prohibido)", 400, api("PUT", f"/api/reservas/{res_id}/", dict(res, estado="finalizada"))[0])
    registrar("Estado: pendiente → confirmada (permitido)", 200, api("PUT", f"/api/reservas/{res_id}/", dict(res, estado="confirmada"))[0])
    registrar("Estado: confirmada → en_curso (permitido)", 200, api("PUT", f"/api/reservas/{res_id}/", dict(res, estado="en_curso"))[0])
    registrar("Estado inventado ('volando')", 400, api("PUT", f"/api/reservas/{res_id}/", dict(res, estado="volando"))[0])
    registrar("Borrar reserva EN CURSO", 409, api("DELETE", f"/api/reservas/{res_id}/")[0])
    registrar("Estado: en_curso → finalizada (permitido)", 200, api("PUT", f"/api/reservas/{res_id}/", dict(res, estado="finalizada"))[0])
    registrar("Estado: finalizada → confirmada (volver atrás, prohibido)", 400, api("PUT", f"/api/reservas/{res_id}/", dict(res, estado="confirmada"))[0])
    registrar("Modificar reserva que no existe", 404, api("PUT", "/api/reservas/99999999/", res)[0])

    titulo("API · PROTECCIÓN DE DATOS RELACIONADOS")
    registrar("Borrar habitación que TIENE reservas", 409, api("DELETE", f"/api/habitaciones/{hab_id}/")[0])
    registrar("Borrar huésped que TIENE reservas", 409, api("DELETE", f"/api/huespedes/{hue_id}/")[0])

    titulo("API · LIMPIEZA (borrados correctos)")
    for rid in creados["res"]:
        registrar(f"Borrar reserva #{rid}", 204, api("DELETE", f"/api/reservas/{rid}/")[0])
    for hid in creados["hue"]:
        registrar(f"Borrar huésped #{hid}", 204, api("DELETE", f"/api/huespedes/{hid}/")[0])
    for bid in creados["hab"]:
        registrar(f"Borrar habitación #{bid}", 204, api("DELETE", f"/api/habitaciones/{bid}/")[0])
    registrar("Consultar la habitación ya borrada", 404, api("GET", f"/api/habitaciones/{hab_id}/")[0])
    st, _ = api("POST", "/api/logout/", {})
    registrar("Cerrar sesión API (borra el token)", 200, st)
    registrar("Usar el token ya borrado", 401, api("GET", "/api/habitaciones/")[0])


# Pruebas web
def probar_web(base, user, clave):
    titulo("WEB · RUTAS PROTEGIDAS (sin iniciar sesión)")
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), SinRedireccion)

    def redirige_a_login(ruta):
        st, _, cab = peticion(op, "GET", base + ruta)
        return st, ("/ingreso/" in cab.get("Location", ""))

    for ruta in ["/", "/habitaciones/", "/habitaciones/crear/", "/huespedes/", "/huespedes/crear/", "/reservas/", "/reservas/crear/", "/habitaciones/editar/1/", "/habitaciones/eliminar/1/"]:
        st, a_login = redirige_a_login(ruta)
        registrar(f"{ruta:<28} sin sesión → redirige al login", 302, st if a_login else f"{st}!")

    def csrf():
        for c in jar:
            if "csrftoken" in c.name:
                return c.value
        return ""

    titulo("WEB · LOGIN")
    peticion(op, "GET", base + "/ingreso/")
    st, txt, _ = peticion(op, "POST", base + "/ingreso/", {"username": user, "password": "incorrecta-xyz", "csrfmiddlewaretoken": csrf()}, form=True)
    registrar("Login con contraseña incorrecta → se queda en login", 200, st, "(muestra error)" if "incorrectos" in txt else "(¡sin mensaje!)")
    registrar("   …y el mensaje NO menciona límite de caracteres", True, "30 caracteres" not in txt)
    st, txt, _ = peticion(op, "POST", base + "/ingreso/", {"username": "", "password": "", "csrfmiddlewaretoken": csrf()}, form=True)
    registrar("Login con campos vacíos → se queda en login", 200, st)
    st, txt, _ = peticion(op, "POST", base + "/ingreso/", {"username": "a" * 200, "password": "b" * 200, "csrfmiddlewaretoken": csrf()}, form=True)
    registrar("Login con 200 caracteres → rechazado", 200, st)
    st, _, _ = peticion(op, "POST", base + "/ingreso/", {"username": user, "password": clave})
    registrar("Login SIN token CSRF → bloqueado", 403, st)
    peticion(op, "GET", base + "/ingreso/")
    st, _, cab = peticion(op, "POST", base + "/ingreso/", {"username": user, "password": clave, "csrfmiddlewaretoken": csrf()}, form=True)
    registrar("Login correcto → redirige al inicio", 302, st)

    titulo("WEB · CON SESIÓN: FORMULARIOS (nada inválido se guarda)")
    for ruta in ["/", "/habitaciones/", "/huespedes/", "/reservas/", "/reservas/crear/"]:
        registrar(f"{ruta:<28} con sesión carga", 200, peticion(op, "GET", base + ruta)[0])
    st, _, cab = peticion(op, "GET", base + "/ingreso/")
    registrar("Entrar a /ingreso/ ya logueada → redirige (no muestra login)", 302, st)

    def enviar(ruta, datos):
        peticion(op, "GET", base + ruta)
        datos = dict(datos, csrfmiddlewaretoken=csrf())
        return peticion(op, "POST", base + ruta, datos, form=True)

    sufijo = random.randint(8000, 8999)
    invalidos = [
        ("Habitación: número 10000", "/habitaciones/crear/", {"numero": "10000", "tipo": "Suite", "precio": "5000"}),
        ("Habitación: número con letras", "/habitaciones/crear/", {"numero": "12ab", "tipo": "Suite", "precio": "5000"}),
        ("Habitación: tipo de 2 letras", "/habitaciones/crear/", {"numero": str(sufijo), "tipo": "Su", "precio": "5000"}),
        ("Habitación: tipo con símbolos", "/habitaciones/crear/", {"numero": str(sufijo), "tipo": "S#$%", "precio": "5000"}),
        ("Habitación: precio 0", "/habitaciones/crear/", {"numero": str(sufijo), "tipo": "Suite", "precio": "0"}),
        ("Habitación: precio 10.000.000", "/habitaciones/crear/", {"numero": str(sufijo), "tipo": "Suite", "precio": "10000000"}),
        ("Habitación: todo vacío", "/habitaciones/crear/", {"numero": "", "tipo": "", "precio": ""}),
        ("Huésped: RUT mal escrito", "/huespedes/crear/", {"nombre": "Ana", "apellido": "Rojas", "rut": "1", "email": "a@a.cl", "telefono": "912345678"}),
        ("Huésped: nombre con números", "/huespedes/crear/", {"nombre": "Ana2", "apellido": "Rojas", "rut": "12.159.159-8", "email": "a@a.cl", "telefono": "912345678"}),
        ("Huésped: correo sin @", "/huespedes/crear/", {"nombre": "Ana", "apellido": "Rojas", "rut": "12.159.159-8", "email": "malo", "telefono": "912345678"}),
        ("Huésped: teléfono con letras", "/huespedes/crear/", {"nombre": "Ana", "apellido": "Rojas", "rut": "12.159.159-8", "email": "a@a.cl", "telefono": "abc"}),
        ("Reserva: sin elegir nada", "/reservas/crear/", {"habitacion": "", "huesped": "", "fecha_entrada": "", "fecha_salida": "", "personas": ""}),
    ]
    for nombre, ruta, datos in invalidos:
        st, txt, _ = enviar(ruta, datos)
        registrar(nombre + " → rechazado (vuelve el formulario)", 200, st, "" if "Revisa los siguientes datos" in txt else "(¡sin lista de errores!)")
    st, txt, _ = peticion(op, "GET", base + "/habitaciones/")
    registrar("   …y ninguna de esas habitaciones inválidas quedó guardada", True, str(sufijo) not in txt and "10000" not in txt)

    titulo("WEB · CERRAR SESIÓN")
    peticion(op, "GET", base + "/")
    st, _, cab = peticion(op, "POST", base + "/salir/", {"csrfmiddlewaretoken": csrf()}, form=True)
    registrar("Salir (POST) → redirige al login", 302, st)
    st, a_login = redirige_a_login("/")
    registrar("Después de salir, entrar a / → vuelve al login", 302, st if a_login else f"{st}!")
    st, a_login = redirige_a_login("/habitaciones/")
    registrar("Después de salir, entrar a /habitaciones/ → login", 302, st if a_login else f"{st}!")


# Prueba de carga
def probar_carga(base, user, clave, n):
    titulo(f"ESTRÉS · {n} peticiones en paralelo")
    op = urllib.request.build_opener()
    st, txt, _ = peticion(op, "POST", base + "/api/token/", {"username": user, "password": clave})
    if st != 200:
        print("  No se pudo obtener token para la prueba de carga."); return
    tok = json.loads(txt)["token"]

    def una(i):
        t0 = time.time()
        tipo = i % 4
        if tipo == 0:   st, _, _ = peticion(op, "GET", base + "/api/habitaciones/", cabeceras={"Authorization": f"Token {tok}"}); esp = 200
        elif tipo == 1: st, _, _ = peticion(op, "GET", base + "/api/reservas/", cabeceras={"Authorization": f"Token {tok}"}); esp = 200
        elif tipo == 2: st, _, _ = peticion(op, "GET", base + "/api/habitaciones/"); esp = 401
        else:           st, _, _ = peticion(op, "GET", base + "/api/habitaciones/99999999/", cabeceras={"Authorization": f"Token {tok}"}); esp = 404
        return st == esp, (time.time() - t0) * 1000, st

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=20) as ex:
        r = list(ex.map(una, range(n)))
    total = time.time() - t0
    bien = sum(1 for ok, _, _ in r if ok)
    ms = sorted(m for _, m, _ in r)
    print(f"  Peticiones: {n}   Respondieron como se esperaba: {bien}   Fallaron: {n - bien}")
    print(f"  Tiempo total: {total:.1f}s   Velocidad: {n / total:.0f} peticiones/s")
    print(f"  Tiempo por petición → promedio {sum(ms) / len(ms):.0f} ms · mediana {ms[len(ms) // 2]:.0f} ms · máximo {ms[-1]:.0f} ms")
    registrar("El sistema respondió correctamente bajo carga", n, bien)


def main():
    ap = argparse.ArgumentParser(description="Prueba de errores de Hotel Aurora")
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--solo", choices=["api", "web"])
    ap.add_argument("--carga", type=int, default=0)
    a = ap.parse_args()
    base = a.url.rstrip("/")
    try:
        urllib.request.urlopen(base + "/ingreso/", timeout=8)
    except Exception as e:
        print(f"No puedo conectar con {base}. ¿Está corriendo 'python manage.py runserver'?\n  ({e})")
        sys.exit(2)
    print(f"\n HOTEL AURORA · prueba de errores contra {base}")
    if a.solo != "web": probar_api(base, a.user, a.password)
    if a.solo != "api": probar_web(base, a.user, a.password)
    if a.carga: probar_carga(base, a.user, a.password, a.carga)
    bien = sum(resultados)
    print(f"\n\033[93m━━ RESUMEN ━━\033[0m\n  {bien} de {len(resultados)} casos respondieron como se esperaba.")
    print("  " + ("\033[92mTodo correcto: el sistema rechaza lo inválido y acepta lo válido.\033[0m" if bien == len(resultados)
                  else "\033[91mHay casos con ✗: revísalos arriba.\033[0m"))
    sys.exit(0 if bien == len(resultados) else 1)


if __name__ == "__main__":
    main()
