from rest_framework import serializers
from vendorapi.models import DeliveryPartnerForm , SetOrderIncentive





class DeliveryPartnerSerializer(serializers.ModelSerializer):
    """
    Serializer for DeliveryPartnerForm.
    JSONField document fields are normalised to their first URL so the
    frontend can render a single <img> without extra logic.
    """

    profile_image         = serializers.SerializerMethodField()
    aadhar_card           = serializers.SerializerMethodField()
    driving_license       = serializers.SerializerMethodField()
    vehicle_rc_certificate = serializers.SerializerMethodField()
    vehicle_image         = serializers.SerializerMethodField()

    latitude  = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model  = DeliveryPartnerForm
        fields = [
            # Identity
            "id",
            "deliver_partnerid",

            # Personal
            "full_name",
            "email",
            "phone_number",
            "city",
            "address",
            "referral_code",
            "work_status",
            "approval_status",

            # Vehicle
            "vehicle_type",
            "vehicle_number",
            "vehicle_model",
            "vehicle_color",
            "manufacturing_year",

            # Bank
            "account_holder_name",
            "account_number",
            "bank_name",
            "branch_name",
            "ifsc_code",

            # Documents  (normalised to first URL via SerializerMethodField)
            "profile_image",
            "aadhar_card",
            "driving_license",
            "vehicle_rc_certificate",
            "vehicle_image",

            # Location
            "latitude",
            "longitude",

            # Meta
            "created_at",
        ]
        read_only_fields = fields   # this serializer is for output only

    # ── Document helpers ──────────────────────────────────────────────────
    @staticmethod
    def _first_url(value):
        """
        JSONField may be stored as:
          - a list of URL strings  → return first element
          - a single URL string    → return as-is
          - None / empty           → return None
        """
        if not value:
            return None
        if isinstance(value, list):
            return value[0] if value else None
        return str(value)

    def get_profile_image(self, obj):
        return self._first_url(obj.profile_image)

    def get_aadhar_card(self, obj):
        return self._first_url(obj.aadhar_card)

    def get_driving_license(self, obj):
        return self._first_url(obj.driving_license)

    def get_vehicle_rc_certificate(self, obj):
        return self._first_url(obj.vehicle_rc_certificate)

    def get_vehicle_image(self, obj):
        return self._first_url(obj.vehicle_image)

    # ── Decimal → float so JSON doesn't get Decimal objects ──────────────
    def get_latitude(self, obj):
        return float(obj.latitude) if obj.latitude is not None else None

    def get_longitude(self, obj):
        return float(obj.longitude) if obj.longitude is not None else None



class  IncentiveSerializer(serializers.ModelSerializer):

    class Meta:
        model = SetOrderIncentive
        
        fields =[
            "id",
            "more_than_order",
            "incentive_amount",
            "created_at"
        ]
    