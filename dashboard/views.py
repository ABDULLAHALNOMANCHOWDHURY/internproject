import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from catalog.models import Brand, Category, Product
from orders.models import Order, OrderItem
from user_management.models import SellerProfile, User

REVENUE_EXPR = ExpressionWrapper(
    F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=14, decimal_places=2)
)

PERIODS = ["all", "today", "week", "month"]


def _period_start(period):
    now = timezone.now()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return None  # "all"


def _top_grouped(relation_field, limit=2):
    """Returns {period: [{"name": ..., "total": Decimal}, ...]} ranking
    catalog.Category or catalog.Brand by revenue (quantity * unit_price)
    across sold order items, for every period tab."""
    result = {}
    for period in PERIODS:
        qs = OrderItem.objects.exclude(**{f"product__{relation_field}__isnull": True})
        start = _period_start(period)
        if start:
            qs = qs.filter(order__created_at__gte=start)
        rows = (
            qs.annotate(revenue=REVENUE_EXPR)
            .values(name=F(f"product__{relation_field}__name"))
            .annotate(total=Sum("revenue"))
            .order_by("-total")[:limit]
        )
        result[period] = [{"name": r["name"], "total": r["total"] or Decimal("0")} for r in rows]
    return result


@login_required
def home(request):
    now = timezone.now()

    # ---- Customers ------------------------------------------------------
    customers = User.objects.filter(user_type=User.UserType.CUSTOMER)
    top_customers = (
        Order.objects.exclude(status=Order.Status.CANCELLED)
        .values("customer__id", "customer__username", "customer__first_name", "customer__last_name")
        .annotate(spent=Sum("total_amount"))
        .order_by("-spent")[:3]
    )

    # ---- Products ---------------------------------------------------------
    products = Product.objects.all()
    inhouse_products = products.filter(is_inhouse=True).count()
    seller_products = products.filter(is_inhouse=False).count()

    # ---- Sales / Orders -----------------------------------------------
    live_orders = Order.objects.exclude(status=Order.Status.CANCELLED)
    total_sales = live_orders.count()
    total_orders = Order.objects.count()
    sales_this_month = live_orders.filter(
        created_at__year=now.year, created_at__month=now.month
    ).aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    inhouse_sales = (
        OrderItem.objects.filter(product__is_inhouse=True)
        .exclude(order__status=Order.Status.CANCELLED)
        .annotate(revenue=REVENUE_EXPR)
        .aggregate(total=Sum("revenue"))["total"]
        or Decimal("0")
    )
    seller_sales = (
        OrderItem.objects.filter(product__is_inhouse=False)
        .exclude(order__status=Order.Status.CANCELLED)
        .annotate(revenue=REVENUE_EXPR)
        .aggregate(total=Sum("revenue"))["total"]
        or Decimal("0")
    )

    # Yearly sales trend (this calendar year, in-house vs seller, by month)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_qs = (
        OrderItem.objects.filter(order__created_at__gte=year_start)
        .exclude(order__status=Order.Status.CANCELLED)
        .annotate(month=TruncMonth("order__created_at"), revenue=REVENUE_EXPR)
    )
    inhouse_by_month = {
        r["month"].strftime("%Y-%m"): r["total"]
        for r in monthly_qs.filter(product__is_inhouse=True).values("month").annotate(total=Sum("revenue"))
    }
    seller_by_month = {
        r["month"].strftime("%Y-%m"): r["total"]
        for r in monthly_qs.filter(product__is_inhouse=False).values("month").annotate(total=Sum("revenue"))
    }
    month_labels, inhouse_series, seller_series = [], [], []
    cursor = year_start.date()
    while cursor <= now.date():
        key = cursor.strftime("%Y-%m")
        month_labels.append(cursor.strftime("%b"))
        inhouse_series.append(float(inhouse_by_month.get(key, 0)))
        seller_series.append(float(seller_by_month.get(key, 0)))
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    # ---- Sellers ----------------------------------------------------------
    sellers = User.objects.filter(user_type=User.UserType.SELLER)
    pending_sellers = SellerProfile.objects.filter(approval_status=SellerProfile.ApprovalStatus.PENDING).count()
    approved_sellers = SellerProfile.objects.filter(approval_status=SellerProfile.ApprovalStatus.APPROVED).count()
    top_sellers = (
        OrderItem.objects.filter(product__is_inhouse=False)
        .exclude(order__status=Order.Status.CANCELLED)
        .annotate(revenue=REVENUE_EXPR)
        .values("product__seller__id", "product__seller__username")
        .annotate(total=Sum("revenue"))
        .order_by("-total")[:3]
    )

    # ---- Category / Brand rankings (by revenue, per period tab) -----------
    category_stats = _top_grouped("category")
    brand_stats = _top_grouped("brand")

    stats = {
        "total_customers": customers.count(),
        "total_products": products.count(),
        "inhouse_products": inhouse_products,
        "seller_products": seller_products,
        "total_sales": total_sales,
        "sales_this_month": sales_this_month,
        "inhouse_sales": inhouse_sales,
        "seller_sales": seller_sales,
        "total_sellers": sellers.count(),
        "pending_sellers": pending_sellers,
        "approved_sellers": approved_sellers,
        "total_categories": Category.objects.count(),
        "total_brands": Brand.objects.count(),
        "total_orders": total_orders,
        "orders_placed": total_orders,
    }

    from dashboard.context_processors import NOT_BUILT_MODULES

    return render(request, "dashboard/home.html", {
        "stats": stats,
        "top_customers": top_customers,
        "top_sellers": top_sellers,
        "category_stats_json": json.dumps(
            {p: [{"name": r["name"], "total": str(r["total"])} for r in rows] for p, rows in category_stats.items()}
        ),
        "brand_stats_json": json.dumps(
            {p: [{"name": r["name"], "total": str(r["total"])} for r in rows] for p, rows in brand_stats.items()}
        ),
        "category_stats_default": category_stats["all"],
        "brand_stats_default": brand_stats["all"],
        "month_labels": json.dumps(month_labels),
        "inhouse_series": json.dumps(inhouse_series),
        "seller_series": json.dumps(seller_series),
        "not_built": NOT_BUILT_MODULES,
    })
