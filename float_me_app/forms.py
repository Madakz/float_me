from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm
from django.utils.timezone import now
from .models import FloatUser, Subscription, InvestmentPlan, UserPaymentInfo

# User registration class for forms
class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(min_length=4, max_length=15, required=True, error_messages={
            'min_length': 'Username must be above 3 characters.',
            'max_length': 'Username must not exceed 15 characters.',
        })
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=FloatUser.ROLE_CHOICES)
    phone_number = forms.CharField(max_length=15, required=True, error_messages={
            'max_length': 'Phone number must not exceed 15 characters.',
        })
    address = forms.CharField(required=True, widget=forms.Textarea, error_messages={
            'required': 'Address is required.',
        })

    class Meta:
        model = FloatUser
        fields = ['username', 'email', 'role', 'phone_number', 'address', 'password1', 'password2']
        error_messages = {
            'username': {
                'required': 'Username is required.',
                'unique': 'This username is already taken.',
            },
            'email': {
                'required': 'Email is required.',
                'invalid': 'Enter a valid email address.',
            },
        }

    #Email validation to ensure email is unique
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if FloatUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def __init__(self, *args, **kwargs):
          # Extract the logged-in user (passed via kwargs)
        request = kwargs.pop('request', None)

        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        # Customize role choices based on logged-in user's role
        if request and request.user.is_authenticated:
            if request.user.is_superuser:
                # Superuser can assign both "admin" and "investor" roles
                self.fields['role'].choices = [
                    ('admin', 'Admin'),
                    ('investor', 'Investor'),
                ]
            elif request.user.role == 'admin':  # Replace with your admin role check
                # Admin can assign only the "investor" role
                self.fields['role'].choices = [
                    ('investor', 'Investor'),
                ]
        else:
            # Default for unauthenticated users (if required)
            self.fields['role'].choices = [
                ('investor', 'Investor'),
            ]
        
        # Remove labels and add placeholders
        for field_name, field in self.fields.items():
            field.label = ''  # Remove label
            field.widget.attrs.update({
                'placeholder': field_name.replace('_', ' ').capitalize(),  # Add placeholder
                'class': 'form-control',
            })
        
        # Customize placeholders for specific fields
        self.fields['password1'].widget.attrs['placeholder'] = 'Enter your password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm your password'


#  Login form class for forms
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'class': 'form-control',
        }),
        required=True
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control',
        }),
        required=True
    )

    # convert username to lower case
    def clean_username(self):
        return self.cleaned_data['username'].lower()

# password reset class for forgot password
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )

#create investment/subscription
class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['plan', 'amount_invested']

        widgets = {
            'plan': forms.Select(attrs={'class': 'form-control'}),
            'amount_invested': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'min': '50'  # Ensures positive input in HTML
            }),
        }

        help_texts = {
            'amount_invested': 'Enter a valid subscription amount.',
        }

        def clean_amount_invested(self):
            amount = self.cleaned_data.get('amount_invested')
            if amount <= 49.99:
                raise forms.ValidationError("Investment amount must be equal to or greater than 50")
            return amount
        
# Add Bank Account form
class BankAccountForm(forms.ModelForm):
    class Meta:
        model = UserPaymentInfo
        fields = ['account_number', 'bank_name', 'account_name']

        widgets = {
            'account_number': forms.NumberInput(attrs={'placeholder': 'Account Number','class': 'form-control',}),
            'bank_name': forms.TextInput(attrs={'placeholder': 'Bank Name', 'class': 'form-control'}),
            'account_name': forms.TextInput(attrs={'placeholder': 'Account Name', 'class': 'form-control'})
            
        }

        help_texts = {
            'account_number': 'Enter your confirmed bank account number',
            'bank_name': 'Enter your confirmed bank name',
            'account_name': 'Enter your confirmed account name',
        }

