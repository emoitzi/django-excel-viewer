from rest_framework import serializers

from frontend.models import ChangeRequest


class ChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        fields = ('new_value', 'target_cell')


class ChangeRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        fields = ('new_value', 'target_cell')
