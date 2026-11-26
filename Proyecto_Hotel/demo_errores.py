#!/usr/bin/env python3
"""Recorre la API con JWT y muestra el codigo HTTP de cada caso.

Uso (con el servidor corriendo):
    python demo_errores.py --user USUARIO --password CLAVE
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

resultados = []


def llamar(base, metodo, ruta, cuerpo=None, token=None):
    cab = {}
    datos = None
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode()
        cab["Content-Type"] = "application/json"
    if token:
        cab["Authorization"] = "Bearer " + token
    req = urllib.request.Request(base + ruta, data=datos, method=metodo, headers=cab)
    try:
        r = urllib.request.urlopen(req, timeout=15)
        codigo, texto = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        codigo, texto = e.code, e.read().decode("utf-8", "replace")
    try:
        return codigo, json.loads(texto)
    except ValueError:
        return codigo, texto


def caso(nombre, esperado, obtenido, detalle=""):
    bien = obtenido == esperado
    resultados.append(bien)
    marca = "OK " if bien else "MAL"
    print(f"  [{marca}] {nombre:<52} esperado {esperado}  obtenido {obtenido}  {detalle}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    a = ap.parse_args()
    b = a.base.rstrip("/")

    print("\nAutenticacion")
    c, _ = llamar(b, "POST", "/api/login/", {"username": a.user})
    caso("Login sin password", 400, c)
    c, _ = llamar(b, "POST", "/api/login/", {"username": a.user, "password": "incorrecta"})
    caso("Login con clave incorrecta", 401, c)
    c, d = llamar(b, "POST", "/api/login/", {"username": a.user, "password": a.password})
    caso("Login correcto (Access + Refresh)", 200, c)
    if c != 200:
        print("\nNo se pudo iniciar sesion; se detiene la prueba.")
        sys.exit(1)
    acc, ref = d["access_token"], d["refresh_token"]

    c, _ = llamar(b, "POST", "/api/refresh/", {})
    caso("Refresh sin token", 400, c)
    c, _ = llamar(b, "POST", "/api/refresh/", {"refresh_token": "basura"})
    caso("Refresh invalido", 401, c)
    c, d2 = llamar(b, "POST", "/api/refresh/", {"refresh_token": ref})
    caso("Refresh correcto (nuevo Access)", 200, c)
    nuevo = d2["access_token"] if c == 200 else acc

    c, _ = llamar(b, "GET", "/api/perfil/")
    caso("GET perfil sin token", 401, c)
    c, _ = llamar(b, "GET", "/api/perfil/", token=nuevo)
    caso("GET perfil con Access valido", 200, c)

    print("\nProteccion con token")
    c, _ = llamar(b, "GET", "/api/habitaciones/")
    caso("GET sin token", 401, c)
    c, _ = llamar(b, "GET", "/api/habitaciones/", token="no.es.token")
    caso("GET con token invalido", 401, c)
    c, _ = llamar(b, "GET", "/api/habitaciones/", token=acc)
    caso("GET con el Access anterior (ya reemplazado)", 401, c)

    print("\nCRUD de habitaciones")
    c, _ = llamar(b, "GET", "/api/habitaciones/", token=nuevo)
    caso("GET lista", 200, c)
    c, _ = llamar(b, "POST", "/api/habitaciones/", {"numero": 0, "tipo": "Suite", "precio": 1000}, nuevo)
    caso("POST con datos invalidos", 400, c)
    c, d = llamar(b, "POST", "/api/habitaciones/", {"numero": 9001, "tipo": "Demo", "precio": 5000, "disponible": True}, nuevo)
    caso("POST crear", 201, c)
    pk = d["habitacion"]["id"] if c == 201 else 0
    c, _ = llamar(b, "GET", f"/api/habitaciones/{pk}/", token=nuevo)
    caso("GET por id", 200, c)
    c, _ = llamar(b, "PUT", f"/api/habitaciones/{pk}/", {"numero": 9001, "tipo": "Demo 2", "precio": 6000, "disponible": False}, nuevo)
    caso("PUT modificar", 200, c)
    c, _ = llamar(b, "PUT", "/api/habitaciones/999999/", {"numero": 9002, "tipo": "Demo", "precio": 1}, nuevo)
    caso("PUT de un id que no existe", 404, c)
    c, _ = llamar(b, "DELETE", f"/api/habitaciones/{pk}/", token=nuevo)
    caso("DELETE", 200, c)
    c, _ = llamar(b, "DELETE", f"/api/habitaciones/{pk}/", token=nuevo)
    caso("DELETE otra vez (ya no existe)", 404, c)

    print("\nLogout")
    c, _ = llamar(b, "POST", "/api/logout/", token=nuevo)
    caso("Logout", 200, c)
    c, _ = llamar(b, "GET", "/api/habitaciones/", token=nuevo)
    caso("GET con el Access revocado", 401, c)
    c, _ = llamar(b, "POST", "/api/refresh/", {"refresh_token": ref})
    caso("Refresh revocado", 401, c)

    ok = sum(resultados)
    print(f"\nResultado: {ok}/{len(resultados)} casos correctos")
    sys.exit(0 if ok == len(resultados) else 1)


if __name__ == "__main__":
    main()
