from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])
def api_habitaciones(request): 
    return Response({"estado": "ok"})

@api_view(['GET', 'PUT', 'DELETE'])
def api_habitacion_detalle(request, pk): 
    return Response({"estado": "ok"})