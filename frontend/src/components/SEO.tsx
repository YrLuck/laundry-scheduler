import { useEffect } from 'react';

interface SEOProps {
  title?: string;
  description?: string;
  canonical?: string;
  ogImage?: string;
  noIndex?: boolean;
}

/**
 * Компонент для управления SEO мета-тегами.
 * Динамически обновляет title, description и другие мета-теги.
 */
const SEO: React.FC<SEOProps> = ({
  title = 'Laundry Scheduler - Система бронирования стиральных машин',
  description = 'Онлайн система бронирования стиральных машин и сушилок. Удобное расписание, управление бронированиями.',
  canonical,
  ogImage = '/og-image.jpg',
  noIndex = false,
}) => {
  useEffect(() => {
    // Обновляем title
    document.title = title;

    // Обновляем meta description
    let metaDescription = document.querySelector('meta[name="description"]');
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.setAttribute('name', 'description');
      document.head.appendChild(metaDescription);
    }
    metaDescription.setAttribute('content', description);

    // Обновляем canonical URL
    if (canonical) {
      let linkCanonical = document.querySelector('link[rel="canonical"]');
      if (!linkCanonical) {
        linkCanonical = document.createElement('link');
        linkCanonical.setAttribute('rel', 'canonical');
        document.head.appendChild(linkCanonical);
      }
      linkCanonical.setAttribute('href', canonical);
    }

    // Open Graph meta tags
    const ogTags = [
      { property: 'og:title', content: title },
      { property: 'og:description', content: description },
      { property: 'og:image', content: ogImage },
      { property: 'og:type', content: 'website' },
      { property: 'og:locale', content: 'ru_RU' },
    ];

    ogTags.forEach(({ property, content }) => {
      let metaTag = document.querySelector(`meta[property="${property}"]`);
      if (!metaTag) {
        metaTag = document.createElement('meta');
        metaTag.setAttribute('property', property);
        document.head.appendChild(metaTag);
      }
      metaTag.setAttribute('content', content);
    });

    // Twitter Card meta tags
    const twitterTags = [
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: title },
      { name: 'twitter:description', content: description },
      { name: 'twitter:image', content: ogImage },
    ];

    twitterTags.forEach(({ name, content }) => {
      let metaTag = document.querySelector(`meta[name="${name}"]`);
      if (!metaTag) {
        metaTag = document.createElement('meta');
        metaTag.setAttribute('name', name);
        document.head.appendChild(metaTag);
      }
      metaTag.setAttribute('content', content);
    });

    // Robots meta tag
    let metaRobots = document.querySelector('meta[name="robots"]');
    if (!metaRobots) {
      metaRobots = document.createElement('meta');
      metaRobots.setAttribute('name', 'robots');
      document.head.appendChild(metaRobots);
    }
    metaRobots.setAttribute('content', noIndex ? 'noindex, nofollow' : 'index, follow');

    // JSON-LD Schema.org
    const schemaScriptId = 'schema-org-json-ld';
    let schemaScript = document.getElementById(schemaScriptId);
    
    const schemaData = {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": title,
      "description": description,
      "url": window.location.href,
    };

    if (!schemaScript) {
      schemaScript = document.createElement('script');
      schemaScript.id = schemaScriptId;
      (schemaScript as HTMLScriptElement).type = 'application/ld+json';
      document.head.appendChild(schemaScript);
    }
    (schemaScript as HTMLScriptElement).text = JSON.stringify(schemaData);

    // Cleanup при размонтировании
    return () => {
      // Можно добавить очистку если нужно
    };
  }, [title, description, canonical, ogImage, noIndex]);

  return null; // Компонент не рендерит ничего видимого
};

export default SEO;
