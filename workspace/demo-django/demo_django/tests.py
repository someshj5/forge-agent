from django.test import TestCase


class DemoProjectTest(TestCase):

    def test_demo_project(self):
        self.assertEqual(1 + 1, 2)