from rest_framework import serializers


class VisitorSerializer(serializers.Serializer):
    """Validação dos dados de cada visitante."""

    name = serializers.CharField(max_length=100)
    # Garante que a data venha no formato YYYY-MM-DD
    birthDate = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])


class BuyerSerializer(serializers.Serializer):
    """Validação dos dados do comprador/pagador."""

    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100)
    address = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    # State pode ser opcional dependendo do país, allow_blank evita erros
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    zipCode = serializers.CharField(max_length=20)


class VoucherStatueLibertySerializer(serializers.Serializer):
    """Serializer principal da Ordem de Serviço."""

    orderId = serializers.CharField(max_length=50)
    ticketType = serializers.CharField(max_length=100)
    # Garante que a data da viagem seja válida
    travelDate = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    departureLocation = serializers.CharField(max_length=100)
    timeSlot = serializers.CharField(max_length=50)

    # Nested Serializers (Listas e Objetos aninhados)
    visitors = VisitorSerializer(many=True)
    buyer = BuyerSerializer()
