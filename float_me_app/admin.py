from django.contrib import admin
from .models import FloatUser, Role, Admin, InvestmentPlan, Subscription, Transaction, Payment, Payout, AuditLog, Notification


admin.site.register(FloatUser)
admin.site.register(Role)
admin.site.register(Admin)
admin.site.register(InvestmentPlan)
admin.site.register(Subscription)
admin.site.register(Transaction)
admin.site.register(Payment)
admin.site.register(Payout)
admin.site.register(AuditLog)
admin.site.register(Notification)



