NOT_BUILT_MODULES = [
    "POS System", "Products", "Notes", "Wholesale Products", "Sales",
    "Delivery Boy", "Refunds", "Uploaded Files", "Reports", "Blog System",
    "Marketing",
]


def sidebar_modules(request):
    return {"not_built_menu": NOT_BUILT_MODULES}
