from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario
from django.core.exceptions import ValidationError

class RegistroForm(UserCreationForm):
    """
    Formulario de registro de usuario personalizado
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu@email.com'
        }),
        label="Correo Electrónico"
    )
    
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Juan'
        }),
        label="Nombre"
    )
    
    last_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pérez'
        }),
        label="Apellido"
    )
    
    telefono = forms.CharField(
        required=True,
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(011) 1234-5678'
        }),
        label="Teléfono"
    )
    
    username = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre_usuario'
        }),
        label="Nombre de Usuario"
    )
    
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'minlength': '6'
        }),
        label="Contraseña"
    )
    
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'minlength': '6'
        }),
        label="Confirmar Contraseña"
    )
    
    terms = forms.BooleanField(
        required=True,
        label="Acepto los términos y condiciones",
        error_messages={'required': 'Debes aceptar los términos y condiciones'}
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'telefono', 'password1', 'password2')
    
    def clean_email(self):
        """Validar que el email no esté registrado"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_username(self):
        """Validar que el username no esté registrado"""
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username
    
    def save(self, commit=True):
        """Guardar usuario con los datos adicionales"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telefono = self.cleaned_data['telefono']
        
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """
    Formulario de login personalizado
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre_usuario o email',
            'autofocus': True
        }),
        label="Usuario o Email"
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        }),
        label="Contraseña"
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        label="Recordarme"
    )