from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib import messages
from django.http import HttpResponse
# import UserRegistrationForm class from forms.py
from .forms import UserRegistrationForm
# import LoginForm class from forms.py
from .forms import UserLoginForm  # Create this form
#import for customising reset pass
from django.contrib.auth.views import PasswordResetView
# import CustomPasswordResetForm class from forms.py
from .forms import CustomPasswordResetForm
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import Subscription, InvestmentPlan, Payment, Payout, FloatUser, Transaction, UserPaymentInfo, Notification
from .forms import SubscriptionForm
import random
import string
from datetime import timedelta
from django.db.models.functions import Coalesce
from django.db.models import F, Value, DecimalField

# Create your views here.
# Landing page
def index(request):
    return render(request, 'index.html')



# superadmin homepage or dashboard
def superadmin_dash(request):
    return render(request, 'superadmin_dashboard/home.html')


#register user
def register(request):
    # form = None  # Initialize the form variable
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            user.username = user.username.lower()  # Convert username to lowercase
            user.save()
            login(request, user)  # Log in the user after registration
            return redirect('user_dashboard')  # Redirect to a dashboard
        else:
            print(form.errors)  # Debugging: Print form errors to the console
    
    else:
        form = UserRegistrationForm(request=request)
    return render(request, 'registration/signup.html', {'form': form})

#login user
def signin(request):
    # This is to prevent a logged in user from accessing the login page
    if request.user.is_authenticated:
        # Redirect based on user role
        if request.user.role == 'super_admin':
            return redirect('superadmin_dashboard')
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')
    
    if request.method == 'POST':
        # I used data=request.POST so that empty fields won't sent that makes POST invalid
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].lower()  # Convert username to lowercase
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # messages.success(request,  f'Welcome back, {user.username}!')
                # Redirect based on role
                if user.role == 'super_admin':
                    return redirect('superadmin_dashboard')
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('user_dashboard')
            else:
                form.add_error(None, "Invalid username or password. Please try again.")
                # form.non_field_errors(None, "Invalid username or password.")
                # messages.error(request, 'Invalid username or password.')
        # else:
        #     messages.error(request, 'Please correct the errors below.')
            
    else: 
        # form = UserLoginForm(request.POST)
        form = UserLoginForm()

    return render(request, 'registration/signin.html', {'form': form})

# Utility function to generate unique random token
def generate_unique_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=15))


# ======== Admin Views Begins ==================
# admin homepage or dashboard
@login_required
def admin_dash(request):
    user = request.user
    
    # Subscription Stats
    pending_subscriptions_count = Subscription.objects.filter(status='pending').count()
    cancelled_subscriptions_count = Subscription.objects.filter(status='cancelled').count()
    completed_subscriptions_count = Subscription.objects.filter(status='completed').count()
    active_subscriptions_count = Subscription.objects.filter(status='active').count()

    # Payment Stats
    total_payments_count = Payment.objects.all().count()
    payments_by_me_count = Payment.objects.filter(performed_by=user).count()

    # Payout Stats
    total_payouts_count = Payout.objects.all().count()
    payouts_by_me_count = Payout.objects.filter(performed_by=user).count()
    all_completed_payouts_count = Payout.objects.filter(status='completed').count()
    all_pending_payouts_count = Payout.objects.filter(status='pending').count()

    # Todays Matured Subscriptions stats
    today_date = now().date()  # Extract only the date
    todays_matured_subscriptions_count = Subscription.objects.filter(maturity_date=today_date, status__in=['completed', 'active']).count()

    # All Matured Subscriptions before today uptill today stats
    all_matured_subscriptions_count = Subscription.objects.filter(maturity_date__lte=now(), status__in=['completed', 'active']).count()

    # Detailed Querysets
    pending_subscriptions = Subscription.objects.filter(status='pending')
    # Adds a computed field (maturity_amount) to each item in the matured_subscriptions queryset.
    all_matured_subscriptions = Subscription.objects.filter(maturity_date__lte=now(), status__in=['completed', 'active']).annotate(
    maturity_amount=Coalesce(F('amount_invested') * Value(2), Value(0), output_field=DecimalField()))
    today_matured_subscriptions = Subscription.objects.filter(maturity_date=today_date, status__in=['completed', 'active']).annotate(
    maturity_amount=Coalesce(F('amount_invested') * Value(2), Value(0), output_field=DecimalField()))
    payments_by_me = Payment.objects.filter(performed_by=user)
    my_messages = Notification.objects.filter(user=user, status='sent')
    pending_payouts_by_me = (
        Payout.objects.filter(performed_by=user, status='pending')
        .select_related('user')  # Optimize query by selecting related user
        .prefetch_related('user__userpaymentinfo_set')  # Prefetch user payment info
    )
    # Prepare response pending_payouts_by_me_with_account_info
    pending_payouts_by_me_with_account_info = []
    for payout in pending_payouts_by_me:
        user_payment_info = UserPaymentInfo.objects.filter(user=payout.user).first()
        pending_payouts_by_me_with_account_info.append({
            "payout_id": payout.id,
            "user_id": payout.user.id,
            "subscription_id": payout.subscription.id,
            "amount_paid": float(payout.amount_paid),
            "payout_date": payout.payout_date,
            "status": payout.status,
            "reference": payout.reference,
            "performed_by": payout.performed_by.id if payout.performed_by else None,
            "username": payout.user.username,
            "user_contact": payout.user.phone_number,
            "user_payment_info": {
                "account_number": user_payment_info.account_number if user_payment_info else None,
                "bank_name": user_payment_info.bank_name if user_payment_info else None,
                "account_name": user_payment_info.account_name if user_payment_info else None,
            } if user_payment_info else None,
        })

    context = {
        'pending_subscriptions_count': pending_subscriptions_count,
        'cancelled_subscriptions_count': cancelled_subscriptions_count,
        'completed_subscriptions_count': completed_subscriptions_count,
        'active_subscriptions_count': active_subscriptions_count,
        'total_payments_count': total_payments_count,
        'payments_by_me_count': payments_by_me_count,
        'total_payouts_count': total_payouts_count,
        'payouts_by_me_count': payouts_by_me_count,
        'all_completed_payouts_count': all_completed_payouts_count,
        'all_pending_payouts_count': all_pending_payouts_count,
        'todays_matured_subscriptions_count': todays_matured_subscriptions_count,
        'all_matured_subscriptions_count': all_matured_subscriptions_count,
        'pending_subscriptions': pending_subscriptions,
        'all_matured_subscriptions': all_matured_subscriptions,
        'today_matured_subscriptions': today_matured_subscriptions,
        'pending_payouts_by_me_with_account_info': pending_payouts_by_me_with_account_info,
        'payments_by_me': payments_by_me,
        'my_messages': my_messages,
    }

    return render(request, 'admin_dashboard/admin_home.html', context)

# admin activate user subscriptions
@login_required
def activate_subscription(request, subscription_user_id, subscription_id, amount_paid):
    # Get the logged-in user
    logged_in_user = request.user

    # Get the related user and subscription using url variables
    user_id = get_object_or_404(FloatUser, id=subscription_user_id)
    subscription = get_object_or_404(Subscription, id=subscription_id)
    investment_plan = subscription.plan  # Subscription has a ForeignKey to InvestmentPlan

    # set todays date as starting day
    starting_date = now().date()

    # Calculate maturity date based on selected plan
    # condition for kindergaten to secondary tuition support
    if investment_plan.name.lower() == 'tuition support a':
        #get user subscription month
        subscription_month = starting_date.month

        # Calculate maturity date based on month of plan activation
        if 2 <= subscription_month <= 6:  # February - June
            maturity_date = starting_date.replace(month=9, day=1)  # September 1st
        elif 7 <= subscription_month <= 10:  # July - October
            maturity_date = starting_date.replace(month=1, day=1, year=starting_date.year + 1)  # January 1st next year
        else:  # November - January
            # November - January, take payment to April next year
            if 11 <= subscription_month <= 12:  # February - June
                maturity_date = starting_date.replace(month=4, day=14, year=starting_date.year + 1)  # April 14 next year
            else: # January
                maturity_date = starting_date.replace(month=4, day=14)  # April 14th

    # condition for rent or university support
    elif investment_plan.name.lower() in ['rent support', 'tuition support b']:
        maturity_date = starting_date + timedelta(weeks=21)  # 5 months approx
    

    # Create a payment instance
    payment = Payment.objects.create(
        user=user_id,
        subscription=subscription,
        amount_paid=amount_paid,
        payment_method="bank deposit",  # You can dynamically set this based on your logic
        payment_status="successful",  # You can set this dynamically as well
        transaction_reference=f"PAYMENT_{now().strftime('%Y%m%d%H%M%S')}",
        performed_by=logged_in_user,
    )

    # create a Transaction instance
    transaction = Transaction.objects.create(
        user=user_id, 
        transaction_type="deposit",
        amount=amount_paid,
        status="completed",
        reference=f"TXN{now().strftime('%Y%m%d%H%M%S')}",
        performed_by=logged_in_user,
    )

    # ====== Update subscription details ======
    subscription.start_date = starting_date
    subscription.maturity_date = maturity_date
    subscription.status = "active"
    subscription.save()
    # ====== Update subscription details ======

    # Redirect back to the referrer page
    return redirect(request.META.get('HTTP_REFERER', '/'))

    # return redirect('user_subscriptions')

# admin creates payouts for matured subscription
@login_required
def payout_matured_subscriptions(request, user_id, subscription_id, amount_paid):
    # Get logged in user
    logged_in_user = request.user

    # Get the related user and subscription using url variables
    user_id = get_object_or_404(FloatUser, id=user_id)
    subscription = get_object_or_404(Subscription, id=subscription_id)
    amount_paid=float(amount_paid)*2
    investment_plan = subscription.plan  # Subscription has a ForeignKey to InvestmentPlan



    # Calculate next maturity date for kindergaten/secondary plan
    if investment_plan.name.lower() == 'tuition support a':
        #get user subscription maturity month from database
        current_maturity_date = subscription.maturity_date
        current_maturity_month = current_maturity_date.month
        current_payout_count = subscription.payout_count

        # Calculate next maturity date based on current maturity month of plan
        if current_payout_count != 3 and current_maturity_month == 9:  # September maturity
            maturity_date = current_maturity_date.replace(month=1, day=1, year=current_maturity_date.year + 1) #next years January            
        elif current_payout_count != 3 and current_maturity_month == 1:  # January maturity
            maturity_date = current_maturity_date.replace(month=4, day=14)  # April 
        elif current_payout_count != 3 and current_maturity_month == 4:  # April maturity
            maturity_date = current_maturity_date.replace(month=9, day=1)  # September 

        #add 1 to payout_count only after checking the current_payout_count
        current_payout_count += 1

        # Set the subscription to completed when payout_count is 3
        if current_payout_count == 3:
            subscription.status = "completed"
        else:   # update next payment date
            subscription.maturity_date = maturity_date
            # subscription.status = "active"

    # condition for rent or university support
    elif investment_plan.name.lower() in ['rent support', 'tuition support b']:
        current_payout_count += 1
        subscription.status = "completed"


    # Create a payout instance
    payment = Payout.objects.create(
        user=user_id,
        subscription=subscription,
        amount_paid=amount_paid,
        status="pending",  
        reference=f"PAYOUT_{now().strftime('%Y%m%d%H%M%S')}",
        performed_by=logged_in_user,
        
    )

    # Send notification to subscrj.li pup9l0u.ibing user

    # Update subscription details, set subscription to completed when payout record of such subscription is added
    subscription.payout_count = current_payout_count
    subscription.save()

    # redirect back to the referrer page
    return redirect(request.META.get('HTTP_REFERER', '/'))

# admin authorize payouts to user with matured subscription
@login_required
def authorize_payouts(request, payout_id, user_id, amount):
    logged_in_user = request.user

    # Get the related user and payout
    user_id = get_object_or_404(FloatUser, id=user_id)
    payout = get_object_or_404(Payout, id=payout_id)
    payout_amount = amount

    # create a Transaction instance
    transaction = Transaction.objects.create(
        user=user_id, 
        transaction_type="payout",
        amount=payout_amount,
        status="completed",
        reference=f"TXN{now().strftime('%Y%m%d%H%M%S')}",
        performed_by=logged_in_user,
    )

    # update payout status to completed
    payout.status = 'completed'
    payout.save()
    
    # redirect back to the referrer page
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ======== Admin Views ends ==================


# =============== User Views ==================
# user homepage or dashboard
@login_required
def home(request):
    user = request.user
    
    # Subscription Stats
    pending_subscriptions_count = Subscription.objects.filter(user=user, status='pending').count()
    cancelled_subscriptions_count = Subscription.objects.filter(user=user, status='cancelled').count()
    completed_subscriptions_count = Subscription.objects.filter(user=user, status='completed').count()
    active_subscriptions_count = Subscription.objects.filter(user=user, status='active').count()

    # Payment Stats
    failed_payments_count = Payment.objects.filter(user=user, payment_status='failed').count()
    successful_payments_count = Payment.objects.filter(user=user, payment_status='successful').count()

    # Payout Stats
    completed_payouts_count = Payout.objects.filter(user=user, status='completed').count()
    pending_payouts_count = Payout.objects.filter(user=user, status='pending').count()

    # All my subscriptions 
    subscriptions = Subscription.objects.filter(user=user)

    # All my Payments 
    payments = Payment.objects.filter(user=user)

    # All my Payouts
    payouts = Payout.objects.filter(user=user)

    # Get all user unread notifications
    my_messages = Notification.objects.filter(user=user, status='sent')

    context = {
        'pending_subscriptions_count': pending_subscriptions_count,
        'cancelled_subscriptions_count': cancelled_subscriptions_count,
        'completed_subscriptions_count': completed_subscriptions_count,
        'active_subscriptions_count': active_subscriptions_count,
        'failed_payments_count': failed_payments_count,
        'successful_payments_count': successful_payments_count,
        'completed_payouts_count': completed_payouts_count,
        'pending_payouts_count': pending_payouts_count,
        'subscriptions': subscriptions,
        'payments': payments,
        'payouts': payouts,
        'my_messages': my_messages,
    }

    return render(request, 'user_dashboard/home.html', context)


# subscribe user to plan only if the user is loggedin
@login_required
def subscribing(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)           
        if form.is_valid():
            subscription = form.save(commit=False)
            # Set additional fields
            subscription.user = request.user
            subscription.start_date = now().date()
            subscription.status = 'pending'
            subscription.sub_token = generate_unique_token()
            
            # Calculate maturity date based on selected plan
            # condition for kindergaten to secondary tuition support
            if subscription.plan.name.lower() == 'tuition support a':
                #get user subscription month
                subscription_month = subscription.start_date.month

                if 2 <= subscription_month <= 6:  # February - June
                    subscription.maturity_date = subscription.start_date.replace(month=9, day=1)  # September 1st
                elif 7 <= subscription_month <= 10:  # July - October
                    subscription.maturity_date = subscription.start_date.replace(month=1, day=1, year=subscription.start_date.year + 1)  # January 1st next year
                else:  # November - January
                    # November - January, take payment to April next year
                    if 11 <= subscription_month <= 12:  # February - June
                        subscription.maturity_date = subscription.start_date.replace(month=4, day=14, year=subscription.start_date.year + 1)  # April 14 next year
                    else: # January
                        subscription.maturity_date = subscription.start_date.replace(month=4, day=14)  # April 14th

            # condition for rent or university support
            elif subscription.plan.name.lower() in ['rent support', 'tuition support b']:
                subscription.maturity_date = subscription.start_date + timedelta(weeks=21)  # 5 months approx

            subscription.save()
            messages.success(request, "Subscription created successfully, click activate to pay and activate subscription.")
            return redirect('user_subscriptions')  # Redirect to a success page or dashboard
    else:
        form = SubscriptionForm()

    return render(request, 'user_dashboard/subscribe_plan.html', {'form': form})

# display user subscriptions
@login_required
def user_subscriptions(request):
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'user_dashboard/subscriptions.html', {'subscriptions': subscriptions})



# cancel_subscription
@login_required
def cancel_subscription(request, subscription_id):

    # Get the related subscription using url variables
    subscription = get_object_or_404(Subscription, id=subscription_id)

    # Update subscription details, set subscription to completed when payout record of such subscription is added
    subscription.status = "cancelled"
    subscription.save()


    # redirect back to the referrer page
    return redirect(request.META.get('HTTP_REFERER', '/'))














 





#Logout User
def user_logout(request):
    logout(request)
    return redirect('signin')  # Redirect to the login page after logout














#class base view for customising forgotten password
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    # form_class = CustomPasswordResetForm
    success_url = '/password_reset/done/'
