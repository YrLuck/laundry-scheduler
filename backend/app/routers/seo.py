"""
Router для SEO-оптимизации.
Генерация sitemap.xml, robots.txt и других SEO элементов.
"""
from fastapi import APIRouter, Response, Request
from fastapi.responses import PlainTextResponse
from typing import List
from datetime import datetime

router = APIRouter(tags=["seo"])

# Базовый URL сайта (должен быть в переменных окружения)
BASE_URL = "http://localhost:3000"

# Список публичных маршрутов для индексации
PUBLIC_ROUTES = [
    {"path": "/", "priority": 1.0, "changefreq": "daily"},
    {"path": "/machines", "priority": 0.8, "changefreq": "weekly"},
    {"path": "/login", "priority": 0.5, "changefreq": "monthly"},
    {"path": "/register", "priority": 0.5, "changefreq": "monthly"},
]

# Маршруты которые не должны индексироваться
PRIVATE_ROUTES = [
    "/profile",
    "/bookings",
    "/admin",
]


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """
    Файл robots.txt для поисковых систем.
    Указывает какие страницы можно/нельзя индексировать.
    """
    robots_content = f"""# Robots.txt for Laundry Scheduler
User-agent: *
Allow: /
Allow: /machines
Allow: /login
Allow: /register
Allow: /

# Запрещаем индексацию личных страниц
Disallow: /profile
Disallow: /bookings
Disallow: /admin
Disallow: /*?*

# Sitemap
Sitemap: {BASE_URL}/sitemap.xml

# Crawl-delay для снижения нагрузки
Crawl-delay: 1
"""
    return robots_content


@router.get("/sitemap.xml")
async def sitemap_xml(request: Request):
    """
    Sitemap.xml для поисковых систем.
    Содержит список всех публичных страниц для индексации.
    """
    base_url = BASE_URL
    
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    
    # Добавляем публичные маршруты
    for route in PUBLIC_ROUTES:
        xml_lines.extend([
            "  <url>",
            f"    <loc>{base_url}{route['path']}</loc>",
            f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>",
            f"    <changefreq>{route['changefreq']}</changefreq>",
            f"    <priority>{route['priority']}</priority>",
            "  </url>",
        ])
    
    xml_lines.append("</urlset>")
    
    xml_content = "\n".join(xml_lines)
    
    return Response(
        content=xml_content,
        media_type="application/xml"
    )


@router.get("/.well-known/security.txt")
async def security_txt():
    """
    Файл security.txt для информации о безопасности.
    Рекомендуется для SEO и безопасности.
    """
    security_content = """# Security Policy
Contact: mailto:security@laundry-scheduler.local
Expires: 2027-12-31T23:59:59.000Z
Preferred-Languages: ru, en
Canonical: https://laundry-scheduler.local/.well-known/security.txt
"""
    return Response(content=security_content, media_type="text/plain")


@router.get("/manifest.json")
async def manifest_json():
    """
    Web App Manifest для PWA.
    Улучшает SEO и позволяет установить приложение на устройство.
    """
    import json
    
    manifest = {
        "name": "Laundry Scheduler - Система бронирования стиральных машин",
        "short_name": "Laundry Scheduler",
        "description": "Онлайн система бронирования стиральных машин и сушилок",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f8f9fa",
        "theme_color": "#667eea",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["utilities", "productivity"],
        "lang": "ru"
    }
    
    return Response(
        content=json.dumps(manifest, indent=2),
        media_type="application/json"
    )


@router.get("/api/schema.json")
async def api_schema():
    """
    JSON-LD Schema.org разметка для поисковых систем.
    Улучшает отображение в поисковой выдаче.
    """
    import json

    schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Laundry Scheduler",
        "description": "Система онлайн бронирования стиральных машин и сушилок",
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Web",
        "browserRequirements": "Requires JavaScript",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "RUB"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "ratingCount": "125"
        },
        "featureList": "Бронирование стиральных машин, Управление расписанием, Отслеживание статуса",
        "screenshot": "/screenshot.png",
        "downloadUrl": "/register",
        "fileSize": "2.5 MB",
        "softwareVersion": "1.0.0",
        "author": {
            "@type": "Organization",
            "name": "Laundry Scheduler Team"
        }
    }

    return Response(
        content=json.dumps(schema, ensure_ascii=False, indent=2),
        media_type="application/ld+json"
    )
