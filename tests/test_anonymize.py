from myskoda.anonymize import VEHICLE_NAME, LICENSE_PLATE, LOCATION, FORMATTED_ADDRESS, anonymize_widget


REAL_VIN = "TMBJN0NZ0ASDFGHJK"
REAL_LAT = 50.123456
REAL_LON = 18.654321


def make_widget_data() -> dict:
    return {
        "vehicle": {
            "name": "Skoda Superb",
            "licensePlate": "DW 12345",
            "renderUrl": f"https://skoda.com/render/{REAL_VIN}/image.png",
        },
        "parkingPosition": {
            "maps": {
                "lightMapUrl": f"https://maps.skoda.com/map?bar=11&latitude={REAL_LAT}&longitude={REAL_LON}&foo=15",
            },
            "gpsCoordinates": {"latitude": REAL_LAT, "longitude": REAL_LON},
            "formattedAddress": "ul. Prawdziwa 1, Wrocław, Poland",
        },
    }


class TestAnonymizeWidget:

    def test_vehicle_name_is_replaced(self):
        result = anonymize_widget(make_widget_data())
        assert result["vehicle"]["name"] == VEHICLE_NAME

    def test_license_plate_is_replaced(self):
        result = anonymize_widget(make_widget_data())
        assert result["vehicle"]["licensePlate"] == LICENSE_PLATE

    def test_render_url_vin_is_replaced(self):
        result = anonymize_widget(make_widget_data())
        assert REAL_VIN not in result["vehicle"]["renderUrl"]
        assert "TMOCKAA0AA000000" in result["vehicle"]["renderUrl"]

    def test_render_url_structure_is_preserved(self):
        result = anonymize_widget(make_widget_data())
        assert result["vehicle"]["renderUrl"].startswith("https://skoda.com/render/")
        assert result["vehicle"]["renderUrl"].endswith("/image.png")

    def test_light_map_url_coordinates_are_replaced(self):
        result = anonymize_widget(make_widget_data())
        assert f"latitude={REAL_LAT}&longitude={REAL_LON}" not in result["parkingPosition"]["maps"]["lightMapUrl"]
        assert f"latitude={LOCATION['latitude']}&longitude={LOCATION['longitude']}" in result["parkingPosition"]["maps"]["lightMapUrl"]

    def test_light_map_url_other_params_are_preserved(self):
        result = anonymize_widget(make_widget_data())
        assert "bar=11" in result["parkingPosition"]["maps"]["lightMapUrl"]
        assert "foo=15" in result["parkingPosition"]["maps"]["lightMapUrl"]

    def test_gps_coordinates_are_replaced(self):
        result = anonymize_widget(make_widget_data())
        assert result["parkingPosition"]["gpsCoordinates"] == LOCATION

    def test_formatted_address_is_replaced(self):
        result = anonymize_widget(make_widget_data())
        assert result["parkingPosition"]["formattedAddress"] == FORMATTED_ADDRESS
