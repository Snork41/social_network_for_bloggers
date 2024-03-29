from django.test import TestCase
from django.urls import reverse


class StaticPagesViewsTests(TestCase):

    def test_about_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени namespase:name, доступен."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)
