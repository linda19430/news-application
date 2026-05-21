from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Article, Newsletter, User


class UserRegisterForm(UserCreationForm):
    """Registration form with role selection and duplicate email validation."""

    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["username", "email", "role", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class UserLoginForm(AuthenticationForm):
    """Login form using Django's built-in AuthenticationForm."""
    pass


class ArticleForm(forms.ModelForm):
    """Form for creating and editing articles."""

    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]


class NewsletterForm(forms.ModelForm):
    """Form for creating and editing newsletters."""

    class Meta:
        model = Newsletter
        fields = ["title", "description", "articles"]
