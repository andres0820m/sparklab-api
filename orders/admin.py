from django.contrib import admin
from .models import Order, AccountType, DocumentType, Bank


# Register your models here.

class AdminOrder(admin.ModelAdmin):
    list_filter = [
        "bank",
        "document_type",
    ]
    search_fields = (
        "bank",
        "document_type",

    )


admin.site.register(AccountType)
admin.site.register(DocumentType)
admin.site.register(Order, AdminOrder)
admin.site.register(Bank)
