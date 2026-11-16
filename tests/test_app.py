import re
import unittest
from decimal import Decimal

from werkzeug.security import generate_password_hash

from app import create_app, parse_csv, validate_product


class ProductValidationTests(unittest.TestCase):
    def test_valid_product_normalizes_optional_fields_and_price(self):
        product, errors = validate_product(
            {"sku": "  MUG-1 ", "name": " Mug ", "price": "12.5", "quantity": "3"}
        )
        self.assertEqual(errors, {})
        self.assertEqual(product["sku"], "MUG-1")
        self.assertEqual(product["category"], "")
        self.assertEqual(product["price"], Decimal("12.50"))
        self.assertEqual(product["quantity"], 3)

    def test_rejects_negative_price_and_non_integer_quantity(self):
        _, errors = validate_product(
            {"sku": "MUG-1", "name": "Mug", "price": "-1", "quantity": "1.5"}
        )
        self.assertIn("price", errors)
        self.assertIn("quantity", errors)

    def test_rejects_price_with_more_than_two_decimal_places(self):
        _, errors = validate_product(
            {"sku": "MUG-1", "name": "Mug", "price": "1.999", "quantity": "0"}
        )
        self.assertIn("price", errors)

    def test_csv_errors_prevent_partial_valid_rows_from_being_returned(self):
        content = "sku,name,price\nMUG-1,Mug,4.50\nMUG-2,,2.00\n"
        records, errors = parse_csv(content)
        self.assertEqual(records, [])
        self.assertTrue(any("Row 3" in error for error in errors))

    def test_csv_rejects_unknown_or_missing_headers(self):
        records, errors = parse_csv("sku,name,price,extra\nMUG-1,Mug,4.50,x\n")
        self.assertEqual(records, [])
        self.assertTrue(errors)

    def test_csv_rejects_rows_with_extra_columns(self):
        records, errors = parse_csv("sku,name,price\nMUG-1,Mug,4.50,unexpected\n")
        self.assertEqual(records, [])
        self.assertTrue(any("more columns" in error for error in errors))


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            DATABASE_URL="postgresql://unused",
            ADMIN_USERNAME="admin",
            ADMIN_PASSWORD_HASH=generate_password_hash("test-password"),
        )
        self.client = self.app.test_client()

    def test_login_requires_csrf_and_authenticates_with_configured_credentials(self):
        response = self.client.get("/login")
        token = re.search(rb'name="_csrf_token" value="([^"]+)"', response.data).group(1).decode()

        rejected = self.client.post(
            "/login", data={"username": "admin", "password": "test-password"}
        )
        self.assertEqual(rejected.status_code, 400)

        accepted = self.client.post(
            "/login",
            data={
                "_csrf_token": token,
                "username": "admin",
                "password": "test-password",
            },
        )
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(accepted.location, "/")

    def test_product_routes_require_login(self):
        response = self.client.get("/products/new")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)


if __name__ == "__main__":
    unittest.main()
