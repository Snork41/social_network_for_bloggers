from http import HTTPStatus

from django.test import TestCase


class StaticPagesURLTests(TestCase):

    def test_url_exists_at_desired_location(self):
        url = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for url_name, expected_code in url.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.client.get(url_name).status_code, expected_code
                )

    def test_url_uses_correct_template(self):
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)
