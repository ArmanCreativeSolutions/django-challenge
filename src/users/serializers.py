import re
from rest_framework import serializers
from users.models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'password', 'confirm_password']

    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "User with this phone number already exists."
            )

        if not re.match(r'^09\d{9}$', value):
            raise serializers.ValidationError(
                "Phone number must start with '09', be 11 digits long."
            )
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['phone_number'],
            phone_number=validated_data['phone_number']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
