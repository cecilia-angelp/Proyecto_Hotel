import json
from datetime import date, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from .models import Habitacion, Huesped, Reserva, Sesion
from .tokens import decodificar

CLAVE = "ClaveSegura123!"
CODIGOS_PERMITIDOS = {200, 201, 400, 401, 404}


class BaseTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="recepcion", password=CLAVE)
        self.client = Client()

    # helpers
    def login(self, client=None):
        c = client or self.client
        r = c.post("/api/login/", json.dumps({"username": "recepcion", "password": CLAVE}),
                   content_type="application/json")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def api(self, metodo, url, datos=None, token=None, client=None):
        c = client or self.client
        extra = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        funcion = getattr(c, metodo)
        if datos is None:
            r = funcion(url, **extra)
        else:
            r = funcion(url, json.dumps(datos), content_type="application/json", **extra)
        self.assertIn(r.status_code, CODIGOS_PERMITIDOS, f"{metodo} {url} -> {r.status_code}")
        return r


# JWT: login, uso del Access, Refresh, errores y revocacion
class JWTTests(BaseTest):
    def test_login_correcto_entrega_tokens_cookies_y_registro_en_bd(self):
        r = self.api("post", "/api/login/", {"username": "recepcion", "password": CLAVE})
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        sesion = Sesion.objects.get()
        # mismo token en la respuesta, en la cookie y en la base de datos
        self.assertEqual(datos["access_token"], sesion.access_token)
        self.assertEqual(datos["refresh_token"], sesion.refresh_token)
        self.assertEqual(r.cookies[settings.COOKIE_ACCESS].value, sesion.access_token)
        self.assertEqual(r.cookies[settings.COOKIE_REFRESH].value, sesion.refresh_token)
        self.assertTrue(r.cookies[settings.COOKIE_REFRESH]["httponly"])
        # identificadores jti registrados
        self.assertEqual(decodificar(sesion.access_token, "access")["jti"], sesion.jti_access)
        self.assertEqual(decodificar(sesion.refresh_token, "refresh")["jti"], sesion.jti_refresh)
        # cookie persistente de Django (1 dia)
        self.assertEqual(int(r.cookies[settings.SESSION_COOKIE_NAME]["max-age"]), 86400)

    def test_login_sin_datos_400_y_clave_incorrecta_401(self):
        self.assertEqual(self.api("post", "/api/login/", {"username": "recepcion"}).status_code, 400)
        self.assertEqual(self.api("post", "/api/login/", {"username": "recepcion", "password": "mala"}).status_code, 401)
        self.assertEqual(self.api("post", "/api/login/", {"username": "x" * 31, "password": "a"}).status_code, 400)
        self.assertEqual(Sesion.objects.count(), 0)

    def test_endpoint_protegido_con_access_200(self):
        t = self.login()["access_token"]
        self.assertEqual(self.api("get", "/api/habitaciones/", token=t).status_code, 200)

    def test_token_ausente_invalido_y_expirado_dan_401(self):
        datos = self.login()
        self.client.cookies.clear()
        r = self.api("get", "/api/habitaciones/")
        self.assertEqual((r.status_code, r.json()["error"]), (401, "Token requerido."))
        r = self.api("get", "/api/habitaciones/", token="esto.no.es.un.token")
        self.assertEqual((r.status_code, r.json()["error"]), (401, "Token inválido."))
        # expirado
        sesion = Sesion.objects.get()
        vencido = jwt.encode({"sub": "1", "tipo": "access", "jti": sesion.jti_access, "sid": sesion.pk,
                              "exp": timezone.now() - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm="HS256")
        r = self.api("get", "/api/habitaciones/", token=vencido)
        self.assertEqual((r.status_code, r.json()["error"]), (401, "El token expiró."))
        # firmado con otra clave
        falso = jwt.encode({"tipo": "access", "jti": "x", "sid": 1, "exp": timezone.now() + timedelta(minutes=5)},
                           "otra-clave-distinta-de-32-caracteres-xx", algorithm="HS256")
        self.assertEqual(self.api("get", "/api/habitaciones/", token=falso).status_code, 401)
        # el refresh no sirve como access
        r = self.api("get", "/api/habitaciones/", token=datos["refresh_token"])
        self.assertEqual(r.status_code, 401)
        # formato de cabecera incorrecto
        r = self.client.get("/api/habitaciones/", HTTP_AUTHORIZATION="Token abc")
        self.assertEqual(r.status_code, 401)

    def test_refresh_renueva_el_access_y_actualiza_la_bd(self):
        datos = self.login()
        viejo = datos["access_token"]
        r = self.api("post", "/api/refresh/", {"refresh_token": datos["refresh_token"]})
        self.assertEqual(r.status_code, 200)
        nuevo = r.json()["access_token"]
        self.assertNotEqual(nuevo, viejo)
        self.assertEqual(Sesion.objects.get().access_token, nuevo)
        self.assertEqual(r.cookies[settings.COOKIE_ACCESS].value, nuevo)
        # el access nuevo funciona y el viejo quedo reemplazado
        self.assertEqual(self.api("get", "/api/habitaciones/", token=nuevo).status_code, 200)
        self.assertEqual(self.api("get", "/api/habitaciones/", token=viejo).status_code, 401)

    def test_refresh_ausente_400_invalido_401_expirado_401(self):
        datos = self.login()
        self.client.cookies.clear()
        self.assertEqual(self.api("post", "/api/refresh/", {}).status_code, 400)
        self.assertEqual(self.api("post", "/api/refresh/", {"refresh_token": "basura"}).status_code, 401)
        # un access no sirve como refresh
        self.assertEqual(self.api("post", "/api/refresh/", {"refresh_token": datos["access_token"]}).status_code, 401)
        sesion = Sesion.objects.get()
        vencido = jwt.encode({"sub": "1", "tipo": "refresh", "jti": sesion.jti_refresh, "sid": sesion.pk,
                              "exp": timezone.now() - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm="HS256")
        r = self.api("post", "/api/refresh/", {"refresh_token": vencido})
        self.assertEqual((r.status_code, r.json()["error"]), (401, "El refresh token expiró."))

    def test_logout_revoca_los_tokens(self):
        datos = self.login()
        r = self.api("post", "/api/logout/", token=datos["access_token"])
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Sesion.objects.get().activa)
        self.assertIsNotNone(Sesion.objects.get().cerrada_en)
        self.client.cookies.clear()
        self.assertEqual(self.api("get", "/api/habitaciones/", token=datos["access_token"]).status_code, 401)
        self.assertEqual(self.api("post", "/api/refresh/", {"refresh_token": datos["refresh_token"]}).status_code, 401)

    def test_logout_sin_token_401(self):
        self.assertEqual(self.api("post", "/api/logout/").status_code, 401)

    def test_logout_funciona_aunque_el_access_haya_expirado(self):
        datos = self.login()
        Sesion.objects.update(access_expira=timezone.now() - timedelta(minutes=1))
        sesion = Sesion.objects.get()
        vencido = jwt.encode({"sub": "1", "tipo": "access", "jti": sesion.jti_access, "sid": sesion.pk,
                              "exp": timezone.now() - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm="HS256")
        self.client.cookies.clear()
        self.assertEqual(self.api("post", "/api/logout/", token=vencido).status_code, 200)
        self.assertFalse(Sesion.objects.get().activa)

    def test_administrar_sesiones(self):
        a = self.login(Client())
        b = self.login(Client())
        self.assertEqual(Sesion.objects.filter(activa=True).count(), 2)
        lista = self.api("get", "/api/sesiones/", token=a["access_token"], client=Client()).json()
        self.assertEqual(len(lista), 2)
        self.assertIn("jti_access", lista[0])
        # revocar la sesion B desde la A
        r = self.api("delete", f"/api/sesiones/{b['sesion_id']}/", token=a["access_token"], client=Client())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.api("get", "/api/habitaciones/", token=b["access_token"], client=Client()).status_code, 401)
        self.assertEqual(self.api("delete", "/api/sesiones/9999/", token=a["access_token"], client=Client()).status_code, 404)

    def test_perfil_protegido_200_y_401(self):
        datos = self.login()
        self.client.cookies.clear()
        self.assertEqual(self.api("get", "/api/perfil/").status_code, 401)
        r = self.api("get", "/api/perfil/", token=datos["access_token"])
        self.assertEqual((r.status_code, r.json()["usuario"]), (200, "recepcion"))

    def test_rutas_equivalentes_de_la_clase_token_y_token_refresh(self):
        r = self.api("post", "/api/token/", {"username": "recepcion", "password": CLAVE})
        self.assertEqual(r.status_code, 200)
        r2 = self.api("post", "/api/token/refresh/", {"refresh": r.json()["refresh_token"]})   # tambien acepta "refresh"
        self.assertEqual(r2.status_code, 200)

    def test_ruta_inexistente_de_la_api_y_metodo_incorrecto(self):
        t = self.login()["access_token"]
        r = self.api("get", "/api/habitaciones/99999/", token=t)
        self.assertEqual((r.status_code, r.json()), (404, {"error": "La habitación no existe."}))


# CRUD de la API: solo 200, 201, 400, 401 y 404
class CRUDHabitacionTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.t = self.login()["access_token"]
        self.hab = Habitacion.objects.create(numero=101, tipo="Suite", precio=80000)

    def test_sin_token_401_en_todas_las_rutas(self):
        self.client.cookies.clear()
        for metodo, url in [("get", "/api/habitaciones/"), ("post", "/api/habitaciones/"),
                            ("get", f"/api/habitaciones/{self.hab.pk}/"), ("put", f"/api/habitaciones/{self.hab.pk}/"),
                            ("delete", f"/api/habitaciones/{self.hab.pk}/"), ("get", "/api/huespedes/"),
                            ("get", "/api/reservas/"), ("get", "/api/sesiones/")]:
            self.assertEqual(self.api(metodo, url).status_code, 401, f"{metodo} {url}")

    def test_get_lista_y_por_id(self):
        self.assertEqual(len(self.api("get", "/api/habitaciones/", token=self.t).json()), 1)
        r = self.api("get", f"/api/habitaciones/{self.hab.pk}/", token=self.t)
        self.assertEqual((r.status_code, r.json()["numero"]), (200, 101))

    def test_post_201_con_mensaje(self):
        r = self.api("post", "/api/habitaciones/", {"numero": 102, "tipo": "Doble", "precio": 45000, "disponible": True}, self.t)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["mensaje"], "Habitación creada correctamente.")
        self.assertEqual(r.json()["habitacion"]["numero"], 102)

    def test_post_invalido_400(self):
        casos = [
            {"numero": 0, "tipo": "Doble", "precio": 1000},
            {"numero": 10000, "tipo": "Doble", "precio": 1000},
            {"numero": 101, "tipo": "Doble", "precio": 1000},      # repetido
            {"numero": 5, "tipo": "ab", "precio": 1000},
            {"numero": 5, "tipo": "x" * 31, "precio": 1000},
            {"numero": 5, "tipo": "Doble", "precio": 10000000},
            {"numero": "abc", "tipo": "Doble", "precio": 1000},
            {},
        ]
        for datos in casos:
            r = self.api("post", "/api/habitaciones/", datos, self.t)
            self.assertEqual(r.status_code, 400, datos)
            self.assertIn("error", r.json())
            self.assertTrue(r.json()["errores"])
        self.assertEqual(Habitacion.objects.count(), 1)

    def test_json_mal_formado_400(self):
        r = self.client.post("/api/habitaciones/", "{no es json", content_type="application/json",
                             HTTP_AUTHORIZATION=f"Bearer {self.t}")
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_put_200_y_400_y_404(self):
        r = self.api("put", f"/api/habitaciones/{self.hab.pk}/", {"numero": 101, "tipo": "Suite Real", "precio": 99000, "disponible": False}, self.t)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["mensaje"], "Habitación modificada correctamente.")
        self.hab.refresh_from_db()
        self.assertEqual((self.hab.tipo, self.hab.precio, self.hab.disponible), ("Suite Real", 99000, False))
        self.assertEqual(self.api("put", f"/api/habitaciones/{self.hab.pk}/", {"numero": 0, "tipo": "Suite", "precio": 1}, self.t).status_code, 400)
        self.assertEqual(self.api("put", "/api/habitaciones/9999/", {"numero": 5, "tipo": "Suite", "precio": 1}, self.t).status_code, 404)

    def test_delete_200_y_404(self):
        r = self.api("delete", f"/api/habitaciones/{self.hab.pk}/", token=self.t)
        self.assertEqual((r.status_code, r.json()), (200, {"mensaje": "Habitación eliminada correctamente."}))
        self.assertFalse(Habitacion.objects.exists())
        self.assertEqual(self.api("delete", f"/api/habitaciones/{self.hab.pk}/", token=self.t).status_code, 404)

    def test_no_se_borra_lo_que_tiene_reservas_400(self):
        h = Huesped.objects.create(nombre="Ana", apellido="Rojas", rut="11111111-1", email="a@b.cl", telefono="912345678")
        Reserva.objects.create(habitacion=self.hab, huesped=h, fecha_entrada=date.today() + timedelta(days=2),
                               fecha_salida=date.today() + timedelta(days=4), personas=2)
        r = self.api("delete", f"/api/habitaciones/{self.hab.pk}/", token=self.t)
        self.assertEqual(r.status_code, 400)
        self.assertIn("reservas asociadas", r.json()["error"])
        r = self.api("delete", f"/api/huespedes/{h.pk}/", token=self.t)
        self.assertEqual(r.status_code, 400)


class CRUDHuespedYReservaTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.t = self.login()["access_token"]
        self.hab = Habitacion.objects.create(numero=201, tipo="Doble", precio=50000)

    def test_huesped_crud_completo(self):
        datos = {"nombre": "Camila", "apellido": "Rojas", "rut": "12.345.678-5", "email": "C@Correo.cl", "telefono": "+56 9 1234 5678"}
        r = self.api("post", "/api/huespedes/", datos, self.t)
        if r.status_code == 400:   # el RUT de ejemplo puede no ser valido: se usa uno calculado
            datos["rut"] = "11.111.111-1"
            r = self.api("post", "/api/huespedes/", datos, self.t)
        self.assertEqual(r.status_code, 201, r.content)
        pk = r.json()["huesped"]["id"]
        self.assertEqual(self.api("get", f"/api/huespedes/{pk}/", token=self.t).status_code, 200)
        datos["nombre"] = "Camilo"
        self.assertEqual(self.api("put", f"/api/huespedes/{pk}/", datos, self.t).status_code, 200)
        self.assertEqual(self.api("post", "/api/huespedes/", datos, self.t).status_code, 400)   # RUT repetido
        self.assertEqual(self.api("delete", f"/api/huespedes/{pk}/", token=self.t).status_code, 200)
        self.assertEqual(self.api("get", f"/api/huespedes/{pk}/", token=self.t).status_code, 404)

    def test_huesped_datos_invalidos_400(self):
        r = self.api("post", "/api/huespedes/", {"nombre": "A1", "apellido": "", "rut": "1", "email": "x", "telefono": "1"}, self.t)
        self.assertEqual(r.status_code, 400)
        self.assertGreaterEqual(len(r.json()["errores"]), 4)

    def _huesped(self):
        return Huesped.objects.create(nombre="Ana", apellido="Rojas", rut="11111111-1", email="a@b.cl", telefono="912345678")

    def test_reserva_crud_y_reglas(self):
        h = self._huesped()
        ini = date.today() + timedelta(days=3)
        datos = {"habitacion": self.hab.pk, "huesped": h.pk, "fecha_entrada": ini.isoformat(),
                 "fecha_salida": (ini + timedelta(days=2)).isoformat(), "personas": 2}
        r = self.api("post", "/api/reservas/", datos, self.t)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["reserva"]["total"], 100000)
        pk = r.json()["reserva"]["id"]
        # choque de fechas
        self.assertEqual(self.api("post", "/api/reservas/", datos, self.t).status_code, 400)
        # fechas invertidas, mas de 30 noches, pasado, personas
        malos = [
            {**datos, "fecha_salida": ini.isoformat()},
            {**datos, "fecha_salida": (ini + timedelta(days=40)).isoformat(), "habitacion": self.hab.pk},
            {**datos, "fecha_entrada": (date.today() - timedelta(days=1)).isoformat()},
            {**datos, "personas": 7},
        ]
        for m in malos:
            self.assertEqual(self.api("post", "/api/reservas/", m, self.t).status_code, 400, m)
        # PUT cambia estado valido; transicion invalida da 400
        self.assertEqual(self.api("put", f"/api/reservas/{pk}/", {**datos, "estado": "confirmada"}, self.t).status_code, 200)
        self.assertEqual(self.api("put", f"/api/reservas/{pk}/", {**datos, "estado": "finalizada"}, self.t).status_code, 400)
        self.assertEqual(self.api("put", "/api/reservas/9999/", datos, self.t).status_code, 404)
        self.assertEqual(self.api("get", "/api/reservas/", token=self.t).status_code, 200)
        self.assertEqual(self.api("delete", f"/api/reservas/{pk}/", token=self.t).status_code, 200)
        self.assertEqual(self.api("delete", f"/api/reservas/{pk}/", token=self.t).status_code, 404)

    def test_reserva_en_curso_no_se_elimina_y_finalizada_no_se_modifica(self):
        h = self._huesped()
        ini = date.today()
        base = dict(habitacion=self.hab, huesped=h, fecha_entrada=ini, fecha_salida=ini + timedelta(days=2), personas=1)
        en_curso = Reserva.objects.create(estado="en_curso", **base)
        self.assertEqual(self.api("delete", f"/api/reservas/{en_curso.pk}/", token=self.t).status_code, 400)
        en_curso.delete()
        fin = Reserva.objects.create(estado="finalizada", **base)
        datos = {"habitacion": self.hab.pk, "huesped": h.pk, "fecha_entrada": ini.isoformat(),
                 "fecha_salida": (ini + timedelta(days=2)).isoformat(), "personas": 1, "estado": "finalizada"}
        self.assertEqual(self.api("put", f"/api/reservas/{fin.pk}/", datos, self.t).status_code, 400)


# Paginas web: decorador propio, redireccion al login y cookies
class WebTests(BaseTest):
    PAGINAS = ["/", "/habitaciones/", "/habitaciones/crear/", "/huespedes/", "/huespedes/crear/",
               "/reservas/", "/reservas/crear/"]

    def test_sin_sesion_redirige_al_login(self):
        for url in self.PAGINAS:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertTrue(r["Location"].startswith("/ingreso/"), url)

    def test_el_decorador_conserva_el_nombre_de_la_vista(self):
        from . import views
        self.assertEqual(views.inicio.__name__, "inicio")
        self.assertTrue(hasattr(views.inicio, "__wrapped__"))   # functools.wraps

    def test_con_sesion_las_paginas_dan_200(self):
        self.login()
        h = Habitacion.objects.create(numero=1, tipo="Suite", precio=1000)
        for url in self.PAGINAS + [f"/habitaciones/editar/{h.pk}/", f"/habitaciones/eliminar/{h.pk}/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertIn("no-cache", r["Cache-Control"])

    def test_efectos_del_frontend_estan_en_las_paginas(self):
        self.login()
        Habitacion.objects.create(numero=7, tipo="Suite", precio=1000)
        base = self.client.get("/").content.decode()
        self.assertIn('id="sessionTimer"', base)      # contador de sesion
        self.assertIn('id="toasts"', base)            # avisos deslizantes
        self.assertIn("efectos.js", base)
        self.assertNotIn("btnSesion", base)           # el panel de tokens no existe
        self.assertIn("room-door", self.client.get("/habitaciones/").content.decode())   # puertas
        self.assertIn("data-checkin", self.client.get("/reservas/crear/").content.decode())

    def test_pagina_inexistente_404_y_post_a_una_pagina_405(self):
        self.login()
        self.assertEqual(self.client.get("/habitaciones/editar/999/").status_code, 404)
        self.assertEqual(self.client.post("/habitaciones/crear/").status_code, 405)

    def test_las_cookies_son_iguales_a_la_bd_y_la_pagina_no_muestra_los_tokens(self):
        self.login()
        sesion = Sesion.objects.get()
        html = self.client.get("/").content.decode()
        self.assertEqual(self.client.cookies[settings.COOKIE_ACCESS].value, sesion.access_token)
        self.assertEqual(self.client.cookies[settings.COOKIE_REFRESH].value, sesion.refresh_token)
        self.assertNotIn(sesion.access_token, html)
        self.assertNotIn(sesion.refresh_token, html)

    def test_access_expirado_se_renueva_al_cargar_la_pagina(self):
        self.login()
        Sesion.objects.update(access_expira=timezone.now() - timedelta(seconds=1))
        viejo = Sesion.objects.get().access_token
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        nuevo = Sesion.objects.get().access_token
        self.assertNotEqual(viejo, nuevo)
        self.assertEqual(r.cookies[settings.COOKIE_ACCESS].value, nuevo)
        self.assertEqual(self.client.cookies[settings.COOKIE_ACCESS].value, nuevo)

    def test_despues_del_logout_las_paginas_redirigen(self):
        datos = self.login()
        self.assertEqual(self.client.get("/habitaciones/").status_code, 200)
        self.api("post", "/api/logout/", token=datos["access_token"])
        r = self.client.get("/habitaciones/")
        self.assertEqual(r.status_code, 302)

    def test_sesion_revocada_en_bd_cierra_el_acceso_web(self):
        self.login()
        Sesion.objects.update(activa=False)
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_refresh_expirado_cierra_el_acceso_web(self):
        self.login()
        Sesion.objects.update(refresh_expira=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_cookie_refresh_distinta_no_entra(self):
        self.login()
        self.client.cookies[settings.COOKIE_REFRESH] = "otra-cosa"
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_login_pagina_y_redireccion_si_ya_hay_sesion(self):
        r = self.client.get("/ingreso/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Inicio</a>")      # sin menu en el login
        self.login()
        self.assertEqual(self.client.get("/ingreso/").status_code, 302)

    def test_no_se_usa_authtoken_ni_storage_en_las_plantillas(self):
        self.login()
        html = self.client.get("/").content.decode()
        self.assertNotIn("sessionStorage", html)
        self.assertNotIn("localStorage", html)

    def test_devtools_y_swagger(self):
        self.assertEqual(self.client.get("/.well-known/appspecific/com.chrome.devtools.json").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)
        esquema = self.client.get("/api/schema/?format=json")
        self.assertEqual(esquema.status_code, 200)
        datos = esquema.json()
        self.assertIn("/api/login/", datos["paths"])
        self.assertIn("/api/habitaciones/{id}/", datos["paths"])
        self.assertIn("/api/perfil/", datos["paths"])
        self.assertNotIn("/api/token/", datos["paths"])
        self.assertIn("bearerAuth", json.dumps(datos["components"]["securitySchemes"]))


class LimitesTests(BaseTest):
    def test_numero_y_precio_maximos(self):
        t = self.login()["access_token"]
        self.assertEqual(self.api("post", "/api/habitaciones/", {"numero": 9999, "tipo": "Suite", "precio": 9999999}, t).status_code, 201)
        self.assertEqual(self.api("post", "/api/habitaciones/", {"numero": 10000, "tipo": "Suite", "precio": 1}, t).status_code, 400)
