from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Habitacion


# API Habitaciones
class HabitacionAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="prueba", password="ClaveSegura123!")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.room = Habitacion.objects.create(numero=101, tipo="Suite", precio=80000)

    def test_api_requiere_token(self):
        self.client.credentials()
        response = self.client.get("/api/habitaciones/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_habitaciones(self):
        response = self.client.get("/api/habitaciones/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_consultar_por_id(self):
        response = self.client.get(f"/api/habitaciones/{self.room.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["numero"], 101)

    def test_crear_habitacion(self):
        response = self.client.post("/api/habitaciones/", {
            "numero": 102, "tipo": "Doble", "precio": 45000, "disponible": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Habitacion.objects.filter(numero=102).exists())

    def test_rechaza_datos_invalidos(self):
        response = self.client.post("/api/habitaciones/", {
            "numero": -1, "tipo": "A", "precio": 0, "disponible": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actualizar_habitacion(self):
        response = self.client.put(f"/api/habitaciones/{self.room.pk}/", {
            "numero": 101, "tipo": "Presidencial", "precio": 120000, "disponible": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.tipo, "Presidencial")

    def test_eliminar_habitacion(self):
        response = self.client.delete(f"/api/habitaciones/{self.room.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habitacion.objects.filter(pk=self.room.pk).exists())

    def test_registro_inexistente(self):
        response = self.client.get("/api/habitaciones/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_login_entrega_token(self):
        self.client.credentials()
        response = self.client.post("/api/token/", {
            "username": "prueba", "password": "ClaveSegura123!"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_token_invalido_da_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token tokenfalso123")
        response = self.client.get("/api/habitaciones/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_con_clave_incorrecta_da_401(self):
        self.client.credentials()
        response = self.client.post("/api/token/", {
            "username": "prueba", "password": "claveMala"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("token", response.data)

    def test_login_sin_datos_da_400(self):
        self.client.credentials()
        response = self.client.post("/api/token/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_numero_duplicado_da_400(self):
        response = self.client.post("/api/habitaciones/", {
            "numero": 101, "tipo": "Doble", "precio": 45000, "disponible": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Habitacion.objects.filter(numero=101).count(), 1)

    def test_actualizar_y_eliminar_inexistente_da_404(self):
        datos = {"numero": 500, "tipo": "Suite", "precio": 1000, "disponible": True}
        self.assertEqual(
            self.client.put("/api/habitaciones/99999/", datos, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete("/api/habitaciones/99999/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_numero_sobre_el_limite_da_400(self):
        response = self.client.post("/api/habitaciones/", {
            "numero": 10000, "tipo": "Doble", "precio": 45000, "disponible": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tipo_sobre_30_caracteres_da_400(self):
        response = self.client.post("/api/habitaciones/", {
            "numero": 150, "tipo": "x" * 31, "precio": 45000, "disponible": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_api_con_texto_demasiado_largo_da_400(self):
        self.client.credentials()
        response = self.client.post("/api/token/", {
            "username": "a" * 31, "password": "ClaveSegura123!"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalida_el_token(self):
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get("/api/habitaciones/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# Web Habitaciones
class HabitacionWebTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="recepcion", password="ClaveSegura123!")
        self.room = Habitacion.objects.create(numero=201, tipo="Suite", precio=90000)

    def entrar(self):
        self.client.login(username="recepcion", password="ClaveSegura123!")

    def test_paginas_privadas_redirigen_al_login(self):
        for url in ["/", "/habitaciones/", "/habitaciones/crear/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response["Location"].startswith("/ingreso/"))

    def test_login_correcto_entra_al_inicio(self):
        response = self.client.post("/ingreso/", {"username": "recepcion", "password": "ClaveSegura123!"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_login_incorrecto_no_entra(self):
        response = self.client.post("/ingreso/", {"username": "recepcion", "password": "mala"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_crear_habitacion_valida(self):
        self.entrar()
        response = self.client.post("/habitaciones/crear/", {
            "numero": "202", "tipo": "Doble", "precio": "50000", "disponible": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Habitacion.objects.filter(numero=202, tipo="Doble").exists())

    def test_crear_con_datos_invalidos_no_guarda(self):
        self.entrar()
        invalidos = [
            {"numero": "", "tipo": "Doble", "precio": "50000"},
            {"numero": "abc", "tipo": "Doble", "precio": "50000"},
            {"numero": "-5", "tipo": "Doble", "precio": "50000"},
            {"numero": "300", "tipo": "A", "precio": "50000"},
            {"numero": "300", "tipo": "Doble", "precio": "0"},
            {"numero": "300", "tipo": "Doble", "precio": "x"},
            {"numero": "201", "tipo": "Doble", "precio": "50000"},
            {"numero": "10000", "tipo": "Doble", "precio": "50000"},
            {"numero": "300", "tipo": "x" * 31, "precio": "50000"},
            {"numero": "300", "tipo": "Doble", "precio": "10000000"},
        ]
        for datos in invalidos:
            response = self.client.post("/habitaciones/crear/", datos)
            self.assertEqual(response.status_code, 200, datos)
            self.assertTrue(response.context["errores"], datos)
        self.assertEqual(Habitacion.objects.count(), 1)

    def test_editar_habitacion(self):
        self.entrar()
        response = self.client.post(f"/habitaciones/editar/{self.room.pk}/", {
            "numero": "201", "tipo": "Presidencial", "precio": "150000",
        })
        self.assertEqual(response.status_code, 302)
        self.room.refresh_from_db()
        self.assertEqual(self.room.tipo, "Presidencial")
        self.assertFalse(self.room.disponible)

    def test_eliminar_habitacion(self):
        self.entrar()
        response = self.client.post(f"/habitaciones/eliminar/{self.room.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Habitacion.objects.filter(pk=self.room.pk).exists())

    def test_login_rechaza_usuario_o_clave_demasiado_largos(self):
        response = self.client.post("/ingreso/", {"username": "a" * 31, "password": "ClaveSegura123!"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        response = self.client.post("/ingreso/", {"username": "recepcion", "password": "x" * 31})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_despues_de_salir_no_se_puede_editar_ni_eliminar(self):
        self.entrar()
        self.client.post("/salir/")
        for url in [f"/habitaciones/editar/{self.room.pk}/", f"/habitaciones/eliminar/{self.room.pk}/", "/habitaciones/"]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response["Location"].startswith("/ingreso/"))
        response = self.client.post(f"/habitaciones/eliminar/{self.room.pk}/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Habitacion.objects.filter(pk=self.room.pk).exists())

    def test_paginas_privadas_no_se_guardan_en_cache(self):
        self.entrar()
        response = self.client.get("/habitaciones/")
        self.assertIn("no-store", response["Cache-Control"])


from datetime import date, timedelta

from .models import Huesped, Reserva


def _fechas(dias_entrada=5, noches=3):
    entrada = date.today() + timedelta(days=dias_entrada)
    return entrada, entrada + timedelta(days=noches)


# API Huespedes
class HuespedAPITests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="prueba", password="ClaveSegura123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
        self.datos = {"nombre": "Camila", "apellido": "Rojas", "rut": "12.159.159-8",
                      "email": "Camila@Correo.cl", "telefono": "+56 9 1234 5678"}

    def test_requiere_token(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/huespedes/").status_code, 401)

    def test_crear_acepta_rut_inventado_y_normaliza(self):
        r = self.client.post("/api/huespedes/", self.datos, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["rut"], "12159159-8")
        self.assertEqual(r.data["email"], "camila@correo.cl")
        self.assertEqual(r.data["telefono"], "+56912345678")

    def test_rechaza_datos_invalidos(self):
        for campo, malo in [("nombre", "Cami1a"), ("apellido", "R"), ("rut", "123"), ("rut", "abcdefgh-1"),
                            ("email", "no-es-correo"), ("telefono", "12ab"), ("nombre", "A" * 41)]:
            datos = dict(self.datos, **{campo: malo})
            r = self.client.post("/api/huespedes/", datos, format="json")
            self.assertEqual(r.status_code, 400, (campo, malo))
        self.assertEqual(Huesped.objects.count(), 0)

    def test_rut_repetido(self):
        self.client.post("/api/huespedes/", self.datos, format="json")
        r = self.client.post("/api/huespedes/", dict(self.datos, rut="12159159-8"), format="json")
        self.assertEqual(r.status_code, 400)

    def test_get_put_delete_y_404(self):
        pk = self.client.post("/api/huespedes/", self.datos, format="json").data["id"]
        self.assertEqual(self.client.get(f"/api/huespedes/{pk}/").status_code, 200)
        r = self.client.put(f"/api/huespedes/{pk}/", dict(self.datos, nombre="Camilo"), format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["nombre"], "Camilo")
        self.assertEqual(self.client.delete(f"/api/huespedes/{pk}/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/huespedes/{pk}/").status_code, 404)


# API Reservas
class ReservaAPITests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="prueba", password="ClaveSegura123!")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
        self.hab = Habitacion.objects.create(numero=101, tipo="Suite", precio=50000)
        self.hab_off = Habitacion.objects.create(numero=102, tipo="Doble", precio=30000, disponible=False)
        self.huesped = Huesped.objects.create(nombre="Camila", apellido="Rojas", rut="12159159-8",
                                              email="c@c.cl", telefono="912345678")

    def _datos(self, **extra):
        e, s = _fechas()
        base = {"habitacion": self.hab.pk, "huesped": self.huesped.pk, "fecha_entrada": e.isoformat(),
                "fecha_salida": s.isoformat(), "personas": 2, "observaciones": ""}
        base.update(extra)
        return base

    def test_crear_calcula_total(self):
        r = self.client.post("/api/reservas/", self._datos(), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["noches"], 3)
        self.assertEqual(r.data["total"], 150000)
        self.assertEqual(r.data["estado"], "pendiente")

    def test_requiere_token(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/reservas/").status_code, 401)

    def test_reglas_de_fechas_y_datos(self):
        e, s = _fechas()
        casos = [
            self._datos(fecha_salida=e.isoformat()),
            self._datos(fecha_salida=(e - timedelta(days=1)).isoformat()),
            self._datos(fecha_entrada=(date.today() - timedelta(days=1)).isoformat()),
            self._datos(fecha_salida=(e + timedelta(days=31)).isoformat()),
            self._datos(personas=0), self._datos(personas=7), self._datos(personas="x"),
            self._datos(habitacion=9999), self._datos(huesped=9999),
            self._datos(habitacion=self.hab_off.pk),
            self._datos(observaciones="x" * 201),
            self._datos(fecha_entrada="31-12-2026"),
            self._datos(estado="confirmada"),
        ]
        for datos in casos:
            self.assertEqual(self.client.post("/api/reservas/", datos, format="json").status_code, 400, datos)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_no_permite_choque_de_fechas(self):
        self.assertEqual(self.client.post("/api/reservas/", self._datos(), format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/reservas/", self._datos(), format="json").status_code, 400)
        e, s = _fechas()
        r = self.client.post("/api/reservas/", self._datos(fecha_entrada=s.isoformat(),
                             fecha_salida=(s + timedelta(days=2)).isoformat()), format="json")
        self.assertEqual(r.status_code, 201)

    def test_estados_validos_e_invalidos(self):
        pk = self.client.post("/api/reservas/", self._datos(), format="json").data["id"]
        self.assertEqual(self.client.put(f"/api/reservas/{pk}/", self._datos(estado="finalizada"), format="json").status_code, 400)
        self.assertEqual(self.client.put(f"/api/reservas/{pk}/", self._datos(estado="confirmada"), format="json").status_code, 200)
        self.assertEqual(self.client.put(f"/api/reservas/{pk}/", self._datos(estado="en_curso"), format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/reservas/{pk}/").status_code, 409)
        self.assertEqual(self.client.put(f"/api/reservas/{pk}/", self._datos(estado="finalizada"), format="json").status_code, 200)
        self.assertEqual(self.client.put(f"/api/reservas/{pk}/", self._datos(estado="confirmada"), format="json").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/reservas/{pk}/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/reservas/{pk}/").status_code, 404)

    def test_no_se_borra_habitacion_ni_huesped_con_reservas(self):
        self.client.post("/api/reservas/", self._datos(), format="json")
        self.assertEqual(self.client.delete(f"/api/habitaciones/{self.hab.pk}/").status_code, 409)
        self.assertEqual(self.client.delete(f"/api/huespedes/{self.huesped.pk}/").status_code, 409)
        self.assertTrue(Habitacion.objects.filter(pk=self.hab.pk).exists())


# Limites y login
class LimitesYLoginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="prueba", password="ClaveSegura123!")

    def test_mensaje_de_login_no_menciona_limite(self):
        r = self.client.post("/ingreso/", {"username": "prueba", "password": "mala"})
        self.assertContains(r, "Usuario o contraseña incorrectos")
        self.assertNotContains(r, "30 caracteres")

    def test_login_no_muestra_menu_ni_con_sesion_iniciada(self):
        r = self.client.get("/ingreso/")
        self.assertNotContains(r, "nav-exit")
        self.client.force_login(self.user)
        r = self.client.get("/ingreso/")
        self.assertRedirects(r, "/", fetch_redirect_response=False)

    def test_rutas_protegidas_sin_sesion(self):
        for url in ["/", "/habitaciones/", "/huespedes/", "/reservas/", "/huespedes/crear/", "/reservas/crear/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/ingreso/", r["Location"])

    def test_numero_habitacion_max_9999_y_precio_max(self):
        self.client.force_login(self.user)
        for datos in [{"numero": "10000", "tipo": "Suite", "precio": "100"},
                      {"numero": "5", "tipo": "Suite", "precio": "10000000"},
                      {"numero": "5", "tipo": "S#!", "precio": "100"},
                      {"numero": "5", "tipo": "Su", "precio": "100"}]:
            self.client.post("/habitaciones/crear/", datos)
        self.assertEqual(Habitacion.objects.count(), 0)
        self.client.post("/habitaciones/crear/", {"numero": "9999", "tipo": "Suite 2", "precio": "9999999"})
        self.assertEqual(Habitacion.objects.count(), 1)

    def test_formularios_web_huesped_y_reserva(self):
        self.client.force_login(self.user)
        malo = {"nombre": "Ana1", "apellido": "R", "rut": "1", "email": "x", "telefono": "1"}
        self.client.post("/huespedes/crear/", malo)
        self.assertEqual(Huesped.objects.count(), 0)
        bueno = {"nombre": "Ana María", "apellido": "Pérez-Rojas", "rut": "12.159.159-8",
                 "email": "ana@correo.cl", "telefono": "912345678"}
        r = self.client.post("/huespedes/crear/", bueno)
        self.assertEqual(r.status_code, 302)
        h = Huesped.objects.get()
        hab = Habitacion.objects.create(numero=7, tipo="Suite", precio=1000)
        e, s = _fechas()
        r = self.client.post("/reservas/crear/", {"habitacion": hab.pk, "huesped": h.pk, "fecha_entrada": e,
                                                  "fecha_salida": s, "personas": "2", "observaciones": ""})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Reserva.objects.get().total, 3000)
        r = self.client.post("/reservas/crear/", {"habitacion": hab.pk, "huesped": h.pk, "fecha_entrada": e,
                                                  "fecha_salida": s, "personas": "2"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ya está reservada")
        self.assertEqual(Reserva.objects.count(), 1)
        r = self.client.post(f"/habitaciones/eliminar/{hab.pk}/", follow=True)
        self.assertContains(r, "tiene reservas asociadas")
        self.assertTrue(Habitacion.objects.filter(pk=hab.pk).exists())
        for url in ["/huespedes/", "/reservas/", "/huespedes/crear/", "/reservas/crear/",
                    f"/huespedes/editar/{h.pk}/", f"/reservas/editar/{Reserva.objects.get().pk}/",
                    f"/reservas/eliminar/{Reserva.objects.get().pk}/", f"/huespedes/eliminar/{h.pk}/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
