from django.test import TestCase
from .models import UserProfile

class UserProfileModelTests(TestCase):

    def test_user_profile_must_be_associated_with_a_base_user_model(self):
        """user_profile contains foreign key for a base user model"""
        user = self.user.id
        self.assertIs(user, False)
