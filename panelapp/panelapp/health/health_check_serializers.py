from rest_framework import serializers

from panelapp.health.enums import STATUS_ORDER

# STATUS_CHOICES is a list as DRF can't pickle generators
STATUS_CHOICES = list((status.value, status.value) for status in STATUS_ORDER)


class DependencySerializer(serializers.Serializer):
    type = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    url = serializers.ListField(child=serializers.CharField())
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    additionalProperties = serializers.DictField(required=False)

    class Meta:
        fields = ("type", "description", "url", "status", "additionalProperties")

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DepencenciesSerializer(serializers.Serializer):
    datastores = DependencySerializer(many=True, default=[])
    apis = DependencySerializer(many=True, default=[])

    class Meta:
        fields = ("datastores", "apis")

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class HealthCheckSerializer(serializers.Serializer):
    serviceName = serializers.CharField(required=False)
    requestUrl = serializers.CharField(required=False)
    datetime = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ%Z")
    components = serializers.ListField(child=serializers.CharField(), required=False)
    unavailableComponents = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    dependencies = DepencenciesSerializer(required=False)

    class Meta:
        fields = (
            "serviceName",
            "requestUrl",
            "status",
            "dependencies",
            "components",
            "unavailableComponents",
        )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
