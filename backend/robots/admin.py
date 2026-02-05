from django.contrib import admin

from .models import RobotGroup, RobotComponent, RiskEvent


@admin.register(RobotGroup)
class RobotGroupAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "expected_total", "updated_at")
    search_fields = ("key", "name")


@admin.register(RobotComponent)
class RobotComponentAdmin(admin.ModelAdmin):
    list_display = (
        "robot",
        "shop",
        "reference",
        "type",
        "tech",
        "mark",
        "level",
        "a1",
        "a2",
        "a3",
        "a4",
        "a5",
        "a6",
        "a7",
        "updated_at",
    )
    list_filter = ("group", "shop", "level")
    search_fields = ("robot", "reference", "type", "tech", "remark")


@admin.register(RiskEvent)
class RiskEventAdmin(admin.ModelAdmin):
    list_display = ("robot_id", "severity", "status", "risk_score", "triggered_at", "updated_at")
    list_filter = ("group", "severity", "status")
    search_fields = ("robot_id", "robot_name", "message", "reason", "notes")

